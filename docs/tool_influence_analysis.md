# AnomalyClaw 工具实现机制与三工具对 VLM 判断影响分析

> 整理自 D1_0029 样本评估会话。涵盖 13 个 agent 工具的实现机制（Tier 1–5），
> 以及 `tool_side_by_side` / `tool_expert_score` / `tool_reference_profiler` 对 qwen3 VLM
> 判断影响的消融实验设计。所有源码位于 `benchmark/scripts/agent_tools_v8.py`（约 1221 行）。

---

## 0. 背景

- 目标：在 **不调用大语言模型** 的前提下，对 D1_0029 样本批量运行全部 13 个工具，
  以可视化方式对比各工具的 tool-use 效果（成功率 / 耗时 / 输出摘要 / 失败原因）。
- 后续目标：深入理解使用率最高的三个工具（`tool_side_by_side`、`tool_expert_score`、
  `tool_reference_profiler`）对 qwen3 VLM 判断的作用，通过消融实验量化其影响。

---

## 1. 公共基础设施

所有工具依赖两个 helper，理解它们即可理解返回格式约定。

### 1.1 `_pil_to_b64` — 图像压缩为 base64 JPEG

保证返回结果可直接嵌入 VLM 的多模态消息：

```python
def _pil_to_b64(img: Image.Image, max_side: int = 512, quality: int = 85) -> str:
    w, h = img.size
    if max(w, h) > max_side:
        scale = max_side / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
```

### 1.2 `_wrap_interpretation` — 主动输出反证条件

每个工具的返回 dict 都被附加 `interpretation` 字段，格式为
`"<verdict> DISCONFIRM: <disconfirm>"`。核心设计：不仅给 VLM 结论，
还**主动给出反证条件**，防止 VLM 过度信任单个工具。

```python
def _wrap_interpretation(obs: dict, verdict: str, disconfirm: str) -> dict:
    obs["interpretation"] = f"{verdict}\nDISCONFIRM: {disconfirm}"
    return obs
```

> 例：expert_score 判定 "LIKELY ANOMALY" 时，disconfirm 会说
> "如果该 bbox 区域在参考图里也有同样纹理，说明 expert 在过检正常变化——降低此分数"。

---

## 2. Tier 1：Expert Probe（1 个工具）

### 2.1 `tool_expert_score` — 域感知缓存专家分数 + 热图 + 建议 bbox

信息密度最高，但**不跑任何模型推理**——它读取预计算的 JSON 缓存。

**核心数据结构：**

```python
EXPERT_POLICY = {
    "D1":  {"expert": "subspacead", "auroc": 0.966, "available": True,  "status": "strong"},
    "D4":  {"available": False, "reason": "all experts <0.5 AUROC on 3D-render items"},
    # ... D1-D12 共 12 个域
}

EXPERT_RANGE_HINTS = {
    "D1":  {"p50": 37.36, "p70": 56.52, "normal_median": 20.00, "anomaly_median": 61.59},
    # ...
}
```

**执行流程：**
1. 从 ctx 取 `_manifest_domain`（如 "D1"），查 `EXPERT_POLICY` 判断该域是否有可用专家；
2. `expert="auto"` 时按 policy 自动选择（D1 → subspacead）；
3. 从 `benchmark/results/subspacead_test.json` 加载缓存，按 `item_id` 查到
   `anomaly_score` 和 `top_patches`；
4. 用 `np.searchsorted` 在该域排序分数数组中做百分位排名：

```python
dom_arr = _domain_score_percentiles(expert, split, dc)  # lru_cache 缓存
rank = float(np.searchsorted(dom_arr, s) / len(dom_arr))
```

5. 若有 `top_patches`（48×48 网格上的热点坐标），调用 `_expert_heatmap_and_bbox`
   生成热图叠加 + 建议裁剪框：

