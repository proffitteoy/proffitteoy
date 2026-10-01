# Public Seed Inventory

本表只列公开仓库和公开上游贡献。私有仓库故意不在公开 profile 仓库中列出。

| Source | 第一批要抽取的资产 | 初始去向 |
| --- | --- | --- |
| `proffitteoy/Topp` | exact PD matching、adaptive routing、benchmark protocol、prepared/batch interface | research / maintain |
| `GUDHI/gudhi-devel #1367` | exact Bottleneck 对称性反例、multi_augment 正确性修复 | upstream |
| `GUDHI/gudhi-devel #1371` | product early-termination criterion 候选理论 | research / upstream |
| `Aequiludium/cocycle-rs` | safe-Rust exact distances、F₂/H₁ optimization、Execution contract、performance negative results | research / upstream |
| `Aequiludium/polars-tda` | DataFrame→TDA expression contract、diagram schema、真实性能边界 | maintain / research |
| `gduf-community/topoquant` | persistence-diagram workload、pivot pruning、mmap sharing、真实下游性能需求 | application oracle |
| `proffitteoy/TILO-PRC` | TILO ordering、PinchRatio、图实验工具、理论审判对象 | research |
| `proffitteoy/early-rumor-propagation-tda` | 多窗口传播树数据管线、MCBI、拓扑特征负增益结果 | archive / negative result |
| `proffitteoy/CNN-for-Ani` | 小数据多来源评估、可恢复训练、ONNX 多平台模型资产 | maintain / benchmark |
| `open-ani/animeko #3172` | 从模型仓库到真实多平台上游部署的完整迁移链 | upstream |
| `proffitteoy/TraceTutor` | evidence-gated state transition、工具权限边界 | architecture |
| `gduf-community/ManiMind` | planner-worker-review-finalize 编排与 artifact review | architecture |
| `proffitteoy/Task-Manager` | 本地优先科研活动记录、研究工作流 telemetry | maintain |
| `GDUF-QUANTLAB/alpha-lab` | 量化研究 workload / Polars consumer 需求 | downstream |
| `GDUF-QUANTLAB/ygo` | 并发任务与进度生命周期 | implementation |

## 首批 cross-project recombination

### R1. Topp + cocycle-rs + polars-tda + topoquant

目标：形成从算法、kernel、DataFrame API 到真实 workload 的一条完整 performance/evidence chain。

最小实验：同一组 persistence diagrams / point clouds 在四层记录 preparation、kernel、whole-pipeline 与 batch throughput。

Kill：若不同层无法共享输入语义或测量边界，拆开报告，不强行宣称全栈 speedup。

### R2. TraceTutor + mathematical claim ledger

把 `pending state delta + evidence gate` 迁移到数学 claim 状态机：

[
	ext{PROPOSED}
	o
	ext{FINITE_VERIFIED}
	o
	ext{PROVED}
	o
	ext{FORMALIZED}.
]

这是 AI 数学系统实验的核心资产。

### R3. ManiMind review orchestration + mathematical artifacts

把 planner / worker / reviewer / finalize 从动画 artifact 替换为 lemma / proof / counterexample / formal proof artifact，测试多 agent 是否降低 false-proof acceptance。

### R4. TILO-PRC + finite-universe methodology

对小图进行 exact enumeration，采用和 homology finite-universe 相同的 claim ledger / counterexample minimization 方法，给 TILO 做 kill-or-revive。

### R5. Negative-result registry + future agent planning

所有新研究任务启动前先检索 negative assets；如果已存在同 scope 的失败实验，必须说明新方案改变了哪个假设，否则不重复消耗算力。
