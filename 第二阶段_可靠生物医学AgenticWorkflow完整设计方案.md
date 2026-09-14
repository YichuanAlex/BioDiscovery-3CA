# 第二阶段：可靠生物医学科学发现 Agentic Workflow 完整设计方案

版本：v0.1（研究与工程设计稿）  
日期：2026-09-11  
适用范围：公开癌症组学数据，重点为单细胞转录组、肿瘤内细胞状态、代谢通路、T 细胞状态与可选 TCR/克隆信息；后续可迁移到受控的 BKI/Ludwig 数据，但本稿不使用或外发未授权内部数据。

---

## 0. 执行结论

第二阶段不应先建设一个“很多 agent 自由对话”的大系统。对本项目最可靠、也最容易被第一阶段 benchmark 检验的最小架构是：

> **类型化状态机 + 版本化领域 skills + 白名单工具 + 隔离执行环境 + 分层验证器 + claim-level 证据账本 + 人类审批门。**

其中：

- 状态机规定哪些步骤不得跳过，负责控制流程；
- skill 编码领域专家实际采用的判断规则、入口条件、输出契约、验证方法和停止条件；
- Python、R、Scanpy、Bioconductor、统计模型、数据库 API 等只是工具，不承担科学裁决；
- 确定性程序先检查数据、统计和文件，再让 LLM 解释；
- Reviewer 使用与分析者隔离的上下文，对计划、结果和结论分别审核；
- 任何结论必须指向数据工件和文献证据，且允许 `inconclusive`；
- 涉及新发现时，数据探索、文献对照、外部验证和实验验证必须分层表述。

物理部署上，v0.1 只需要三个运行主体：

1. 一个 Orchestrator/Analyst 模型实例，按状态机调用 skills；
2. 一个受控的 Python/R 执行环境；
3. 一个独立 Reviewer 模型实例，加一组不依赖 LLM 的验证脚本。

文中列出的 Data Steward、Literature Worker、Hypothesis Reviewer 等是**逻辑角色和权限边界**，不要求一开始做成八个服务。只有当第一阶段 benchmark 证明拆分确实提高科学分数或可靠性时，再增加物理 agent 数量。

首个可交付版本应只跑通两条工作流：

- `WF-3CA-MP-01`：在冻结的 3CA 2023 子集上重新发现恶性细胞转录程序；
- `WF-3CA-MET-01`：对经过校验的代谢基因集做 program 映射、患者级统计、敏感性分析和外部验证。

同时对同一模型运行：

- `P0 Direct`：一句话问题 + 数据说明 + 输出契约；
- `P1 Flow`：同样的问题、数据和预算，但启用完整 workflow 和 skills。

这会直接回答导师提出的核心问题：专家工作流及 skills 是否比单纯增加 prompt 长度或模型规模更可靠。第一阶段已有的 `task.yaml`、`run.json`、`events.jsonl`、`submission/` 和 grader 应原样复用，不另造一套不兼容格式。

---

## 1. 设计目标、非目标与成功定义

### 1.1 目标

第二阶段的目标不是让模型“看起来像科学家”，而是让一次分析满足以下六项可检查条件：

1. **数据正确**：数据来源、版本、许可、哈希、预处理状态和样本语义明确；
2. **统计正确**：推断单位、重复结构、协变量、效应量、不确定性和多重检验处理合理；
3. **计算可重现**：从只读输入可在干净环境中重新产生计分工件；
4. **结论有出处**：每条 claim 能追溯到数据工件和/或可信文献；
5. **反例被主动检查**：至少有敏感性分析、负对照或外部队列检验；
6. **不确定性可见**：证据不足、数据冲突或设计不可识别时能停止并给出 `inconclusive`。

### 1.2 非目标

v0.1 明确不做：

- 不自动作出临床诊断、治疗或患者级医疗建议；
- 不自动执行湿实验，也不把实验提纲伪装成已验证结果；
- 不给 agent 无限制联网、安装软件、访问凭据或写入原始数据的权限；
- 不把同一个模型的自我批评当成独立验证；
- 不把“代码成功退出”当成“科学结论正确”；
- 不把转录表达直接表述为代谢通量或因果机制；
- 不自动将所有成功轨迹写入长期记忆或第三阶段训练集；
- 不在 v0.1 上线向量数据库、微服务总线或复杂 agent 通信协议，普通文件、JSONL、YAML 和只读数据目录已足够。

### 1.3 成功定义

工作流成功必须同时满足：

- 所有硬门通过；
- `reproduce.sh` 在新环境成功；
- 主要工件符合 schema；
- 所有主要 claim 有可解析的 evidence reference；
- Reviewer 没有未解决的高优先级异议；
- 负对照没有被错误解释为阳性发现；
- 运行日志、错误、重试、参数变化和人类干预均可追踪。

科学假设未获支持并不等于工作流失败。正确地得到“未支持”或“无法判断”，属于有效科学输出。

---

## 2. 从芯片设计 agentic workflow 可迁移什么

附件中总结的芯片设计工作对本项目有价值，但需要区分“可迁移机制”和“领域专用实现”。SPICE、拓扑和器件尺寸不能直接移植到生物医学；可迁移的是如何约束复杂搜索、如何接入外部真实性检查，以及如何保存可复用的专家结构。

| 芯片设计经验 | 论文中的实际机制 | 生物医学对应设计 | 不应照搬的部分 |
|---|---|---|---|
| HeaRT 的层级推理树 | 离线从电路图/网表建立层级结构，在线按问题遍历相关分支；只在关键处调用 LLM，再把优先变量交给优化器[^1] | 建立“研究问题→数据层→设计层→方法层→证据层→claim”的 Biomedical Analysis Reasoning Graph；仅检索当前状态需要的 skill、数据字典和证据 | 不把自然语言推理树当作真值；生物数据结构不是稳定电路拓扑 |
| AnaFlow 的分阶段验证 | 先做便宜的 DC operating-point 检查，再进入昂贵的全仿真和优化循环[^2] | 先做数据 manifest、样本表、counts 状态、小子集 smoke test、设计可识别性检查，再运行全量 NMF、整合或大规模富集 | 不允许 agent 反复调参数直到“显著”；科学分析不是寻找任意满足规格的解 |
| Topology generation 与 inverse design 分离 | 先生成架构，再在固定架构中寻找参数[^3] | 把“科学解释/模型结构候选”与“具体分析参数和执行”分离；先列备选分析图，再冻结主分析和敏感性分支 | 不把新颖性等同于正确性；候选假设仍需反证和外部验证 |
| RF-Agent 的知识蒸馏 | 从七本教材构造 QTSA 数据并比较 SFT 与不同 RAG[^4] | 把教材、方法论文、实验室 SOP 和资深分析者决策编码为可版本化 skills；保留来源与适用边界 | 合成 reasoning 样本不能未经专家和执行验证直接进入训练集 |
| RFAmpDesigner 的动作成本意识 | 区分不同成本的设计动作，复用历史优化经验[^5] | 将动作分为 cheap/medium/expensive：元数据检查 < 小样本试跑 < 全量计算 < 外部验证；优先进行能最大幅度降低不确定性的低成本检查 | 历史成功参数不能跨队列无条件复用 |
| 仿真器闭环 | 电路性能由 SPICE 或实测指标反馈，而不是由 LLM 自评 | 统计程序、数据 schema、负对照、外部队列、独立复算和最终实验是“现实反馈” | LLM reviewer 不能替代统计检验、实验或独立数据 |
| OpenLayout 的整体平台方向 | 附件将其列为从规格到 layout 的整体 agentic 平台，但目前可核验的公开技术细节不足 | 只吸收“统一入口、统一工具接口、统一工件”的平台方向 | 不根据名称推断其内部 agent、memory 或评价机制 |

HeaRT 的一个尤其重要的启示是：它并未让 LLM 在每次优化迭代都重新长篇推理，而是先构建可复用结构，再用一次在线推理缩小搜索空间；报告的一个案例中仿真次数由 516 降至 165。该数字仅是芯片任务结果，不能预期在生物医学中复现，但“先缩小可信分析空间，再调用成熟数值工具”的原则非常适合本项目。[^1]

另一个重要边界是：优化器、生成器、数据库和仿真器本身不是 agent。我们的 NMF、差异表达、GSEA、混合模型、COBRApy 或 TCR 分析工具也应被视为确定性或随机性受控的工具；agent 的价值在于选择、连接、检查和解释这些工具。

---

## 3. 相关生物医学系统给出的直接证据

### 3.1 值得复用的机制