```python
def _expert_heatmap_and_bbox(query_path, top_patches, grid_size=48, target_side=256, pad_frac=0.2):
    # 在 48x48 网格上填入 patch 分数 → 归一化 → 双线性上采样到 256x256
    grid = np.zeros((grid_size, grid_size), dtype=np.float32)
    for r, c, s in valid:
        grid[r, c] = max(grid[r, c], s)
    grid = grid / grid.max()
    heat_img = Image.fromarray((grid * 255).astype(np.uint8), mode="L").resize(
        (target_side, target_side), resample=Image.BILINEAR)

    # 红色 alpha 叠加到 resize 后的 query 上
    q = Image.open(query_path).convert("RGB").resize((target_side, target_side))
    blended = q_arr * (1.0 - alpha * mask) + red * (alpha * mask)

    # top patches 的包围盒 → 映射到 256 坐标 → 加 pad_frac 边距
    bbox = [_m(c0, target_side), _m(r0, target_side), _m(c1, target_side), _m(r1, target_side)]
    return heat_b64, bbox
```

**返回**：`score_raw`, `rank_in_domain`, `range_hint`, `top_patches`,
`suggested_bbox_256`（可直接传给 `side_by_side` 或 `zoom_bbox`）, `heatmap_b64`。

**为什么快（~35ms）**：纯 JSON 查表 + numpy 排序，无 GPU 调用。
`_load_expert_scores` 和 `_domain_score_percentiles` 均有 `@lru_cache`。

---

## 3. Tier 2：Visual Inspection（6 个工具，纯 PIL/numpy）

### 3.1 `tool_hotspot_cropper` — 专家热点区域 query-vs-ref 同框对比

依赖 expert_score 的 `top_patches`。把 48×48 网格坐标映射回像素坐标，
对 query 和每张 ref 在**相同 bbox** 处裁剪拼成横向 composite：

```python
x0, x1 = int(c0 / grid * W), int(c1 / grid * W)
y0, y1 = int(r0 / grid * H), int(r1 / grid * H)

def _crop_one(path):
    im = Image.open(path).convert("RGB").resize((W, H))
    return im.crop((x0, y0, x1, y1)).resize((tile_side, tile_side))

tiles = [("query", _crop_one(query_path))]
for i, rp in enumerate((ref_paths or [])[:3]):
    tiles.append((f"ref{i}", _crop_one(rp)))
composite = Image.new("RGB", (total_w, tile_side + 18), (255, 255, 255))
```

**意图**：把 expert 的数值热点转化为直接视觉证据——query 和 ref 同位置并排，
VLM 可一眼看出 query 独有特征。

### 3.2 `tool_zoom_bbox` — Agent 指定区域放大裁剪

最简单工具——接受像素坐标 `[x0, y0, x1, y1]`，裁剪后返回 b64：

```python
def tool_zoom_bbox(query_path: str, bbox: list[int], **_) -> dict:
    x0, y0, x1, y1 = bbox
    img = Image.open(query_path).convert("RGB")
    crop = img.crop((x0, y0, x1, y1))
    return {"bbox": [x0, y0, x1, y1], "crop_b64": _pil_to_b64(crop), ...}
```

用于 VLM 在 overview 上看到可疑区域后主动放大检查。

### 3.3 `tool_patch_grid` — 规则网格切分

把图像切成 `rows×cols`（最多 3×3）个 tile，每 tile 返回独立 b64：

```python
rows = min(rows, 3)  # 最多 3x3
for i in range(rows):
    for j in range(cols):
        x0, y0 = j * tw, i * th
        x1 = (j + 1) * tw if j < cols - 1 else W  # 最后一列吃到边界
        crop = img.crop((x0, y0, x1, y1))
        tiles.append({"cell": [i, j], "bbox": [x0, y0, x1, y1],
                      "crop_b64": _pil_to_b64(crop, max_side=256)})
```

**用途**：当 agent 没有候选 bbox 时，用网格切分系统扫描，找与其他 tile 明显不同的一块。

