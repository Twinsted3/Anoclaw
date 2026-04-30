# Task: Migrate §4 Main Results from v1 test to manifests_v2 test

> Handoff prompt for a new Claude conversation. Copy the content below the
> separator into the new conversation as your first message. Edit anything
> in `{braces}` or flagged TODO before sending.

---

## 先读这 3 个文件再开始
1. `RESUME.md` — 项目整体状态
2. `review-stage/AUTO_REVIEW.md` — 已完成 3 轮 codex review，Round 3 @ 6.4/10 "almost"
3. `paper/sections/4_experiments.tex` — 当前 §4 内容和表格结构

## 背景（别重复问）

- **CrossDomainVAD-11 有两个版本的 manifest**，§4 当前用 v1，§5 已切换到 v2
- `benchmark/manifests/D*_manifest.json` = v1（12 codes 含 D5a/b/c/d 子切分 + D8 Avenue surveillance）
- `benchmark/manifests_v2/D*_manifest.json` = **v2（12 codes 干净命名 D1–D12，加入 Real3D-AD 作 D6，加入 DermaMNIST 作独立 D8，删除 Avenue）**
- 两版 test 各 1418 items，但**除 D1/D2 外 items 基本不同**（同源数据集的不同采样）
- 问题：§4 还在 v1 上跑，§5 在 v2 上，审稿人会问为什么不统一
- 决策：**§4 全面迁移到 manifests_v2**

## v2 vs v1 域对照（按 source dataset）

| v2 | source | v1 对应 |
|---|---|---|
| D1 | MVTec-AD | v1 D1 |
| D2 | GoodsAD | v1 D2 |
| D3 | VisA | v1 D10 |
| D4 | SDNET2018 | v1 D4 |
| D5 | MVTec-LOCO | v1 D9 |
| **D6** | **Real3D-AD** | **新（v1 无）** |
| D7 | LEVIR-CD+ | v1 D6 |
| **D8** | **DermaMNIST** | v1 D5（和 BraTS 混用），现独立 |
| D9 | BraTS2021 | v1 D5b |
| D10 | BMAD-Liver | v1 D5c |
| D11 | HyperKvasir | v1 D5d |
| D12 | BDD100K + RoadAnomaly21 | v1 D7 |

## 具体任务

### A. 需要重跑的 §4 实验（按优先级）

1. **3 个 backbone × Direct 在 v2 test**（Qwen3.5-VL-27B / GPT-5.4 / SeedVL）
2. **3 个 backbone × Agent 在 v2 test**（v6.5 on Qwen3.5+SeedVL, v6.6 self-ensemble on GPT-5.4）
3. **v6+Direct ensemble（macro AUROC） + bootstrap CI + P(Δ>0)**
4. Per-domain 主表重算、bias 报告、score-diversity ablation（可延后）

### B. 已有资源（不用白白重跑）

- `benchmark/scripts/agent_v9.py` 接受 `--manifest` + `--split test` + `--backend {gpt,seedvl,qwen3}`
- `benchmark/scripts/agent_v6.py` / `agent_v6_5.py` / `agent_v6_6.py` 同样的 CLI
- `benchmark/results/verbalized/passive_dev/` 已有 v9 在 v2 **dev** 上的结果（§5 副产品，可能不是你要的但可参考）
- `benchmark/results/verbalized/passive_test/` **§5 正在跑** Passive v9 在 v2 test 上（主对话启动，预计 ~13:30 完成）。**你可以等它跑完再合并，或者自己再跑**

### C. 环境 / 基础设施（已就绪，不要关）

- **vLLM for Qwen3.5**：4 replica 在 GPU 0/1/2/7 运行，外挂 LB 在 port 8210
- `export QWEN_API_BASE=http://localhost:8210/v1 QWEN_MODEL=Qwen3.5-VL-27B QWEN_API_KEY=EMPTY`
- **GPT-5.4**：sub2api 在 `http://localhost:8080`，`GPT_MODEL=gpt-5.4`
- **SeedVL**：远程 API，用 `doubao-seed-2-0-lite-260215`

## 重要约束（不要破坏）

1. ⚠️ **不要杀当前运行的 `run_passive_test_all.sh`（PID 1909730 左右）** —— 它是 §5 baseline 的一部分，后面主对话要用
2. ⚠️ **不要动 `paper/sections/verbalized.tex`**（§5 的内容）
3. ⚠️ **不要关 vLLM replicas**（4 个 vllm + 1 个 LB）
4. ⚠️ **不要 commit** —— 先跑完实验、对齐数字、等主对话 review 后再 commit
5. 保留 `benchmark/results/*` 原有 v1 结果文件（别删）；新结果写到 `benchmark/results/v2/` 或带 `_v2` 后缀的文件名

## 建议的产出

- `benchmark/results/v2/v6_direct_{qwen3,gpt,seedvl}_test.json`
- `benchmark/results/v2/v6_5_agent_qwen3_test.json`
- `benchmark/results/v2/v6_6_agent_gpt_test.json`
- `benchmark/results/v2/v6_agent_seedvl_test.json`
- `paper/sections/4_experiments.tex` 新版（或先并存为 `paper/sections/4_experiments_v2.tex`）
- 一份 migration report 写入 `refine-logs/v2_migration_report.md`，含：
  - 旧数字 vs 新数字 per-domain diff
  - bootstrap CI 的变化
  - 3 个 backbone 的 macro Δ 新值
  - 哪些 §4 的 finding 仍然成立、哪些需要修改

## 补一个开放问题

v2 D6 Real3D-AD 是全新的 3D 工业 AD 域，v1 没有对应。你要决定：
- 是否需要为 D6 单独构建 descriptor-router 和 calibration-router 规则
- 是否纳入 main table 还是放 appendix
- 如何用 n=1418（v2 total 和 v1 相同但 items 变了）保持论文 narrative 一致

## 工作流建议

1. Read files, verify environment（`curl http://localhost:8210/v1/models` 应返回 `Qwen3.5-VL-27B`）
2. 小烟雾测试：拿 D1 + Qwen3.5 + Direct 跑 10 items，确认输出格式和 v1 兼容
3. 按 backbone 并发跑 Direct（Qwen3.5 在 LB，GPT 和 SeedVL 直连 API），大概 1–2h
4. 跑 Agent（v6.5 / v6.6），大概 3–5h per backbone
5. 算 ensemble、bootstrap CI，补表格
6. 写 migration report
7. 回主对话汇报

不要擅自改 v1 已提交的数字 / 已发表 claim；只产出 v2 版本供选择。