| 系统 | 已公开机制 | 对本项目的启示 | 证据边界 |
|---|---|---|---|
| AutoBA | 用户以 YAML 提供数据路径、描述和目标；系统规划、逐步生成代码、执行，并用 automated code repair 修复运行错误[^6] | 输入必须结构化；运行错误应自动回写；本地部署有利于敏感数据 | ACR 修复的是运行失败，不自动保证推断单位和生物解释正确 |
| CellAgent | Planner、Executor、Evaluator 三类角色，层级决策和自迭代优化[^7] | 角色拆分和局部反馈有用 | 公开实现中的满意判定仍高度依赖 LLM 文本，不能作为硬科学门 |
| CellVoyager | 将假设生成与执行分开，在 Jupyter 中逐步分析，可暂停让用户检查；CellBench 覆盖 76 项已发表单细胞研究[^8] | Notebook 适合作为人类审阅界面；开放探索需要可暂停、可续跑 | Notebook 不能是唯一重现入口；专家认为“有创意”不等于已验证 |
| GeneAgent | 生成→claim 拆分→数据库核验→修改→总结；用多数据库支持或反驳原始描述[^9] | 结论应先原子化，再逐条核验，支持/反驳结果必须回写 | 自验证仍可能受工具覆盖和相同模型偏差影响，因此需要独立 reviewer |
| CRISPR-GPT | Planner 把任务 state machine 串联；提供 Meta、Auto、Q&A 三种自动化模式和用户代理；使用专家指南及专用工具[^10] | 本项目也应有 Guided、Auto 和 Audit 三种模式；高风险节点强制人类确认 | 基因编辑实验设计与我们的计算发现任务不同；湿实验结论不能类推 |
| Biomni | 统一生物医学工具、数据库、软件和 protocol action space；检索增强规划并执行 Python/R/Bash[^11] | 工具注册表、按需检索、可扩展 action space 值得借鉴 | 截至本稿主要论文仍为预印本；官方仓库明确警告生成代码拥有系统权限，应沙箱化 |
| BioMedAgent | 通过探索学习工具链，并将成功经验写入 memory retrieval；在 327 个任务的 BioMed-AQA 上报告 77% 成功率[^12] | 可将经验证轨迹升级为经验库；应按 milestone 评价中间步骤 | 论文任务覆盖广，与 3CA 专题的统计和机制要求不完全相同；memory 不能直接污染 sealed benchmark |
| OpenScientist | Agent Skills + MCP；每轮把发现、假设、分析和图保存到 JSON knowledge state；Docker 运行；使用真实外部数据和随机标签负对照[^13] | skill 与核心控制器解耦、知识状态和负对照值得采用 | 当前证据仍较新；固定 10 轮不是科学停止规则，且每个结论仍需独立统计审计 |
| MechAInistic | Architect 与隔离上下文的 Reviewer；Reviewer 按 rubric 审计划和中间结果，不达阈值则重规划；推理以可执行 COBRApy 模型为依据[^14] | 独立 reviewer、阶段性 rubric、可执行机制模型非常适合代谢分支 | 截至本稿为预印本且只展示少量免疫细胞案例，不能视为通用验证 |
| Co-Scientist | Generation、Reflection、Ranking、Evolution、Proximity、Meta-review 与 Supervisor；通过 tournament 迭代假设[^15] | 可在“假设优先级”阶段使用生成、反思、去重和 pairwise top-k 比较 | 适合开放假设生成，不适合替代数据清洗、统计分析或确定性 grader |
| Robin | 文献 agents + 数据分析 agent；开放分析用多条独立轨迹再汇总；作者观察到工具几乎总按同一顺序调用，最后改成更稳定的确定性 notebook[^16] | 高频重复任务应编码成状态机，不必维持自由 agent swarm；多轨迹只用于开放问题 | 多轨迹共识不能消除所有轨迹共享的系统性偏差 |
| gSage | 在肿瘤精准医学场景中，20 个受控工具的 workflow agent 优于开放 200 多工具的 function-calling/ReAct 对照[^17] | “工具面小而准、知识有版本”优先于“工具越多越好” | 属于临床决策支持评估，不能直接当作单细胞发现性能证据 |

### 3.2 综合判断

现有证据不支持“agent 数量越多越可靠”。相反，最稳定的共同模式是：

1. 将专家工作拆成明确阶段；
2. 每个阶段只暴露必要的工具；
3. 运行结果回写到结构化状态；
4. 用独立或外部证据检查，而不是只看语言流畅性；
5. 对已稳定的调用顺序进行确定化；
6. 只把通过复算的经验写入长期 memory。

2026 年“skill-augmented agent 在 BixBench verified 子集上显著改善”的预印本结果进一步支持 skills 的方向，但该结果很新，且 benchmark 较小，方案中将其视为待复验信号，而不是已确立定律。[^18]

---

## 4. 总体架构：六个平面

工作名可暂定为 `BioDiscovery-Flow v0.1`。系统分为六个平面，但可以在同一个代码仓库和一个进程内实现。

### 4.1 Contract Plane：任务和数据契约

负责冻结：

- 科学问题、研究类型和允许的结论等级；
- 输入文件、数据字典、哈希和版本；
- 推断单位和实验设计；
- 网络、工具、时间、内存和 token 预算；
- 必须提交的工件和 schema；
- 人类审批点和风险等级。

输入直接复用第一阶段的 `public/task.yaml` 与 `data_manifest.public.json`。工作流不能悄悄修改题目或数据定义。

### 4.2 Control Plane：状态机与 Orchestrator

Orchestrator 只做：

- 检查当前状态的入口条件；
- 选择允许的 skill；
- 组装 skill 输入；
- 接收结构化结果；
- 触发 validator、重试、重规划或人类 gate；
- 记录事件和预算。

它不直接决定某基因是否有生物学意义，也不直接把 stdout 写成最终结论。

### 4.3 Skill Plane：领域决策程序

skill 保存可复用的人类工作方法，包括：适用条件、必须检查的元数据、推荐方法、禁止做法、可选分支、输出字段、验证方法、失败和停止条件。

skill 可以调用脚本或工具，但 skill 不是单纯 prompt；没有输入/输出 schema、validator 和版本的长提示词不能算本项目的正式 skill。

### 4.4 Execution Plane：受控计算与工具

包括：

- 只读数据挂载；
- 每次运行独立工作目录；
- Python/R 环境锁定；
- 白名单 CLI、数据库和 API；
- CPU、内存、时间和网络配额；
- stdout/stderr、退出码、文件变化和图表来源表记录。

### 4.5 Evidence Plane：证据账本

所有结果组织为以下关系：

    Question
      ├── generated_by → Plan
      ├── uses → DataSnapshot
      ├── produces → Artifact
      └── yields → Claim
                        ├── supported_by → Artifact / Source
                        ├── contradicted_by → Artifact / Source
                        ├── qualified_by → Limitation
                        └── tested_by → Sensitivity / ExternalValidation

v0.1 不必建立图数据库；`claims.jsonl`、`evidence.jsonl` 和稳定 ID 已足够。发布时可把这些关系映射到 W3C PROV 或 Workflow Run RO-Crate。后者专门描述 workflow 输入、输出、代码、容器和步骤 provenance。[^19][^20]

### 4.6 Governance Plane：权限、安全和人类控制

负责：

- 数据分类和模型端点策略；
- 网络白名单；
- 凭据隔离；
- prompt injection 防护；
- 双用途审查；
- clinical/experimental claim 限制；
- 审批记录和审计导出。

agent scaffold 可能显著放大底层模型的能力，包括双用途能力，因此安全评价必须针对“模型 + tools + workflow”的整体系统，而不是只看基础模型。[^21]

---

## 5. 状态机：从问题到可审计结论

### 5.1 主状态

| 状态 | 目的 | 必须产出 | 硬退出条件 |
|---|---|---|---|
| `S0_INTAKE` | 形成研究章程 | `research_charter.yaml` | 问题、数据权限、推断单位或目标输出不明确 |
| `S1_DATA_FREEZE` | 定位并冻结数据 | `data_manifest.resolved.json`、初始 workspace manifest | 哈希不匹配、许可不允许、关键文件缺失 |
| `S2_DATA_AUDIT` | 检查结构和设计可识别性 | `data_audit.json`、QC 概览 | 无 sample/patient ID；分组与批次完全混杂且无可识别对比 |
| `S3_PLAN` | 生成类型化分析 DAG | `plan.json` | 步骤缺输入/输出/validator；遗漏必需负对照或统计单位 |
| `S4_PLAN_REVIEW` | 独立审核计划 | `plan_review.json` | 高优先级问题未解决；超预算或权限 |
| `S5_PREFLIGHT` | 在小规模数据和 cheap checks 上试跑 | `preflight.json` | 工具不可用、字段错、输出 schema 错、资源估计失控 |
| `S6_PRIMARY_ANALYSIS` | 运行冻结主分析 | 任务定义的主要表格与模型结果 | 运行失败或主工件不完整 |
| `S7_ROBUSTNESS` | 敏感性、负对照、留一法 | `robustness.json`、支持表 | 必需检验未完成；不得因未显著而反复调参 |
| `S8_EVIDENCE` | 文献和数据库核验 | `evidence.jsonl` | 关键来源无法定位或证据与 claim 不对应 |
| `S9_HYPOTHESIS` | 生成和排序可证伪假设 | `hypotheses.jsonl` | 假设不可证伪、越过证据等级或有未处理安全风险 |
| `S10_REPRODUCE` | 干净环境独立复算 | `reproduction.json` | 入口无法重跑或主要数字超容差 |
| `S11_FINAL_REVIEW` | claim-level 审核 | `review.json` | 主要 claim 无证据、统计错误或夸大 |
| `S12_REPORT` | 生成人类报告和提交包 | `report.md`、`claims.jsonl`、`provenance.json` | 输出契约不通过 |
| `S13_HUMAN_GATE` | PI/领域专家批准、退回或归档 | `approval.json` | 未批准的高风险结果不得向下游传播 |

### 5.2 允许的转移

正常路径为：

    S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8 → S9 → S10 → S11 → S12 → S13

只允许以下回路：

- `S4 → S3`：Reviewer 要求修改计划；
- `S5 → S2/S3`：preflight 暴露数据或资源问题；
- `S6 → S3`：主分析发生预先未覆盖的技术失败；
- `S7 → S6`：执行预先登记的敏感性分支，不覆盖主分析；
- `S8 → S9`：证据影响假设排序；
- `S10 → S6`：重现失败，修复后生成新 run revision；
- `S11 → S7/S8/S9`：Reviewer 指定需要补的证据类型；
- `S13 → 指定状态`：人类退回，必须写明理由。

禁止 `S9 → S6` 在不留痕的情况下修改主分析来迎合已生成的假设。若新假设需要新分析，应创建 `exploratory_branch_id`，并标注为 post hoc。

### 5.3 三种运行模式

| 模式 | 适用 | 行为 |
|---|---|---|
| `guided` | 新用户、benchmark 的 guided reproduction | 固定主流程；在关键点提示用户；禁止自行增加高风险分析 |
| `auto` | 公开数据、已验证 skills、明确权限 | 在状态机内自动选择分支；遇到硬门或重大歧义暂停 |
| `audit` | 复查现有人类/agent 分析 | 不重做整个研究，读取工件和日志后运行 validators、反例和证据审核 |

这对应 CRISPR-GPT 的多自动化层级，但本项目把“权限”和“可重复性”也纳入模式定义。[^10]