### 3.4 `tool_image_diff` — 像素级差异 + mask（域门控）

对 query 和 ref resize 到 256×256 后逐像素求差，生成 diff mask：

```python
ALIGNED_DOMAINS = {"D1", "D5", "D3"}  # 只有对齐域才能用

def tool_image_diff(query_path, ref_path, threshold=30.0, _manifest_domain=None, **_):
    if _manifest_domain and _manifest_domain not in ALIGNED_DOMAINS:
        return {"error": "image_diff not applicable to ..."}
    q = np.array(Image.open(query_path).convert("RGB").resize((256, 256)))
    r = np.array(Image.open(ref_path).convert("RGB").resize((256, 256)))
    diff = np.abs(q.astype(float) - r.astype(float)).mean(axis=2)  # 灰度差
    mask = (diff > threshold).astype(np.uint8) * 255
    change_pct = float(mask.mean() / 255 * 100)
    unreliable = (mean_diff > 40.0) or (change_pct > 45.0)
```

**关键设计**：`unreliable_alignment` 标志——若 mean_diff > 40 或 change_pct > 45%，
说明 query 和 ref 根本没对齐（不同实例/视角），diff mask 是噪声而非缺陷。
此时 interpretation 明确说 "DO NOT use this tool's output as evidence"。

### 3.5 `tool_rotate_align` — 旋转容限对齐 diff

与 image_diff 类似，但在 ±10° 范围搜索最佳旋转角后再做 diff：

```python
for angle in [-10, -5, 0, 5, 10]:
    r_rot = np.array(r_img.rotate(angle, resample=Image.BILINEAR))
    d = np.abs(q.astype(float) - r_rot.astype(float)).mean(axis=2)
    mse = float(d.mean())
    if mse < best_mse:
        best_mse, best_angle, best_diff = mse, angle, d
```

**适用场景**：MVTec 工业件有轻微旋转抖动（±10°），先对齐再 diff 消除旋转噪声。
同样受 `ALIGNED_DOMAINS` 门控。

### 3.6 `tool_side_by_side` — query 裁剪 + 多 ref 裁剪横向拼图

与 hotspot_cropper 类似，但 bbox 由 agent 指定（256 归一化坐标），最多拼 4 张 ref：

```python
def _crop(path):
    img = Image.open(path).convert("RGB").resize((256, 256))
    return img.crop((xa, ya, xb, yb)).resize((128, 128))

crops = [_crop(query_path)] + [_crop(p) for p in ref_paths[:4]]
total_w = 128 * len(crops)
composite = Image.new("RGB", (total_w, 128), (255, 255, 255))
```

**与 hotspot_cropper 的区别**：hotspot_cropper 的 bbox 来自 expert 的 top_patches（自动），
side_by_side 的 bbox 来自 agent 判断（手动），且 side_by_side 可在非对齐域使用
（只做视觉对比，不做 pixel diff）。

---

## 4. Tier 3：Reference Understanding（2 个工具）

### 4.1 `tool_reference_profiler` — VLM 描述正常基线（需要 LLM）

**需要 LLM 的两个工具之一**。把 4 张参考图发给 VLM，用结构化 prompt 提取正常性画像：

```python
PROFILER_SYSTEM = (
    "You are describing NORMAL reference images for anomaly detection. Output ONLY "
    "what normal looks like. Return JSON with these EXACT fields:\n"
    "  object: the main object/scene content\n"
    "  expected_color: 2-3 dominant colors\n"
    "  expected_shape: overall geometric/structural pattern\n"
    "  allowed_variation: list 2-4 variations that are NORMAL across refs"
)

def tool_reference_profiler(ref_paths, vlm_client=None, vlm_model=None, **_):
    if vlm_client is None or vlm_model is None:
        return {"error": "vlm_client and vlm_model required"}
    parts = [text_msg(PROFILER_SYSTEM)]
    for p in ref_paths[:4]:
        parts.append(img_msg(load_and_encode(p)))
    text, _, _ = call_llm(vlm_client, vlm_model, messages, ...)
    parsed = extract_json(text) or {}
```

