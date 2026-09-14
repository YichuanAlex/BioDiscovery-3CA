# BioDiscovery-3CA

**可审计的生物医学科学发现 Agent 项目 / An Auditable Agent System for Biomedical Scientific Discovery**

> **项目定位 / Project position**  
> 本项目以 Weizmann Institute 的 [Curated Cancer Cell Atlas（3CA）](https://www.weizmann.ac.il/sites/3CA/) 为首个公开试验场，研究如何把真实论文、公开单细胞数据、计算工具、统计约束和领域知识组织成一个可执行、可追溯、可复核的生物医学科学发现系统。  
> This project uses the Weizmann Institute [Curated Cancer Cell Atlas (3CA)](https://www.weizmann.ac.il/sites/3CA/) as its first public testbed for studying how real papers, public single-cell data, computational tools, statistical constraints, and domain knowledge can be assembled into an executable, traceable, and reviewable biomedical discovery system.

**当前版本 / Current version:** project README v1.0  
**更新日期 / Last updated:** 2026-09-14  
**当前成熟度 / Current maturity:** benchmark curation release + completed 3CA metabolic pilot + audited local/reference comparison; executable benchmark leaderboard and domain-student training remain future work

> **GitHub 镜像说明 / GitHub mirror notice:** 项目本地总量约 65.9 GiB。34 个超过 100 MiB 的文件合计约 63.736 GiB，超过当前 Git LFS 免费容量且有 23 个文件超过单文件限制；另有一个 12.2 MiB 的 `tokenizer.json` 受模型目录既有 LFS 属性约束。根据仓库所有者的规则，这 35 个对象保留在本地、不上传；其余文件全部纳入 Git。精确清单见 [`LFS_EXCLUDED_FILES.md`](./LFS_EXCLUDED_FILES.md)。`.gitignore` 不含任何忽略规则。  
> The local project is approximately 65.9 GiB. Thirty-four files larger than 100 MiB total approximately 63.736 GiB, exceeding the available Git LFS allowance, and 23 also exceed the per-file limit; one additional 12.2 MiB `tokenizer.json` is covered by existing model-directory LFS attributes. Per the repository owner's instruction, these 35 objects remain local and are not uploaded; all remaining files are included in Git. See [`LFS_EXCLUDED_FILES.md`](./LFS_EXCLUDED_FILES.md). `.gitignore` contains no ignore patterns.

[中文说明](#中文说明) · [English version](#english-version) · [核心证据目录 / Evidence map](#核心证据目录--evidence-map)

---

## 先看结论 / Executive snapshot

本项目的价值不在于再做一个“会谈论生物学”的聊天模型，而在于建立一条可以被检验的科学发现链：

```mermaid
flowchart LR
    A[论文与公开数据<br/>Papers & public data] --> B[阶段一：Benchmark<br/>定义什么叫做对]
    B --> C[阶段二：可靠 Workflow<br/>提高做对的概率]
    C --> D[可执行工件、证据与失败轨迹<br/>Artifacts, evidence & failures]
    D --> E[阶段三：小模型训练<br/>压缩已验证行为]
    E --> F[封闭论文族与新鲜数据评估<br/>Sealed-family & fresh-data evaluation]
    F --> B
```

截至 2026-09-14，本仓库已经形成以下可核验进展：

| 对象 | 当前结果 | 准确边界 |
|---|---|---|
| 3CA 数据访问与试点 | 已定位并处理 `3ca:20773`（Choudhury et al. 2022，meningioma），覆盖 58,843 个细胞、10 个样本、6 位患者，其中 3,624 个细胞被精确注释为 CD8 T cells | 单研究探索，不代表 pan-cancer 外部验证 |
| 代谢基因输入 | 用户表含 1,988 个唯一符号；试点数据中初始精确匹配 1,798 个 | 不同 prevalence 规则使下游保留基因数不同；仍有基因符号和重复行问题需要统一处理 |
| 三个生物学问题 | 已完成两条独立分析路线及细胞级比较审计 | 支持“存在可分割的转录结构”，不支持“已证明离散、代谢特异、跨患者复现的代谢状态” |
| 本地小模型工作流 | `QA_R10` 的核心计算与参考分析在总体科学方向上收敛，并识别到几乎同一组 54–55 个 CD8 罕见细胞 | 属于一个案例上的可比性证据；R10 最终报告仍有患者数、归一化公式和随机对照表述错误 |
| Benchmark v0.1 | 30 篇论文的 curation/file-level 验收于本次重新运行后 `pass=true`，无结构性问题 | 目前 30 个公开任务仍为 `scoreable:false`，数据快照、独立 gold、grader 和封闭模型评测尚未全部完成 |
| 第三阶段领域模型 | 已有完整训练方案，并用现成本地 4B 模型演示了 workflow 的价值 | 尚未完成计划中的 workflow-native 8B SFT/DPO 领域模型训练，不能把现有 4B 演示写成第三阶段已经完成 |

关于“效果可以媲美 ChatGPT 5.6 Sol”的最严谨表述是：

> 在当前 3CA 代谢试点、相同数据和相同细胞集合上，本地工作流与用户指定的 ChatGPT 5.6 Sol/Codex 参考分析对三个问题给出了相同方向的科学结论，并在 CD8 子集中独立恢复了几乎同一个罕见异常群；因此可以称为**案例级、结论级可比**。目前没有覆盖 30 篇 benchmark、预注册等效界值、多次重复和任务级置信区间的正式结果，所以尚不能称为**benchmark 级模型能力等效**。

The most defensible interpretation of “comparable to ChatGPT 5.6 Sol” is therefore **case-level and conclusion-level comparability on one audited 3CA pilot**, not benchmark-wide model parity.

---

<a id="中文说明"></a>

# 中文说明

## 1. 这个项目试图解决什么问题

通用大模型可以快速生成分析计划、代码和解释，但生物医学科学发现的难点并不只是“能否写出流畅答案”。一个结果要具有科学意义，至少需要同时回答：

1. 用的是不是正确的数据、研究、版本和数据层；
2. 基因符号、物种、表达矩阵方向和细胞元数据是否匹配；
3. 统计推断单位是细胞、样本、患者还是研究，是否发生伪重复；
4. 主分析、参数选择、负对照和敏感性分析是否在结果出现前受到约束；
5. 结果是否能从只读输入和固定环境重新产生；
6. 每条结论是否指向具体表格、标签、模型输出或文献证据；
7. 当数据不支持、设计不可识别或不同方法冲突时，系统是否会正确停止并报告 `inconclusive`；
8. 转录表达、通路活性、推断代谢通量、实测通量和因果机制是否被严格区分。

本项目把这些要求从“写在方法学建议里”推进到机器可检查的任务合同、状态机、工件、验证器和审计记录中。研究对象因此不是一个孤立模型，而是：

> **模型 × agent scaffold × skills × 工具环境 × 数据快照 × 验证器 × 权限和预算。**

这一定义改变了评价问题。我们不只问“哪个模型写得更像专家”，而是问：在相同输入、权限和预算下，哪个系统更经常选择正确数据、运行正确分析、发现并修复错误、生成可复算工件，并把结论限制在证据允许的范围内。

## 2. 为什么选择 3CA

[3CA 门户](https://www.weizmann.ac.il/sites/3CA/)汇集了多个癌种和研究的单细胞 RNA-seq 数据，并提供统一组织的表达矩阵、基因、细胞/样本注释及部分研究级派生资源。其[方法页面](https://www.weizmann.ac.il/sites/3CA/methods)说明了数据筛选、细胞类型核验、预处理、样本内 NMF、稳健程序筛选以及 meta-program 构建逻辑；对应的 2023 年 Nature 论文最终保留了 41 个 meta-program，并将其归纳为 11 类转录异质性 hallmarks。

3CA 适合作为首个公开试验场，原因包括：

- **问题真实。** 数据来自已发表癌症单细胞研究，不是为 agent 人工构造的玩具表格。
- **层级复杂。** 细胞嵌套于样本和患者，研究之间还有平台、癌种和处理差异，能够暴露伪重复、批次和推断单位错误。
- **结果可复核。** 论文、官方方法、代码和派生资源为受约束再发现提供了锚点。
- **既能复现，也能探索。** 可以严格复现 2023 冻结发现，也可以在当前门户或特定研究上提出新的、但必须限定范围的问题。
- **适合迁移。** 在公开数据上验证的数据合同、统计门禁、T-cell 状态分析和证据账本，可以在权限明确后迁移到 BKI/Ludwig 等受控数据环境。

需要特别区分两个版本概念：2023 Nature 工作的冻结队列与持续更新的 3CA 门户不是同一数据快照。网页适合发现研究和定位资源，但正式任务必须下载文件、保存获取时间和许可证，并记录哈希，不能把变化中的网页展示值当作不可变分析输入。

本次 3CA 访问快照记录于 2026-09-14。主页当时显示 124 个研究、2,836 个样本和 5,658,705 个细胞；机器可读目录汇总为 124 个唯一引用、2,838 个样本和 5,658,779 个细胞。项目保留这一小幅门户/目录差异，而没有静默选择其中一个数字。当前代谢试点使用的研究为：

| 字段 | 值 |
|---|---|
| 3CA ID | `3ca:20773` |
| 研究 | Choudhury et al. 2022 |
| 疾病 | Meningioma |
| 技术 | 10x scRNA-seq |
| 3CA 目录记录 | 10 samples，58,843 cells |
| 元数据解析 | 10 samples，6 patients |
| 精确 CD8 T-cell 子集 | 3,624 cells |
| 研究页面 | [3CA Brain collection](https://www.weizmann.ac.il/sites/3CA/brain) |
| 原始研究 | [Choudhury et al., Nature Genetics 2022](https://www.nature.com/articles/s41588-022-01061-8) |

## 3. 三阶段总体设计

三阶段不是三个互相独立的项目，而是一条有硬依赖的闭环。

| 阶段 | 核心问题 | 主要输入 | 主要输出 | 进入下一阶段前必须证明什么 |
|---|---|---|---|---|
| 第一阶段：科学发现 Benchmark | 什么叫“做对”，怎样在不泄漏答案的情况下评分？ | 同行评审论文、冻结数据、原子化 claim、独立复算 | TaskCapsule、DataSnapshot、private gold、grader、split、RunBundle | 任务可执行、gold 可复算、评分器与专家一致、论文/数据家族无泄漏 |
| 第二阶段：可靠 Agentic Workflow | 哪些专家步骤和验证器真正提高科学可靠性？ | Benchmark 任务、领域 SOP、工具和错误类型 | 状态机、skills、工件、证据账本、审计日志、Direct-vs-Flow 消融 | 相同模型和预算下，Flow 在多个任务族中稳定减少 critical failures 或提高科学分数 |
| 第三阶段：小型领域 Agent 模型 | 能否把已验证的下一步决策压缩到可本地部署的小模型？ | 经过许可、脱敏、去泄漏、可重放的成功/修复/拒绝轨迹 | 8B 级 SFT/DPO student、模型卡、成本—性能—隐私 Pareto | 在封闭论文族和新鲜数据上优于未训练基座，且关键错误不增加 |

三阶段最重要的依赖关系是：

> **Benchmark 先定义正确性，Workflow 再提高正确率，训练最后压缩已经被证明有效的行为。**

如果 gold 或 grader 不可靠，第三阶段只会训练模型迎合错误奖励；如果 workflow 本身没有经过对照证明有效，就没有理由把它的轨迹大规模写进模型。

### 3.1 第一阶段：把论文结论变成可执行任务

第一阶段不是把论文摘要改写成问答。一个合格任务应同时具有：

- 一个中性、不会泄漏结论的科学问题；
- 一个冻结且校验过的数据快照；
- 明确的细胞—样本—患者—研究层级和推断单位；
- 预先声明的主要输出、容差和失败条件；
- 从数据独立复算得到的 private gold；
- 负对照、敏感性和必要的外部验证；
- 以确定性程序为主的 grader；
- 公共任务包与私有答案/评分规则的物理隔离；
- 可重放的运行记录，而不只是最终文字回答。

任务的基本证据单位可表示为：

```text
PaperRecord
  └── DataSnapshot
        └── TaskCapsule
              └── RunBundle
                    ├── metrics.json
                    ├── claims.jsonl
                    ├── provenance.json
                    ├── figures/tables
                    └── report.md or report.pdf
```

主榜应以受约束的再发现为核心：隐藏论文结论，让系统从冻结数据重新得到方向、效应量、排序、集合或正确的 `inconclusive`。开放式假设生成可以作为单独挑战，但不应使用一个主观“有创意”分数替代可执行科学评价。

### 3.2 第二阶段：把专家流程写成可靠系统

第二阶段采用“最少但足够”的实现：一个编排/分析主体、受控 Python/R 环境、一个隔离上下文的 reviewer，加上不依赖 LLM 的验证程序。逻辑上分为六个平面：

| 平面 | 作用 | 典型内容 |
|---|---|---|
| Contract Plane | 冻结题目与边界 | 数据版本、推断单位、预算、权限、输出契约 |
| Control Plane | 控制允许的状态转移 | 入口条件、技能选择、重试上限、停止和人工 gate |
| Skill Plane | 保存可复用领域决策规则 | 适用条件、输入/输出 schema、禁止做法、validator、版本 |
| Execution Plane | 运行真实计算 | 只读原始数据、隔离目录、固定 Python/R、资源和网络白名单 |
| Evidence Plane | 连接 claim 与证据 | `claims.jsonl`、`evidence.jsonl`、工件哈希、支持/反驳/限制 |
| Governance Plane | 管理安全、许可和人员责任 | 数据分级、凭据隔离、审计、受控数据和人工审批 |

工作流从研究章程和数据冻结开始，依次经过数据审计、分析计划、独立计划审核、小规模预检、主分析、稳健性检验、证据核验、假设生成、干净环境复算、最终审核和报告。任何阶段都可以因为数据身份不确定、推断单位错误、设计不可识别、负对照失败或证据不足而停止。

这一结构的意义是把模型最不稳定的部分限制在“选择、连接、解释和修复”，把数值计算、schema、哈希、权限和硬门交给确定性程序。运行成功不等于科学正确，reviewer 的语言判断也不能豁免数据和统计硬门。

### 3.3 第三阶段：训练会使用工作流的小模型

第三阶段的目标不是训练一个把数据库和论文答案背进参数的“全知生物学家”，而是训练一个在冻结状态机中做出正确下一步动作的策略模型。它需要学习：

- 读取任务合同、当前状态和前序工件；
- 选择正确 skill 或工具，并生成合法参数；
- 根据真实执行结果继续、修复、回退或停止；
- 遵守患者级推断、数据版本、基因 ID、负对照和敏感性等科学不变量；
- 将 claim 绑定到可解析的工件或来源；
- 在证据不足时正确给出 `inconclusive`。

训练监督以可观察、可执行记录为主：状态、动作、工具参数、真实工具输出、validator 结果、修复动作、decision summary、claim 和 provenance。项目不要求也不依赖模型供应商的 hidden chain-of-thought。

推荐顺序为：

1. 先冻结 benchmark 的论文/数据家族 split 和 Phase 2 的核心 schema；
2. 收集通过重放、许可、隐私、泄漏和关键 validator 的完整 episodes；
3. 用 4B 只做数据与训练管线 smoke test；
4. 选择一个 7–9B instruction 基座做 QLoRA/LoRA SFT；
5. 比较 `Base + Direct`、`Base + Flow`、`SFT + Direct`、`SFT + Flow`；
6. 只有 SFT 在封闭任务上稳定增益时才做 DPO；
7. 只有可执行奖励与专家评价一致、且通过 reward-hacking 审计时才做多轮 RL；
8. 只有 8B 的残余错误确实来自长程规划或多证据整合时，才比较约 16B/32B。

训练后仍必须保留外部 workflow、tools、validators 和独立 reviewer。模型参数应降低决策成本和延迟，而不是替换可审计结构。

## 4. 当前 Benchmark 已经完成了什么

当前目录为 [`benchmark/metabolic_scRNA_benchmark_v0.1`](./benchmark/metabolic_scRNA_benchmark_v0.1/)，版本语义是 **`0.1.0-curation`**。

2026-09-14 重新运行结构和文件级验收，结果为 `pass=true`：

| 验收项 | 当前数量 |
|---|---:|
| 论文目录 / 注册论文 | 30 |
| A / B / C 数据可用性层级 | 24 / 4 / 2 |
| Q1 / Q2 / Q3 / METHOD 任务轴 | 13 / 8 / 8 / 1 |
| 来源文件 | 196 |
| 来源总字节 | 396,985,659 |
| 主文文件 / Supporting Information 文件 | 49 / 147 |
| 有本地主文的论文 | 30 / 30 |
| 有 Supporting Information 的论文 | 16 / 30 |
| 冻结用户基因符号 | 1,988 |
| 建议的人类同源/符号映射 | 1,727 |
| 尚未解决的符号 | 82 |
| 结构性问题 | 0 |

这说明以下工作已经完成：论文去重和 DOI/PMID 注册、每篇论文的标准目录、合法来源下载记录、文件级 provenance、基因集合冻结与物种/符号初筛、公共/私有信息分离框架、registry/schema 以及自动构建验收。

但“benchmark 已通过验证”目前只表示**benchmark 包本身的构建与文件验收通过**，不表示 agent 已经在 30 篇论文上完成正式模型评测。当前边界包括：

- 30 个 dataset registry 条目仍为 `registered_not_materialized`；
- 公开 task registry 当前均为 `scoreable:false`；
- 当前 split 是 provisional `curation_pool`，不是最终 train/dev/sealed 划分；
- private claims 和 rubrics 仍是非计分草案；
- 尚未为全部任务完成独立复算、敏感性、负对照、grader 对抗测试和双人签字；
- benchmark 包中没有正式的多模型执行轨迹或 leaderboard 分数。

因此下一道发布门不是继续增加论文，而是先将最小的八个 pilot 变成可执行任务：P001/P002（Q1）、P003/P004（Q3）、P014/P015（替代代谢推断）和 P028/P029（统计 hard gates）。

## 5. 3CA 代谢试点如何回答三个问题

用户提供的 [`metabolic genes total.csv`](./standard/metabolic%20genes%20total.csv) 含 1,988 个唯一基因符号。两条分析都使用 `3ca:20773` 的同一份原始 archive、同一批 58,843 个细胞和同一批 3,624 个精确 CD8 T cells，并做了以下共同步骤：

1. 核验 3CA study、数据 archive、元数据和输入基因表；
2. 从原始 UMI 计算每细胞 library size；
3. 归一化到每细胞 10,000 counts，再做 `log1p`；
4. 只用经过过滤的代谢基因构建降维空间；
5. 在所有细胞和 CD8 子集分别做无监督聚类；
6. 用多随机种子检查算法稳定性；
7. 用 19 个随机基因集合做描述性对照；
8. 聚类后再检查 cell type/subtype、patient、sample 和转录复杂度；
9. 比较两条独立流程的逐细胞标签，而不是只比较文字结论。

两条流程有意保留了方法差异：

- `QA_R10` 使用 15-NN 图和 Leiden，固定至少 20 个细胞表达的 prevalence 门槛，并在原始计数层面对重复 gene symbol 求和；
- `Q1_R18` 使用 PCA + MiniBatchKMeans、每个 scope 至少 1% 且不少于 20 个细胞表达的门槛，并规定主要解中每个簇至少占 5%；随机对照还近似匹配了表达 prevalence 和平均 count。

这种差异使“跨算法共同恢复的结构”比某一个算法的簇编号更有解释价值。

### 5.1 问题一：代谢基因能否形成不同的转录代谢状态簇

**短答案：可以形成算法可分割的转录结构，但当前证据不能证明这些结构是离散、代谢特异、可跨患者复现的生物学状态。**

主要证据：

- R10 在 1,646 个保留代谢基因上得到 17 个 Leiden 簇，主解 silhouette 约 0.217；
- R18 在 1,415 个保留代谢基因上得到 6 个满足 5% 最小簇规则的 k-means 簇，silhouette 约 0.213；
- 对全部 58,843 个共同细胞直接对齐标签，得到 ARI = 0.4407、NMI = 0.6209、AMI = 0.6208；
- 将每个 R10 簇映射到其占比最大的 R18 簇，细胞加权纯度为 0.8788，说明两者恢复了部分共同的大尺度结构，但 R10 切分更细；
- 在 R18 的表达匹配随机对照中，19/19 个随机基因集合的对照 silhouette 不低于代谢集合对应值，未显示代谢集合具有特异优势；
- 聚类同时与细胞类型、患者、样本和 library complexity 相关。

因此“能聚类”是真的，但“发现了真实代谢状态”仍是未证实的解释。K-means 和 Leiden 都会对连续空间产生分割；算法稳定性也不等于跨患者生物学复现。

### 5.2 问题二：这些分组是否与不同细胞类型相关

**短答案：存在明确的描述性关联，但关联不是代谢特异性，也不是因果关系。**

R18 的全局标签关联为：

| 注释层 | NMI |
|---|---:|
| Cell type | 0.3544 |
| Cell subtype | 0.4764 |
| Patient | 0.4073 |
| Sample | 0.3607 |

这些数字表明代谢基因空间与已知细胞身份有关系，尤其在 subtype 层面更明显；但 patient 关联也处在相近量级。合理解释是：细胞谱系和状态差异会体现在代谢相关转录中，同时患者/样本结构、RNA complexity、应激、增殖以及其他细胞程序也会影响该空间。

这项分析支持“分组组成在细胞类型间不同”，但不能支持“细胞类型由这些代谢状态决定”或“这些簇是纯代谢生物学”。真正的 cell-type-specific 代谢比较还需要在每种细胞类型内建模，并以患者或样本作为生物学重复。

### 5.3 问题三：同一细胞类型内，例如 CD8 T cells，是否存在不同代谢状态

**短答案：当前没有稳健证据证明 CD8 T cells 中存在多个跨患者复现的离散代谢状态；最强信号是一个需要优先做质量审计的罕见异常群。**

R10 将 3,624 个 CD8 T cells 分成 6 个 Leiden 簇，最小簇为 55 个细胞；R18 的无约束 k=2 诊断解包含 54 个细胞和 3,570 个细胞，但 54 个细胞只占 1.49%，不满足预设的 5% 最小簇规则，因此 R18 没有接受合格的 CD8 主解。

逐细胞对齐揭示了重要的跨算法收敛：

- R10 的 55 细胞簇包含 R18 全部 54 个罕见群细胞，外加 1 个主群细胞；
- R10 的其余五个簇全部来自 R18 的 3,570 细胞主群；
- R10 罕见簇的 55 个细胞中，45 个来自 patient 1；
- 该簇中位 complexity 为 8,379，R18 对应罕见群为 8,384.5，而 R18 主群为 1,182；
- R18 中没有任何患者同时以至少 5% 的比例包含两个候选分组。

因此，两条路线确实恢复了同一个强离群信号，但没有就主体 CD8 细胞能否稳定分成多个状态达成一致。更合理的下一步是检查 doublets、非 T-cell markers、ambient RNA、线粒体比例、解剖来源、处理批次和 patient 1 特异因素；只有质量审计通过且在多个独立患者中复现后，才适合给这个群命名为候选代谢状态。

### 5.4 三问统一结论

> 在该 meningioma 单研究数据中，只使用用户提供的代谢基因可以得到可计算的转录分组；这些分组与细胞类型/亚型有关，但也与患者、样本和转录复杂度有关，表达匹配随机基因集合没有支持代谢集合的特异优势。在 CD8 T cells 中，两种算法共同识别到一个 54–55 个细胞、patient 1 富集且复杂度异常高的罕见群，但当前不支持多个跨患者复现的离散 CD8 代谢状态。所有结果描述的是转录状态，而不是实测代谢通量或因果机制。

## 6. 本地工作流与 ChatGPT 5.6 Sol/Codex 参考结果的关系

本项目当前最有价值的系统证据，不是两边输出了相同的簇数，而是它们在使用不同聚类算法和不同过滤约束时仍得到相同方向的结论，并在 CD8 子集恢复了几乎完全相同的罕见群。

| 比较层 | 本地工作流 `QA_R10` | ChatGPT 5.6 Sol/Codex 参考 `Q1_R18` | 判断 |
|---|---|---|---|
| 数据身份 | `3ca:20773`，58,843 cells，3,624 CD8 | 相同 | 一致 |
| 用户基因表 SHA-256 | `7503180d…02e41a9` | 相同 | 一致 |
| 全局聚类 | Leiden，17 clusters | k-means，6 clusters | 粒度不同，不能逐簇等同 |
| 全局标签关系 | ARI 0.4407，NMI 0.6209，R10→R18 purity 0.8788 | 同一交叉审计 | 部分结构一致 |
| CD8 主要现象 | 55-cell rare cluster + further subdivision | 54-cell rare diagnostic group + one large group | 对罕见群高度一致，对主体细分不一致 |
| 三问结论 | 探索性分组；cell-type association；CD8 不足以建立稳健状态 | 同方向，限制更明确 | 结论级一致 |
| 报告质量 | 结构完整，但有重大语义错误 | 整体更专业，但也有重复符号和 silhouette 表述问题 | 本地报告尚未达到参考报告的语义可靠性 |

### 6.1 为什么可以称为“案例级可比”

- 输入数据和用户基因表完全一致；
- 两个系统独立产生了可执行结果，而不是互相复制最终文字；
- 高层结论一致：可分组不等于代谢特异状态，细胞类型关联受其他结构竞争解释，CD8 缺少跨患者稳健多状态证据；
- 两种算法对 CD8 罕见群的细胞级重合接近完全；
- 本地工作流保留了 archive/gene-list hash、核心标签、结果 JSON/CSV、报告、session 和 supervisor audit，允许事后定位错误。

### 6.2 为什么还不能称为“模型能力等效”

- 目前只审计了一个研究和一组三问，不是 30 篇 benchmark；
- 没有预注册“等效”阈值、主指标和 critical failure 规则；
- 没有在多个任务族上进行至少三次独立重复和任务级 bootstrap/层级统计；
- 两个系统的工具、算法、预算和工作流并未完全配平；
- R10 报告把 10 个样本误写成 10 位患者，归一化公式与代码不一致，并错误描述两个随机对照比较基线；
- R18 代码没有正确聚合重复 gene symbol，使主要 `SOD2` 行被漏用，且 CD8 silhouette 来自固定子样本而不是完整 3,624 个细胞；
- “同样写出谨慎结论”不自动等于推理过程、计算质量、成本和泛化能力相同。

所以当前最准确的研究主张是：**领域 workflow 能让本地小模型驱动的系统在一个真实、复杂、可审计的 3CA 任务上接近前沿参考分析的科学判断；该结果是值得扩大验证的初步证据，而不是已经完成的通用模型胜负结论。**

## 7. 项目的科学与工程意义

### 7.1 将“答案评价”推进到“发现过程评价”

传统问答 benchmark 主要检查最终文本。真实科学任务却可能出现“答案方向碰巧正确，但数据、统计或代码路径错误”的情况。本项目把数据身份、代码执行、工件、负对照、敏感性、复算和 claim-evidence 关系纳入评价，使系统更难通过记忆论文摘要或写作技巧投机。

### 7.2 把失败变成一等科学产物

科学系统不仅要保存成功轨迹，也要保存：错误数据版本、无 patient ID、完全混杂的设计、负对照失败、随机对照同样好、重复基因符号、报告与代码不一致以及正确停止的 `inconclusive`。这些失败既能改进 workflow，也能成为第三阶段更有价值的训练监督。

### 7.3 分离模型能力与工作流增益

通过同一模型下的 `Direct` 与 `Flow` 对照，以及相同 workflow 下的 base/SFT 对照，可以分别回答：

- 领域 skills 和硬门是否比加长 prompt 更有效；
- 小模型是否因为训练而进步，还是只受益于外部 workflow；
- 模型规模增加是否解决真正的推理瓶颈，还是只改善语言风格；
- 性能提升是否伴随成本、延迟、隐私或 critical failure 的代价。

### 7.4 为本地和受控部署提供路径

如果较小模型在外部状态机、工具和验证器帮助下达到任务级等效区间，它可以降低 API 成本和数据外传需求，并更容易部署到受控研究环境。但本项目不会用“小模型”作为降低科学门槛的理由；本地部署仍需相同的数据版本、统计和证据审计。

### 7.5 从公开 3CA 到受控 BKI/Ludwig 的可信迁移

3CA 提供公开、可复现的开发环境。只有公开任务达到数据、统计、重现和证据门槛后，才应把 workflow 迁移到 BKI/Ludwig 的 T-cell atlas、TCR/克隆或临床元数据。两条跑道共享接口和 skills，但未经授权的内部数据、衍生特征、执行轨迹和未公开结论不能进入公共 benchmark、外部模型上下文或公开训练集。

### 7.6 形成可发表的系统性研究问题

项目可以产生四类相互连接、但可独立检验的研究贡献：

1. 真实论文与原始组学数据驱动的 gold-blind rediscovery benchmark；
2. 将生物统计不变量和证据边界编码进 agent workflow 的方法；
3. 模型、skills、validators 和 workflow 的因果消融；
4. 从可执行、可观察轨迹训练本地小模型，并报告科学分数—成本—隐私 Pareto。

## 8. 当前完成状态与证据成熟度

| 模块 | 已完成 | 尚未完成 | 当前可主张的结论 |
|---|---|---|---|
| 三阶段研究设计 | 四份详细方案，覆盖 benchmark、workflow、训练、治理和路线图 | 尚需根据正式实验持续版本化 | 研究问题与接口已经定义 |
| Benchmark curation | 30 篇论文、196 个来源文件、schema/registry、基因审计、file-level pass | 数据物化、independent gold、scoreable tasks、sealed split、leaderboard | curation release 已完成，不是模型榜单 release |
| 3CA 数据试点 | 官方目录发现、数据/元数据下载与哈希、同一细胞集双流程分析 | 多研究/多癌种外部复现 | 单研究分析可重放 |
| 三问生物学结果 | 全局、细胞类型关联和 CD8 子集均有结果；完成跨流程逐细胞审计 | doublet/污染审计、患者级独立复现、代谢组/flux 验证 | 探索性转录结论，不能升级为代谢通量或因果机制 |
| 本地 Agentic Workflow | QA_R10 工程运行完成，核心文件可追溯，相关测试通过 | 语义 validator 需补患者数、公式和比较对象一致性 | 工作流执行完成；科学语义验收 `needs_followup` |
| 小型领域模型 | 已有训练数据、SFT/DPO/RL、规模和治理方案；现成 4B 基座完成示范 | workflow-native 8B student、封闭评测、模型卡、训练数据卡 | 第三阶段仍是待验证研究计划 |

## 9. 仓库结构

<a id="核心证据目录--evidence-map"></a>

### 核心证据目录 / Evidence map

| 路径 | 内容 | 用途 |
|---|---|---|
| [`第一阶段_生物医学科学发现Benchmark数据集构建规则.md`](./第一阶段_生物医学科学发现Benchmark数据集构建规则.md) | Benchmark 的实体、SOP、公共/私有隔离、评分、防泄漏和验收规则 | 定义“什么叫做对” |
| [`第二阶段_可靠生物医学AgenticWorkflow完整设计方案.md`](./第二阶段_可靠生物医学AgenticWorkflow完整设计方案.md) | 六平面架构、状态机、skills、工具、验证、证据账本和安全 | 定义“怎样更可靠地做对” |
| [`第三阶段_小型生物医学领域模型训练完整方案.md`](./第三阶段_小型生物医学领域模型训练完整方案.md) | 可训练轨迹、Go/No-Go、SFT/DPO/RL、模型规模、评估和治理 | 定义“如何压缩已验证行为” |
| [`3CA_生物医学科学发现Agent三阶段完整方案.md`](./3CA_生物医学科学发现Agent三阶段完整方案.md) | 项目总论、3CA/BKI 边界和三阶段接口 | 总体研究路线 |
| [`benchmark/metabolic_scRNA_benchmark_v0.1/`](./benchmark/metabolic_scRNA_benchmark_v0.1/) | 30 篇 curation release、registry、schemas、来源和验收报告 | Phase 1 当前实物 |
| [`benchmark/metabolic_scRNA_benchmark_v0.1/构建与验收报告.md`](./benchmark/metabolic_scRNA_benchmark_v0.1/构建与验收报告.md) | 当前 benchmark 的数字、QA、边界和下一 gate | 判断 benchmark 实际成熟度 |
| [`3CA/QA_R10/`](./3CA/QA_R10/) | 本地小模型工作流的分析工件、标签、报告和 README | 本地流程结果 |
| [`supervisor/QA_R10/final-audit.json`](./supervisor/QA_R10/final-audit.json) | 工程完成与科学语义验收的分层结论 | 独立监督证据 |
| [`workflow_codex/.runtime/codex-home/sessions/QA/R10-rollout-2026-09-14T14-29-24-0722bd5e-b4a.jsonl`](./workflow_codex/.runtime/codex-home/sessions/QA/R10-rollout-2026-09-14T14-29-24-0722bd5e-b4a.jsonl) | QA_R10 可观察执行事件 | 过程级审计 |
| [`standard/3CA_metabolic_states_Q1_R18/`](./standard/3CA_metabolic_states_Q1_R18/) | ChatGPT 5.6 Sol/Codex 参考分析的代码、结果、图和 LaTeX/PDF | 独立参考路线 |
| [`standard/QA_R10_vs_Q1_R18_comparative_audit.md`](./standard/QA_R10_vs_Q1_R18_comparative_audit.md) | 数据、计算、报告和可观察思考过程的逐项比较 | 当前“可比性”主证据 |
| [`better.md`](./better.md) | 各轮修改、实测、失败、启动和审计事实的追加记录 | 项目历史与故障知识库 |

## 10. 最小复核方式

以下命令假定 Windows PowerShell、Python 3.12，并从项目根目录运行。

### 10.1 复核 Benchmark curation 包

```powershell
Set-Location C:\Users\User\Desktop\agentic
py -3.12 .\benchmark\build_benchmark.py --verify-only
```

预期结果包括 `expected_papers=30`、`paper_folders=30`、`gene_symbols=1988`、`problems=[]` 和 `pass=true`。该检查验证目录、registry、来源文件和基因审计的一致性，不运行 30 个科学任务。

### 10.2 运行参考分析的最小自检

```powershell
Set-Location C:\Users\User\Desktop\agentic
py -3.12 .\standard\3CA_metabolic_states_Q1_R18\code\analyze_metabolic_states.py --self-test
```

### 10.3 重新运行参考分析

```powershell
Set-Location C:\Users\User\Desktop\agentic
py -3.12 .\standard\3CA_metabolic_states_Q1_R18\code\analyze_metabolic_states.py
```

正式重跑前应先修复 R18 的重复 gene-symbol 聚合问题，并保留旧结果作为历史版本；不要用修复后的输出静默覆盖现有审计证据。

## 11. 必须保留的科学边界

1. **RNA 表达不等于代谢通量。** 代谢基因转录、gene-set score、模型推断通量、代谢组/Seahorse/同位素示踪和因果扰动属于不同证据等级。
2. **细胞数不等于患者重复数。** 当前 58,843 个细胞来自 10 个样本和 6 位患者；任何患者级结论都必须以患者/样本为推断单位。
3. **聚类一定会产生分组，但分组不一定离散。** 必须与连续结构、随机/匹配基因集、不同算法、参数和重抽样比较。
4. **细胞类型关联不是代谢特异性。** 谱系、complexity、应激、增殖、批次和患者都可能产生相似结构。
5. **算法稳定性不是外部复现。** 固定 PCA/图上换随机种子，只测条件稳定性；新患者、新研究和新平台才是更强验证。
6. **门户会更新。** 正式任务必须使用 accession、snapshot time、archive hash 和代码版本。
7. **报告流畅不等于内容正确。** QA_R10 已证明结构 validator 通过后仍可能存在患者数和公式错误，语义对照必须读取核心 JSON/CSV。
8. **参考分析也不是 gold。** Q1_R18 存在重复符号覆盖和 `SOD2` 漏用，因此应修复重跑，而不是将其当作无条件标准答案。
9. **当前结果不是临床建议。** 本项目不做患者级诊断、治疗决策或自动湿实验执行。
10. **公开可下载不自动意味着可训练或再分发。** 数据、论文、代码、教师输出和患者相关材料需要分别核对许可。

## 12. 下一步优先级

### P0：修复已经确认的语义和实现错误

- 在本地 workflow 报告 validator 中加入 `n_samples`/`n_patients` 与正文的语义一致性检查；
- 将归一化公式的变量和分母与执行代码自动对照；
- 将“2/19、17/19”等计数绑定到精确的比较对象，而不是只检查数字是否出现；
- 强制执行提示合同中的表格数量和必需表检查；
- 对 R18 重复 gene symbols 在原始 count 层面聚合并重跑，检查 `SOD2` 修复是否改变结果；
- 对 CD8 54–55 细胞罕见群做 doublet、marker、ambient RNA、mitochondrial fraction、解剖来源和 patient/sample enrichment 审计。

### P1：把 curation release 推进为可计分 benchmark

- 物化并哈希八个最小 pilot 的公开矩阵和元数据；
- 独立复算 candidate claims，冻结 private gold；
- 完成 matched-null、label permutation、patient-aware statistics 和必要的外部验证；
- 对 grader 做对抗测试，并由领域和计算 curator 双签；
- 按论文/数据家族冻结 train/dev/sealed split；
- 发布首个可计分的内部 leaderboard，而不是先扩大论文数量。

### P2：正式检验 workflow 是否优于 direct prompting

- 选择 2–3 个模型、至少两个 3CA task family；
- 在相同问题、数据、预算和工具上比较 `Direct` 与 `Flow`；
- 每个配置进行至少三次运行或使用适当的任务级 bootstrap；
- 预注册 scientific score、critical failures、成本和等效界值；
- 做 `no-stat-guard`、`no-evidence-review`、`broad-tools` 等消融，确认增益来自哪里。

### P3：满足 Go/No-Go 后启动领域小模型训练

- 只使用 train split、许可明确、脱敏、无 gold 泄漏且可重放的轨迹；
- 同时收集成功、失败后修复、正确拒绝和 `inconclusive`；
- 首先训练一个 7–9B student，比较 final-answer-only 与 observable-trajectory SFT；
- SFT 稳定增益后再做 DPO；reward 审计通过后再决定是否做 RL；
- 以残余错误决定是否扩大到 16B/32B，而不是按模型规模惯性推进。

## 13. 项目成功应如何定义

项目成功不是“生成一份漂亮报告”，也不是“某次运行得到与论文相同的结论”。建议使用分层标准：

- **Benchmark 成功：** 任务可重放、gold 独立、grader 与专家一致、无家族泄漏、存在 null 和 flipped cases；
- **Workflow 成功：** 相同模型和预算下，跨任务族稳定提高科学工件分数或降低 critical failures；
- **系统成功：** 本地小模型 + Flow 在预设等效区间内接近 Frontier + Flow，同时成本、延迟或隐私更优；
- **部署成功：** 能在受控环境离线或有限联网运行，保存审计轨迹并遵守 BKI/患者数据权限；
- **科学成功：** 新结论在独立患者/队列中复现，并在需要时获得正交测量或扰动实验支持。

这些成功层级应分别报告，不能用一个总平均分掩盖严重的数据或统计错误。

## 14. 适用对象

本仓库主要面向：

- 计算生物学、单细胞组学、肿瘤免疫和癌症代谢研究者；
- 研究 scientific agents、tool-use、可执行推理和 agent evaluation 的 AI/ML 团队；
- 需要在本地或受控环境分析内部组学数据的研究机构；
- 负责 benchmark curation、统计审核、数据治理和研究可复现性的协作者。

它目前适合作为研究原型、方法学试验场和审计材料，不应作为未经专家审核的临床或湿实验自动决策系统。

## 15. 数据治理、许可与引用

- 3CA 数据、上游论文、代码和模型各自保留原始许可证与引用要求；请从具体来源文件和官方页面核对。
- 项目根目录当前没有统一的仓库级许可证，因此不要默认所有文件都可再分发、商用或用于训练。
- `Public`、`Internal`、`Controlled` 和 `Prohibited` 数据必须使用不同执行与模型调用策略。
- 未经书面授权，BKI/Ludwig 内部数据、患者相关信息、衍生特征、未公开结论和轨迹不得进入公共 benchmark 或公共模型训练。
- 使用本项目结果时，应同时引用 3CA 门户、对应原始研究、实际使用的数据快照和本项目的具体版本/commit；不要只引用 README。

核心外部来源：

- [3CA portal](https://www.weizmann.ac.il/sites/3CA/)
- [3CA methods](https://www.weizmann.ac.il/sites/3CA/methods)
- [3CA official repository](https://github.com/tiroshlab/3ca)
- [Gavish et al., Nature 2023](https://doi.org/10.1038/s41586-023-06130-4)
- [Choudhury et al., Nature Genetics 2022](https://www.nature.com/articles/s41588-022-01061-8)
- [Accelerating scientific discovery with Co-Scientist, Nature 2026](https://doi.org/10.1038/s41586-026-10644-y)

---

<a id="english-version"></a>

# English version

## 1. Problem statement

General-purpose language models can quickly produce analysis plans, code, and scientific prose. Biomedical discovery, however, is not reliable merely because an answer is fluent. A defensible result must establish, among other things:

1. that the correct study, dataset, version, and expression layer were used;
2. that gene identifiers, species, matrix orientation, and cell metadata were handled correctly;
3. whether the inferential unit is a cell, sample, patient, clone, or study, and whether pseudoreplication occurred;
4. whether the primary analysis, parameter choices, negative controls, and sensitivity analyses were constrained before the result was known;
5. whether the reported artifacts can be reproduced from read-only inputs in a pinned environment;
6. whether every material claim resolves to a table, label file, model output, or literature source;
7. whether the system stops with `inconclusive` when evidence is insufficient or the design is not identifiable; and
8. whether transcription, pathway activity, inferred flux, measured flux, and causal mechanism are kept at distinct evidence levels.

BioDiscovery-3CA turns these requirements into task contracts, state transitions, machine-readable artifacts, validators, and audit records. The evaluated object is therefore not a model name in isolation. It is the full configuration:

> **model × agent scaffold × skills × tool environment × data snapshot × validators × permissions and budget.**

The central question is not which model writes the most expert-sounding prose. It is which system, under matched inputs and constraints, more reliably selects the right data, performs the right analysis, detects and repairs failures, emits reproducible artifacts, and keeps its conclusions within the evidence boundary.

## 2. Why 3CA is the first testbed

The [Curated Cancer Cell Atlas](https://www.weizmann.ac.il/sites/3CA/) aggregates single-cell RNA-seq studies across cancers and exposes consistently organized expression matrices, genes, cell/sample annotations, and selected derived resources. The [3CA methods page](https://www.weizmann.ac.il/sites/3CA/methods) describes dataset selection, annotation checks, preprocessing, within-sample NMF, robust program selection, and meta-program construction. The associated 2023 Nature study retained 41 meta-programs grouped into 11 hallmarks of transcriptional intratumour heterogeneity.

3CA is useful for this project because it is:

- **scientifically real:** the data come from published cancer studies rather than synthetic agent exercises;
- **hierarchically difficult:** cells are nested in samples and patients, and studies vary by platform, disease, and processing;
- **reviewable:** papers, official methods, code, and derived resources provide anchors for constrained rediscovery;
- **suitable for both reproduction and extension:** the 2023 frozen findings can be reproduced, while updated portal data can support clearly labelled new analyses; and
- **transferable:** contracts, statistical gates, T-cell state analysis, and evidence ledgers developed on public data can later move into controlled BKI/Ludwig environments.

The 2023 Nature cohort and the continuously updated portal are not the same snapshot. Portal pages should be used for discovery and provenance, while formal tasks should rely on downloaded, checksummed, dated, and licence-audited assets.

The portal snapshot recorded for this project on 14 September 2026 displayed 124 studies, 2,836 samples, and 5,658,705 cells. The machine-readable catalog contained 124 unique citations but summed to 2,838 samples and 5,658,779 cells. This small portal/catalog discrepancy is retained as provenance rather than silently reconciled.

The metabolic pilot uses:

| Field | Value |
|---|---|
| 3CA ID | `3ca:20773` |
| Study | Choudhury et al. 2022 |
| Disease | Meningioma |
| Technology | 10x scRNA-seq |
| 3CA catalog | 10 samples, 58,843 cells |
| Parsed metadata | 10 samples, 6 patients |
| Exact CD8 T-cell subset | 3,624 cells |
| Study page | [3CA Brain collection](https://www.weizmann.ac.il/sites/3CA/brain) |
| Primary study | [Choudhury et al., Nature Genetics 2022](https://www.nature.com/articles/s41588-022-01061-8) |

## 3. The three-stage design

The three stages form a gated feedback loop rather than three independent projects.

| Stage | Central question | Main inputs | Main outputs | Gate to the next stage |
|---|---|---|---|---|
| Phase 1: Scientific-discovery benchmark | What counts as correct, and how can it be scored without leaking the answer? | Peer-reviewed papers, frozen data, atomic claims, independent recalculation | TaskCapsules, DataSnapshots, private gold, graders, splits, RunBundles | Executable tasks, independently reproducible gold, calibrated graders, and no paper/data-family leakage |
| Phase 2: Reliable agentic workflow | Which expert steps and validators actually improve reliability? | Benchmark tasks, domain SOPs, tools, and observed failure modes | State machine, skills, artifacts, evidence ledger, audit logs, Direct-vs-Flow ablations | Stable gains or fewer critical failures across task families under matched model and budget |
| Phase 3: Small biomedical agent model | Can validated decisions be compressed into a locally deployable model? | Licensed, de-identified, leakage-audited, replayable success/repair/refusal trajectories | An approximately 8B SFT/DPO student, model card, and performance-cost-privacy Pareto | Gains over the untrained base on sealed paper families and fresh data without increased critical failures |

The dependency is deliberate:

> **The benchmark defines correctness; the workflow increases the probability of correctness; training compresses only behavior already shown to be useful.**

Unreliable gold or graders produce reward misspecification. An unvalidated workflow produces training trajectories with no demonstrated scientific value.

### 3.1 Phase 1: turning papers into executable tasks

Phase 1 is not a paper-abstract question-answer dataset. A valid task requires:

- a neutral scientific question that does not leak the conclusion;
- a frozen, checksummed data snapshot;
- explicit cell–sample–patient–study hierarchy and inferential unit;
- preregistered outputs, tolerances, and failure conditions;
- private gold obtained through independent recalculation;
- negative controls, sensitivities, and external validation where needed;
- predominantly deterministic graders;
- physical separation between public inputs and private answers/rubrics; and
- a replayable run record, not merely a final paragraph.

The evidence unit is:

```text
PaperRecord
  └── DataSnapshot
        └── TaskCapsule
              └── RunBundle
                    ├── metrics.json
                    ├── claims.jsonl
                    ├── provenance.json
                    ├── figures/tables
                    └── report.md or report.pdf
```

The primary track is gold-blind constrained rediscovery: hide the paper’s conclusion and ask the system to recover a direction, effect, ranking, set, or correct `inconclusive` from frozen inputs. Open-ended hypothesis generation can be a separate challenge, but a subjective creativity score should not replace executable evaluation.

### 3.2 Phase 2: encoding expert practice into a reliable workflow

The minimum complete implementation is one orchestrator/analyst, a controlled Python/R environment, an isolated reviewer, and deterministic validation programs. The logical design has six planes:

| Plane | Responsibility | Typical content |
|---|---|---|
| Contract | Freeze the task and its boundaries | Data version, inferential unit, budget, permissions, output contract |
| Control | Enforce legal state transitions | Entry conditions, skill routing, retry limits, stopping, human gates |
| Skill | Store reusable domain decisions | Applicability, I/O schema, prohibited actions, validator, version |
| Execution | Run real computation | Read-only raw data, isolated workspace, pinned Python/R, resource and network allowlists |
| Evidence | Link claims to support and contradiction | `claims.jsonl`, `evidence.jsonl`, artifact hashes, limitations and tests |
| Governance | Manage safety, rights, and accountability | Data classes, credential isolation, audit export, controlled-data approvals |

The workflow moves from research charter and data freeze through data audit, typed planning, independent plan review, preflight, primary analysis, robustness, evidence review, hypothesis generation, clean-environment reproduction, final review, and reporting. It may stop whenever data identity is uncertain, the inferential design is invalid, a negative control fails, or the evidence cannot support the intended claim.

The model is used for selecting, connecting, interpreting, and repairing. Numerical computation, schemas, hashes, permissions, and hard gates remain external and deterministic. A successful process exit is not scientific correctness, and an LLM reviewer cannot waive a statistical hard gate.

### 3.3 Phase 3: training a model that knows how to use the workflow

The Phase 3 target is not an omniscient biomedical chatbot that memorizes papers and databases. It is a policy model that selects the correct next action within a frozen workflow. It should learn to:

- read the task contract, current state, and prior artifacts;
- choose a valid skill or tool and produce legal parameters;
- continue, repair, roll back, or stop based on actual execution results;
- respect patient-level inference, versions, gene identifiers, negative controls, and sensitivities;
- bind claims to resolvable artifacts or sources; and
- return `inconclusive` when the design or evidence is insufficient.

Training supervision is based on observable and executable records: states, actions, tool parameters, actual outputs, validator results, repairs, decision summaries, claims, and provenance. It does not require provider-private hidden chain-of-thought.

The proposed sequence is:

1. freeze benchmark family splits and the core Phase 2 schemas;
2. collect episodes that pass replay, rights, privacy, leakage, and critical-validator gates;
3. use a 4B model only for a data/training-pipeline smoke test;
4. run QLoRA/LoRA SFT on one 7–9B instruction model;
5. compare `Base + Direct`, `Base + Flow`, `SFT + Direct`, and `SFT + Flow`;
6. run DPO only after stable sealed-task SFT gains;
7. run multi-turn RL only after executable rewards agree with expert review and resist reward hacking; and
8. compare approximately 16B/32B only if the residual errors genuinely require longer-horizon planning or cross-evidence synthesis.

The workflow, tools, validators, and independent reviewer remain in place after training. Model weights should reduce decision cost and latency, not replace auditable controls.

## 4. What the benchmark currently contains

The current release is [`benchmark/metabolic_scRNA_benchmark_v0.1`](./benchmark/metabolic_scRNA_benchmark_v0.1/), with semantic status **`0.1.0-curation`**.

The construction and file-level verification was rerun on 14 September 2026 and returned `pass=true`:

| Verification item | Current count |
|---|---:|
| Paper folders / registered papers | 30 |
| Tier A / B / C data availability | 24 / 4 / 2 |
| Q1 / Q2 / Q3 / METHOD axes | 13 / 8 / 8 / 1 |
| Source files | 196 |
| Total source bytes | 396,985,659 |
| Main-article / supporting-information files | 49 / 147 |
| Papers with local main text | 30 / 30 |
| Papers with supporting information | 16 / 30 |
| Frozen input gene symbols | 1,988 |
| Symbols with recommended human mapping | 1,727 |
| Unresolved symbols | 82 |
| Structural problems | 0 |

Completed work includes paper deduplication and DOI/PMID registration, standardized paper folders, typed lawful-retrieval provenance, frozen gene-set and species/symbol review, public/private separation scaffolding, registries/schemas, and automated build verification.

The phrase “benchmark validation completed” currently means **the benchmark package passed its construction and file-level acceptance checks**. It does not mean that the agent has been evaluated on 30 executable tasks. At present:

- all 30 dataset registry entries remain `registered_not_materialized`;
- public tasks remain `scoreable:false`;
- the split is a provisional `curation_pool`, not a final train/dev/sealed split;
- private claims and rubrics remain non-scoreable drafts;
- independent gold, sensitivities, negative controls, adversarial grader tests, and dual sign-off are incomplete; and
- there is no formal multi-model trajectory set or leaderboard score in the benchmark release.

The next release gate is therefore to materialize and score the smallest eight pilots: P001/P002 for Q1, P003/P004 for Q3, P014/P015 for alternative metabolic inference, and P028/P029 for statistical hard gates.

## 5. The 3CA metabolic pilot and the three questions

The user-provided [`metabolic genes total.csv`](./standard/metabolic%20genes%20total.csv) contains 1,988 unique symbols. Both analyses use the same `3ca:20773` archives, the same 58,843 cells, and the same 3,624 exact CD8 T cells. Their shared analytical skeleton is:

1. verify the 3CA study, data and metadata archives, and gene list;
2. derive each cell’s total library size from raw UMI counts;
3. normalize each cell to 10,000 counts and apply `log1p`;
4. construct the feature space using filtered metabolic genes only;
5. cluster all cells and the exact CD8 subset separately;
6. assess conditional algorithmic stability across random seeds;
7. run 19 descriptive random-gene controls;
8. inspect cell type/subtype, patient, sample, and transcript complexity after clustering; and
9. compare cell-level labels across pipelines rather than only comparing prose.

The methods intentionally differ. `QA_R10` uses a 15-nearest-neighbour graph plus Leiden, a minimum detection count of 20, and count-level aggregation of duplicate symbols. `Q1_R18` uses PCA plus MiniBatchKMeans, a within-scope 1% prevalence threshold with a floor of 20 cells, and a 5% minimum-cluster rule for primary solutions; its random controls are approximately matched by prevalence and mean count.

### 5.1 Q1: Are there distinct clusters of transcriptional metabolic states?

**Short answer: the metabolic-gene space contains algorithmically separable transcriptional structure, but the current evidence does not establish discrete, metabolism-specific, cross-patient biological states.**

Evidence:

- R10 retained 1,646 metabolic genes and produced 17 Leiden clusters with a silhouette of approximately 0.217;
- R18 retained 1,415 genes and produced six k-means clusters satisfying its 5% minimum-cluster rule, with a silhouette of approximately 0.213;
- direct alignment of all 58,843 cells gave ARI = 0.4407, NMI = 0.6209, and AMI = 0.6208;
- mapping each R10 cluster to its majority R18 cluster gave a cell-weighted purity of 0.8788, consistent with shared coarse structure but finer R10 subdivision;
- all 19 expression-matched random controls in R18 had a comparison silhouette at least as high as the metabolic set, providing no evidence of metabolic-set specificity; and
- the partitions were also associated with cell identity, patient, sample, and library complexity.

Thus, “the cells can be clustered” is supported. “The clusters are real metabolic states” is not yet supported. Both Leiden and k-means partition continuous spaces, and seed stability is not equivalent to replication in new patients.

### 5.2 Q2: Are the groups associated with distinct cell types?

**Short answer: yes, descriptively, but the association is neither metabolism-specific nor causal.**

For the R18 global labels:

| Annotation | NMI |
|---|---:|
| Cell type | 0.3544 |
| Cell subtype | 0.4764 |
| Patient | 0.4073 |
| Sample | 0.3607 |

Metabolic-gene expression therefore carries lineage and subtype information, but patient structure is of a comparable magnitude. Lineage, state, RNA complexity, stress, proliferation, and sample effects are competing explanations for the observed geometry.

The evidence supports the statement that cluster composition differs across annotated cell types. It does not support the claims that cell type is determined by these metabolic states or that the clusters represent purely metabolic biology. A definitive cell-type-specific analysis should be fitted within each cell type and use samples or patients as biological replicates.

### 5.3 Q3: Within CD8 T cells, are there different metabolic states?

**Short answer: there is no robust evidence for multiple discrete, cross-patient CD8 metabolic states; the strongest signal is a rare group that should first be treated as a quality-control target.**

R10 partitioned the 3,624 CD8 T cells into six Leiden clusters, the smallest containing 55 cells. R18’s unconstrained k=2 diagnostic solution contained 54 and 3,570 cells, but the 54-cell group represented only 1.49% of the subset and failed the preregistered 5% minimum-cluster rule. R18 therefore did not accept a valid primary CD8 solution.

Cell-level alignment showed strong cross-algorithm convergence on the rare group:

- the R10 55-cell cluster contained all 54 R18 rare-group cells plus one main-group cell;
- all other R10 CD8 clusters were subdivisions of the R18 3,570-cell main group;
- 45 of the 55 R10 rare-cluster cells came from patient 1;
- median complexity was 8,379 in the R10 rare cluster and 8,384.5 in the corresponding R18 group, compared with 1,182 in the R18 main group; and
- no R18 patient contained both candidate groups at a frequency of at least 5%.

The two methods therefore recovered the same dominant outlier signal, but they did not agree that the main CD8 population contains multiple stable states. Doublets, non-T-cell markers, ambient RNA, mitochondrial fraction, anatomical site, processing, and patient-1-specific factors should be audited before assigning a biological state name.

### 5.4 Unified answer

> In this single meningioma study, the user-provided metabolic genes produce computable transcriptional partitions. Those partitions are associated with cell type and subtype, but also with patient, sample, and transcript complexity, and expression-matched random genes do not establish a metabolic-specific advantage. Within CD8 T cells, two algorithms independently identify the same 54–55-cell, patient-1-enriched, unusually high-complexity group, but the current data do not support multiple cross-patient discrete CD8 metabolic states. These are transcriptional observations, not measurements of metabolic flux or causal mechanism.

## 6. Relationship to the ChatGPT 5.6 Sol/Codex reference

The most informative agreement is not identical cluster counts. It is convergence of scientific interpretation and recovery of nearly the same CD8 rare group despite different algorithms and guardrails.

| Comparison layer | Local workflow `QA_R10` | ChatGPT 5.6 Sol/Codex reference `Q1_R18` | Assessment |
|---|---|---|---|
| Data identity | `3ca:20773`, 58,843 cells, 3,624 CD8 | Same | Matched |
| Gene-list SHA-256 | `7503180d…02e41a9` | Same | Matched |
| Global clustering | Leiden, 17 clusters | k-means, 6 clusters | Different granularity; cluster IDs are not interchangeable |
| Global label relation | ARI 0.4407, NMI 0.6209, R10→R18 purity 0.8788 | Same cross-audit | Partial structural agreement |
| Main CD8 phenomenon | 55-cell rare cluster plus subdivision | 54-cell rare diagnostic group plus one main group | Near-identical rare group; disagreement on further subdivision |
| Answers to the three questions | Exploratory partitioning, descriptive cell-type association, insufficient robust CD8-state evidence | Same direction with stricter limitations | Conclusion-level agreement |
| Report quality | Complete structure but material semantic errors | More polished overall, but not error-free | Local prose reliability remains lower |

### 6.1 Why this supports case-level comparability

- the data and user gene-list inputs are identical;
- both systems produced executable analysis artifacts rather than copying final prose;
- their top-level scientific conclusions agree;
- their rare CD8 groups overlap at the individual-cell level; and
- the local run preserves hashes, label files, structured results, a report, an event log, and an independent supervisor audit.

### 6.2 Why this is not yet model-level equivalence

- only one study and one three-part question have been audited;
- no equivalence margin, primary metric, or critical-failure rule was preregistered;
- there are no three-or-more repeated trials across multiple task families with task-level uncertainty;
- tool access, algorithms, workflow, and budget were not completely matched;
- the R10 report incorrectly described 10 samples as 10 patients, gave a normalization equation inconsistent with its code, and attached random-control counts to the wrong comparison baselines;
- R18 failed to aggregate duplicate gene symbols, omitting the active `SOD2` row, and described a subsampled CD8 silhouette as full-data; and
- agreement on a cautious conclusion does not prove equal reasoning quality, compute quality, cost, or generalization.

The bounded research claim is therefore: **a domain workflow enabled a locally driven small-model system to approach the scientific judgment of a frontier reference on one real, complex, and auditable 3CA task. This is evidence worth scaling, not a completed general model comparison.**

## 7. Scientific and engineering significance

### 7.1 Evaluating discovery processes, not only answers

A text-only benchmark can reward a correct-looking conclusion reached through the wrong data or invalid statistics. This project evaluates data identity, code execution, artifacts, negative controls, sensitivities, reproduction, and claim-evidence links. It therefore makes paper-memory and rhetorical fluency less effective shortcuts.

### 7.2 Treating failure as a first-class research artifact

The system preserves wrong versions, missing patient IDs, non-identifiable designs, failed negative controls, equally strong random controls, duplicate gene symbols, report-code inconsistencies, and correct `inconclusive` stops. These failures improve the workflow and provide more informative Phase 3 supervision than success-only final answers.

### 7.3 Separating model capacity from workflow value

Matched `Direct` versus `Flow` experiments, followed by base-versus-SFT experiments under the same flow, can distinguish:

- the effect of expert skills and hard gates from a longer prompt;
- training gains from external workflow gains;
- genuine planning improvements from stylistic improvements; and
- scientific performance from cost, latency, privacy, and critical-failure trade-offs.

### 7.4 A path to local and controlled deployment

If a small model plus external state, tools, and validators reaches a task-level equivalence interval, it may reduce API cost and external data transfer and become easier to deploy in controlled environments. Local deployment does not lower the scientific bar: the same version, inference, and evidence audits remain mandatory.

### 7.5 A defensible bridge from public 3CA to controlled BKI/Ludwig data

3CA provides a public and reproducible development track. Workflow transfer to a BKI/Ludwig T-cell atlas, TCR/clonotype data, or clinical metadata should occur only after public tasks meet data, statistical, reproducibility, and evidence gates. The tracks may share interfaces and skills, but unauthorized internal data, derived features, trajectories, and unpublished findings must not enter public benchmarks, external-model context, or public training data.

### 7.6 A coherent research contribution

The project can yield four connected but separately testable contributions:

1. a gold-blind rediscovery benchmark built from real papers and omics data;
2. a biomedical agent workflow with encoded statistical invariants and evidence boundaries;
3. causal ablations of models, skills, validators, and workflow structure; and
4. workflow-native small-model training with a scientific-performance–cost–privacy Pareto analysis.

## 8. Current evidence maturity

| Module | Completed | Pending | Defensible claim today |
|---|---|---|---|
| Three-stage research design | Four detailed specifications covering benchmark, workflow, training, governance, and roadmap | Iterative versioning after formal experiments | The research questions and interfaces are defined |
| Benchmark curation | 30 papers, 196 source files, schema/registry, gene audit, file-level pass | Materialized inputs, independent gold, scoreable tasks, sealed split, leaderboard | Curation release complete; not a model leaderboard release |
| 3CA pilot | Official catalog discovery, data/metadata acquisition and hashes, two analyses on the same cells | Multi-study and multi-cancer replication | The single-study analysis is replayable |
| Biological answers | Global, cell-type association, and CD8 results with cross-pipeline cell-level audit | Doublet/contamination audit, patient-level replication, metabolomic/flux validation | Exploratory transcriptional conclusions only |
| Local agentic workflow | QA_R10 engineering run completed, core artifacts traceable, relevant tests passed | Stronger semantic validators | Workflow completion accepted; scientific semantic acceptance remains `needs_followup` |
| Small domain model | Training-data, SFT/DPO/RL, scaling, evaluation, and governance plans; off-the-shelf 4B demonstration | Workflow-native 8B student, sealed evaluation, model and data cards | Phase 3 remains a research plan |

## 9. Repository map

See the bilingual [Evidence map](#核心证据目录--evidence-map) above for direct links to the four design documents, benchmark release, local run, supervisor audit, reference run, comparison audit, and append-only project log.

## 10. Minimal verification

Run the following from Windows PowerShell with Python 3.12.

### 10.1 Verify the benchmark curation package

```powershell
Set-Location C:\Users\User\Desktop\agentic
py -3.12 .\benchmark\build_benchmark.py --verify-only
```

Expected fields include `expected_papers=30`, `paper_folders=30`, `gene_symbols=1988`, `problems=[]`, and `pass=true`. This validates package construction, not 30 scientific task executions.

### 10.2 Run the reference-analysis self-test

```powershell
Set-Location C:\Users\User\Desktop\agentic
py -3.12 .\standard\3CA_metabolic_states_Q1_R18\code\analyze_metabolic_states.py --self-test
```

### 10.3 Rerun the reference analysis

```powershell
Set-Location C:\Users\User\Desktop\agentic
py -3.12 .\standard\3CA_metabolic_states_Q1_R18\code\analyze_metabolic_states.py
```

Before treating a rerun as a new reference, fix duplicate-symbol aggregation in R18 and preserve the current audited results as immutable history.

## 11. Scientific boundaries that must remain explicit

1. **RNA expression is not metabolic flux.** Transcription, gene-set activity, model-inferred flux, metabolomics/Seahorse/isotope tracing, and causal perturbation are distinct evidence levels.
2. **Cells are not patient replicates.** The 58,843 cells come from 10 samples and six patients.
3. **A clustering algorithm will partition data even when the underlying structure is continuous.** Continuous alternatives, matched genes, algorithms, parameters, and resampling must be compared.
4. **Cell-type association is not metabolic specificity.** Lineage, complexity, stress, proliferation, batch, and patient effects are competing explanations.
5. **Seed stability is not external replication.** New patients, studies, and platforms provide stronger validation.
6. **The portal changes.** Formal tasks require accession, snapshot time, archive hash, and code version.
7. **Fluent reports can be wrong.** QA_R10 passed structural validation while retaining patient-count and equation errors.
8. **The reference is not infallible gold.** Q1_R18 has a duplicate-symbol/`SOD2` implementation defect and should be corrected and rerun.
9. **The current results are not clinical guidance.** The system does not make patient-level diagnoses or treatment decisions.
10. **Publicly downloadable does not automatically mean trainable or redistributable.** Rights must be checked separately for data, papers, code, teacher output, and patient-related material.

## 12. Prioritized next steps

### P0: repair confirmed semantic and implementation defects

- cross-check `n_samples` and `n_patients` against report prose;
- compare normalization equations directly with executed code;
- bind random-control counts to the exact metric and baseline being compared;
- enforce exact output-contract requirements, not only minimum presence;
- aggregate duplicate symbols at the raw-count layer in R18 and rerun, including `SOD2` impact analysis; and
- audit the 54–55-cell CD8 group for doublets, markers, ambient RNA, mitochondrial fraction, anatomy, and patient/sample enrichment.

### P1: promote the curation release into a scoreable benchmark

- materialize and checksum public matrices and metadata for the eight smallest pilots;
- independently reproduce candidate claims and freeze private gold;
- complete matched nulls, label permutations, patient-aware inference, and required external validation;
- adversarially test graders and obtain domain/computational dual sign-off;
- freeze train/dev/sealed splits by paper and dataset family; and
- publish a first internal scoreable leaderboard before increasing the paper count.

### P2: formally test workflow value

- compare `Direct` and `Flow` across 2–3 models and at least two 3CA task families;
- match question, data, tool access, budget, and stopping criteria;
- run at least three trials per stochastic configuration or use appropriate task-level bootstrap;
- preregister the scientific score, critical failures, cost metrics, and equivalence margin; and
- run `no-stat-guard`, `no-evidence-review`, and `broad-tools` ablations.

### P3: train the domain student only after Go/No-Go

- use only licensed, de-identified, no-gold, replayable train-split trajectories;
- include successes, repair trajectories, correct refusals, and `inconclusive` cases;
- first train one 7–9B student and compare final-answer-only with observable-trajectory SFT;
- run DPO only after stable SFT gains, and RL only after reward audit; and
- let residual error types, not model-size momentum, determine whether 16B/32B is warranted.

## 13. Success criteria

Success should be reported at multiple levels:

- **benchmark success:** replayable tasks, independent gold, calibrated graders, no family leakage, and null/flipped cases;
- **workflow success:** stable cross-family improvement in scientific artifacts or lower critical-failure rates under matched model and budget;
- **system success:** Local Small Model + Flow falls within a preregistered equivalence interval of Frontier + Flow while improving cost, latency, or privacy;
- **deployment success:** controlled/offline execution, complete audit trails, and compliance with BKI/patient-data permissions; and
- **scientific success:** replication in independent patients or cohorts, followed by orthogonal measurement or perturbation when the claim requires it.

These levels must remain separate. A single mean score should not hide a data-identity, statistical, or evidence-critical failure.

## 14. Intended users

This repository is intended for:

- computational biology, single-cell genomics, tumour immunology, and cancer-metabolism researchers;
- AI/ML groups studying scientific agents, tool use, executable reasoning, and agent evaluation;
- research institutions that need local or controlled analysis of internal omics data; and
- benchmark curators, biostatisticians, data stewards, and reproducibility reviewers.

It is currently a research prototype, methods testbed, and audit package. It is not an autonomous clinical or wet-lab decision system.

## 15. Governance, licensing, and citation

- 3CA data, upstream papers, source code, and models retain their own licences and citation requirements.
- No repository-wide licence is currently declared at the project root; do not assume that all material can be redistributed, commercialized, or used for training.
- `Public`, `Internal`, `Controlled`, and `Prohibited` data require different execution and model-access policies.
- Unauthorized BKI/Ludwig data, patient-related information, derived features, unpublished findings, and trajectories must not enter public benchmarks or public model training.
- Cite the 3CA portal, the relevant primary study, the exact data snapshot, and the project version/commit used; the README alone is not a sufficient scientific citation.

Core external sources:

- [3CA portal](https://www.weizmann.ac.il/sites/3CA/)
- [3CA methods](https://www.weizmann.ac.il/sites/3CA/methods)
- [3CA official repository](https://github.com/tiroshlab/3ca)
- [Gavish et al., Nature 2023](https://doi.org/10.1038/s41586-023-06130-4)
- [Choudhury et al., Nature Genetics 2022](https://www.nature.com/articles/s41588-022-01061-8)
- [Accelerating scientific discovery with Co-Scientist, Nature 2026](https://doi.org/10.1038/s41586-026-10644-y)

---

## 最后一条原则 / Final principle

> **没有可重放工件的结论，不应获得高科学分；没有独立验证的流畅报告，不应被当作可靠发现；没有通过 benchmark 和 workflow 对照的轨迹，不应被直接写入领域模型。**  
> **A claim without replayable artifacts should not receive a high scientific score; a fluent report without independent validation should not be treated as a reliable discovery; and a trajectory that has not passed benchmark and workflow controls should not be distilled into the domain model.**