---

## 6. 角色、权限和隔离

### 6.1 逻辑角色

| 角色 | 能做什么 | 不能做什么 | 结构化输出 |
|---|---|---|---|
| Orchestrator | 状态转移、预算、skill 路由、gate | 不直接更改原始数据；不自行豁免 validator | `state.json`、`events.jsonl` |
| Data Steward | 解析 manifest、版本、数据字典、样本结构 | 不提出最终生物学结论 | `data_audit.json` |
| Analysis Planner | 把问题转成 DAG、参数和敏感性分支 | 不执行；不查看 benchmark 隐藏 gold | `plan.json` |
| Executor | 生成/运行 Python/R，保存表格和模型 | 不将 stdout 直接升级为 claim；不得写原始数据 | 工件、代码、日志 |
| Deterministic Validator | schema、数值、哈希、重复结构、统计断言 | 不生成叙事性结论 | `validation/*.json` |
| Literature Worker | 检索、去重、定位来源、抽取 claim-support | 不把检索排名当证据强度；不能更改分析结果 | `evidence.jsonl` |
| Hypothesis Synthesizer | 生成可证伪假设、预测和替代解释 | 不宣称实验验证；不隐藏反例 | `hypotheses.jsonl` |
| Independent Reviewer | 审计划、结果、证据和语言强度 | 不共享 Analyst 的完整对话上下文；不直接改结果 | `review.json` |
| Human PI/Domain Expert | 确认科学范围、重大方法变更、最终传播 | 审批应留痕，不能在发布后无记录地改 gold | `approval.json` |

### 6.2 为什么 Reviewer 要隔离

MechAInistic 把 Architect 和 Reviewer 放在不同对话历史中，使 Reviewer 不继承分析者为自己选择辩护的上下文；GeneAgent 则说明逐 claim 核验比整段“感觉正确”更有效。[^9][^14]

因此 Reviewer 最少只接收：

- 原始问题和数据字典；
- 冻结 plan；
- 主要工件的摘要和可访问路径；
- claim/evidence ledger；
- validator 报告；
- 不含隐藏思维链的可观察事件摘要。

Reviewer 不应看到第一阶段 private gold，也不应把 Analyst 的结论当作事实前提。

### 6.3 同一模型能否承担多个角色

可以，但必须：

- 使用独立上下文；
- 使用不同角色 prompt 和工具权限；
- 在 `run.json` 记录 model、role 和 revision；
- 对关键实验增加异构模型 reviewer 或人工抽查作为敏感性分析。

“同一模型多角色”不是独立证据，只是降低上下文污染的工程措施。

---

## 7. Skill 的正式定义

### 7.1 一个正式 skill 必须包含什么

推荐最小目录：

    skills/
      sample-aware-de/
        1.0.0/
          SKILL.md
          manifest.yaml
          input.schema.json
          output.schema.json
          run.py                 # 可选；能复用现有包时不再造包装层
          test_cases/
            smoke.json

`SKILL.md` 是人类可读的领域程序；`manifest.yaml` 是机器路由信息；schema 是执行边界；只在确有稳定机械步骤时提供脚本。

### 7.2 manifest.yaml 最低字段

```yaml
schema_version: 1.0
skill_id: sample-aware-de
skill_version: 1.0.0
title: Sample-aware differential expression
status: validated
domain: [single_cell, transcriptomics, cancer]
risk_level: medium
entry_conditions:
  - raw_counts_available
  - biological_replicate_id_available
  - comparison_groups_defined
inputs_schema: input.schema.json
outputs_schema: output.schema.json
allowed_tools: [R, edgeR, limma, DESeq2, Python]
default_budget_class: medium
validators:
  - de_schema
  - replicate_count
  - p_q_consistency
  - shuffled_label_control
human_gate_when:
  - complete_batch_condition_confounding
  - fewer_than_3_replicates_per_group
forbidden_claims:
  - cell_level_independence_as_patient_level_evidence
  - causality_from_observational_de
references:
  - doi:10.1038/s41467-021-25960-2
```

### 7.3 SKILL.md 内容顺序

每个 skill 必须按同一顺序写：

1. Purpose；
2. Scope and non-scope；
3. Required inputs；
4. Entry checks；
5. Decision rules；
6. Execution steps；
7. Required outputs；
8. Deterministic validators；
9. Sensitivity/negative controls；
10. Failure, abstention and human-gate rules；
11. Interpretation limits；
12. References and version history。

### 7.4 Skill 结果信封

所有 skill 返回同一种外层结构，具体结果放在 `payload`：

```json
{
  "schema_version": "1.0",
  "skill_id": "sample-aware-de",
  "skill_version": "1.0.0",
  "step_id": "step-060",
  "status": "succeeded",
  "input_refs": ["data/expression.h5ad", "data/sample_metadata.parquet"],
  "input_hashes": {"data/expression.h5ad": "sha256:..."},
  "parameters_ref": "parameters/step-060.json",
  "artifacts": [
    {"path": "results/de.parquet", "media_type": "application/vnd.apache.parquet", "sha256": "..."}
  ],
  "validators": [
    {"id": "replicate_count", "status": "passed", "report_ref": "validation/step-060-replicates.json"}
  ],
  "warnings": [],
  "decision_summary": "Used donor-level pseudobulk because multiple cells are nested within donor.",
  "payload": {"n_genes_tested": 18231, "n_replicates": 24},
  "started_at": "...",
  "finished_at": "..."
}
```

`decision_summary` 记录可审计的选择理由，不要求供应商披露内部 chain-of-thought。

---

## 8. Skill library：从 v0.1 到扩展版

### 8.1 v0.1 必须先做的八个 skills

| Skill | 关键输入 | 必须产出 | 核心 hard checks |
|---|---|---|---|
| `dataset-resolver` | accession、URL、论文、期望版本 | resolved manifest、下载记录、许可、哈希 | accession/版本不唯一则停止；网页实时数据不能冒充冻结数据 |
| `data-contract-auditor` | h5ad/矩阵/metadata、数据字典 | 数据形状、层状态、ID 关系、重复结构、缺失和混杂报告 | counts/normalized 不明；sample/patient ID 缺失；一对多关系异常 |
| `gene-set-validator` | GMT/基因表、物种、ID 体系 | 标准化基因集、未映射/重复/别名报告、背景基因 | 物种不明；映射损失超预设阈值；背景 universe 缺失 |
| `single-cell-qc-auditor` | counts、细胞/样本 metadata | before/after QC 表、阈值依据、样本级异常、doublet/ambient 指标 | 不能只给 UMAP；每个阈值必须可追溯；不得删掉整个条件而不报警 |
| `sample-aware-statistics` | 设计矩阵、cell/sample IDs、目标变量 | 冻结模型式、可识别性报告、效应量和 CI | 把 cell 当患者重复；完全混杂；只报告 p 值 |
| `program-discovery-and-matching` | 分样本表达、NMF 参数范围 | program×gene、program×sample、稳定性、匹配表 | 多随机种子；跨样本 recurrence；禁止只挑最好看的 K |
| `pathway-metabolism-interpretation` | 排名基因、gene set、背景 | ORA/GSEA 结果、方向、冗余、matched-null、限制 | 必须记录 gene-set version、null 类型和背景；转录不等于 flux |
| `claim-evidence-reporter` | 所有工件、统计结果、来源 | `claims.jsonl`、`evidence.jsonl`、报告 | 每条 claim 指向工件；无证据时 `inconclusive`；语言强度匹配等级 |

### 8.2 v0.5 扩展 skills

- `batch-and-integration-audit`：判断何时只建模 batch、何时整合，检查过度校正；
- `cell-annotation-evidence`：参考映射、marker、自动注释的一致性和不确定性；
- `malignant-cell-validation`：CNV、marker、作者标签和样本背景的多证据验证；
- `pseudobulk-de`：按 patient/sample 聚合并运行 edgeR/limma/DESeq2；
- `mixed-model-de`：在预先定义条件下使用 GLMM，并与 pseudobulk 比较；
- `meta-analysis-across-cohorts`：效应量、异质性、随机/固定效应、leave-one-study-out；
- `external-cohort-validation`：冻结映射、方向、效应量和 `inconclusive`；
- `tcell-state-scoring`：CD4/CD8、耗竭、应激、反应性等 signature 校验；
- `tcr-clonotype-analysis`：克隆定义、扩增、共享、patient-aware 检验；
- `survival-analysis-audit`：时间零点、删失、比例风险、泄漏和验证集；
- `literature-search-and-dedup`：多源检索、版本、去重、纳排；
- `claim-verification`：将 claim 拆成最小断言，分别找支持、反驳和缺口；
- `hypothesis-generation`：从已审计 observations 生成可证伪假设；
- `counterexample-search`：反向检索、外部癌种、随机标签、matched gene set；
- `fresh-environment-reproduction`：在干净容器运行并比较容差。

### 8.3 单细胞统计 skill 的关键规则

多细胞来自同一 donor/sample，不能把细胞当成患者级独立重复。系统 benchmark 显示，忽略生物重复会低估方差并产生假阳性，pseudobulk 通常能显著改善这种问题；同时，混合模型在部分设计中也有优势，batch、测序深度和稀疏度会影响方法表现。[^22][^23][^24]

因此正式规则不是“永远 pseudobulk”，而是：

1. 先显式画出 `cell → sample → patient → study → condition` 层级；
2. 若目标是患者/样本层群体差异，默认以 sample/patient 为推断单位；
3. 主分析使用 pseudobulk 或能正确建模嵌套结构的方法；
4. 将另一种合理方法作为敏感性分析；
5. 少于预设生物重复数、完全混杂或仅一个 donor 时，不输出人群层显著性结论；
6. integration 表达矩阵不默认用于 DE，原始 counts 或适配模型的输入应保留；
7. 报告效应量、CI、方向、q-value、每组 donor 数和每 donor 细胞数，而不只报告 marker 列表。

### 8.4 基因集和通路 skill 的关键规则