**返回**：`object`, `expected_color`, `expected_shape`, `allowed_variation`。
后续 agent 拿 query 对比此基线——若 query 差异属于 `allowed_variation` 项，则属正常而非异常。

### 4.2 `tool_reference_retriever` — DINOv2 语义检索 top-k 参考图

唯一需要 GPU 推理的纯 CV 工具。用 DINOv2 ViT 编码 query，与预计算域内 embedding 库
做余弦相似度检索：

```python
def _load_retrieval_model_v6(device="cuda"):
    model = timm.create_model("vit_small_patch14_dinov2.lvd142m",
                              pretrained=True, num_classes=0)
    model = model.to(device).eval()
    cfg = timm.data.resolve_data_config(model.pretrained_cfg)
    transform = timm.data.create_transform(**cfg, is_training=False)
    return model, transform

def tool_reference_retriever(query_path, domain_code, k=4, ...):
    model, transform = _load_retrieval_model_v6(device)
    tensor = transform(img).unsqueeze(0).to(device)
    with torch.no_grad():
        emb = model(tensor).cpu().numpy().flatten()
    emb = emb / (np.linalg.norm(emb) + 1e-8)              # L2 归一化
    data = np.load(f"{domain_code}_index.npz", allow_pickle=True)
    sims = data["embeddings"] @ emb                       # 点积 = 余弦相似度
    top_idx = np.argsort(sims)[::-1][:k]
    for r in results[:4]:
        rim = Image.open(r["path"]).convert("RGB")
        retrieved_b64.append(_pil_to_b64(rim, max_side=256))
```

**关键设计**：
- 索引为预计算 `.npz` 文件（`embeddings` + `paths`），每域一个（如 `D1_index.npz`）；
- v8 改进是**返回实际图片**（b64）而非只有路径——VLM 下一轮可直接看到检索到的参考图；
- 检索结果可喂给 `side_by_side` 的 `ref_paths`，形成工具链。

---

## 5. Tier 4：Structural Analysis（3 个工具）

### 5.1 `tool_component_counter` — 连通域分析 + blob 可视化

分析 expert 的 top_patches 在 48×48 网格上形成几个连通域（4-邻接 flood fill）：

```python
grid = np.zeros((48, 48), dtype=np.int32)
for p in patches:
    grid[r, c] = 1

label = np.zeros_like(grid)
n = 0
for i in range(48):
    for j in range(48):
        if grid[i, j] and not label[i, j]:
            n += 1
            stack = [(i, j)]
            while stack:
                ii, jj = stack.pop()
                if (0 <= ii < 48 and 0 <= jj < 48 and grid[ii, jj] and not label[ii, jj]):
                    label[ii, jj] = n
                    stack.extend([(ii+1, jj), (ii-1, jj), (ii, jj+1), (ii, jj-1)])
```

**判断逻辑**：
- `n == 1`：单个连通 blob → 典型局部缺陷信号；
- `n <= 3`：中度集中 → 检查最大 blob；
- `n > 3`：分散散布 → 常是纹理噪声导致的误报。

v8 生成彩色 blob 可视化（不同连通域不同颜色），叠加到 query：

```python
palette = np.array([[0,0,0], [255,80,80], [80,170,255], ...])
grid_rgb = palette[label % len(palette)]
grid_img = Image.fromarray(grid_rgb).resize((256, 256), resample=Image.NEAREST)
```

### 5.2 `tool_segment_and_count` — 8×8 粗粒度变化热图

把 query 和 ref[0] resize 到 256×256，按 8×8 网格取均值后做差：

