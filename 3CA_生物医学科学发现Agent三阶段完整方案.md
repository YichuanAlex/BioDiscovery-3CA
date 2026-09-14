# 生物医学科学发现 Agent：Benchmark、可靠工作流与小模型训练的三阶段完整方案

## 0. 执行摘要

这项工作的核心，不应被定义为“让大模型读论文并给出看起来合理的答案”，而应被定义为：

> 在冻结的数据、问题、工具权限和计算预算下，检验一个模型—工作流系统能否产生可执行、可追溯、统计上成立且与已知证据一致的生物医学发现；再将稳定的专家流程编码为 skills，最后把高质量执行轨迹蒸馏到较小模型中。

上传材料与进一步检索到的证据共同支持这一总体方向，但也要求做出几个关键收缩：

1. **leaderboard 的参赛对象必须是“模型 + agent scaffold + skills + 工具 + 预算”的完整配置，而不只是模型名称。** ScienceAgentBench、PaperBench、BixBench、CellVoyager 等工作均表明，科研任务表现高度依赖代码执行、环境、工具和验证器；只报告“某模型准确率”会混淆模型能力与系统工程能力。<sup>[[9]](#source-9)</sup><sup>[[10]](#source-10)</sup><sup>[[12]](#source-12)</sup><sup>[[17]](#source-17)</sup>
2. **不要第一天就整理 100–200 篇论文。** 先用 20–30 篇论文形成 40–60 个可运行任务，证明任务封装、评分和防泄漏方案有效；再扩展到 120 篇、约 240 个任务。120 篇位于导师建议的范围内，也足以进行分层统计。
3. **主榜只评“受约束的再发现”，不把开放式灵感写作当主要分数。** 开放式假设生成可以作为挑战赛，但主要 benchmark 必须有冻结输入、原子化结论和可计算评分。
4. **工作流先做一个编排器、一个证据账本和一个独立验证器。** Co-Scientist 的多个 agent 角色提供了很有价值的认知分工，但不应机械复制成六个自由对话的 agent。第一版把 Generation、Reflection、Ranking、Evolution、Meta-review 映射成有输入输出契约的步骤；只有消融实验显示多 agent 确有增益时，才增加并行角色。<sup>[[8]](#source-8)</sup>
5. **3CA 试点必须拆成两个问题。** 一是严格复现 2023 Nature 论文的恶性细胞内肿瘤异质性程序；二是在更新后的 3CA 和 T 细胞数据上研究导师给定代谢基因集。后者是外推或新分析，不能写成“复现了 2023 论文”。2023 论文使用 77 个研究、1,456 个样本并在过滤后分析 1,163 个样本；当前 3CA 门户已更新到 124 个研究、2,836 个样本和 5,658,705 个细胞，两者不是同一冻结数据版本。<sup>[[3]](#source-3)</sup><sup>[[4]](#source-4)</sup><sup>[[5]](#source-5)</sup>
6. **小模型训练是第三阶段的工程假设，不是已证实结论。** 现有生物医学小模型多在医学问答或知识任务上验证，尚不能证明 8B/16B/32B 模型能在这里达到或超过通用前沿模型。合理路线是先在一个 7–9B 开源基座上做 QLoRA/SFT，再做偏好优化；只有建立了可靠、难以投机的自动奖励后，才考虑在线强化学习。<sup>[[37]](#source-37)</sup><sup>[[38]](#source-38)</sup><sup>[[39]](#source-39)</sup><sup>[[40]](#source-40)</sup>

建议把博士阶段或长期项目的主线固定为以下闭环：

    冻结论文与数据
          ↓
    标准任务 + 可执行评分器
          ↓
    一句话 prompt / 通用 agent / 领域 skills / 完整 workflow 对照
          ↓
    产生带证据和失败记录的执行轨迹
          ↓
    SFT → 偏好优化 → 必要时强化学习
          ↓
    回到未见过的论文族和封闭测试集评估
          ↺

最先应该交付的不是庞大的平台，而是一个端到端、可重复的 3CA 代谢试点：同一问题、同一数据、同一预算，比较“一句话 prompt”与“显式专家工作流 + 必要工具”，并让评分器自动判断数据是否找对、统计单位是否正确、主要结论是否被重新发现。会议中导师对这一对照方向给出了明确肯定。<sup>[[2]](#source-2)</sup>

---

## 1. 从现有材料得到的研究边界

### 1.1 四组材料分别解决什么问题

| 材料 | 能提供的东西 | 不能直接推出的东西 |
|---|---|---|
| 2023 Nature 3CA 论文与代码 | 一个高质量的 pan-cancer 单细胞“已知发现”来源；冻结方法、恶性细胞程序、41 个 meta-program 和 11 类 hallmarks | 不能自动代表 T 细胞图谱；不能证明当前 3CA 门户上的结果等同于 2023 冻结版本 |
| 当前 3CA 门户与 3CA v2 代码 | 更大规模的数据入口、更新的细胞类型和 T 细胞相关基因集，可用于外部泛化和新问题 | 网站展示结果不是自动化 benchmark 的稳定数据接口；更新数据不能替代冻结基准 |
| BKI/Ludwig T 细胞图谱材料 | 指出正式合作阶段的真实需求：动态参考映射、临床元数据、患者/批次校正、TCR 克隆与肿瘤反应性工具 | 属于合作或未公开内容，不能未经书面授权进入公开 benchmark、训练集或报告细节 |
| Co-Scientist 与相关科研 agent 论文 | 给出生成、反思、排序、演化、元审查、人机协作等认知模块；表明工具化科研 agent 可以产生可验证候选 | 不能证明其完整系统已开源；第三方复现仓库只能作为工程参考，不能当作官方复现或生物学证据 |

上传的检索记录正确识别了 3CA 官方代码、Zenodo 数据、MSigDB C4:3CA、MANAscore 与 Clonotrace 等重要资源；需要修正的重点有两点：第一，Co-Scientist 第三方实现不能代替官方方法学证据；第二，scMetabolism 是伴随结直肠癌肝转移研究发布的分析包，不能把它当成经过独立系统 benchmark 的“代谢真值生成器”。<sup>[[1]](#source-1)</sup><sup>[[24]](#source-24)</sup>

### 1.2 当前 3CA 试点与正式 BKI 项目要分层

会议记录反映了两个时间尺度：

- **入组或合作前能力测试：** agent 自动定位 3CA 资源，分析导师给定的代谢基因集，并与 2023 Nature 的已知程序比较。允许 AI 方法或传统生物统计方法，重点是能否可靠完成整个过程。
- **正式合作项目：** 面向 BKI pan-cancer T-cell atlas 的映射、状态解释、TCR/克隆信息、临床元数据及可能的网页/AI 接口。这一部分应在权限、保密和数据使用边界明确后开始。

因此，本方案将 3CA 作为公开、可复现的第一条跑道，把 BKI 作为通过质量门槛后的第二条迁移跑道。二者共享 workflow 和 skill 接口，但不共享未经授权的数据与训练轨迹。BKI 部分只采用用户提供的内部演示材料所允许的高层研究方向，不在本报告中展开未公开数据、结果或合作细节。<sup>[[43]](#source-43)</sup>

### 1.3 事实、假设与工程选择必须分开记录

建议每一条结论都标记为以下四类之一：

- **E1 已验证事实：** 在同行评审论文和对应数据中有直接证据。
- **E2 可复现发现：** 本项目在冻结数据上重新得到，且通过预设评分。
- **H 研究假设：** 有机制或关联依据，但尚未在独立数据或实验中验证。
- **D 工程设计：** benchmark、权重、模型或软件架构的选择，不是生物学结论。

例如，“2023 论文得到 41 个 meta-program”是 E1；“某代谢基因集在更新 3CA 的 CD8 T 细胞中与呼吸程序相关”在完成分析前是 H；“科学分数中结果工件占 45%”是 D；“小模型超过前沿模型”目前仍是 H，而不是 E1 或 E2。

---

## 2. 总体研究设计

### 2.1 三阶段之间的依赖关系

| 阶段 | 核心问题 | 主要输入 | 主要输出 | 进入下一阶段的硬门槛 |
|---|---|---|---|---|
| 第一阶段：Benchmark | 系统能否在相同条件下重新发现已知结论？ | 冻结论文、数据、任务、评分器 | 标准任务集、评分器、基线结果、leaderboard | 至少 80% 任务可重复执行；关键评分器人工一致性达到预设标准；没有论文族泄漏 |
| 第二阶段：Workflow | 哪些专家步骤真正提高可靠性？ | benchmark 任务、领域方法与工具 | skills、编排器、证据账本、错误恢复、消融结果 | 领域 workflow 对主基线有统计显著且跨任务族稳定的增益 |
| 第三阶段：小模型 | 能否以更低成本复制稳定 workflow？ | 经过审计的执行轨迹、偏好对、失败轨迹 | SFT/DPO 模型、工具策略、成本—性能曲线 | 在完全封闭的论文族上达到预设科学分数、校准和安全门槛 |

这里的关键逻辑是：**benchmark 先定义什么叫“做对”，workflow 再提高做对的概率，训练最后把已经有效的行为压缩进模型。** 如果第一阶段评分不可信，第三阶段只会训练模型去迎合一个错误奖励。

### 2.2 研究对象不是单一模型

每次实验的最小可复现配置应写成：

> 模型版本 × 推理强度 × agent scaffold 版本 × skill 集版本 × 工具镜像 × 数据快照 × 网络权限 × 时间/令牌/费用预算 × 随机种子

同一模型在“一句话 prompt”和“领域 workflow”下应当作为两个独立参赛配置。不同模型比较时，必须同时报告两种预算：

- **等资源比较：** 相同时间、最大工具调用数和近似费用；
- **最佳能力比较：** 每个系统在预先规定的最高预算内发挥最佳表现。

费用和延迟不应混入科学正确性主分数，而应形成 Pareto 图：横轴成本或时间，纵轴科学分数。否则廉价但错误的系统和昂贵但可靠的系统会被一个不可解释的总分掩盖。

---

## 3. 第一阶段：建立科学发现 Benchmark

## 3.1 先做 30 篇，再扩到 120 篇

### 版本 0：可行性试点

- 20–30 篇论文；
- 每篇 1–3 个任务，共 40–60 个任务；
- 仅纳入公开数据、公开方法、可在合理计算资源中运行的任务；
- 至少覆盖单细胞 QC、差异表达、基因程序、通路/代谢、T 细胞状态、TCR/克隆和外部验证；
- 目标不是发布榜单，而是验证 task capsule、评分器和泄漏防护。

### 版本 1：正式 benchmark

建议固定为 **120 篇论文、约 240 个任务**。推荐分布如下：

| 论文族 | 论文数 | 代表任务 |
|---|---:|---|
| 恶性细胞状态、转录程序与肿瘤内异质性 | 25 | NMF/程序复现、meta-program 匹配、跨癌种保守性 |
| T 细胞状态、耗竭/应激、肿瘤反应性与 TCR | 25 | 状态识别、反应性评分、克隆扩增/迁移 |
| 癌症代谢与免疫代谢 | 20 | 基因集评分、代谢通路差异、转录—通量推断一致性 |
| 肿瘤微环境、空间与多模态 | 15 | 细胞组成、空间邻域、跨模态关联 |
| 治疗反应、预后与生物标志物 | 20 | 患者级分类、生存、独立队列复现 |
| 扰动、CRISPR 与正交实验验证 | 15 | 扰动方向、靶点优先级、实验结果一致性 |
| **合计** | **120** | 约 240 个原子或组合任务 |

这个结构比简单随机抽取 120 篇更重要。随机抽取会被数据容易获得的癌种、常用任务和热门方法支配，最后只能测出“谁更会做差异表达”。

## 3.2 论文纳入与排除标准

每篇候选论文由两名领域评审者独立按 0–2 分评价六项：

1. **科学相关性：** 是否属于癌症、代谢、细胞状态或可迁移的方法任务；
2. **数据可获得性：** 原始数据、处理数据、明确 accession 和下载权限；
3. **方法可执行性：** 分析步骤、参数、代码或足够详细的方法；
4. **结论可计算性：** 至少有一个能表示为方向、效应、排序、集合或预测指标的核心结论；
5. **验证强度：** 是否有跨队列、正交模态、扰动或实验验证；
6. **许可与治理：** 数据、代码、衍生物和公开发布是否允许。

建议总分至少 9/12，且“数据可获得性”“结论可计算性”“许可与治理”三项不得为 0。分歧由第三人裁决。同行评审论文作为主体；高影响但尚未同行评审的方法可进入“前沿扩展集”，不得与主榜混为一体。

按数据可用性再分三层：

- **A 级：** 原始或接近原始数据公开，能从 QC 开始复现；
- **B 级：** 处理后的表达矩阵/嵌入/元数据公开，能复现主要分析；
- **C 级：** 只有作者汇总表或图中数值。只适合局部任务或教学，不进入主发现榜。

## 3.3 任务必须有三条独立跑道

### R1：方法复现跑道

向 agent 提供论文 Methods、必要背景和数据，但隐藏 Results、图注中的结论以及作者代码的最终结果。测试的是：能否把描述转成可运行分析并产生接近论文的工件。

### R2：盲法再发现跑道

只给中性科学问题、数据字典、数据和允许使用的通用工具；隐藏目标论文标题、结果、特征基因和最终参数。该跑道是主 leaderboard，因为它最接近“从数据重新得到已知发现”。

### R3：外部泛化跑道

把在源论文中提出的结论放到独立队列、更新数据版本或相邻癌种中检验。它回答“系统是在复制作者路径，还是掌握了可迁移的分析原则”。

开放式新假设可设为 R4 挑战赛，但应单独评审。它不宜进入主分数，因为新颖性、可行性和真伪在短期内通常没有确定答案。

## 3.4 每个 task capsule 的标准结构

每个任务不是一个自然语言问题，而是一个版本化 capsule：

| 字段 | 内容 |
|---|---|
| task_id / version | 永久标识和语义化版本 |
| source_record | 论文 DOI、数据 accession、代码 commit、发布日期 |
| scientific_question | 不泄露结论的中性问题 |
| unit_of_inference | 患者、样本、克隆、细胞或研究；必须显式 |
| input_manifest | 文件、校验和、大小、格式、样本数、许可 |
| allowed_resources | 网络、文献、包、数据库、GPU/CPU、时间限制 |
| output_schema | 必交表格、图、结构化结论和运行日志 |
| claim_ledger | 原子结论、方向、效应范围、证据等级和接受规则 |
| gold_artifacts | 作者结果或独立复现的参考工件 |
| graders | 确定性评分器、统计容差、人工复核规则 |
| negative_controls | 标签置换、无关基因集、样本打乱或空任务 |
| provenance | 环境镜像、包版本、随机种子、处理历史 |
| leakage_notes | 预训练记忆、公开答案、相同数据家族等风险 |

### 从论文到可发布任务的九步生产线

1. **检索登记：** 保存检索式、数据库、日期、命中数和去重记录；
2. **题录筛选：** 两人独立按六项标准筛选，记录排除原因；
3. **数据 dry run：** 在写任务前实际下载文件、核对哈希并打开数据；无法稳定获取的数据降级或排除；
4. **claim 抽取：** 把正文、图、补充材料中的主要结论拆成原子 claims，并标出直接证据；
5. **独立复现：** 一名未参与原论文的分析者按 Methods 重跑，记录哪些结论能复现、哪些依赖未公开步骤；
6. **任务遮蔽：** 移除题名、作者、结果、答案基因和可直接定位原文的线索，形成 R1/R2 输入；
7. **gold 与 grader：** 将作者工件和独立复现工件综合成容差范围；优先建立数值和 schema 评分；
8. **red-team：** 测试错误文件、标签置换、单位混淆、伪造引用和空输出能否被 grader 识别；
9. **版本发布：** 冻结 capsule、数据 manifest、环境和测试记录；任何实质变化增加版本号。

gold 不应只等于作者输出。如果独立复现发现原论文的参数缺失、数值不一致或结论不稳，应把该 claim 标记为“有争议/范围受限”，保留多个可接受实现，必要时不计入自动主分。这样 benchmark 才不会把论文中的偶然错误固化成模型目标。

为兼顾局部能力和真实研究，建议每篇论文尽量产生两类任务：

- **原子任务：** 一个明确输入—输出，例如 cell-state annotation、DE、通路富集或克隆分类；
- **组合任务：** 从数据确认到结论报告的 5–10 步 study-scale 分析。

正式集合中可将约 20% 设为原子/低难度任务、50% 为多步中等任务、30% 为 study-scale 高难度任务。BixBench3 对原始数据级任务的结果提示，大数据和长序列分析明显更困难，因此不能只用短任务推断 agent 的真实发现能力。<sup>[[11]](#source-11)</sup>

按试点阶段的规划估算，一篇论文完成下载、claim ledger、独立复现、grader 和复核通常需要数个人日；这个数字必须在前 10 篇中实测。若平均每篇超过预期，优先减少同质论文、复用同一 task family 的 grader，而不是降低双人审核和独立复现标准。

一个最小任务定义可以是：

    task_id: 3ca_mp_hypoxia_01
    track: blind_rediscovery
    question: 哪些恶性细胞转录程序在多个癌种中稳定出现并与低氧相关？
    inference_unit: tumor_sample
    inputs:
      - frozen_expression_matrix
      - sample_metadata
    hidden:
      - source_results
      - MP_gene_lists
      - figure_legends
    required_outputs:
      - programs.tsv
      - matched_meta_programs.tsv
      - claims.json
      - provenance.json
    primary_metrics:
      - program_overlap
      - sample_score_correlation
      - cross_cancer_recurrence

## 3.5 “已知结论”要拆成原子 claim

不能用“报告与原论文大致一致”作为 gold standard。每篇论文应由生物学家和统计学家共同建立 claim ledger。每条 claim 至少包括：

- 实体：细胞状态、通路、基因、癌种、治疗或临床结局；
- 关系：升高、降低、富集、相关、预测、必要、充分或无关联；
- 方向和效应；
- 适用范围：癌种、细胞类型、时间点和人群；
- 最小证据：分析、外部验证、扰动或实验；
- 可接受容差；
- 原论文证据位置；
- 反例和限制。

例如，“CD8 T 细胞中糖酵解得分更高”仍不完整，至少要写清在哪个队列、比较哪两个状态、以患者还是细胞为统计单位、使用何种通路基因集、效应方向在多少研究中成立。只有这样，评分器才能区分“方向正确但统计单位错了”和“真正复现”。

## 3.6 数据冻结与标准化

每个任务同时保留两种入口：

- **原始入口：** GEO/SRA/ArrayExpress/Zenodo 等原始或作者格式，用于测试数据定位、格式解析和版本确认；
- **标准入口：** 冻结后的 h5ad、parquet、TSV 或其他统一格式，用于比较下游科学推理，避免下载失败和格式差异掩盖模型能力。

主榜应分别报告：

- DataOps 分数：能否找到正确数据、校验版本、构建分析对象；
- Science 分数：在相同标准输入上能否得到正确结论。

所有数据文件使用内容哈希；容器或环境锁定语言和依赖版本；原始数据只读；每次运行在隔离目录中产生工件。3CA 的 2023 冻结版本应优先使用论文对应代码和 Zenodo 快照，而不是实时抓取网页。3CA 官方仓库已经分别提供 ITH_hallmarks 和 3CA_v2 代码路径，可作为版本化实现依据。<sup>[[6]](#source-6)</sup>

## 3.7 训练、开发、测试不能按任务随机切分

同一论文、同一 accession、同一患者队列或同一派生数据必须属于同一 split。否则一个任务可能出现在开发集，而同一矩阵的另一个问题出现在测试集，造成严重泄漏。

120 篇论文建议分为：

- 60 篇公开开发集：任务、数据、评分器全部公开；
- 30 篇封闭测试集：问题和输入可见，gold 与评分器核心隐藏；
- 30 篇滚动新鲜集：按季度或半年更新，优先加入近期论文或新释放数据。

公共论文已经可能进入模型预训练，无法彻底消除记忆。可采取四种补救：

1. 从提示中移除论文标题、作者和能直接搜索答案的 accession；
2. 使用中性问题和重新组织的输入文件；
3. 加入独立队列、更新版数据和标签置换负对照；
4. 维护新鲜封闭集，并单独报告“潜在污染集”与“低污染集”。

如果模型在真实数据上复述正确结论，却在标签置换数据上仍给出相同答案，应判定存在答案记忆或确认偏差，不能计入再发现分数。LAB-Bench 使用公开/私有题目来监测污染，GeneBench-Pro 使用受控生成问题和确定性评分，这些设计都说明封闭或新鲜测试集不可省略。<sup>[[13]](#source-13)</sup><sup>[[14]](#source-14)</sup>

## 3.8 任务族与自动评分指标

### A. 数据定位和版本确认

- accession、物种、平台、样本数、文件哈希是否正确；
- 论文队列与下载队列的一致率；
- 是否发现撤回、替换、版本更新或缺失文件；
- 结果可重复下载比例。

### B. 单细胞 QC 与样本审计

- 与人工审计或 gold 标签相比的异常样本召回率和精确率；
- 双细胞、低质量细胞、环境 RNA 的检测一致性；
- 保留细胞数和关键群体保留率；
- 对阈值扰动的稳定性。

QC 不应只评“删掉多少细胞”。更重要的是避免某一病例、组织处理批次或稀有生物群体被系统性删除。

### C. 细胞类型和状态

- macro-F1、balanced accuracy、AUROC/AUPRC；
- 层级标签距离，例如把 CD8 effector 误判成 CD8 memory 比误判成肿瘤细胞惩罚小；
- 未知类拒绝率和校准误差；
- 患者留一法、研究留一法的泛化。

### D. 差异表达和关联

- log fold-change 的 Spearman 相关；
- 方向一致率；
- 显著基因集合的 Jaccard/加权重合；
- 假阳性率、FDR 校准；
- 以患者/样本为单位的 pseudobulk 或混合模型是否正确。

单细胞不能默认把每个细胞当成独立生物重复。多项研究显示，忽略层级结构会夸大有效样本量和 I 类错误；pseudobulk 或适当的混合模型通常更可靠。<sup>[[19]](#source-19)</sup><sup>[[20]](#source-20)</sup>

### E. 基因程序、NMF 和 meta-program

- 用 Hungarian matching 在发现程序与 gold 程序之间做最佳匹配；
- top genes 的加权 Jaccard 或 overlap coefficient；
- 程序得分在样本中的相关；
- 跨癌种复现比例；
- 程序数选择稳定性；
- 对随机初始化、细胞下采样和基因过滤的敏感性。

### F. 基因集与代谢

- 通路排名相关、方向一致率、已知阳性/阴性通路 AUPRC；
- 两种不同评分算法的一致性；
- 与独立蛋白组、代谢组、同位素示踪或功能实验的一致性；
- 对表达量匹配的随机基因集是否显著；
- 将“表达程序”“代谢潜能”“模型推断通量”和“实测通量”分开评分。

Compass、scFEA 和 METAFlux 都利用转录数据推断代谢状态或通量，但假设和分辨率不同；METAFlux 明确采用群体或细胞簇层面的约束以应对单细胞稀疏性。任何 agent 如果仅凭通路打分就声称“代谢通量升高”，应在证据准确性上扣分。<sup>[[21]](#source-21)</sup><sup>[[22]](#source-22)</sup><sup>[[23]](#source-23)</sup>

### G. TCR、克隆和肿瘤反应性

- 肿瘤反应性标签的 AUROC/AUPRC；
- 克隆扩增与状态富集的 odds ratio 和置信区间；
- 克隆迁移或状态转变与参考结果的一致性；
- 不同患者阈值下的敏感性；
- 配对 TCR 缺失和低克隆数时能否拒绝分析。

MANAscore 的三基因框架为 ENTPD1、CXCL13 和 IL7R，论文同时强调阈值具有患者异质性，不能把一个固定 cut-off 当成跨队列真理。Clonotrace 适合有足够扩增克隆的配对 TCR—转录组数据，但当前证据成熟度低于已同行评审工具，应放在扩展集并显式标记。<sup>[[28]](#source-28)</sup><sup>[[29]](#source-29)</sup>

### H. 临床预测和生存

- AUROC/AUPRC、C-index、time-dependent AUC、Brier score；
- 校准曲线和 decision-curve net benefit；
- 患者级拆分、时间外验证和机构外验证；
- 与简单临床基线的增量价值；
- 缺失数据、批次和治疗线别敏感性。

### I. 原子结论和证据

结论输出使用结构化 claim，而非只交一份 prose：

    {
      "entity": "CD8_T_cell",
      "relation": "higher_pathway_activity",
      "target": "oxidative_phosphorylation",
      "comparison": "state_A_vs_state_B",
      "direction": "positive",
      "effect": 0.42,
      "uncertainty": {"ci95": [0.21, 0.63], "q": 0.004},
      "inference_unit": "patient",
      "evidence": ["result_table_3", "figure_2b"],
      "status": "supported"
    }

评分优先使用规则和数值比较；语言模型 judge 只处理无法规则化的范围限定、证据质量和论证一致性，并且必须由盲法人工抽样校准。PaperBench 使用作者参与构建的细粒度 rubric，BixBench 以分析工件和发现问题为中心，这两类经验都比“让另一个模型整体打分”更可靠。<sup>[[10]](#source-10)</sup><sup>[[12]](#source-12)</sup>

## 3.9 建议的总分与硬门槛

主科学分数建议为：

    Scientific Score
      = 45% 结果工件正确性
      + 25% 原子结论正确性
      + 15% 稳健性与敏感性
      + 15% 可追溯性与不确定性报告

同时设置以下硬门槛：

- 数据集或物种错误：该任务总分为 0；
- 将细胞错误当成生物重复并产生核心显著性结论：总分最高不超过 40；
- 无法复现环境或缺失主要工件：总分最高不超过 60；
- 引用不存在的论文或伪造结果：证据分为 0，并单独报告幻觉事件；
- 负对照仍输出同一肯定结论：结论分为 0；
- 未经授权外传受控数据：安全失败，整次运行无效。

45/25/15/15 是第一版工程权重，应在 20–30 篇试点中通过评审者一致性和专家排序进行校准，而不是宣称为普适标准。

## 3.10 统计比较方案

- 每个系统至少运行一次全部任务；
- 在按难度、任务族、数据规模分层抽取的 20% 任务上运行 3 次，估计随机性；
- 预算允许后，正式榜对全部测试任务运行 3 次；
- 使用以论文或数据集为聚类单位的 bootstrap 置信区间，而不是把 240 个任务都视为完全独立；
- 系统间采用配对比较，报告平均差、置信区间、胜/平/负比例；
- 多个 task family 同时检验时控制 FDR；
- 同时报告失败率、拒绝率、无效运行率和校准，而不只报告成功任务平均值。

榜单中每一行是一个完整配置，并至少显示：

| 配置 | Science | DataOps | Robustness | Calibration | Invalid runs | Median cost | Median time |
|---|---:|---:|---:|---:|---:|---:|---:|
| Model A + one-line prompt |  |  |  |  |  |  |  |
| Model A + generic tools |  |  |  |  |  |  |  |
| Model A + domain skills |  |  |  |  |  |  |  |
| Model A + full workflow/critic |  |  |  |  |  |  |  |

## 3.11 第一阶段必须包含的对照实验

这正是导师会议建议可以形成论文贡献的部分：

1. **P0 一句话 prompt：** 只给问题和基本文件说明；
2. **P1 详细 prompt：** 给分析要求，但没有工具化 skill；
3. **P2 通用 coding agent：** 能读写文件、运行代码、检索文献；
4. **P3 领域 skills：** 加入数据确认、QC、pseudobulk、基因集校验、敏感性和证据报告；
5. **P4 完整 workflow + 独立 verifier：** 显式阶段、失败恢复、claim ledger 和反例检查；
6. **P5 可选多 agent：** analyst 与 critic 分离，或并行假设生成，仅在 P4 后评估。

需要保持模型、数据、预算和工具镜像相同，才能把差异归因于 workflow。另做跨模型因子实验：

    模型规模/家族 × prompt/workflow 条件 × 任务族

主要检验：

- skills 的平均增益是否显著；
- 增益是否集中在复杂多步任务；
- skills 是否减少统计错误、版本错误和伪造引用；
- 小模型在 workflow 下是否接近无 workflow 的大模型；
- 多 agent 是否真正增加科学分数，还是只增加成本和文本长度。

## 3.12 第一阶段交付物与完成标准

交付物：

- benchmark registry；
- 公开开发集与封闭测试服务；
- 每个任务的 capsule、数据 manifest、gold claim 和 grader；
- 至少四类基线配置；
- 可复现结果数据库；
- 方法论文和公开 leaderboard；
- 数据卡、模型卡、泄漏与限制声明。

进入第二阶段前建议达到：

- 至少 40 个端到端试点任务，其中 90% 能在干净环境中运行；
- 确定性评分覆盖至少 70% 总分；
- 剩余人工/模型 judge 与专家评分的相关达到预设阈值，例如 Spearman ≥ 0.8；
- 同一参考系统重复运行的任务级标准差可接受；
- 论文/数据族拆分和污染审计通过；
- 至少一种领域 workflow 对一句话 prompt 显示可重复增益。

---

## 4. 第二阶段：建立可靠的生物医学 Agent Workflow

## 4.1 设计原则

可靠 workflow 的价值不在于 prompt 更长，而在于把以下内容变成机器可检查的约束：

- 何时开始和何时停止；
- 必须使用什么输入；
- 哪个层级是统计单位；
- 哪些中间工件必须产生；
- 哪些条件下必须拒绝或回退；
- 哪些结论只能写成关联，哪些可以写成机制；
- 证据如何指回文件、表格和代码；
- 不确定性和反例如何报告。

第一版不需要复杂的微服务或 agent 社会。最小可用架构只有六部分。CRISPR-GPT 已经用 planner、executor、user proxy、tool provider 和任务状态机展示了“专家流程 + 工具”在生物医学实验设计中的可行性，并建立了 288 个案例的 Gene-editing bench；它支持状态机路线，但并不意味着本项目需要复制其全部多 agent 结构。<sup>[[31]](#source-31)</sup>

1. **Orchestrator：** 按状态机推进任务；
2. **Skill registry：** 保存版本化领域步骤；
3. **Tool sandbox：** 执行 R/Python、数据库检索和文件处理；
4. **Artifact store：** 保存输入、代码、表格、图和日志；
5. **Claim/evidence ledger：** 让每个结论链接到证据；
6. **Verifier：** 在不知道 agent 思考过程的情况下检查输出。

Biomni 这类通用生物医学 agent 展示了大规模工具目录、数据库检索和代码执行的覆盖能力，适合用作“工具可发现性”的工程参考；由于其核心证据目前仍来自预印本，本项目应在自己的封闭任务上重新验证每类工具的可靠性。<sup>[[33]](#source-33)</sup>

## 4.2 标准状态机

### Step 0：任务契约

输出：

- 科学问题；
- 主要和次要终点；
- 比较组；
- 统计单位；
- 允许的数据和工具；
- 成功、拒绝和停止条件。

如果问题是“代谢是否增强”，必须先追问或自动解析它是指通路基因表达、酶活潜能、模型推断通量、代谢物水平还是功能表型。否则后续再精细的统计也无法修复概念混淆。

### Step 1：数据定位与版本确认

自动产生 data manifest：

- DOI、accession、下载 URL、release/version；
- 文件哈希和大小；
- 物种、组织、癌种、平台；
- 患者/样本/细胞数；
- raw counts、normalized matrix 或 derived data；
- 许可、受控访问和引用要求。

验证论文 Methods、repository metadata 和实际文件三者是否一致。任何不一致进入 issue ledger，不静默猜测。

### Step 2：预检与 QC

- 文件完整性和 schema；
- 基因 ID、物种、重复符号；
- 元数据缺失、批次与患者结构；
- 每样本细胞数、library size、基因数、线粒体比例；
- 双细胞、环境 RNA 和异常样本；
- 是否有足够生物重复支持问题。

输出 QC 表、排除清单以及排除前后的群体构成。阈值既要有默认值，也必须保留数据驱动调整和敏感性分析。

### Step 3：分析计划

在看主要结果前冻结：

- 主分析方法；
- 协变量；
- 多重检验；
- 主要对比；
- 最小效应；
- 备选方法；
- 敏感性分析；
- 负对照。

这相当于一个轻量 preregistration，可降低 agent 看到结果后不断换方法直到得到显著性的风险。

### Step 4：执行与中间验证

每个分析步骤都输出可验证工件。出现以下情况必须停止或回退：

- 样本数与 manifest 不符；
- 主键重复；
- 分组与患者混淆；
- 模型不收敛；
- 结果由单个研究或患者完全驱动；
- 批次与目标标签完全混杂；
- 目标工具所需输入不存在。

### Step 5：统计与稳健性

至少执行：

- 患者或样本级主分析；
- 一种合理的替代方法；
- leave-one-study-out 或 leave-one-patient-out；
- 关键 QC/参数扰动；
- 表达量匹配的空基因集或标签置换；
- 如适用，独立队列验证。

### Step 6：文献检索与反例检查

文献检索分两次：

- **分析前检索：** 只查方法、数据说明和通用背景，目标论文 Results 保持遮蔽；
- **分析后检索：** 对结果进行解释，主动搜索相反方向、无效结果、癌种差异和方法限制。

这种两阶段检索能减少 agent 先读到结论、再反向拼出分析的确认偏差。

### Step 7：结论、证据与不确定性

每条结论必须给出：

- 结构化 claim；
- 直接支持它的表、图、统计模型和代码位置；
- 效应量、区间和多重校正；
- 稳健性结果；
- 与已有文献一致或冲突之处；
- 可替代解释；
- 证据等级；
- 下一步最有信息增益的验证实验。

### Step 8：打包与复核

最终包至少包括：

- analysis script 或 notebook；
- environment lock；
- results tables；
- figures；
- claims.json；
- provenance.json；
- robustness report；
- failure/issue ledger；
- 面向研究者的简明报告。

## 4.3 Skill 的统一契约

每个 skill 都应是可组合、可单独测试的“专家程序”，而不是一段长提示。统一模板：

    name
    version
    scientific_purpose
    typed_inputs
    preconditions
    allowed_tools
    ordered_steps
    invariants
    validators
    outputs
    failure_modes
    escalation_rules
    evidence_policy
    tests

例如 pseudobulk 差异表达 skill 的关键不变量：

- biological replicate 是患者或样本；
- 聚合前检查每个样本每个细胞类型的细胞数；
- 设计矩阵不满秩时拒绝拟合；
- 报告效应量和区间，不只报告 P 值；
- 患者不足时明确写“探索性”，不把细胞数当作样本量；
- 输出每个对比的样本构成、模型公式和过滤规则。

## 4.4 第一批应实现的 skills

### A. 基础设施 skills

1. task-contract：把自然语言问题转成可检查任务；
2. dataset-resolver：定位 accession、版本和许可；
3. data-manifest：哈希、schema、样本结构；
4. environment-freezer：记录包、容器和随机种子；
5. artifact-validator：检查必交工件和 schema；
6. claim-ledger：把结论链接到证据；
7. citation-verifier：核验 DOI、题名、年份及论断支持范围。

### B. 单细胞分析 skills

1. scRNA-preflight；
2. sample-aware-QC；
3. doublet/ambient-RNA audit；
4. cell-type/state annotation with unknown rejection；
5. malignant-cell calling；
6. batch-assessment and integration；
7. pseudobulk-DE / mixed-model；
8. NMF-program discovery and matching；
9. gene-set scoring and null-set test；
10. study-level meta-analysis；
11. leave-one-study-out sensitivity；
12. external-cohort validation。

scIB 的经验表明，整合必须同时评价 batch removal 和 biological conservation，不能把“不同批次混得很好”当成成功，因为过度校正会删除真实生物差异。<sup>[[18]](#source-18)</sup>

### C. 代谢 skills

1. gene-set identity and universe check；
2. transcriptomic pathway score；
3. enzyme/reaction mapping；
4. Compass/scFEA/METAFlux 适配器；
5. metabolomics/proteomics concordance；
6. metabolite-mediated communication，例如 MEBOCOST；
7. metabolism claim guardrail。

最后一个 guardrail 专门限制术语：

| 观测 | 允许表述 | 不允许直接表述 |
|---|---|---|
| 通路基因集得分 | 转录层面的通路程序增强/减弱 | 代谢通量已升高 |
| 约束代谢模型结果 | 模型推断的相对通量/代谢潜能变化 | 已实测代谢通量 |
| 代谢组差异 | 代谢物丰度变化 | 某酶因果驱动 |
| 同位素示踪/功能扰动 | 在该实验条件下支持通量或功能改变 | 跨癌种普遍机制 |

MEBOCOST 可为代谢物介导的细胞通讯提出候选，但其统计关联和酶/感受器表达仍需空间、扰动或患者级数据验证。<sup>[[25]](#source-25)</sup>

### D. T 细胞与 TCR skills

1. pan-cancer T-cell reference mapping；
2. state transition / stress/exhaustion scoring；
3. tumor-reactivity scoring；
4. TCR QC and clonotype construction；
5. clone-state enrichment；
6. paired TCR-expression integration；
7. patient-specific threshold calibration。

公开 pan-cancer T 细胞图谱已经覆盖 21 种癌症、316 名供者；T cell stress atlas 汇总了 16 种癌症、375 名患者的 308,048 个 T 细胞。这些资源适合在 BKI 受控数据前作为公开开发和外部验证来源。<sup>[[26]](#source-26)</sup><sup>[[27]](#source-27)</sup>

### E. 科学发现与审查 skills

1. literature-evidence retrieval；
2. hypothesis generator；
3. counterexample search；
4. causal-language checker；
5. evidence-strength grader；
6. uncertainty reporter；
7. next-experiment prioritizer；
8. independent meta-review。

“生成更多假设”不是首要目标。更应评价每个假设是否可证伪、是否已有相反证据、需要什么最小实验，以及如果错误会在哪个观察上失败。

## 4.5 Co-Scientist 思路如何落地而不过度复杂

Co-Scientist 的 Generation、Reflection、Ranking、Evolution、Proximity 与 Meta-review 可映射为：

| 原角色 | 本项目的最小实现 |
|---|---|
| Generation | 依据数据工件产生有限数量的结构化 hypotheses |
| Reflection | 对统计、数据质量和机制解释逐项检查 |
| Ranking | 按证据、可证伪性、新颖性、实验成本排序 |
| Evolution | 只对前几名假设做合并、修订或限定范围 |
| Proximity | 检查候选是否只是同一假设的改写 |
| Meta-review | 独立读取最终工件和 claim ledger，不能读取生成者的自由文本推理 |

默认让一个 orchestrator 串行调用这些 skills。多 agent 版本只保留两个真正需要隔离的角色：

- analyst：执行分析、生成 claims；
- verifier/critic：只看输入与工件，尝试推翻 claims。

如果两角色版本在封闭 benchmark 上没有稳定增益，就不增加更多 agent。Virtual Lab 和 Robin 展示了多 agent 科研系统的潜力，但它们的实验成功不能证明多 agent 对所有单细胞分析都优于结构化单 agent。<sup>[[32]](#source-32)</sup><sup>[[34]](#source-34)</sup>

---

## 5. 3CA 代谢试点：第一个端到端案例

## 5.1 研究问题的正确拆分

在导师尚未提供最终代谢基因集、方向和目标癌种之前，先把它们作为任务参数，不猜测。

### 核心问题 A：严格复现 2023 3CA 发现

> 使用与论文一致的冻结数据和方法，能否重建恶性细胞内的转录程序，并重新识别与呼吸、低氧、谷胱甘肽等代谢相关的 meta-program？

这是 benchmark reproduction。

### 核心问题 B：导师代谢基因集映射

> 给定一个经过版本和符号校验的代谢基因集，它与 41 个恶性细胞 meta-program 的重合、富集和样本级得分关系是什么？这种关系是否跨癌种、跨研究稳定？

这是在已知 atlas 上的受约束分析。

### 扩展问题 C：更新 3CA 与 T 细胞

> 在当前 3CA v2 或公开 T 细胞图谱中，该基因集是否与 CD4/CD8 的糖酵解—MYC、呼吸、应激、耗竭或肿瘤反应性状态相关？

这是外部泛化或新发现，不能表述为 2023 论文复现。MSigDB 的 C4:3CA 当前收录 148 个 3CA 基因集，其中包括恶性细胞和 CD4/CD8 T 细胞相关程序，可作为标准化映射资源。<sup>[[7]](#source-7)</sup>

### 扩展问题 D：TCR/克隆约束

> 如果有配对 TCR 数据，该代谢状态是否在扩增克隆、肿瘤反应性克隆或特定克隆状态迁移中富集？

只有配对 TCR、足够扩增克隆和患者级重复时才执行。否则 workflow 应拒绝，而不是用表达相似性假装谱系关系。

## 5.2 数据和版本

建议创建三个清晰分离的数据快照：

1. **3CA-2023-frozen：** 论文对应数据、代码 commit、41 MPs 和 11 hallmarks；
2. **3CA-current：** 当前门户/3CA v2 的下载数据和代码版本，记录其 2024 更新；
3. **Tcell-external：** 公开 pan-cancer T-cell、T_STR、MANAscore 验证集，以及有条件的 TCR 数据。

不从网页界面抓取数值作为主要输入；网页只用于导航和版本说明。下载文件必须哈希，并在 manifest 中记录获取日期和许可证。

## 5.3 端到端分析步骤

### 1. 基因集预检

- 固定物种和 HGNC 版本；
- 将历史符号、别名和 Ensembl ID 映射到唯一人类基因；
- 报告未匹配、一对多和重复基因；
- 明确基因集是否有正负方向、权重和预期细胞类型；
- 检查线粒体、核糖体、细胞周期、应激和 housekeeping 基因比例；
- 固定背景基因 universe；
- 构建按平均表达和检出率匹配的随机基因集。

### 2. 数据预检与 QC

- 对每个研究、患者、样本和细胞类型统计规模；
- 复核作者过滤后的样本数；
- 检查 raw counts 与 normalized matrix；
- 检查患者、癌种、研究和批次是否混杂；
- 恶性细胞分析与 T 细胞分析建立独立对象；
- 保存 QC 前后样本构成，确保没有删除某一整个组。

### 3. 复现恶性细胞程序

按 2023 方法路线运行：

- 每个肿瘤或样本对高变基因做 NMF；
- rank K 在 4–9 范围；
- 多次初始化；
- 选择稳健程序；
- 对程序 top genes 进行跨肿瘤聚类；
- 合并为 meta-program；
- 与作者 41 MPs 做最佳匹配。

官方 ITH_hallmarks 代码显示了 K=4–9、重复 NMF、稳健程序筛选和 meta-program 构建的具体实现，可作为 R1 方法复现的参考。<sup>[[6]](#source-6)</sup>

第一轮无需立刻重跑全部近 70 万恶性细胞。先选 3–5 个癌种、覆盖不同数据平台和样本规模，证明程序匹配和评分器可工作；通过后再扩展到完整冻结集。这是计算范围的收缩，不改变科学标准。

### 4. 导师基因集与 MPs 的关联

至少使用三类证据：

- **集合证据：** Fisher/hypergeometric、加权 overlap、GSEA；
- **样本证据：** 基因集得分与 MP 得分在患者/样本层面的相关；
- **跨研究证据：** 每个研究估计效应，再用随机效应 meta-analysis 汇总。

避免只看“有几个基因重合”。长基因集、高表达基因和广泛应激程序天然容易重合，应使用固定 universe 和表达匹配空集。

### 5. T 细胞扩展

- 先做 CD4/CD8 大类和主要状态映射；
- 在患者内计算基因集与糖酵解—MYC、呼吸、应激/耗竭程序的关联；
- 用 pseudobulk 或患者随机效应；
- 跨研究做 meta-analysis；
- 对 MANAscore 用患者特异阈值或连续分数，避免固定阈值泛化；
- 有配对 TCR 时才分析克隆扩增和状态关系。

CoNGA 等方法提供了联合 TCR 与基因表达图分析的同行评审基线，可与较新的 Clonotrace 进行方法级比较。<sup>[[30]](#source-30)</sup>

### 6. 稳健性和负对照

必做：

- 两种基因集评分方法，例如 AUCell/UCell 类秩方法与标准化平均表达；
- 改变最小检出率、QC 阈值和协变量；
- leave-one-study-out；
- leave-one-cancer-out；
- 每患者细胞数下采样；
- 表达匹配随机基因集；
- 标签置换；
- 移除线粒体/核糖体/细胞周期基因；
- 分别分析治疗前后、原发/转移和组织来源；
- 检查效应是否由一个患者或研究驱动。

### 7. 结果解释与证据分级

最终每个候选结论标记：

- Level 0：单一分析中的探索性关联；
- Level 1：同一数据内多方法稳健；
- Level 2：跨研究或跨癌种复现；
- Level 3：独立队列验证；
- Level 4：蛋白组/代谢组/空间/TCR 等正交支持；
- Level 5：遗传、药理或功能实验支持；
- Level 6：前瞻临床或干预证据。

3CA 转录数据通常最多直接支持 Level 1–3；没有代谢组、示踪或扰动时，不应写成已证明代谢机制。

## 5.4 自动评分

核心复现指标：

- 作者 MP 与复现 MP 的 top-gene overlap；
- 样本/细胞程序得分 Spearman；
- 可匹配 MP 的数量；
- 代谢相关 MPs 的排名和方向；
- 跨癌种重复出现比例；
- 计算结果在随机种子和下采样下的稳定性；
- 原子 claims 的 precision、recall 与方向一致率。

工作流指标：

- 是否下载正确版本；
- 是否正确区分患者、样本和细胞；
- 是否完成基因符号校验；
- 是否运行负对照；
- 是否将转录得分误称为通量；
- 是否链接证据工件；
- 是否报告不能回答的问题。

## 5.5 试点的四个基线

同一个模型、相同计算预算：

1. 一句话 prompt；
2. 详细方法 prompt；
3. 通用 coding agent；
4. 完整 skills workflow + verifier。

另选择一个较小开源模型重复 1 和 4，初步回答：

- workflow 增益是否大于模型规模增益；
- 小模型 + workflow 是否能接近大模型 + 简单 prompt；
- 错误减少来自哪里：数据定位、统计、反例检查，还是文字解释。

这个试点本身就可以成为第一篇方法论文的最小故事：**领域 skills 对生物医学再发现的因果贡献**。

---

## 6. 第三阶段：训练小型领域模型

## 6.1 何时才应该开始训练

满足以下条件前不建议训练：

- benchmark 版本冻结且测试集隔离；
- workflow 相比基线有跨任务族的稳定增益；
- skill 输出 schema 不再频繁改变；
- 至少有约 2,000 条经过人工或自动审计的有效轨迹；
- 每条轨迹的输入许可、数据许可和训练用途明确；
- 能区分成功轨迹、修复后成功轨迹和不可回答轨迹。

否则训练集会把早期错误、临时格式和 benchmark 泄漏固化到模型中。

## 6.2 什么是可训练轨迹

不需要也不应保存不可审计的隐藏思维链。保存可观察的决策记录：

- task contract；
- 数据 manifest；
- 计划中的分析步骤和理由摘要；
- 工具调用及参数；
- 关键工具输出；
- 中间验证结果；
- 错误、回退和修复；
- claims、证据链接和不确定性；
- verifier 反馈；
- 最终得分。

轨迹样本类型：

| 类型 | 用途 |
|---|---|
| 成功轨迹 | SFT 学习稳定流程和工具格式 |
| 失败后修复轨迹 | 学习诊断、回退和重试 |
| 正确拒绝轨迹 | 学习在数据不足、设计混杂时停止 |
| 好/坏成对轨迹 | DPO 或其他偏好优化 |
| 对抗/负对照轨迹 | 防止确认偏差和答案记忆 |
| 高成本与低成本等价轨迹 | 学习效率和早停 |

训练数据按论文族和数据集族去重；同一封闭测试论文的任何轨迹不得进入训练。

## 6.3 模型路线

### 第一步：只选一个 7–9B 基座

选择标准：

- 权重和商业/研究许可清晰；
- 中英文科学文本能力；
- 代码、长上下文和工具调用能力；
- 本地硬件可部署；
- tokenizer 对基因名、公式和路径不过度碎片化；
- 有稳定推理框架支持。

先做一个基座能迅速判断“训练是否值得”。不建议同时启动 8B、16B、32B 三条完整训练线。

### 第二步：QLoRA/SFT

训练目标：

- task contract 生成；
- tool-call schema；
- 数据和统计不变量；
- 失败识别；
- 证据化结论；
- skill 选择和有条件的早停。

QLoRA 能以 4-bit 量化降低微调显存需求，适合作为首轮参数高效训练方案。<sup>[[37]](#source-37)</sup>

### 第三步：偏好优化

构建偏好对：

- 患者级统计优于细胞伪重复；
- 有证据的限定结论优于过度因果结论；
- 正确拒绝优于编造；
- 通过负对照的分析优于只报告显著结果；
- 更低成本但同等正确的轨迹优于冗长轨迹。

DPO 可在不单独训练奖励模型和不进行复杂在线 rollout 的情况下进行偏好优化，因此应优先于强化学习。<sup>[[38]](#source-38)</sup>

### 第四步：仅在必要时继续预训练

如果 error analysis 证明主要瓶颈是领域知识检索、术语或论文语言，而不是工具使用和统计推理，再考虑用合法的生物医学语料进行 continued pretraining。BioMistral、PMC-LLaMA 等工作说明领域语料可以提升部分医学任务，但这些结果主要来自问答评估，不能替代本 benchmark 验证。<sup>[[39]](#source-39)</sup>

### 第五步：最后才考虑在线 RL

只有奖励满足以下条件时才考虑：

- 主要由确定性 grader 构成；
- 对 reward hacking 做过对抗测试；
- 负对照和安全失败有强惩罚；
- 奖励在封闭任务上与专家排序高度一致；
- 训练不会访问 test gold。

否则 RL 很可能训练模型优化格式、关键词或评分器漏洞，而不是真正提高科学发现能力。

## 6.4 从 8B 到 16B、32B 的扩展决策

第一轮 8B 后按错误类型决策：

| 主要错误 | 首选动作 | 是否立即增大模型 |
|---|---|---|
| 不遵守固定流程/工具格式 | 加强 SFT、grammar 和 validator | 否 |
| 数据/统计基本错误 | 增加高质量修复轨迹和 hard negatives | 否 |
| 长任务状态丢失 | 外部状态、摘要和 artifact retrieval | 不一定 |
| 知识检索不足 | 改进 retrieval；必要时 continued pretraining | 不一定 |
| 多步推理在充分工具下仍明显受限 | 比较 16B | 是 |
| 16B 已进入收益递减、部署允许 | 再评估 32B | 条件性 |

这里坚持“外部 workflow 能解决的，不用参数规模硬记”。模型负责选择和解释，确定性软件负责计算、schema、版本和验证。

## 6.5 第三阶段评价

必须回到第一阶段的封闭测试和滚动新鲜集，且报告：

- Scientific/DataOps/Robustness/Calibration；
- 工具调用成功率和无效运行率；
- 任务完成成本、延迟和峰值显存；
- 本地离线部署可行性；
- 通用能力回退；
- 安全和数据外传测试；
- 对新论文族、新癌种和新工具的泛化。

可设置一个**研究目标而非承诺**：

> 小模型在封闭科学分数上达到最佳通用前沿系统的 90%，同时可变推理成本不高于其 25%，并能在受控本地环境运行。

如果小模型在简单任务达到这一目标、复杂任务明显落后，也应报告分层 Pareto，而不是用平均分掩盖。

## 6.6 隐私与 BKI 数据

- 公开数据和受控/患者数据使用物理或逻辑隔离的运行环境；
- 受控环境默认无公网出口；
- 日志脱敏，不保存直接或可推断身份信息；
- 训练用途必须在 DUA、IRB/伦理和合作协议中明确；
- 未经授权，BKI 数据、衍生特征、未公开结论和执行轨迹不得进入公开 benchmark 或通用模型训练；
- 公开模型只能接触合成、公开或明确授权的数据；
- 对受控模型建立删除、版本追踪和访问审计。

---

## 7. 最小工程实现

不建议一开始建设复杂平台。一个仓库即可：

    project/
      benchmark/
        registry/
        splits/
        capsules/
        graders/
      skills/
      runner/
      results/
      docs/

核心对象只有五个：

- TaskCapsule；
- DataManifest；
- RunConfig；
- ArtifactBundle；
- ClaimLedger。

runner 负责读取 capsule、创建隔离环境、授予工具权限、收集工件并调用 grader。leaderboard 直接从不可修改的运行结果表生成。数据库第一版可以使用 SQLite 或结构化 parquet，不需要服务化数据库。

建议的可复现技术选择：

- 环境：容器或锁定环境文件；
- 数据工作流：Snakemake/Nextflow 只在确实需要大规模 DAG 时使用；试点可以由简单 runner 调度；
- 单细胞对象：h5ad 为主，必要时保留 Seurat 对象；
- 表格：parquet/TSV；
- provenance：W3C PROV/RO-Crate 兼容字段；
- CI：每个 skill 一个最小合成数据测试，每个任务一个 smoke test；
- 结果：append-only，禁止覆盖历史运行。

FAIR、DOME 和 RO-Crate/Workflow Run RO-Crate 可分别约束数据可发现性、机器学习报告和计算运行溯源。<sup>[[35]](#source-35)</sup><sup>[[36]](#source-36)</sup><sup>[[41]](#source-41)</sup>

---

## 8. 项目管理、角色与时间表

## 8.1 建议角色

| 角色 | 责任 |
|---|---|
| 领域负责人/导师 | 科学范围、关键 claims、临床和实验解释 |
| Benchmark curator | 论文筛选、capsule、数据许可、split |
| 单细胞/统计负责人 | QC、统计单位、grader 和敏感性 |
| Agent/ML 负责人 | runner、skills、模型实验和训练 |
| 独立评审者 | 盲法审查 claims 和争议评分 |
| 数据治理负责人 | DUA、受控环境、发布边界 |

一个人可以兼任多个角色，但 benchmark gold 的作者与最终系统开发者最好部分隔离，以降低主观偏差。

## 8.2 36 个月路线

### M0：第 0–1 个月——规格与资源审计

- 固定 3CA-2023 数据和代码；
- 获取导师基因集及其定义；
- 建立 5 个候选任务；
- 完成 task capsule、claim ledger 和 manifest schema；
- 定义四个基线配置；
- 审核 BKI 合作边界。

**Go/No-Go：** 至少一个 3CA 任务可从干净环境运行到自动评分。

### M1：第 2–3 个月——3CA 端到端试点

- 复现 3–5 个癌种的 NMF/meta-program；
- 完成导师代谢基因集映射；
- 跑一句话 prompt 与 workflow 对照；
- 建立负对照和稳健性分析；
- 形成第一份技术报告。

**Go/No-Go：** 主要工件与论文结果达到预设匹配；workflow 能减少至少一种关键错误。

### M2：第 4–9 个月——Benchmark v0.5

- 30 篇论文、60 个任务；
- 覆盖六个论文族；
- 建立公开开发集与小型封闭集；
- 校准自动 grader 与专家评分；
- 发布内部 leaderboard。

**Go/No-Go：** 任务执行成功率、评审一致性和泄漏审计达到第一阶段标准。

### M3：第 10–15 个月——Benchmark v1

- 扩至 120 篇、约 240 个任务；
- 完成论文/数据族拆分；
- 加入滚动新鲜集；
- 评测多个模型和 agent 配置；
- 形成 benchmark 论文、数据卡和公开榜单。

### M4：第 16–24 个月——Workflow 与 BKI 迁移

- 实现优先级最高的 15–20 个 skills；
- 完成 prompt、generic agent、skills、full workflow、多 agent 消融；
- 在公开 T-cell/TCR 数据上验证；
- 权限允许后迁移到 BKI 受控数据；
- 将失败模式反馈到 benchmark。

### M5：第 25–30 个月——小模型 SFT/DPO

- 审计和去重训练轨迹；
- 训练一个 7–9B QLoRA/SFT；
- 构建偏好对并做 DPO；
- 在封闭集上评估；
- 根据错误类型决定是否扩到 16B。

### M6：第 31–36 个月——扩展、外部验证与发布

- 条件性测试 16B/32B 或 RL；
- 独立实验室/队列外部验证；
- 完成本地部署和隐私审计；
- 发布成本—性能 Pareto、模型卡和最终论文。

## 8.3 每月必须监控的项目指标

- 可运行任务数和失败原因；
- 自动评分覆盖率；
- gold 审核积压；
- 数据许可状态；
- 各 task family 的模型分数；
- workflow 相对基线增益；
- 幻觉引用、伪重复和版本错误率；
- 单任务成本与运行时间；
- 封闭集污染风险；
- 训练数据中来自同一论文族的占比。

---

## 9. 风险登记与应对

| 风险 | 后果 | 检测 | 应对 |
|---|---|---|---|
| 公共论文被预训练记忆 | 假再发现 | 负对照、目标隐藏、新鲜集 | 分层报告污染风险，维护滚动封闭集 |
| gold 本身有争议或不可复现 | 错误奖励 | 独立复现、作者代码、双评审 | claim 标记确定/范围/争议，不强行单一答案 |
| 单细胞伪重复 | 大量假阳性 | 检查 inference unit 和设计矩阵 | pseudobulk/混合模型硬门槛 |
| 批次校正删除生物信号 | 结论失真 | biology conservation 指标 | 未整合、整合和分层 meta-analysis 对照 |
| 代谢表达被写成通量 | 机制过度解释 | claim guardrail | 分开表达程序、推断通量和实测通量 |
| 多 agent 只增加成本 | 系统复杂、难复现 | P4/P5 消融 | 默认单 orchestrator + 独立 verifier |
| 自动 judge 可被迎合 | leaderboard 失真 | 对抗输出、专家抽样 | 规则评分优先，judge 只补充 |
| 训练集泄漏测试任务 | 小模型虚高 | 论文族哈希和 lineage | 严格数据谱系与不可访问 gold |
| 工具/网页版本变化 | 任务失效 | 下载哈希和定期 smoke test | 冻结镜像，网页只作导航 |
| BKI 保密信息外泄 | 合作与伦理风险 | 网络、日志、访问审计 | 隔离环境、书面授权、禁止默认训练 |
| 100–200 篇人工整理过慢 | 项目停滞 | 每任务 curator 工时 | 先 30 篇；半自动抽取、人工双审 |
| 模型通过写作掩盖错误 | 高可读但不正确 | artifact-first grader | 没有工件的 prose 不得高分 |

---

## 10. 近期四周可执行清单

### 第 1 周：冻结范围

- 获得导师代谢基因集原始文件，并确认物种、方向、权重、来源和预期生物学；
- 冻结 3CA-2023 数据、代码 commit 和环境；
- 写出 3–5 条原子科学问题；
- 建立 data manifest 和 claim ledger 空模板。

### 第 2 周：建立 gold 与评分器

- 从 2023 论文和官方代码提取代谢相关 MPs；
- 选择 3–5 个代表癌种；
- 跑作者代码或人工复现，保存 gold artifacts；
- 实现程序匹配、得分相关、方向和跨癌种稳定性评分；
- 加入标签置换和随机基因集负对照。

### 第 3 周：实现最小 workflow

- 实现 dataset-resolver、gene-set-validator、sample-aware-QC、NMF/program matcher、pseudobulk/meta-analysis、claim reporter 六个 skills；
- 加入一个独立 verifier；
- 固定输出 schema；
- 在干净环境做 smoke test。

### 第 4 周：跑对照

- 用同一模型依次跑 P0–P4；
- 记录科学分数、失败类型、成本和时间；
- 让两名评审者盲法评价 claims；
- 根据错误分析决定下个月扩充哪些任务，而不是先扩充软件架构。

四周结束时应当能回答三个具体问题：

1. agent 能否在冻结 3CA 子集上重新得到已知代谢相关程序？
2. skills 相比一句话 prompt 改善了哪些可量化错误？
3. 当前瓶颈是模型推理、数据工程、统计设计，还是 gold/评分器？

---

## 11. 建议优先纳入的文献种子

这不是最终 120 篇清单，而是用于构建论文族和第一批任务的种子。

| 方向 | 种子工作 | 用途 | 证据成熟度 |
|---|---|---|---|
| 3CA/肿瘤内程序 | Gavish et al., Nature 2023 | NMF、MP、跨癌种复现主任务 | 同行评审 + 官方代码/数据 |
| 单细胞整合 | scIB, Nature Methods 2022 | batch removal/biology conservation grader | 同行评审 + reproducible workflow |
| 单细胞统计 | Squair et al. 2021；Zimmerman et al. 2021 | pseudobulk、伪重复 hard gate | 同行评审 |
| 代谢 | Compass 2021 | 转录约束代谢与功能验证 | 同行评审 |
| 代谢 | scFEA 2021 | 单细胞代谢流相对推断 | 同行评审 |
| 代谢 | METAFlux 2023 | 群体 FBA、跨数据验证 | 同行评审 |
| 代谢通讯 | MEBOCOST 2025 | 代谢物—感受器候选与验证层级 | 同行评审 |
| T 细胞图谱 | Zheng et al., Science 2021 | 公共 pan-cancer T-cell reference | 同行评审 |
| T 细胞应激 | Chu et al., Nature Medicine 2023 | T_STR 与疗效 | 同行评审 |
| 肿瘤反应性 | MANAscore 2025 | 患者特异反应性评分 | 同行评审 + 代码 |
| TCR—表达 | CoNGA 2021 | 联合图基线 | 同行评审 |
| 克隆轨迹 | Clonotrace 2025 | clone-state 迁移扩展任务 | 预印本/作者稿 + 代码 |
| 科学 agent benchmark | ScienceAgentBench 2025 | 真实论文任务、执行与结果评分 | ICLR |
| 生物数据分析 benchmark | BixBench 2025 / BixBench3 2026 | 分析胶囊、盲法发现、工件评分 | 预印本/公开 benchmark |
| 论文复现 benchmark | PaperBench 2025 | 作者 rubric 和 judge 校准 | 公开 benchmark |
| 单细胞 agent | CellVoyager/CellBench 2026 | 直接可比的单细胞 agent 设计 | Nature Methods |
| 半自动建榜 | HeurekaBench 2026 | 从论文/代码扩展任务 | ICLR |
| 自动科研系统 | Co-Scientist 2026 | 生成—反思—排序—元审查 | Nature |
| 自动科研系统 | Virtual Lab 2025 | 多 agent + 实验验证 | Nature |
| 自动科研系统 | Robin 2026 | 假设与数据分析 agent 联合 | Nature |
| 生物工具 agent | Biomni 2025 | 大规模工具库和检索执行 | 预印本 + 代码 |
| 实验设计 agent | CRISPR-GPT 2025/2026 | 规划、执行、人类监督 | Nature Biomedical Engineering |
| 小模型 | BioMistral 2024 | 7B 领域继续预训练基线 | ACL Findings |
| 参数高效训练 | QLoRA 2023 | 低资源 SFT | NeurIPS |
| 偏好优化 | DPO 2023 | preference learning | NeurIPS |

近期出现的 TruthInsightBench、SciAgentArena、scBench、GeneBench、GeneBench-Pro 和 LifeSciBench 很值得持续跟踪，但部分仍是很新的预印本或版本快速变化项目。它们适合提供任务设计思想和外部比较，不应在未经复核时直接当成本项目的 gold。HeurekaBench 则可作为从论文与代码半自动扩展开放问题的设计参考，但自动抽取出的任务仍需领域专家复核。特别是 scBench 预印本和当前仓库显示的任务数量并不一致，这本身说明 benchmark 必须发布版本号和冻结 manifest。<sup>[[11]](#source-11)</sup><sup>[[14]](#source-14)</sup><sup>[[15]](#source-15)</sup><sup>[[16]](#source-16)</sup><sup>[[42]](#source-42)</sup>

---

## 12. 最终判断

这项计划最可能形成独立贡献的部分，不是再造一个“能聊天的生物医学 agent”，而是以下组合：

1. 一个以真实论文和原始数据为基础、同时具有封闭再发现与外部泛化跑道的 benchmark；
2. 一个把统计单位、数据版本、负对照、敏感性和证据账本编码进去的可靠 workflow；
3. 一组能隔离“模型规模效应”和“人类 workflow/skills 效应”的严格消融；
4. 一条从已验证轨迹到本地小模型的可审计蒸馏路线。

最关键的第一步是把 3CA 任务真正跑通，而不是继续扩大概念范围。只要能在一个冻结子集上证明：同一模型使用领域 skills 后，数据版本错误、伪重复、代谢过度解释和无证据结论显著减少，这个项目就获得了可量化、可扩展的核心。随后扩到 120 篇论文和 BKI T 细胞数据才有稳定基础。

---

## Sources

1. <a id="source-1"></a>[用户上传的官方代码、数据与第三方复现检索记录](C:/Users/User/.codex/attachments/8b6f587a-c4f4-419e-91a9-bf603cc1f1a4/pasted-text.txt)。
2. <a id="source-2"></a>[与导师的会议记录稿件](C:/Users/User/Desktop/agentic/material/会议记录稿件.md)，特别是关于 skills、对照实验和三阶段路线的讨论。
3. <a id="source-3"></a>Gavish A. et al. Hallmarks of transcriptional intratumour heterogeneity across a thousand tumours. Nature 2023. [DOI](https://doi.org/10.1038/s41586-023-06130-4)；[本地 PDF](C:/Users/User/Desktop/agentic/material/2023-Nature-Hallmarks%20of%20transcriptional%20intratumour.pdf)。
4. <a id="source-4"></a>3CA. [Methods](https://www.weizmann.ac.il/sites/3CA/methods)。
5. <a id="source-5"></a>Weizmann Institute. [3CA portal](https://www.weizmann.ac.il/sites/3CA/)。
6. <a id="source-6"></a>Tirosh Lab. [3CA official repository](https://github.com/tiroshlab/3ca)，含 ITH_hallmarks 与 3CA_v2；[2023 数据快照](https://doi.org/10.5281/zenodo.7688626)。
7. <a id="source-7"></a>MSigDB. [C4:3CA gene-set collection](https://www.gsea-msigdb.org/gsea/msigdb/human/genesets.jsp?collection=3CA)。
8. <a id="source-8"></a>Gottweis J. et al. Accelerating scientific discovery with Co-Scientist. Nature 2026. [DOI](https://doi.org/10.1038/s41586-026-10644-y)；[本地 PDF](C:/Users/User/Desktop/agentic/material/2026-Nature-Accelerating%20scientific%20discovery%20with%20Co-Scientist.pdf)。
9. <a id="source-9"></a>ScienceAgentBench. ICLR 2025. [Conference paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/f12b4df26344f3be803c06b555252efe-Abstract-Conference.html)。
10. <a id="source-10"></a>FutureHouse. [BixBench](https://www.futurehouse.org/research/bixbench)；[arXiv](https://arxiv.org/abs/2503.00096)。
11. <a id="source-11"></a>BixBench3. Study-scale scientific discovery from raw data. 2026 preprint. [arXiv](https://arxiv.org/abs/2608.25286)。
12. <a id="source-12"></a>OpenAI. [PaperBench: Evaluating AI’s ability to replicate AI research](https://openai.com/index/paperbench/), 2025。
13. <a id="source-13"></a>FutureHouse. [LAB-Bench](https://www.futurehouse.org/research/lab-bench-measuring-capabilities-of-language-models-for-biology-research)。
14. <a id="source-14"></a>OpenAI. [GeneBench-Pro](https://openai.com/index/introducing-genebench-pro/), 2026；[GeneBench technical report](https://cdn.openai.com/pdf/6dc7175d-d9e7-4b8d-96b8-48fe5798cd5b/oai_genebench_benchmark.pdf)。
15. <a id="source-15"></a>HeurekaBench. ICLR 2026. [Conference paper](https://proceedings.iclr.cc/paper_files/paper/2026/hash/12d25b1673452b017fe9c866d9f494a0-Abstract-Conference.html)。
16. <a id="source-16"></a>scBench. [arXiv](https://arxiv.org/abs/2602.09063)；[official repository](https://github.com/latchbio/scbench)。
17. <a id="source-17"></a>CellVoyager: an autonomous agent for single-cell analysis. Nature Methods 2026. [Article](https://www.nature.com/articles/s41592-026-03029-6)；[code](https://github.com/zou-group/CellVoyager)。
18. <a id="source-18"></a>Luecken M.D. et al. Benchmarking atlas-level data integration in single-cell genomics. Nature Methods 2022. [Article](https://www.nature.com/articles/s41592-021-01336-8)。
19. <a id="source-19"></a>Squair J.W. et al. Confronting false discoveries in single-cell differential expression. Nature Communications 2021. [Article](https://www.nature.com/articles/s41467-021-25960-2)。
20. <a id="source-20"></a>Zimmerman K.D. et al. A practical solution to pseudoreplication bias in single-cell studies. Nature Communications 2021. [Article](https://www.nature.com/articles/s41467-021-21038-1)。
21. <a id="source-21"></a>Wagner A. et al. Metabolic modeling of single Th17 cells reveals regulators of autoimmunity. Cell 2021. [DOI](https://doi.org/10.1016/j.cell.2021.05.045)。
22. <a id="source-22"></a>Alghamdi N. et al. A graph neural network model to estimate cell-wise metabolic flux using single-cell RNA-seq data. Genome Research 2021. [Article](https://genome.cshlp.org/content/31/10/1867)。
23. <a id="source-23"></a>METAFlux: inferring metabolism from bulk and single-cell RNA-seq data. Nature Communications 2023. [Article](https://www.nature.com/articles/s41467-023-40457-w)。
24. <a id="source-24"></a>Wu Y. et al. Spatiotemporal immune landscape of colorectal cancer liver metastasis at single-cell level. Cancer Discovery 2022. [Article](https://aacrjournals.org/cancerdiscovery/article/12/1/134/675646/)；[scMetabolism code](https://github.com/wu-yc/scMetabolism)。
25. <a id="source-25"></a>MEBOCOST: metabolite-mediated cell communication inference. [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12199156/)。
26. <a id="source-26"></a>Zheng L. et al. Pan-cancer single-cell landscape of tumor-infiltrating T cells. Science 2021. [PubMed](https://pubmed.ncbi.nlm.nih.gov/34914499/)。
27. <a id="source-27"></a>Chu Y. et al. Pan-cancer T cell atlas links a cellular stress response state to immunotherapy resistance. Nature Medicine 2023. [Article](https://www.nature.com/articles/s41591-023-02371-y)。
28. <a id="source-28"></a>Zeng Z. et al. A minimal gene set characterizes TIL specific for diverse tumor antigens across different cancer types. Nature Communications 2025. [Article](https://www.nature.com/articles/s41467-024-55059-3)；[PubMed](https://pubmed.ncbi.nlm.nih.gov/39900903/)；[code](https://github.com/BKI-immuno-KNS/MANAscore)。
29. <a id="source-29"></a>Clonotrace. [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12486112/)；[code](https://github.com/yuntianf/Clonotrace)。
30. <a id="source-30"></a>Schattgen S.A. et al. Integrating T cell receptor sequences and transcriptional profiles by clonotype neighbor graph analysis. Nature Biotechnology 2022. [Article](https://www.nature.com/articles/s41587-021-00989-2)。
31. <a id="source-31"></a>Qu Y. et al. CRISPR-GPT for agentic automation of gene-editing experiments. Published online 30 July 2025; Nature Biomedical Engineering 10, 245–258 (2026). [Article](https://www.nature.com/articles/s41551-025-01463-z)。
32. <a id="source-32"></a>Swanson K. et al. The Virtual Lab: AI agents design new SARS-CoV-2 nanobodies with experimental validation. Nature 2025. [Article](https://www.nature.com/articles/s41586-025-09442-9)。
33. <a id="source-33"></a>Biomni: a general-purpose biomedical AI agent. 2025 preprint. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.05.30.656746v1)；[code](https://github.com/snap-stanford/Biomni)。
34. <a id="source-34"></a>A multi-agent system for automating scientific discovery. Nature 2026. [Article](https://www.nature.com/articles/s41586-026-10652-y)。
35. <a id="source-35"></a>Wilkinson M.D. et al. The FAIR Guiding Principles for scientific data management and stewardship. Scientific Data 2016. [Article](https://www.nature.com/articles/sdata201618)。
36. <a id="source-36"></a>Walsh I. et al. DOME: recommendations for supervised machine learning validation in biology. Nature Methods 2021. [Article](https://www.nature.com/articles/s41592-021-01205-4)。
37. <a id="source-37"></a>Dettmers T. et al. QLoRA: Efficient Finetuning of Quantized LLMs. NeurIPS 2023. [Paper](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1feb87871436031bdc0f2beaa62a049b-Abstract.html)。
38. <a id="source-38"></a>Rafailov R. et al. Direct Preference Optimization. NeurIPS 2023. [Paper](https://proceedings.neurips.cc/paper_files/paper/2023/hash/a85b405ed65c6477a4fe8302b5e06ce7-Abstract-Conference.html)。
39. <a id="source-39"></a>Labrak Y. et al. BioMistral: A collection of open-source pretrained large language models for medical domains. ACL Findings 2024. [Paper](https://aclanthology.org/2024.findings-acl.348/)。
40. <a id="source-40"></a>Small language models learn enhanced reasoning skills from medical textbooks. npj Digital Medicine 2025. [Article](https://www.nature.com/articles/s41746-025-01653-8)。
41. <a id="source-41"></a>Workflow Run RO-Crate / provenance packaging. [arXiv](https://arxiv.org/abs/2312.07852)；W3C [PROV-O](https://www.w3.org/TR/2013/REC-prov-o-20130430/)。
42. <a id="source-42"></a>TruthInsightBench. 2026 preprint. [arXiv](https://arxiv.org/abs/2609.05079)；SciAgentArena. 2026 preprint. [arXiv](https://arxiv.org/abs/2606.12736)；OpenAI [LifeSciBench](https://openai.com/index/introducing-life-sci-bench/)。
43. <a id="source-43"></a>[BKI/Ludwig Pan-Cancer T-cell atlas 内部演示材料](C:/Users/User/Desktop/agentic/material/BKI%20Ludwig_Pan%20Cancer%20T%20cell%20Presentation.pdf)。该材料按合作/保密内容处理，仅用于界定本方案的高层研究需求，不作为可公开发布的数据源。
