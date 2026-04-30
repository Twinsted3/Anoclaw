# AnomaClaw Agent System V2: Tool-Augmented Agent Loop

**Date**: 2026-04-04
**Source**: Team meeting notes + experiment insights

## 从 V1 (固定流程) 到 V2 (Agent Loop)

### V1 的问题
- 固定流程: Profile → Scout → Judge，不管什么域都走一样的路径
- 没有检索: refs 是 manifest 里预选的，不是动态检索的
- 缺乏领域知识: VLM 不知道"黑色素瘤长什么样"，只能和 refs 比
- 效率低: 每次都跑 3 个 API call，简单案例也不例外

### V2 核心设计

```
┌─────────────────────────────────────┐
│           Main Agent (MLLM)          │
│  职责: 推理、调度、整合             │
│  能力: Reasoning + Action            │
│                                      │
│  Loop: Prompt → Think → Tool → Parse │
│        → Think → Tool → ... → Answer │
└───────────┬─────────────────────────┘
            │ 调用
    ┌───────┼───────┬──────────┐
    ▼       ▼       ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│Visual│ │Domain│ │Expert│ │Reference │
│Retri-│ │Know- │ │Model │ │Comparison│
│eval  │ │ledge │ │(SOTA)│ │          │
└──────┘ └──────┘ └──────┘ └──────────┘
```

## Tool 定义

### Tool 1: Visual Retrieval (视觉检索)
```
功能: 给定 query 图片，从 normal image bank 中检索 Top-K 最相似的参考图
实现: ViT embedding + cosine similarity
输入: query_image, image_bank, k=4
输出: [ref_image_1, ref_image_2, ..., ref_image_k], similarity_scores
无需训练: 使用 DINOv2/CLIP 的预训练 embedding
```

### Tool 2: Domain Knowledge (领域知识检索)
```
功能: 检索与当前域/类别相关的异常描述和判断标准
实现: 本地知识库 (爬取维基百科 + 领域文档)
输入: domain_name, category, query_description
输出: relevant_knowledge_text
示例: 
  input: "skin lesion", "melanoma"
  output: "ABCDE criteria for melanoma: Asymmetry, Border irregularity, 
           Color variation, Diameter >6mm, Evolving..."
```

### Tool 3: Expert Model (专家模型调用)
```
功能: 调用特定域的 SOTA 异常检测模型获取异常分数
实现: 封装预训练模型为 API (PatchCore, WinCLIP, etc.)
输入: query_image, ref_images
输出: anomaly_score, anomaly_map (heatmap)
无需训练: 使用 few-shot 或 zero-shot AD 模型
```

### Tool 4: Reference Comparison (参考比较)
```
功能: 详细比较 query 和 refs 的视觉差异
实现: VLM 调用 (当前的 Scout 功能)
输入: query_image, ref_images, context
输出: differences_list
```

## Agent Loop 流程

```python
def agent_loop(query_image, domain_code, max_rounds=3):
    # Round 1: 检索参考图 + 初始判断
    refs = tool_visual_retrieval(query_image, domain_code, k=4)
    initial_judgment = main_agent.think(query_image, refs)
    
    if initial_judgment.confidence > 0.9:
        return initial_judgment  # 简单案例，直接返回
    
    # Round 2: 需要更多信息
    if initial_judgment.needs_knowledge:
        knowledge = tool_domain_knowledge(domain_code, initial_judgment.category)
        refined = main_agent.think(query_image, refs, knowledge)
    
    if initial_judgment.needs_expert:
        expert_score = tool_expert_model(query_image, refs)
        refined = main_agent.think(query_image, refs, expert_score)
    
    # Round 3: 不确定时，换参考图重试
    if refined.confidence < 0.6:
        new_refs = tool_visual_retrieval(query_image, domain_code, k=4, exclude=refs)
        final = main_agent.think(query_image, new_refs, knowledge)
    
    return final
```

## Baseline 重新定义

| 方法 | 检索 | 知识 | 专家 | 多轮 | 定义 |
|------|------|------|------|------|------|
| **V0 Baseline** | ❌ 随机 refs | ❌ | ❌ | ❌ | 当前 baseline，不含任何 tool |
| **V0 + Retrieval** | ✅ | ❌ | ❌ | ❌ | 只加检索 |
| **Agent (ours)** | ✅ | ✅ | ✅ | ✅ | 完整 agent loop |
| **Agent - Knowledge** | ✅ | ❌ | ✅ | ✅ | 去掉知识 (ablation) |
| **Agent - Expert** | ✅ | ✅ | ❌ | ✅ | 去掉专家 (ablation) |

## 实现优先级

1. **Visual Retrieval Tool** — 最关键，直接影响所有域的 baseline
   - 用 DINOv2 提取 embedding
   - 构建每个域的 normal image bank (train set)
   - 检索 Top-4 最相似的 refs
   
2. **Domain Knowledge Tool** — 对医学域影响最大
   - 构建本地知识库: 异常类型描述、判断标准
   - D5: ABCDE melanoma criteria
   - D5b: brain tumor MRI characteristics
   - D5c: liver tumor CT features
   
3. **Expert Model Tool** — 增强难域
   - 封装 WinCLIP (zero-shot, 无需训练)
   - 或用 PatchCore (few-shot)
   
4. **Agent Loop** — 整合所有 tool 的调度逻辑

## 与现有实验的关系

现有的 V0 baseline test set 结果仍然有效 — 它就是"不含任何 tool"的 baseline。
新的实验矩阵在这个 baseline 之上叠加 tool。