```python
cell = 256 // grid_size  # 32
q_grid = q.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))  # 8x8 均值
r_grid = r.reshape(grid_size, cell, grid_size, cell).mean(axis=(1, 3))
diff = np.abs(q_grid - r_grid)
changed = int((diff > 20).sum())

heat = Image.fromarray((norm * 255).astype(np.uint8), mode="L").resize(
    (256, 256), resample=Image.NEAREST)

top_idx = np.argsort(diff.ravel())[::-1][:5]
for i in top_idx:
    bbox = [cc * cell, rr * cell, (cc+1) * cell, (rr+1) * cell]
    top_cells.append({"row": rr, "col": cc, "diff": round(v, 1), "bbox_256": bbox})
```

**用途**：agent 还没有候选 bbox 时，给"哪里最不同"的粗定位，top-5 cells 的 bbox 可传
`side_by_side` 精检。

### 5.3 `tool_texture_fft` — 频域周期性分析 + 频谱图

对 query 做 2D FFT，计算周期性分数（top-10 频率分量能量占比）：

```python
img = np.array(Image.open(query_path).convert("L").resize((256, 256))).astype(float)
img -= img.mean()
spec = np.abs(np.fft.fftshift(np.fft.fft2(img)))
spec_vis[cy - 3:cy + 3, cx - 3:cx + 3] = 0   # 抹掉 DC 附近

total = float(spec_vis.sum()) + 1e-8
top_k = float(np.sort(spec_vis.ravel())[::-1][:10].sum())
periodicity = min(1.0, max(0.0, top_k / total))

if ref_paths:
    rspec = np.abs(np.fft.fftshift(np.fft.fft2(ri)))
    ref_periodicity = round(min(1.0, max(0.0, rtop / rtot)), 3)
```

**判断逻辑**：若 ref 周期性高但 query 周期性低（delta > 0.08），说明 query 中有东西
**打断了原本规则纹理**——典型场景是混凝土裂纹（D6）破坏骨料周期模式。
v8 还返回 `log-magnitude` 频谱图供 VLM 直接观察亮峰。

---

## 6. Tier 5：Semantic Knowledge（1 个工具）

### 6.1 `tool_domain_knowledge` — LLM 视觉线索释义查询（需要 LLM）

**第二个需要 LLM 的工具**。当 agent 在图像中看到视觉特征但不确定含义时
（良性伪影还是红旗信号），用纯文本查询 LLM：

```python
KNOWLEDGE_SYSTEM = (
    "You are a visual-cue lookup assistant for anomaly detection. "
    "The agent has already SEEN a specific visual feature and wants to "
    "know what that feature MEANS. Give concrete visual criteria in "
    "2-4 sentences. Return JSON: {\"answer\": \"...\"}."
)

def tool_domain_knowledge(question, llm_client=None, llm_model=None, **_):
    messages = [
        {"role": "system", "content": KNOWLEDGE_SYSTEM},
        {"role": "user", "content": question},
    ]
    text, _, _ = call_llm(client, model, messages, max_tokens=300, temperature=0.0)
    parsed = extract_json(text) or {}
    return {"error": None, "answer": parsed.get("answer", text.strip()[:300])}
```

**关键约束**：prompt 强制 agent 描述**具体视觉特征**而非泛泛领域知识。好例子：
"在皮肤镜下，一个深色均匀棕色、边界光滑规则的痣是良性还是恶性？"；坏例子："什么是黑色素瘤？"

---

## 7. 调度器 `dispatch_tool` 与安全设计

所有 13 个工具通过统一调度器调用。核心设计是 **PROTECTED_CTX_KEYS**：

```python
PROTECTED_CTX_KEYS = (
    "query_path", "ref_paths", "item_id", "split",
    "vlm_client", "vlm_model", "llm_client", "llm_model",
    "_expert_patches", "_manifest_domain", "index_dir",
)

def dispatch_tool(name, args, ctx=None):
    injected = {k: v for k, v in args.items() if k not in PROTECTED_CTX_KEYS}
    for k in PROTECTED_CTX_KEYS:
        if k in ctx:
            injected[k] = ctx[k]
    return fn(**injected)
```