富集方法的 null hypothesis、基因集大小、背景基因和重叠结构都会影响结果；不同方法甚至可在同一数据上报告完全不同数量的显著 gene sets。[^25]

因此必须：

- 保存数据库名称、release、collection、物种和获取日期；
- 明确 competitive/self-contained、ORA/rank-based test；
- 对 ORA 保存可检测基因 universe；
- 对 rank-based test 保存完整排序和打分方向；
- 对多基因集做多重检验；
- 合并或标注高度冗余 pathway；
- 用 size、平均表达和必要时 GC/长度匹配的随机基因集作 null；
- 主要 pathway 至少由核心基因、方向和独立来源解释，不凭 pathway 名称讲机制；
- GeneAgent 式逐 claim 数据库核验用于解释层，不替代富集统计。[^9]

### 8.5 代谢 skill 的证据等级

仅有 scRNA-seq 时，表达和代谢模型主要支持“代谢相关转录状态”或“模型预测的代谢活动”。即使将基因表达约束进 genome-scale model，也常不能得到唯一通量，且交换约束、稳态假设和细胞间竞争会显著影响结果。[^26][^27]

采用以下等级：

| 等级 | 可用证据 | 允许表述 |
|---|---|---|
| M0 | 单基因/少量酶表达 | 某些代谢基因表达改变 |
| M1 | 经过校验的代谢 gene set / program | 代谢相关转录程序增强或减弱 |
| M2 | 多方法 gene-set 与 patient-level 复现 | 与某代谢过程一致的稳定转录状态 |
| M3 | 约束代谢模型 + 合理交换条件 + 敏感性分析 | 模型预测某些反应/路径活性变化 |
| M4 | 代谢组、Seahorse、同位素示踪等正交证据 | 支持功能性代谢改变 |
| M5 | 扰动与救援实验 | 支持因果代谢机制 |

agent 不得把 M1–M3 写成 M4–M5。

---

## 9. Tool registry 与选择策略

### 9.1 工具注册字段

每个工具条目至少包括：

```yaml
tool_id: scanpy
version: 1.11.x
kind: python_package
capabilities: [h5ad_io, qc, clustering, visualization]
input_formats: [h5ad]
output_formats: [h5ad, parquet, png]
determinism:
  seedable: true
  known_nondeterminism: [neighbors_parallel]
resource_class: medium
network_required: false
license: BSD-3-Clause
approved_for_data_classes: [public, internal_local]
wrapper_ref: null
health_check: "import scanpy; print(scanpy.__version__)"
```

### 9.2 选择规则

1. 先匹配输入/输出 schema 和数据类别；
2. 再匹配被验证的 capability；
3. 同类工具优先选择已在 benchmark 参考任务中验证、版本稳定、可本地运行者；
4. 先调用 cheap 工具确认数据和设计，再调用 expensive 工具；
5. 只有当现有工具不满足明确需求时才扩展 registry；
6. 每个 skill 默认暴露 3–8 个工具，不向模型一次展示全部工具；
7. 工具调用失败是技术事件，不是选择另一个能产生显著结果的理由。

Biomni 说明广泛 action space 可以增强通用性，但其代码执行风险和 gSage 的受控工具结果共同提示，本项目 v0.1 应优先小而受控的工具面。[^11][^17]

### 9.3 网络模式

- `sealed`：禁止网络；用于 benchmark test，原论文和 gold 来源屏蔽；
- `restricted`：只允许 PubMed、Crossref、NCBI、EBI、GEO、SRA、Zenodo、MSigDB 等白名单；
- `open-reviewed`：开放检索，但所有 URL、时间和快照均记录；用于真实开放发现；
- `offline-sensitive`：内部/BKI 数据只在本地分析，外部模型只接收批准后的非敏感摘要，或完全使用本地模型。

网页、论文正文、README 和数据文件都是不可信内容，不能改变 system policy、工具权限或写入范围。

---

## 10. 计划格式：不是自然语言清单，而是可执行 DAG

`plan.json` 的每个步骤至少包含：

```json
{
  "plan_version": "1.0",
  "plan_id": "plan-3ca-met-001-r1",
  "question_id": "Q1",
  "primary_analysis_frozen": false,
  "steps": [
    {
      "step_id": "step-030",
      "purpose": "Validate metabolic gene identifiers and analysis universe",
      "depends_on": ["step-020"],
      "skill_ref": "gene-set-validator@1.0.0",
      "input_refs": ["data/metabolic_genes.gmt", "data/expression.h5ad"],
      "parameter_ref": "parameters/step-030.json",
      "expected_outputs": ["results/gene_set_validated.tsv", "validation/gene_set.json"],
      "validators": ["gene_id_namespace", "mapping_loss", "universe_membership"],
      "cost_class": "cheap",
      "retry_policy": {"technical": 1, "scientific": 0},
      "failure_transition": "S3_PLAN",
      "human_gate": false
    }
  ],
  "primary_endpoints": ["program_overlap", "patient_level_activity"],
  "negative_controls": ["expression_matched_random_gene_sets", "shuffled_patient_labels"],
  "sensitivity_branches": ["alternative_program_mapping", "leave_one_cancer_out"],
  "stopping_rules": ["budget_exhausted", "all_required_outputs_valid", "design_not_identifiable"]
}
```

### 10.1 Plan Reviewer 的 rubric

每项为 `pass / revise / block`：

- 问题与输入是否匹配；
- inference unit 是否明确；
- 主终点和 exploratory 终点是否分开；
- 方法是否适配 counts、normalized、rank 或 summary statistics；
- 是否有必要的 QC、negative control、sensitivity 和 external validation；
- 是否存在 data leakage、label leakage 或 gold leakage；
- 每步是否有输出和 validator；
- 失败能否区分 technical failure 与 null result；
- 预算是否现实；
- 结论等级是否受数据类型约束。

### 10.2 冻结规则

通过 `S4_PLAN_REVIEW` 后，将：

- `plan.json`、参数、skill 版本和输入 hash 固定；
- 主分析标记 `primary_analysis_frozen=true`；
- 后续修改产生新的 `plan_revision`，不能覆盖；
- 任何观察结果后新增的分析都标为 `exploratory`；
- 不能自动尝试多套方法后只报告最显著的一套。

---

## 11. 执行、错误修复和停止规则

### 11.1 三类失败必须分开

| 类别 | 示例 | 可否自动重试 | 输出 |
|---|---|---|---|
| 技术失败 | 包缺失、内存不足、字段名错误、API 暂时失败 | 可，最多 1–2 次；参数语义不得变化 | `TECHNICAL_ERROR` |
| 方法/契约失败 | 输入不满足方法假设、输出 schema 错、样本结构不支持模型 | 返回 Planner 或 human gate | `METHOD_INVALID` |
| 科学 null/冲突 | 无显著差异、外部队列不复现、证据相反 | 不为“得到阳性”而重试 | `SUPPORTED/UNSUPPORTED/CONTRADICTED/INCONCLUSIVE` |

AutoBA 证明将运行错误回写给代码生成器可提升端到端稳定性；本项目保留该机制，但将 retry 限制为技术修复。[^6]

### 11.2 标准错误码

- `DATA_ID_MISMATCH`
- `DATA_HASH_MISMATCH`
- `METADATA_INCOMPLETE`
- `DESIGN_CONFOUNDED`
- `INFERENCE_UNIT_UNAVAILABLE`
- `TOOL_UNAVAILABLE`
- `SCHEMA_VALIDATION_FAILED`
- `RESOURCE_EXCEEDED`
- `NUMERICAL_INSTABILITY`
- `NEGATIVE_CONTROL_FAILED`
- `EVIDENCE_UNRESOLVED`
- `REPRODUCTION_FAILED`
- `POLICY_BLOCKED`
- `HUMAN_DECISION_REQUIRED`

### 11.3 停止规则

系统在以下情况应停止，而不是继续“探索”：

- 必需输入或许可无法确认；
- 研究设计无法识别目标效应；
- 预算达到 90% 且必需输出仍不可达；
- 同一技术错误修复两次仍失败；
- Reviewer 两轮仍指出相同阻断问题；
- 新分析只是在追逐显著性；
- 假设需要超出当前授权的数据或实验；
- 安全策略阻止后续行动。

---

## 12. 分层验证：把 LLM 评价放在正确位置

### 12.1 七层验证栈

| 层 | 验证对象 | 首选验证方式 | LLM 的角色 |
|---|---|---|---|
| V1 Schema | 文件、列、类型、枚举、唯一键 | JSON Schema、Parquet schema、断言 | 无 |
| V2 Data identity | accession、版本、hash、行列关系 | manifest、checksum、referential integrity | 解释异常 |
| V3 Computation | 退出码、随机种子、数值范围、重跑 | 脚本和容差比较 | 修复技术错误 |
| V4 Statistics | 推断单位、模型式、重复、CI、FDR、负对照 | 专用 validator + statistician rubric | 提出可能遗漏 |
| V5 Biological plausibility | marker、pathway、状态、跨队列一致性 | 领域数据库、替代方法、外部数据 | 生成可检查解释 |
| V6 Evidence | claim 与工件/文献对应、支持和反驳 | claim-level ledger、引用定位 | 综合与审查 |
| V7 Independent reproduction | 干净环境、独立 reviewer、外部 cohort/实验 | 新容器、外部队列、人类/湿实验 | 汇总但不能豁免失败 |

### 12.2 Hard gate 与 soft warning

Hard gate 示例：

- 数据 hash 错；
- patient ID 缺失但声称患者级差异；
- p-value 不在 `[0,1]`；
- q-value 与登记方法不一致；
- 主工件无法由入口脚本生成；
- claim 引用不存在的 artifact；
- benchmark sealed 模式访问原论文答案。

Soft warning 示例：

- 某癌种重复数偏少；
- 两个合理方法方向一致但显著性不同；
- pathway 高度冗余；
- 外部数据平台不同；
- 文献仅有预印本或间接支持。

### 12.3 Negative controls

每条发现 workflow 至少选择一项数据负对照和一项解释负对照：

