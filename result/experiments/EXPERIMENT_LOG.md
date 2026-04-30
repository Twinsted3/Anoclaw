# AnomalyClaw 实验日志

## 实验配置

- **主 VLM 后端**: GPT-5.4 (sub2api, localhost:8080)
- **辅助 VLM**: doubao-seed-2-0-lite-260215 (Volcano Engine), Qwen3.5-27B, Qwen2.5-VL-7B
- **评测数据**: D1-D12, 1418 test items (60 normal + 60 anomalous per domain, D7=98)
- **评测指标**: Image-level AUROC, Macro AUROC (12 domains 均值)
- **Expert backbone**: DINOv2 ViT-S/14 (timm)
- **随机种子**: 42
- **图片预处理**: 长边 resize 到 512px

---

## 一、文档要求 (EXPERIMENT_BRIDGE_GUIDE.md)

### Table 3: Main Results — 9 methods, SeedVL 后端

| # | 方法 | 类别 | 说明 |
|---|------|------|------|
| 1 | CLIP-ZeroShot | Expert-only | CLIP ViT-B/16, "normal/defective" prompt |
| 2 | WinCLIP | Expert-only | 官方实现或复现 |
| 3 | PatchCore Expert | Expert-only | DINOv2 patch kNN, k=4, top-1% |
| 4 | VLM-Direct | Single-pass VLM | 仅 query 图, 无 reference |
| 5 | Retrieval+VLM | Single-pass VLM | DINOv2 CLS 检索 + VLM |
| 6 | Expert-Informed VLM | Single-pass VLM | Patch+Retrieval 文本证据 + 单次 VLM |
| 7 | AgentIAD | Multi-round | 复现其迭代 tool-calling 策略 |
| 8 | Symmetric Debate | Multi-round | 两个相同 VLM agent 对称辩论, 无 expert |
| 9 | AnomalyClaw (ours) | Multi-round | 完整系统: 非对称辩论 + expert pool + controller |

### Table 4: Debate Ablation — 5 configs, SeedVL

| # | Config | Expert | Debate |
|---|--------|--------|--------|
| 1 | Single-pass, no expert | None | No |
| 2 | Single-pass, with expert | Patch+Retrieval | No |
| 3 | Symmetric debate, no expert | None | Symmetric |
| 4 | Symmetric debate, with expert | Patch+Retrieval | Symmetric |
| 5 | AnomalyClaw (asymmetric) | Patch+Retrieval | Asymmetric |

### Table 5: Expert Pool Ablation — 5 configs, SeedVL, asymmetric debate

| # | Config | Experts |
|---|--------|---------|
| 1 | Debate only | None |
| 2 | Retrieval only | Retrieval |
| 3 | Patch only | Patch |
| 4 | Patch + Retrieval | Patch + Retrieval |
| 5 | All experts | Patch + Retrieval + Texture |

### Table 6: Depth Ablation — 4 configs, SeedVL

| D_max | 报告 |
|-------|------|
| 1 | AUROC + avg VLM calls |
| 2 | AUROC + avg VLM calls |
| 3 | AUROC + avg VLM calls |
| 4 | AUROC + avg VLM calls |

### Table 7: Multi-VLM — 3+ VLMs

每个 VLM 跑 VLM-Direct + AnomalyClaw:
- GPT-4o
- GPT-5.4 (或其他)
- 至少一个开源 VLM

---

## 二、已完成实验及结果

### 2.0 已有的 GPT-5.4 实验 (benchmark/results/v4/, agent_infer_v4.py)

**这些是之前已经跑好的主实验，使用 GPT-5.4 + sub2api**，domain 用旧编码 (D5b=Brain, D5c=Liver, D5d=GI, D6=Remote, D8=Surveillance(dropped))。

| # | 方法 (v4文件名) | Macro AUROC | 说明 |
|---|----------------|------------|------|
| 1 | DINOv2 Global (dinov2_global_test) | 0.628 | CLS token 检索 |
| 2 | DINOv2 Patch (dinov2_patch_test) | 0.635 | PatchCore-style kNN |
| 3 | Expert Only (expert_only_test) | **0.795** | Patch+Retrieval expert, 无VLM |
| 4 | Expert-Informed VLM (expert_informed_test) | **0.832** | Expert 文本 + 单次 VLM |
| 5 | Expert+VLM (expert_vlm_test) | 0.806 | Expert + VLM 判断 |
| 6 | Agent Full (agent_test) | 0.809 | 完整 agent 流程 |
| 7 | Knowledge-Informed (ablation) | 0.826 | domain knowledge 注入 |
| 8 | Ret+Knowledge (ablation) | 0.814 | retrieval + knowledge |
| 9 | Cal-Tuned Fusion (reproduced) | **0.882** | 校准后的融合方法 |