**安全意图**：防止 VLM 通过构造恶意参数把工具重定向到其他 item/split，或注入假
`_manifest_domain` 绕过域门控。`query_path`、`ref_paths`、`_manifest_domain` 等敏感字段
永远从 session ctx 取，VLM 无法覆盖。

---

## 8. 工具间的数据流链条

工具不是孤立的，形成数据流水线：

```
expert_score → 输出 top_patches + suggested_bbox_256
    ├→ hotspot_cropper(patches=...)    用 expert 的 patches 裁剪
    ├→ component_counter(patches=...) 用 expert 的 patches 做连通域
    ├→ side_by_side(bbox=suggested_bbox_256)  用 expert 的 bbox 做对比
    └→ zoom_bbox(bbox=suggested_bbox_256)     用 expert 的 bbox 放大

reference_retriever → 输出 retrieved_images_b64 + paths
    └→ side_by_side(ref_paths=retrieved_paths)  用检索到的图做对比

segment_and_count → 输出 top_cells[].bbox_256
    └→ side_by_side(bbox=top_cell.bbox_256)  用粗定位的 bbox 做精检
```

expert_score 仅 35ms 却是信息量最大的工具——一跳即可驱动下游 4 个工具的后续调用。

---

## 9. 三工具对 qwen3 VLM 判断影响的消融实验设计

脚本：`exp_tool_influence.py`。直接调用 `agent_v12.run_v12_item`（AD 模式），
唯一变量是**哪些工具可用**。

### 9.1 实验条件（ablation）

| 条件 | 可用工具 | 度量什么 |
|---|---|---|
| `none` | 无 | 纯视觉基线（VLM 只看 query + refs） |
| `expert_score` | 仅数值专家 | 分数/域内排名/热图如何改变判断 |
| `side_by_side` | 仅同框对比 | 裁剪对比图如何改变判断 |
| `reference_profiler` | 仅正常画像 | 结构化正常性描述如何改变判断 |
| `except_expert` | 仅没有数值专家 | 在没有数据先验情况下如何判断 |

被禁用的工具不会静默失败——dispatcher 返回显式 "ablation gate" 错误观测，VLM 看到后
必须自己调整策略。**被拒绝的调用尝试本身也是重要数据**：VLM 在没有 expert bbox 时
会不会想调 side_by_side？

### 9.2 插桩实现

- **对话记录**：patch `agent_v9.call_llm`，捕获每轮发给 VLM 的完整消息
  （图像按 md5 去重存为 PNG 文件引用）；
- **VLM 思考记录**：默认开启 thinking，捕获 qwen3 的 `reasoning_content`
  （带 extra_body 三种变体回退链，后端不兼容时自动降级并标记 `thinking_captured: false`）；
  同时保存每轮 action JSON 里的 `thought` / `visual_evidence` 字段；
- **工具调用记录**：patch `agent_tools_v8.dispatch_tool`，记录参数 / 观测 / 耗时 / 产出图像；
- **省成本设计**：Direct 分支（无 agent 的 run_v0）每 item 只调一次，跨 5 个条件缓存复用
  （temperature=0 确定性），作为稳定"无工具锚点"。

### 9.3 产出结构（需保存的五类数据）

```
output/tool_influence/D1_0029/
├── none/ ... all_three/        每条件 5 类数据:
│   ├── conversation.json       时序转录：VLM调用 ↔ 工具调用交错
│   ├── llm_calls/call_NN.json  消息增量 + thinking + 响应 + token
│   ├── tool_calls/*.json       参数 + 观测 + 图像清单
│   ├── images/*.png            热图/裁剪图等（去重）
│   └── result.json             最终判断 + 理由 + 分数轨迹
├── comparison.html             5 条件对比看板（分数条 / 判断对错 / Δ vs baseline / 逐轮思考折叠面板 / 图像）
└── summary_item.json
```
