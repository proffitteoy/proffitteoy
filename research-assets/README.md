# Research Asset Archaeology

本目录把“旧仓库复盘”改造成跨仓库资产提取工程。

目标不是给每个 repository 写总结，而是拆掉 repository 边界，把过去产生的算法、定理、数据、benchmark、状态机、负结果和实验协议抽成可重组的 Research Asset。

## 核心原则

仓库不是研究资产的最小单位。

一个旧项目可能同时包含：

- 一个值得独立维护的算法；
- 一套以后仍能复用的 benchmark protocol；
- 一个已经证伪的研究方向；
- 一份真实数据集；
- 一种 provenance / state-transition 设计；
- 一段可以迁移到其他研究线的高质量工程基础设施。

因此中央索引使用 Asset 而不是 Repository 作为记录单位。

## Asset 类型

首版统一使用以下类型：

- `theorem`：已证明数学结论；
- `conjecture`：仍开放、量词明确的候选命题；
- `algorithm`：可独立描述的算法或优化；
- `implementation`：有复用价值的工程实现；
- `dataset`：可合法复用的数据或 fixture；
- `benchmark`：可重放的性能/正确性实验协议；
- `oracle`：独立正确性判据或对拍实现；
- `negative_result`：已明确失败、无增益或存在反例的方向；
- `architecture`：可迁移的状态机、provenance、agent/workflow 结构；
- `literature_map`：已完成的系统文献对照；
- `upstream_contribution`：已经进入外部主线的实质贡献。

Schema 见 [schema.json](schema.json)。

## 三层考古流程

### A. Repository excavation

每个仓库由独立 agent 读取：

- README / docs；
- 关键源码；
- tests；
- issues / PR；
- benchmark；
- 历史失败实验。

只回答：

1. 有哪些可独立抽出的 asset？
2. 每个 asset 的证据在哪里？
3. 哪些结果实际上已经失败或不值得继续？
4. 哪些东西可迁移到别的项目？

不得把“仓库功能列表”当作考古结果。

### B. Asset normalization

第二层 agent 不再看仓库整体，只处理 asset record：

- 合并重复资产；
- 区分概念与实现；
- 区分正结果与负结果；
- 标记成熟度；
- 建 dependency / reuse edges；
- 检查是否存在未经证实的宣传性 claim。

### C. Cross-project recombination

第三层只看资产图，寻找原仓库之间不存在的组合。

候选组合必须写成：

[
A+B\longrightarrow\text{new research question}
]

并说明：

- 为什么原项目没有直接覆盖；
- 需要什么最小实验；
- 成功/失败怎样判定；
- 是否值得建立新仓库。

## 成熟度

统一等级：

- `L0 IDEA`：只有想法；
- `L1 PROTOTYPE`：有代码或局部推导；
- `L2 VERIFIED`：有可复现实验/精确证据；
- `L3 RESEARCH`：有明确数学/科学 claim 与边界；
- `L4 PUBLISHED_OR_UPSTREAM`：论文发表、正式发布或外部上游接受。

成熟度高不等于研究价值高；负结果也可以达到 L2/L3。

## 特别重要：Negative Result Registry

失败结果必须保留。

例如：

[
\text{“减少一次复制”}\not\Rightarrow\text{“端到端一定更快”},
]

或者某一特征组在公平 baseline 下没有稳定增益。

这类结果必须成为可查询 asset，避免未来 agent 因为不知道历史，再次建议已经失败的路线。

## 隐私边界

这个索引位于公开 profile repository。

因此：

- 这里只提交公开仓库、公开上游贡献以及可公开的抽象资产；
- 私有仓库名称、路径、数据和未公开研究结果不进入本目录；
- 私有仓库可以使用同一 schema 做本地/私有考古，但只有经过显式公开审查的 asset 才进入本索引。

## 第一批公开考古对象

见 [PUBLIC_SEED.md](PUBLIC_SEED.md)。

优先级按“过去投入较多 + 已出现独立资产 + 有跨项目复用可能”选择，不按 star 排名。

## 完成标准

第一轮不是“所有仓库都有一段总结”，而是：

- 至少 30 个规范化 asset；
- 至少 10 个 `negative_result`；
- 至少 10 条跨仓库 reuse edge；
- 至少 5 个 cross-project recombination proposal；
- 每个 proposal 都有最小实验和 kill 条件；
- 明确一份 archive / maintain / research / upstream 四类去向表。

如果一个旧仓库只能产出“做过一个网站/模型”的描述，没有独立算法、数据、协议、负结果或架构资产，则不强行保留。