Domain 映射 (旧→新): D1→D1, D2→D2, D10→D3, D4→D4, D9→D5, D6→D7, D5→D8, D5b→D9, D5c→D10, D5d→D11, D7→D12, D8→dropped

Per-domain (新编码, 11/12域, 缺D6 Real3D-AD):
```
Method                 MVTec Goods  VisA SDNET  LOCO LEVIR  Derm Brain Liver    GI  Road  Macro
Expert Only            0.960 0.905 0.874 0.743 0.699 0.502 0.738 0.913 0.718 0.760 1.000 0.801
Expert-Informed VLM    0.968 0.888 0.906 0.748 0.796 0.561 0.848 0.975 0.716 0.922 1.000 0.848
Expert+VLM             0.963 0.914 0.893 0.739 0.777 0.502 0.738 0.928 0.725 0.760 1.000 0.813
Agent (Full)           0.968 0.908 0.900 0.740 0.795 0.502 0.736 0.929 0.735 0.760 1.000 0.816
DINOv2 Global          0.755 0.626 0.659 0.785 0.619 0.440 0.642 0.521 0.460 0.464 1.000 0.634
DINOv2 Patch           0.690 0.617 0.603 0.800 0.617 0.438 0.605 0.517 0.678 0.482 0.998 0.640
```

### 2.05 GPT-5.4 补全实验 (2026-04-08)

用 agent_infer_v4.py + sub2api GPT-5.4 补跑了:
1. **VLM-Direct baseline (12域, 1298+120 items)** → Macro AUROC = 0.790
2. **D6 (Real3D-AD) 全部方法** → 所有方法 ~0.55-0.56 (接近随机，渲染点云困难)

完整 GPT-5.4 主实验 (12域):
```
Method                 MVTec Goods  VisA SDNET  LOCO Real3D LEVIR  Derm Brain Liver    GI  Road  Macro
VLM-Direct             0.958 0.785 0.880 0.677 0.738 0.559 0.594 0.812 0.930 0.627 0.924 0.993 0.790
Expert Only            0.960 0.905 0.874 0.743 0.699 0.559 0.502 0.738 0.913 0.718 0.760 1.000 0.781
Expert-Informed VLM    0.968 0.888 0.906 0.748 0.796 0.548 0.561 0.848 0.975 0.716 0.922 1.000 0.823
Expert+VLM             0.963 0.914 0.893 0.739 0.777 0.560 0.502 0.738 0.928 0.725 0.760 1.000 0.792
Agent (Full)           0.968 0.908 0.900 0.740 0.795 0.560 0.502 0.736 0.929 0.735 0.760 1.000 0.794
```

### 2.1 新跑的实验 (run_experiments_async.py, SeedVL 后端)

| # | 方法 | Macro AUROC | 状态 | 备注 |
|---|------|------------|------|------|
| 1 | CLIP-ZeroShot | 0.540 | ✅ | openai/clip-vit-base-patch16, 新12域 |
| 2 | WinCLIP | — | ❌ 未做 | |
| 3 | PatchCore Expert | 0.780 | ✅ | 新12域 |
| 4 | VLM-Direct | 0.646 | ✅ | SeedVL, 新12域 |
| 5 | Retrieval+VLM | 0.624 | ✅ | SeedVL |
| 6 | Expert-Informed VLM | 0.751 | ✅ | SeedVL |
| 7 | AgentIAD | — | ❌ 未做 | |
| 8 | Symmetric Debate | 0.674 | ⚠️ | 实现可能不准确 |
| 9 | AnomalyClaw (ours) | 0.575 | ⚠️ | SeedVL, 评分机制有问题 |

### 2.2 Table 4-6 进展

全部 ❌ 未做。

### 2.3 Table 7: Multi-VLM 进展

| VLM | VLM-Direct | AnomalyClaw | 状态 |
|-----|-----------|-------------|------|
| GPT-5.4 | (v4已有) | (v4已有) | ✅ 主实验已有 |
| SeedVL (Seed2.0-Lite) | 0.646 | 0.575 | ✅ |
| GPT-4o | 0.638 | 0.703 (1411/1418) | ⚠️ |
| Qwen3.5-27B-FP8 | 0.641 | ⏳ 744/1418 | 跑着 |
| Qwen2.5-VL-7B | 0.533 | 0.573 | ✅ |

额外跑了:
- Expert+VLM SeedVL: 0.751
- Expert+VLM GPT-4o: 0.790

---

## 三、问题记录

### 问题 1: AnomalyClaw SeedVL AUROC 偏低 (0.575)

**现象**: AnomalyClaw (0.575) 显著低于 Expert+VLM (0.751) 和 VLM-Direct (0.646)