- 随机置换 condition，但保持 patient/study 结构；
- expression/size-matched 随机 gene sets；
- 负相关或不相关 pathway；
- leave-one-patient/study/cancer-out；
- 在不应出现信号的 cell type 或 cohort 中检验；
- 对假设主动检索反向结果和失败研究；
- 外部验证集的随机标签副本。

OpenScientist 在真实验证集和随机标签副本上分别检验假设，是值得直接复用的设计。[^13]

### 12.4 多轨迹何时有用

Robin 对开放数据分析运行多条独立轨迹并做共识，说明多轨迹可覆盖不同分析思路；但作者也指出，固定流程最终更稳定。[^16]

本项目规则：

- QC、版本确认、schema 检查：单一路径，确定性执行；
- 预先规定的 DE/NMF：单一主分析 + 固定敏感性分支；
- 开放假设生成：可运行 3–5 条不同 seed/不同方法提示的轨迹；
- 共识必须基于相同结构化工件，不以多数语言表述为真；
- 轨迹共享数据偏差时，外部队列和负对照优先于增加轨迹数。

---

## 13. 文献检索与证据核验工作流

### 13.1 两阶段检索，避免把文献答案倒灌进数据分析

对于真实发现任务：

1. 先在 `S6–S7` 保存 data-driven observations；
2. 再让 Literature Worker 在 `S8` 搜索支持、反驳、既有相似发现和方法限制；
3. 原始 observation 不因文献结果而被覆盖；
4. 文献启发的新分析进入 exploratory branch。

对于 blind benchmark：

- Literature Worker 不得访问目标论文、作者代码、gold gene set 或能直接泄漏答案的页面；
- 可使用 task 允许的通用数据库和预冻结文献库；
- 所有访问记录在 `events.jsonl`。

### 13.2 检索角色分工

- **Retriever**：生成 query、搜索多个来源、记录完整命中；
- **Deduplicator**：按 DOI/PMID/title 合并版本；
- **Source Assessor**：标记同行评审、预印本、数据库、指南、撤稿/勘误；
- **Claim Extractor**：只提取与当前 claim 对应的最小证据；
- **Contradiction Checker**：主动找不支持、不同条件和相反方向；
- **Citation Verifier**：确认题名、作者、年份、DOI/PMID 和原文位置。

这些可由一个 Literature Worker 顺序执行，不必变成六个 agent。

### 13.3 evidence.jsonl

```json
{
  "evidence_id": "EV-00031",
  "claim_id": "CL-00007",
  "source_id": "PMID:12345678",
  "source_type": "peer_reviewed_article",
  "source_version": "version_of_record",
  "retrieved_at": "2026-09-11T10:00:00+08:00",
  "locator": {"figure": "3", "section": "Results"},
  "stance": "supports",
  "directness": "direct",
  "population_match": "partial",
  "modality_match": "direct",
  "summary": "The study reports donor-level replication of the same direction in ...",
  "limitations": ["different cancer composition"],
  "verified_by": "citation-verifier@1.0.0"
}
```

PaperQA2 展示了对科学检索、总结和矛盾发现进行专门评价的价值；但本项目仍需保存每条 claim 的来源定位，而不是只保留一段带引用的最终总结。[^28]

---

## 14. Hypothesis Engine：生成、去重、反证与排序

### 14.1 假设生成的输入边界

Hypothesis Synthesizer 只能看到：

- 已通过 V1–V4 的 observations；
- robustness 和 negative-control 结果；
- 已核验 evidence ledger；
- 明确的研究约束和可用验证资源。

不能把失败日志、未验证 notebook 注释或模型自己的先验当成数据证据。

### 14.2 hypothesis.jsonl

```json
{
  "hypothesis_id": "H-0004",
  "statement": "In context X, program P may mark ... through mechanism M.",
  "scope": {"cancer_types": ["..."], "cell_type": "CD8 T", "population": "..."},
  "source_observations": ["OBS-0012", "OBS-0017"],
  "supporting_evidence": ["EV-0031", "EV-0032"],
  "contradicting_evidence": ["EV-0040"],
  "causal_status": "associational_hypothesis",
  "predictions": [
    {"id": "P1", "statement": "...", "test": "external cohort ..."}
  ],
  "falsifiers": ["No donor-level association in two external cohorts"],
  "alternative_explanations": ["stress response", "cell-cycle composition"],
  "required_validation": ["paired metabolomics", "perturbation"],
  "novelty_status": "uncertain",
  "feasibility": "medium",
  "safety_status": "allowed",
  "status": "candidate"
}
```

### 14.3 先过滤，再排序

硬过滤：

- 与问题无关；
- 无数据 observation；
- 不可证伪；
- 结论等级越界；
- 与已知事实冲突但无解释；
- 需要未授权数据或工具；
- 安全风险未解决。

通过后，分别报告以下维度，不急于压成一个总分：

- data support；
- cross-patient/cohort robustness；
- external evidence；
- novelty；
- falsifiability；
- mechanistic specificity；
- validation feasibility；
- clinical relevance；
- uncertainty/risk。

对 top 10 可以采用 Co-Scientist/Robin 式 pairwise comparison 和去重图，但 LLM 排名只是分配验证资源的启发式，不能提升证据等级。[^15][^16]

### 14.4 默认优先级公式只作为工程起点

若系统必须排序，v0.1 可用：

    priority = 0.25*data_support
             + 0.20*robustness
             + 0.15*external_evidence
             + 0.15*falsifiability
             + 0.10*novelty
             + 0.10*feasibility
             + 0.05*clinical_relevance

每项 0–4，权重由项目目标冻结并在 benchmark 中校准。这些权重是工程决策，不是科学真理；最终报告保留分项分数和 Reviewer 理由。

---

## 15. Memory：只保存经验证经验

### 15.1 四类 memory

| Memory | 内容 | 生命周期 | 是否可跨任务 |
|---|---|---|---|
| Source Registry | 数据 accession、文献、工具和版本 | release 级 | 可以，受许可约束 |
| Skill/Know-how | 专家 SOP、决策规则、方法限制 | 版本化 | 可以 |
| Working State | 当前 plan、错误、工件、未决问题 | run 级 | 不可以直接跨 run |
| Validated Experience | 已复算的成功/失败模式、适用上下文 | 经审核后长期 | 可以，需防 benchmark 泄漏 |

### 15.2 经验升级门槛

一段轨迹只有同时满足以下条件才能进入 `validated_experience/`：

- 输入和输出可复现；
- hard gates 全部通过；
- Reviewer 无高优先级问题；
- 不含敏感数据、凭据、隐藏 gold 或不可公开全文；
- 已提取成“上下文—动作—结果—适用边界—失败条件”，而不是直接存原始聊天；
- 有 skill/version、tool/version 和数据类型标签。

BioMedAgent 和 RFAmpDesigner 都强调从经验中复用，但本项目必须防止“成功偏差”：null result、失败原因和反例也应进入经验库。[^5][^12]

### 15.3 Benchmark 隔离

- dev 任务允许从 dev validated experience 检索；
- sealed test 禁止检索相同论文、相同 cohort、同一 leakage group 的经验；
- gold、grader 和 private reference workflow 永不进入模型可见 memory；
- 每次检索返回条目 ID 和 hash，写入 events。

---

## 16. 与第一阶段 Benchmark 的无缝连接

### 16.1 不改第一阶段的四实体

继续使用：

- `PaperRecord`
- `DataSnapshot`
- `TaskCapsule`
- `RunBundle`

第二阶段只新增：

- `FlowDefinition`
- `SkillPackage`
- `EvidenceLedger`
- `HypothesisCard`

### 16.2 目录

```text
benchmark/
  tasks/...
  flows/
    bio-discovery-flow/
      0.1.0/
        flow.yaml
        tool_registry.yaml
        schemas/
        skills/
  runs/
    <run_id>/
      run.json
      state.json
      plan.json
      events.jsonl
      human.log
      checkpoints/
      validation/
      submission/
        reproduce.sh
        environment.lock
        src/
        analysis.ipynb
        results/
        figures/
        claims.jsonl
        evidence.jsonl
        hypotheses.jsonl
        methods.md
        report.md
        provenance.json
```

`events.jsonl` 仍是行为轨迹真相源；`state.json` 是最新状态快照；`plan.json` 是审核后的分析 DAG；最终可选择生成 `ro-crate-metadata.json`，不作为 v0.1 的运行依赖。

### 16.3 核心实验矩阵

每个模型、每个 task 至少比较：

| 条件 | 题干/数据/预算 | 变化项 | 目的 |
|---|---|---|---|
| P0 Direct | 相同 | 无 skills，只给输出契约 | 基线能力 |
| P1 Fixed Flow | 相同 | 固定状态机 + 全部必需 skills | 测完整专家 flow 增益 |
| P2 Dynamic Router | 相同 | 状态机不变，模型选择允许分支 | 测适应性是否带来额外价值 |
| P3 Oracle Plan | 相同 | 提供正确高层 plan | 区分规划失败与执行失败 |
| A1 no-stat-guard | 相同 | 去掉 sample-aware statistics | 测伪重复防护贡献 |
| A2 no-evidence-review | 相同 | 去掉 claim verifier | 测无支持 claim 变化 |
| A3 no-negative-control | 相同 | 去掉负对照 | 测过拟合和阳性偏差 |
| A4 self-review-only | 相同 | 去掉独立 reviewer | 测上下文隔离贡献 |
| A5 broad-tools | 相同 | 暴露大工具集 | 测工具面大小影响 |
| A6 no-memory | 相同 | 禁用 validated experience | 测经验复用收益与泄漏风险 |

每个 `system × task` 至少 3 次；开放发现任务建议 5 次。比较以 task 为配对单位，不能把 cell、gene 或 artifact 当独立重复。

### 16.4 评价指标

#### 科学结果指标

沿用第一阶段 task-specific graders：program matching、rank correlation、gene-set recovery、方向、效应量、CI、跨患者复现、external validation 和 calibration。

#### 工作流可靠性指标

