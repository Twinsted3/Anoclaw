# Future Paper: Multi-Component Industrial Anomaly Detection via Agent Orchestration

**Status**: Idea stage, not started
**Source**: Discussion on 2026-04-01

## Core Idea

工业检测不只是"一张图有没有异常"，而是一套结构化质检流程。LLM 作为 controller 根据中间结果动态编排多步检测。重要的是可以结合现有的异常检测模型。

## Multi-Step Inspection Pipeline

```
整板图像
├── 整体检测：大面积缺陷（变形、烧焦）
├── 分割部件：SAM/DINO 切出每个元器件
├── 计数：电容/电阻数量是否正确
├── 连接关系：焊点走线是否正确（图结构/拓扑）
├── 部件级检测：每个元器件单独做异常检测
├── 异常分类：虚焊/冷焊/桥接/缺件
└── 诊断报告：LLM 汇总所有结果
```

步骤间有**依赖关系和条件分支**：
- 整体检测 pass → 不需要细查
- 计数发现缺件 → 直接报缺件，不需要部件级检测
- 部件检测出异常 → 才需要分类异常类型

## 类比 Claude Code 的 Tool Architecture

| Claude Code | IAD Agent |
|---|---|
| FileReadTool | GlobalInspector（整体检测） |
| SearchTool | ComponentSegmentor（分割定位部件） |
| BashTool | PartDetector（部件级检测） |
| AgentTool（子agent） | 对每个部件派子agent并行检测 |

## 学术空白

| 现有工作 | 做了什么 | 缺什么 |
|---------|---------|--------|
| ComAD/CSAD | Component-aware, 固定pipeline | 没有LLM agent动态编排 |
| AgentIAD | Single agent + 2 tools | Tool少，编排简单 |
| AD-Copilot | MLLM comparison | 没有多步编排 |

**空白**: MLLM-driven 多步工业检测 agent，根据中间结果动态编排

## 适合的数据集

- MVTec-LOCO (逻辑异常：缺件、多件、错误组装)
- MVTec-AD (基础的纹理+结构异常)
- VisA (主要测多物体和复杂物体)
- 可能需要自建复杂装配数据集

## 相关文献

- ComAD: Component-aware AD (ScienceDirect)
- AgentIAD: Tool-Augmented Single-Agent (arXiv 2512.13671)
- VisProg/ViperGPT: Visual Programming
- VipAct: Specialized VLM Agent Collaboration (AAAI 2026)
- PyVision: Self-generated Python tools for visual reasoning (NeurIPS 2025)