**原因分析**:
- Advocate 角色在 Seed2.0-Lite 上过于激进，对真实异常也能找到反驳理由
- refute_confidence 普遍在 0.4-0.6 区间，导致评分公式 `claim_conf × (1 - refute_conf)` 将大多数分数压到 0.2-0.4
- 弱模型的置信度校准差，无法有效区分真假异常

**影响**: Table 3 中 AnomalyClaw 不是最优方法；但 GPT-4o 上 AnomalyClaw (0.703) > VLM-Direct (0.638)，说明辩论机制在强模型上有效。

**待修复**:
- [ ] 调整评分公式，减轻 Advocate 的惩罚力度
- [ ] 或者在 Advocate prompt 中降低攻击性
- [ ] 或者引入 claim 数量/类型作为辅助特征

### 问题 2: Symmetric Debate 实现不准确

**文档要求**: "Two identical VLM agents debating (same prompt, no Proposer/Advocate roles, **no expert evidence**)"

**实际实现**: 
- ✅ 两个相同 agent, 无角色区分
- ✅ 无 expert evidence
- ⚠️ 但 Agent B 看到了 Agent A 的完整输出（包含 reference 图），更像是 review 而非对称辩论
- 结果 0.674，高于 VLM-Direct (0.646)，低于 Expert+VLM (0.751)

### 问题 3: 评分函数经历了两版

**V1 (已废弃)**: 基于 verdict 的离散映射
- anomaly → max(0.6, claim_conf)
- normal → claim_conf × 0.3 或 0.1
- uncertain → 0.5
- 问题: 太离散，大量样本聚在 0.1 和 0.7

**V2 (当前)**: 连续评分
- score = max(claim_conf × (1 - refute_conf)) 对所有 claim
- 无 claim → 0.05
- 问题: Advocate 过于激进时，所有分数被压低

### 问题 4: GPT-4o sub2api 不稳定

sub2api 在 4/6 晚间曾宕机约 2 小时，导致 GPT-4o AnomalyClaw 有 530 个 error。
后续 resume 补回到 1411/1418，剩余 7 个始终失败。

---

## 四、改进记录

### 改进 1: 同步 → 异步并行 (2026-04-06 18:48)

**问题**: `run_experiments.py` 顺序执行 VLM 调用，VLM-Direct 1418 items 需要 ~2.8 小时

**方案**: 创建 `run_experiments_async.py`，用 asyncio + semaphore 控制并发

**效果**: VLM-Direct 从 0.14 items/s → 1.14 items/s (8x)

### 改进 2: Balanced sampling (2026-04-06 18:45)

**问题**: `max_per_domain` 只取前 N 项，全是 normal，导致 AUROC=NaN

**方案**: 分层采样 (50% normal + 50% anomalous)

### 改进 3: 评分函数 V2 (2026-04-06 21:05)

见问题 3。

### 改进 4: Qwen3.5 单独 venv (2026-04-06 21:42)

**问题**: Qwen3.5 model_type `qwen3_5` 需要 transformers>=5.x，但 vLLM 0.8.5 不兼容

**方案**: 创建 `.venv_qwen35/`，安装 vLLM 0.19.0 + transformers 5.x

**端口**: vLLM 服务在 localhost:8001

---

## 五、代码文件清单

| 文件 | 用途 |
|------|------|
| `run_experiments.py` | 同步实验 runner (用于 PatchCore, CLIP 等本地方法) |
| `run_experiments_async.py` | 异步并行 runner (用于 VLM 方法) |
| `aggregate_results.py` | 结果聚合和表格生成 |
| `result/experiments/*_detail.jsonl` | 逐样本结果 (item_id, domain, label, score) |
| `result/experiments/*_results.json` | 实验汇总 (macro/micro AUROC, per-domain) |

---

## 六、待办

### 优先级 1 (必须)
- [ ] 修复 AnomalyClaw 评分机制 → 使 SeedVL 上 AnomalyClaw > Expert+VLM
- [ ] 修正 Symmetric Debate 实现 (严格无 expert)
- [ ] 实现 WinCLIP baseline
- [ ] 实现 AgentIAD baseline (或说明为何省略)

### 优先级 2 (Ablation)
- [ ] Table 4: Debate Ablation (5 configs, SeedVL)
- [ ] Table 5: Expert Pool Ablation (5 configs, SeedVL)
- [ ] Table 6: Depth Ablation (4 configs, SeedVL)

### 优先级 3 (Multi-VLM)
- [ ] 完成 Qwen3.5 AnomalyClaw
- [ ] GPT-4o AnomalyClaw 补齐最后 7 项
- [ ] 考虑是否跑 GPT-5.4 (文档提到)