- `data_identity_pass_rate`
- `inference_unit_correct_rate`
- `plan_gate_pass_rate`
- `required_step_coverage`
- `tool_selection_precision`
- `technical_repair_success_rate`
- `negative_control_specificity`
- `sensitivity_completion_rate`
- `claim_artifact_traceability`
- `citation_verification_rate`
- `unsupported_claim_rate`
- `appropriate_abstention_rate`
- `fresh_reproduction_success_rate`
- `human_intervention_minutes`
- `median_cost`、`wall_clock`、`tokens`

#### Flow 增益

```text
ΔScientific(model, task) = Score(P1) - Score(P0)
ΔHardFailure             = FailureRate(P0) - FailureRate(P1)
MarginalCost             = Cost(P1) - Cost(P0)
SkillEfficiency          = ΔScientific / max(MarginalCost, ε)
```

`SkillEfficiency` 只作辅助指标，不能用便宜但科学分低的系统替代可靠系统。

#### Hard-gated 报告

不建议把所有内容合并成一个 leaderboard 总分。若必须给主分：

- 数据身份、推断单位、可重现入口任一 hard gate 失败，run 标记 invalid；
- invalid run 的科学分单独展示，不能与有效 run 平均后掩盖失败；
- 主表同时报告 scientific score、reproducible success、hard-failure、cost 和 time。

---

## 17. 3CA 工作流 A：恶性细胞程序重新发现

工作流 ID：`WF-3CA-MP-01`

### 17.1 问题

使用与 2023 Nature 论文相符的冻结表达数据和样本信息，在不暴露作者 meta-program 答案的条件下，能否重新识别跨肿瘤复现的恶性细胞内在转录程序？2023 工作报告了 77 项研究、1,456 个样本，过滤后分析 1,163 个样本，并总结出 41 个 meta-program；当前 3CA portal 已扩展，不能将实时页面数据与论文快照混为一谈。[^29][^30]

### 17.2 状态映射

1. `S0`：定义 blind rediscovery、恶性细胞、patient/sample 推断层级和输出；
2. `S1`：冻结 2023 数据、官方代码 commit、Zenodo hash；
3. `S2`：检查 `X/layers/raw`、gene ID、patient/sample/cancer、恶性细胞标签；
4. `S3`：预登记 NMF 的 K 范围、重复次数、program 过滤、匹配和 leave-one-cancer-out；
5. `S5`：选择 2–3 个小癌种/样本 smoke test，验证内存和输出 schema；
6. `S6`：每样本/肿瘤独立 program discovery，合并为 meta-program；
7. `S7`：多 seed、K 范围、不同相似度阈值、leave-one-study/cancer-out；
8. `S8`：只做通用 pathway 解释；sealed 模式屏蔽目标论文答案；
9. `S10`：干净环境重跑；
10. grader 私下与作者 41 MPs 和独立复算结果匹配。

### 17.3 必需工件

- `results/program_genes.parquet`
  - `program_id, gene_id, rank, weight, source_sample`
- `results/program_activity.parquet`
  - `program_id, patient_id, sample_id, cancer_type, activity`
- `results/program_recurrence.parquet`
  - `program_id, n_samples, n_patients, n_cancers, recurrence_rate`
- `results/program_matching.parquet`
  - 只保存 agent 内部候选间匹配；gold matching 由 private grader 产生
- `validation/nmf_stability.json`
- `validation/leave_one_cancer_out.json`

### 17.4 验证重点

- 不能在全队列一次 NMF 后把批次/癌种差异当作 ITH；
- program recurrence 以独立样本/患者计，不以细胞数计；
- 随机 seed 和 K 的稳定性必须报告；
- 稀有 program 不因频率低自动判错，但需要证据和置信区间；
- 图必须能由表格重建；
- “匹配已知 MP”与“发现新 MP”分开标注。

---

## 18. 3CA 工作流 B：代谢相关 program 与患者级验证

工作流 ID：`WF-3CA-MET-01`

### 18.1 问题

给定一个导师提供、但先经过物种和 ID 校验的代谢基因集，判断它与 3CA 恶性细胞 programs 的重合、排名富集和患者级活性的关系，报告跨癌种复现、异质性、反例和外部验证。

### 18.2 详细流程

#### A. Gene-set 冻结

- 记录来源、物种、版本、原始 ID；
- HGNC/Ensembl 映射、别名、重复、一对多和未映射；
- 保存原始集、有效集和表达矩阵 universe；
- 映射损失超过预设阈值进入 human gate；
- 不因结果不好在分析后删基因。

#### B. Program-level mapping

- top-k overlap，k 在 plan 中冻结；
- 以可检测基因作背景的 hypergeometric/ORA；
- 使用 program 全排名做 directional enrichment；
- 报告核心 leading-edge genes；
- 对 highly overlapping pathways 做 redundancy grouping；
- 与 size/expression-matched 随机 gene sets 比较。

#### C. Patient-level activity

- 在每个 sample/patient 内计算 program/gene-set activity；
- 检查 activity 是否被 library size、线粒体比例、应激、细胞周期或肿瘤纯度驱动；
- 按 cancer/study 估计效应，而不是把所有 cell 合并；
- 跨癌种用效应量 meta-analysis 或明确的层级模型；
- 报告异质性，不只报告 pooled p-value。

#### D. Sensitivity

- 至少两种 activity/scoring 方法；
- leave-one-study 和 leave-one-cancer-out；
- 不同 malignant-cell QC 阈值；
- matched random gene sets；
- label permutation 保留 study/patient 结构；
- 排除单个高权重 gene 后复算。

#### E. External validation

- 先冻结 mapping 和效应方向；
- 在不同 cohort/platform 中复算；
- 报告方向、效应量、CI、复现和 inconclusive；
- 外部集不用于回调主阈值。

#### F. Interpretation

- 若只有转录证据，最高到 M2；
- 若加入 COBRApy/Compass/METAFlux 等模型，必须记录模型版本、交换边界和敏感性，最高到 M3；
- 需要代谢组、Seahorse、同位素示踪或扰动才上升到 M4/M5。[^26][^27]

### 18.3 必需工件

- `results/gene_set_mapping.tsv`
- `results/program_enrichment.parquet`
- `results/patient_activity.parquet`
- `results/cancer_effects.parquet`
- `results/meta_analysis.parquet`
- `results/leading_edge.tsv`
- `validation/matched_null.json`
- `validation/leave_one_out.json`
- `validation/external_validation.json`
- `claims.jsonl` 与 `hypotheses.jsonl`

---

## 19. T 细胞状态/TCR 扩展工作流

工作流 ID：`WF-TCELL-STATE-01`

### 19.1 适用顺序

先在公开 pan-cancer T-cell atlas 和 T-cell stress 数据上开发，再迁移到 BKI/Ludwig 受控数据。内部数据不得进入公开 benchmark、外部模型上下文或公共 memory，除非获得明确授权。

### 19.2 主要分支

1. **Data audit**：CD4/CD8、tumor/adjacent/blood、patient、study、treatment、TCR availability；
2. **Annotation audit**：参考映射 + marker evidence + 不确定细胞；
3. **State scoring**：代谢、应激、耗竭、细胞毒、增殖和 tumor-reactivity signatures；
4. **Patient-aware comparison**：按 patient/sample 汇总，避免 cell-level pseudoreplication；
5. **TCR branch**：只有 paired TCR 且 clonotype 质量足够时启用；
6. **Cross-cancer meta-analysis**：方向、异质性和 leave-one-cancer-out；
7. **External validation**：独立 atlas 或治疗前后队列；
8. **Hypothesis and experimental proposal**：明确关联、模型预测和实验需求。

### 19.3 TCR 特殊检查

- 明确 clonotype 定义：CDR3α/β、V/J、exact/near；
- 双链缺失、多链细胞和重复 barcode 处理；
- expanded clone 阈值预登记；
- patient 内克隆扩增与跨 patient public clone 分开；
- clone-level 和 patient-level 统计分开；
- transcriptomic state 与 clone expansion 的方向和时间关系不能自动等同因果；
- 无足够扩增克隆时返回 `inconclusive`。

### 19.4 MANAscore/类似 signature 的规则

- 保存原始基因、版本和方向；
- 优先连续 score；
- 如使用阈值，应检查 patient-specific 或队列特异性；
- 与耗竭、应激、细胞毒和增殖 signature 做区分效度；
- 在外部癌种检验，而不是把已训练癌种当独立验证；
- signature 与抗原反应性关系应标记为预测，除非有功能实验或已知抗原证据。

---

## 20. 报告与 claim 语言控制

### 20.1 每条 claim 的状态

- `supported`
- `unsupported`
- `contradicted`
- `inconclusive`

### 20.2 证据成熟度

| 等级 | 定义 | 推荐语言 |
|---|---|---|
| E0 | 模型/文献先验，无本项目数据 | “提出/推测” |
| E1 | 单一内部计算观察 | “观察到相关” |
| E2 | 内部敏感性和独立重复稳定 | “在本数据中稳健相关” |
| E3 | 外部队列复现 | “在独立数据中复现” |
| E4 | 正交实验支持 | “获得功能性支持” |
| E5 | 预先设计的扰动/救援支持 | “支持因果机制” |

### 20.3 禁止语言升级

- DE/相关性不得写成“驱动”；
- signature enrichment 不得写成“代谢通量升高”；
- pooled cell p-value 不得写成“患者中显著”；
- 单队列发现不得写成“pan-cancer conserved”；
- 未检索到反例不得写成“无反例”；
- 预印本支持不得与多中心实验验证等权；
- LLM ranking 不得写成“最有临床价值”。

### 20.4 最终报告固定结构

1. Research question and scope；
2. Data snapshot and design；
3. Frozen primary plan；
4. QC and exclusions；
5. Primary results with effect sizes；
6. Sensitivity and negative controls；
7. External validation；
8. Literature support and contradictions；
9. Claims by evidence level；
10. Candidate hypotheses and falsification tests；
11. Limitations and unresolved issues；
12. Reproduction instructions and provenance。

---

## 21. 安全、隐私与数据治理

### 21.1 数据级别

| 级别 | 示例 | 允许执行位置 | 允许的模型调用 |
|---|---|---|---|
| Public | 3CA 公开快照、GEO | 隔离本地/云 | 批准的外部或本地模型 |
| Internal | 未公开但去标识的合作数据 | 项目受控环境 | 仅合同允许端点；默认不外发原始数据 |
| Controlled | 患者/临床、受 DUA 限制 | 指定安全计算环境 | 本地或明确获批服务 |
| Prohibited | 未授权 PHI、凭据、恶意双用途材料 | 不进入 workflow | 禁止 |

### 21.2 执行安全

- 原始数据只读；
- 工作目录只能写当前 run；
- 禁止访问用户 home、SSH key、浏览器 cookie 和系统凭据；
- 网络 egress 默认关闭；
- 包安装必须从冻结 lock 或批准镜像；
- 命令、参数、URL 和文件写入全记录；
- 每个命令有超时和资源限制；
- 输出扫描密钥、PHI 和路径泄漏；
- 外部文献内容不能触发工具调用或政策修改；
- 人类审批后才导出内部报告。

### 21.3 生物安全

BioVeil MATRIX 的初步结果提示，agent scaffold 可能比基础模型单独使用时表现出更高的双用途能力。[^21] 因此：

- 本项目的工具和 skills 限于癌症组学分析与非操作性假设生成；
- 不自动生成或执行病原体增强、毒性优化等高风险 protocol；
- 实验计划进入独立安全审查；
- 安全拒绝和分类结果记录在 run bundle；
- 不以“科研用途”自动豁免高风险操作。

---

## 22. 工程实现：最小但完整

### 22.1 推荐技术边界

v0.1：

- 一个 Python CLI 作为 runner；
- JSON/YAML/JSONL/Parquet 作为契约；
- Docker 或等价隔离环境；
- Python 与 R 子进程；
- 本地文件索引或简单全文检索；
- 现有 Scanpy/Bioconductor/统计包；
- 第一阶段 grader 和 run bundle。

暂不需要：

- Kubernetes；
- 多服务消息队列；
- 图数据库；
- 自建模型网关；
- 自定义 workflow DSL；
- 将所有工具包装成 MCP；
- 对每个逻辑角色启动独立长驻 agent。

当并发任务、多人共享、跨机器恢复或工具数量显著增加时，再评估成熟 workflow engine 和 Workflow Run RO-Crate 集成。[^19]

### 22.2 flow.yaml

```yaml
schema_version: 1.0
flow_id: bio-discovery-flow
flow_version: 0.1.0
entry_state: S0_INTAKE
default_mode: guided
roles:
  orchestrator: {context: primary, tools: [state, skill_router]}
  reviewer: {context: isolated, tools: [artifact_reader, literature_search]}
states:
  S2_DATA_AUDIT:
    skill: data-contract-auditor@1.0.0
    required_outputs: [data_audit.json]
    gates: [data_identity, inference_unit]
    on_pass: S3_PLAN
    on_block: S13_HUMAN_GATE
budgets:
  max_replans: 2
  max_technical_retries_per_step: 2
  wall_clock_seconds: 14400
policies:
  raw_data_read_only: true
  network: restricted
  hidden_gold_access: forbidden
  require_fresh_reproduction: true
```

### 22.3 state.json

```json
{
  "schema_version": "1.0",
  "run_id": "...",
  "task_id": "...",
  "flow_ref": "bio-discovery-flow@0.1.0",
  "current_state": "S7_ROBUSTNESS",
  "completed_states": ["S0_INTAKE", "S1_DATA_FREEZE", "S2_DATA_AUDIT", "S3_PLAN", "S4_PLAN_REVIEW", "S5_PREFLIGHT", "S6_PRIMARY_ANALYSIS"],
  "active_plan_ref": "plan.json",
  "input_manifest_sha256": "...",
  "open_issues": ["WARN_LOW_REPLICATES_OV"],
  "artifacts": ["results/program_enrichment.parquet"],
  "budget": {"used_seconds": 1820, "used_tokens": 44210},
  "last_event_sequence": 231,
  "checkpoint_ref": "checkpoints/cp-007.json",
  "human_approvals": []
}
```

---

## 23. 开发路线图与 Go/No-Go

### M0：第 1–2 周，契约和 runner

交付：

- `flow.yaml`、`state.json`、`plan.json` schemas；
- 第一阶段 task/run/submission 格式适配；
- events logger、checkpoint、预算和错误码；
- 一个 dummy task 从 S0 跑到 S13。

Go/No-Go：重启后可从 checkpoint 恢复；所有状态转移有事件；越权写入被拒绝。

### M1：第 3–5 周，八个核心 skills

交付：

- 八个 v0.1 skills；
- 每个 skill 至少一个 smoke test；
- tool registry；
- deterministic validators；
- independent plan reviewer。

Go/No-Go：同一小型 scRNA task 连续三次产生符合 schema 的工件；错误的 patient/cell 推断单位被 hard block。

### M2：第 6–9 周，3CA MP 工作流

交付：

- 3CA 2023 冻结快照；
- NMF/program discovery、matching、稳定性和 leave-one-cancer-out；
- 干净环境重现；
- 与 private gold 的 grader 对接。

Go/No-Go：至少一个 3CA 子任务端到端自动评分；主要表可由 `reproduce.sh` 重新生成。

### M3：第 10–13 周，代谢工作流

交付：

- gene-set validator；
- program overlap、GSEA/ORA、patient-level activity、meta-analysis；
- matched-null、label permutation、外部验证；
- 代谢证据等级控制。

Go/No-Go：系统不会把转录证据写成 flux/causality；负对照阳性时自动降级或阻断 claim。

### M4：第 14–17 周，P0/P1 对照

交付：

- 2–3 个模型 × 2 个 3CA tasks × 3 trials；
- Direct vs Flow；
- no-stat-guard、no-evidence-review、broad-tools 三个 ablations；
- 分数、失败率、成本、时间和人工干预表。

Go/No-Go：若 P1 没有提高科学分或 hard-failure，停止扩展 agent 数量，回到 skill 和 grader 诊断。

### M5：第 18–24 周，T-cell 公共数据迁移

交付：

- T-cell state 和可选 TCR skills；
- 公开 pan-cancer atlas 外部验证；
- BKI 数据迁移前的权限和本地部署演练。

Go/No-Go：公开数据上达到复现、统计和证据门槛后，才申请进入受控内部数据。

### M6：第 6–12 个月，扩展与第三阶段接口

交付：

- 20–30 个经过 benchmark 验证的 skills；
- 经过筛选的 validated trajectories；
- 失败轨迹、反例和 reviewer corrections；
- 供 SFT/post-training 使用的数据卡和许可清单。

Go/No-Go：任何轨迹进入训练集前必须通过复现、隐私、许可和 leakage 审核。

---

## 24. 人员分工与审核节奏

最小团队：

- 1 名计算生物学负责人：定义任务、skills 和结果边界；
- 1 名 agent/工程负责人：runner、schema、sandbox、events 和 model adapters；
- 1 名生物统计顾问（可兼职）：统计 gates、negative controls 和 grader；
- 1 名领域 PI/肿瘤免疫专家：优先级、反例和最终审批；
- 数据管理员/安全人员在接入内部数据时加入。

建议审核：

- 每个 skill 至少一名领域作者 + 一名独立审阅者；
- 每个 benchmark task 的 workflow 与 gold curator 分离；
- 每周审失败轨迹，不只审最高分；
- 每月冻结一个 flow/skill release，不在正式对照中使用浮动最新版；
- 勘误使用新 patch version，不覆盖历史 run。

---

## 25. 主要失败模式与预防

| 失败模式 | 表现 | 预防/检测 |
|---|---|---|
| 数据版本漂移 | 当前 portal 结果冒充论文快照 | accession + hash + snapshot date + code commit |
| 伪重复 | 数十万细胞产生极小 p 值 | inference-unit gate、pseudobulk/混合模型、patient-level CI |
| 批次与条件混杂 | agent 自动 integration 后仍声称 condition effect | design identifiability gate、batch balance table |
| 数据泄漏 | gold label、作者结果藏在 `uns` 或文件名 | public package scrub、sealed network、leakage scanner |
| 追逐显著性 | 重试不同阈值直到阳性 | frozen primary plan、branch IDs、所有尝试留痕 |
| 运行成功即科学成功 | 退出码 0 但统计或生物解释错 | V1–V7 分层 validation |
| 自我确认 | Analyst 与 Reviewer 共享全部上下文 | isolated reviewer、确定性 checks、外部 cohort |
| 引用幻觉 | DOI 错或来源不支持句子 | citation verifier、claim-level locator、stance 字段 |
| pathway 过度解释 | 名称相似即宣称机制 | core genes、direction、null、冗余和反例 |
| 代谢越级 | RNA 表达写成通量和因果 | M0–M5 等级、正交证据 gate |
| 多 agent 噪声 | 反复交接、成本增加、状态冲突 | 逻辑角色顺序执行；benchmark 证明收益后才物理拆分 |
| memory 污染 | 错误或 gold 被长期复用 | validated-only promotion、split isolation、hash audit |
| 工具面过大 | 选错工具、不可重现、权限扩大 | per-skill allowlist、tool health check、版本冻结 |
| 随机性不受控 | 每次结论不同 | seed、重复、稳定性和 fresh reproduction |
| 共识假象 | 多轨迹共享同一偏差 | 方法多样性、负对照、独立数据优先 |
| 内部数据外泄 | model prompt/log 含受控数据 | offline-sensitive、日志去标识、endpoint allowlist |

---

## 26. 最先实施的具体清单

按优先级：

1. 冻结 `WF-3CA-MP-01` 与 `WF-3CA-MET-01` 的 task 和输入；
2. 定义 `flow.yaml`、`state.json`、`plan.json`、skill result schema；
3. 先做 `dataset-resolver`、`data-contract-auditor`、`gene-set-validator`；
4. 做 inference-unit hard gate；
5. 跑一个 3CA 小子集 preflight；
6. 接入 program discovery 和 task-specific grader；
7. 做 matched gene-set、label permutation 和 leave-one-cancer-out；
8. 做 claim/evidence ledger 与独立 Reviewer；
9. 在干净环境重跑；
10. 同一模型做 P0 Direct 与 P1 Flow 的三次配对实验；
11. 只有看到具体失败类型后，再新增 skill；
12. 只有看到多角色确实提高分数后，再增加物理 agent。

这套顺序把项目最重要的科学风险——数据找错、统计单位错、代谢过度解释、缺乏反例、无法复算——放在系统最前面，而不是把工程投入优先用在 UI、agent 数量或 prompt 长度上。

---

## 27. 十条不可妥协的规则

1. **先冻结数据，后分析。**
2. **先确认推断单位，后做显著性检验。**
3. **主分析先冻结，观察结果后的修改另开 exploratory branch。**
4. **skill 必须有 schema、validator、版本和停止条件。**
5. **工具运行成功不等于科学正确。**
6. **LLM reviewer 不得豁免确定性 hard gate。**
7. **每条主要 claim 必须指向数据工件和证据。**
8. **负对照、敏感性和外部验证至少占其一，发现任务原则上三者都要。**
9. **允许 unsupported、contradicted 和 inconclusive。**
10. **只有通过复算、隐私和 leakage 审核的轨迹才能进入长期 memory 和第三阶段训练集。**

---

## 28. 与现有项目文档的关系

- 第一阶段的任务、工件、轨迹和 leaderboard 规范见：[第一阶段 Benchmark 数据集构建规则](C:/Users/User/Desktop/agentic/第一阶段_生物医学科学发现Benchmark数据集构建规则.md)。
- 三阶段总体研究路线、3CA/代谢/T-cell 背景和证据边界见：[三阶段完整方案](C:/Users/User/Desktop/agentic/3CA_生物医学科学发现Agent三阶段完整方案.md)。
- 导师会议中对 human-aligned skill library、可复用 workflow，以及“一句话 prompt vs 写入人类工作流程和工具的 agent flow”的讨论见：[会议记录稿件](C:/Users/User/Desktop/agentic/material/会议记录稿件.md)。
- BKI/Ludwig 演示材料只用于界定受控数据下的高层研究需求，不作为公开 benchmark 数据或未经授权的训练来源。

---

## Sources

[^1]: Poddar S. et al. [HeaRT: A Hierarchical Circuit Reasoning Tree-Based Agentic Framework for AMS Design Optimization](https://arxiv.org/abs/2511.19669). arXiv, 2025. 预印本；重点核对离线层级树、在线 query-conditioned traversal、优化器连接和实验限制。
[^2]: Ahmadzadeh M., Chen K., Gielen G. [AnaFlow: Agentic LLM-based Workflow for Reasoning-Driven Explainable and Sample-Efficient Analog Circuit Sizing](https://arxiv.org/abs/2511.03697). ICCAD 2025 / arXiv. 重点核对先 DC operating-point、再高成本仿真的分阶段策略。
[^3]: Wang S. et al. [Multi-Agent Generative Synthesis for Analog/RF Circuit: from Scalable Topology Generation to Efficient Inverse Design](https://doi.org/10.1109/ICCAD66269.2025.11240792). ICCAD 2025. 同行评议会议论文；IEEE 公开摘要支持 topology generation 与 device-parameter inverse design 的两阶段表述。
[^4]: Xing Y. et al. [RF-Agent: A Practical Framework for Building Language Agents for RFIC Design](https://arxiv.org/abs/2607.18772). arXiv, 2026. 预印本；七本教材、QTSA 数据、SFT/RAG 比较等数字来自作者报告。
[^5]: Lu H. et al. [RFAmpDesigner: A Self-Evolving Multi-Agent LLM Framework for Automated Radio Frequency Amplifier Design](https://arxiv.org/abs/2605.10093). arXiv, 2026. 预印本；用于动作成本和经验复用设计参考。
[^6]: Zhou J. et al. [An AI Agent for Fully Automated Multi-Omic Analyses](https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202407094). Advanced Science, 2024. AutoBA 官方论文。
[^7]: Xiao Y. et al. [CellAgent: An LLM-driven Multi-Agent Framework for Automated Single-cell Data Analysis](https://arxiv.org/abs/2407.09811). ICLR 2026 conference paper / arXiv. 规划、执行、评价和自迭代机制来自论文；本方案另审阅了公开代码的具体实现。
[^8]: Alber S. et al. [CellVoyager: AI CompBio agent generates new insights by autonomously analyzing biological data](https://www.nature.com/articles/s41592-026-03029-6). Nature Methods, 2026；[official repository](https://github.com/zou-group/CellVoyager)。
[^9]: Wang Z. et al. [GeneAgent: self-verification language agent for gene-set analysis using domain databases](https://www.nature.com/articles/s41592-025-02748-6). Nature Methods, 2025；[official code](https://github.com/ncbi-nlp/GeneAgent)。
[^10]: Qu Y. et al. [CRISPR-GPT for agentic automation of gene-editing experiments](https://www.nature.com/articles/s41551-025-01463-z). Nature Biomedical Engineering, 2025.
[^11]: Huang K. et al. [Biomni: A General-Purpose Biomedical AI Agent](https://www.biorxiv.org/content/10.1101/2025.05.30.656746v1). bioRxiv, 2025；[official repository](https://github.com/snap-stanford/Biomni)。截至本稿按预印本处理；安全警告来自官方 README。
[^12]: [Empowering AI data scientists using a multi-agent LLM framework with self-evolving capabilities for autonomous, tool-aware biomedical data analyses](https://www.nature.com/articles/s41551-026-01634-6). Nature Biomedical Engineering, 2026. BioMedAgent；论文页面同时给出 BioMed-AQA 数据和运行过程入口。
[^13]: [OpenScientist: evaluating an open agentic AI co-scientist to accelerate biomedical discovery](https://pmc.ncbi.nlm.nih.gov/articles/PMC13015679/). 2026；[official repository](https://github.com/openscientist-io/openscientist)。证据较新，方案只吸收 skills、KSDS、Docker 和负对照机制。
[^14]: Loecker J. et al. [MechAInistic: A Reviewer-Supervised Multi-Agent LLM System for Auditable Mechanistic Drug-Hypothesis Generation](https://pubmed.ncbi.nlm.nih.gov/42182411/). bioRxiv/PMC, 2026. 预印本。
[^15]: Gottweis J. et al. [Accelerating scientific discovery with Co-Scientist](https://www.nature.com/articles/s41586-026-10644-y). Nature, 2026.
[^16]: Ghareeb A.E. et al. [A multi-agent system for automating scientific discovery](https://www.nature.com/articles/s41586-026-10652-y). Nature, 2026. Robin；重点核对文献 agent、Finch 数据分析、多轨迹和确定性工作流观察。
[^17]: [Optimizing genomics-aware clinical agents in precision oncology](https://www.nature.com/articles/s41540-026-00753-9). npj Systems Biology and Applications, 2026. 属于肿瘤临床问答场景，本方案只迁移“受控工具和版本化知识优于开放工具面”的架构证据。
[^18]: [Skill-Augmented Frontier Agents Nearly Saturate BixBench-Verified-50](https://www.biorxiv.org/content/10.64898/2026.04.28.721523v1). bioRxiv, 2026. 预印本；因样本规模和发布时间，只作待复验信号。
[^19]: ResearchObject community. [Workflow Run RO-Crate](https://www.researchobject.org/workflow-run-crate/). 用于 workflow 输入、输出、代码、容器和运行 provenance 的开放规范。
[^20]: W3C. [PROV-O: The PROV Ontology](https://www.w3.org/TR/2013/REC-prov-o-20130430/). W3C Recommendation, 2013.
[^21]: [BioVeil MATRIX: Uncovering and categorizing vulnerabilities of agentic biological AI scientists](https://arxiv.org/abs/2605.00927). arXiv, 2026. 预印本；用于 agent-level 双用途风险提示，不作为定量安全定论。
[^22]: Squair J.W. et al. [Confronting false discoveries in single-cell differential expression](https://www.nature.com/articles/s41467-021-25960-2). Nature Communications, 2021.
[^23]: Zimmerman K.D. et al. [A practical solution to pseudoreplication bias in single-cell studies](https://www.nature.com/articles/s41467-021-21038-1). Nature Communications, 2021.
[^24]: Nguyen H.C.T. et al. [Benchmarking integration of single-cell differential expression](https://www.nature.com/articles/s41467-023-37126-3). Nature Communications, 2023.
[^25]: Geistlinger L. et al. [Toward a gold standard for benchmarking gene set enrichment analysis](https://academic.oup.com/bib/article/22/1/545/5722384). Briefings in Bioinformatics, 2021.
[^26]: Li Z. et al. [Characterizing cancer metabolism from bulk and single-cell RNA-seq data using METAFlux](https://www.nature.com/articles/s41467-023-40457-w). Nature Communications, 2023.
[^27]: Artyomov M.N., Van den Bossche J. et al. [Systems-based approaches to study immunometabolism](https://www.nature.com/articles/s41423-021-00783-9). Cellular & Molecular Immunology, 2022.
[^28]: Skarlinski M.D. et al. [Language agents achieve superhuman synthesis of scientific knowledge](https://arxiv.org/abs/2409.13740). arXiv, 2024；[PaperQA official repository](https://github.com/future-house/paper-qa)。
[^29]: Gavish A. et al. [Hallmarks of transcriptional intratumour heterogeneity across a thousand tumours](https://www.nature.com/articles/s41586-023-06130-4). Nature, 2023.
[^30]: Tirosh Lab. [3CA official repository](https://github.com/tiroshlab/3ca)；[3CA portal](https://www.weizmann.ac.il/sites/3CA/)；[2023 data snapshot](https://doi.org/10.5281/zenodo.7688626)。
