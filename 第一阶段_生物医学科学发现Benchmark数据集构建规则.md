# 生物医学科学发现 Benchmark 第一阶段数据集构建规则

## 0. 执行结论

本项目第一阶段不应把 benchmark 理解为“一张包含问题和答案的表”，也不应把“论文复现”简单等同于“让 agent 重写作者代码”。更合适的定义是：

> 从可靠论文、冻结的数据快照和经独立复算的原子科学结论出发，构造一组在答案隐藏条件下、能够要求 agent 实际读取数据、完成分析并提交可程序化评分证据的科学发现任务。

经过对 ScienceAgentBench、PaperBench、BixBench、HeurekaBench、CellVoyager／CellBench、scBench、BixBench3 及过程轨迹数据集的代码和公开数据结构进行核对，本项目应采用下面这套最小但完整的组织方式：

1. 一个 Paper Package 记录论文、代码、数据来源和可验证结论。
2. 一个 Task Package 只包含一个主要科学问题、一个明确推断单位、一组冻结输入和一个输出契约。
3. 一个 Run Package 记录某个模型与某个 agent flow 在某个任务版本上的一次独立运行，包括可观察轨迹、提交物和评分。
4. 题干与金标准必须物理分离。公开任务目录中不得出现答案、作者结果表、gold notebook、gold script 或可直接反推出答案的文件名。
5. 评分以结果 artifact 和统计性质为主，以自然语言答案为辅。LLM judge 只能承担难以规则化的一小部分，不得决定主要分数。
6. 同一模型至少比较“一句话 prompt”和“包含领域工作流程、skills 与必要工具的 agent flow”；两组除 flow 外使用相同任务、数据、预算、运行环境和重复次数。
7. 第一版无需建设数据库服务。Git 管理小型元数据和评分器；大数据放对象存储或正式数据仓库；所有文件以版本号、相对路径和 SHA-256 校验值关联。

推荐的规范性规则是：正文中使用“必须”“不得”“应”“可以”。“必须／不得”是进入正式 benchmark 的硬门槛；“应”是默认要求，偏离时必须留下书面理由。

---

## 1. 对现有 benchmark 的格式审计

### 1.1 哪些设计最值得本项目复用

| Benchmark | 从论文到任务的构造方式 | 题干与输入如何保存 | 轨迹如何保存 | 结果与评分如何保存 | 本项目应吸收的做法 | 不应照搬的问题 |
|---|---|---|---|---|---|---|
| [ScienceAgentBench](https://arxiv.org/abs/2410.05080) | 由领域专家从 44 篇同行评议论文构造 102 个数据驱动任务，并提供数据、领域知识、目标输出和评分程序 | Hugging Face 行记录包含 task instruction、domain knowledge、数据目录树、数据预览、gold program 名称和 eval script 名称；磁盘上分 datasets、gold programs、eval programs、rubrics | 运行 history 和 cost 以 JSONL 保存，生成程序单独保存 | 执行预测程序，再由任务专用脚本评分 | 明确给 agent 数据树与预览；统一可执行提交；每题一个 evaluator | 轨迹行本身缺少显式 task_id/run_id，较依赖行顺序；公开 gold 名称容易形成泄漏面；2026 年又发布 verified split，说明题目和 grader 必须支持勘误与版本更新 |
| [PaperBench](https://arxiv.org/abs/2504.01848) | 从 20 篇 ICML 2024 Spotlight/Oral 论文构建整篇复现任务；每篇论文由作者或专家定义分层 rubric | 每篇一个目录，含 paper.pdf、paper.md、addendum.md、assets、rubric.json、blacklist.txt、config.yaml | agent.log、运行日志和阶段快照；提交物打包为 tar.gz | agent rollout、全新容器 reproduction、第三个容器 grading；rubric 叶节点评分后加权 | 将“生成”“重跑”“评分”隔离；要求 reproduce.sh；rubric 是递归、可解释的原子要求 | 主要面向整篇机器学习论文复现，单题成本过高；大量条目仍需 judge，不能直接作为 100–200 篇生物医学论文的唯一评分方式 |
| [BixBench 1.5](https://huggingface.co/datasets/futurehouse/BixBench) | 当前版本从 60 个已发表生物信息学 notebook capsule 中保留 205 个可回答问题 | 一题一行 BixBench.jsonl；字段包含 question、ideal、distractors、paper DOI、capsule UUID、data folder、eval mode；数据和 executed notebook 在 ZIP capsule 中 | 每题保存 summary JSON 和完整 transition JSONL，另含运行 notebook | open answer、MCQ 或 hypothesis 模式；结果表与评估 CSV 分开 | capsule 便于冻结复杂数据；一题一行；保留完整 notebook 和 transition trace | 公开行同时包含 question 与 ideal/hypothesis/result，不适合密封测试；早期版本中有题目事实上不可充分回答，1.5 版才重新筛选，说明 answerability 必须成为发布硬门槛 |
| [HeurekaBench／sc-HeurekaBench](https://arxiv.org/abs/2601.01678) | 从 13 篇 Nature/Cell 论文中验证 41 个 insight，构造 50 道 OEQ 和 50 道 MCQ；论文文本抽取 insight；代码描述；insight 与作者代码匹配；生成复现代码并人工验证；再删除无数据也能答、幻觉和重复题 | 论文目录含 paper.pdf、code、data；中间结果为 TXT、JSON、ipynb；最终 oeq.json/mcq.json 按 paper→insight 嵌套，记录 summary、how、relevant text、data paths 和问题 | 各 agent 实现不统一；Biomni 适配主要把 prompt 和 stdout 保存为 TXT，再解析 solution 标签 | OEQ 主要用 LLM judge；MCQ 用准确率/F1 | “论文结论—作者代码—数据—独立复算—问题”的链条最贴近本项目；增加无数据可答过滤 | 最终 JSON 把多个问题与答案嵌在同一 Markdown 字符串；题号不稳定；公开／隐藏边界不够强；开放题评分过度依赖 LLM |
| [CellVoyager／CellBench](https://www.nature.com/articles/s41592-026-03029-6) | CellBench 只给论文背景，要求预测被隐藏的单细胞分析；CellVoyager 再从 h5ad 执行 notebook 式分析 | CellBench 用 CSV 保存 context、analysis titles、analysis descriptions、id；CellVoyager 读取 paper summary 和 h5ad | 生成 ipynb，同时写人类可读日志 | 预测分析计划主要由 LLM 匹配；具体分析产出在 notebook 中 | 可作为“假设和分析计划生成”辅助赛道；适合单细胞 notebook artifact | CSV 单元格里塞序列化列表并通过 eval 解析，脆弱且不安全；它不等于从原始数据重新发现论文结论；不能承担主 leaderboard |
| [scBench](https://arxiv.org/abs/2602.09063) | 195 个单细胞工作流题；每题为数据快照、自然语言问题和确定性 grader，公开 6 个 canonical examples，完整测试集保留 | 每题一个 JSON：id、task、data_node、canary、grader、metadata、timeout；数据为 h5ad；题干规定精确的结构化输出 | trajectory.json 记录 agent message、命令开始／结束、输出、退出码和 token usage；result.json 与 eval_answer.json 分开 | numeric tolerance、marker precision/recall、Jaccard、distribution comparison、multiple choice | 一题一个 JSON、确定性评分、精确输出标签、公开样例＋隐藏全集、完整可观察轨迹；尤其适合 QC、DE、注释等技能测试 | 当前任务偏工作流技能和局部答案，不一定来自论文核心发现；公开样例把 ground truth 和 curator notes 放在同一个 JSON，正式密封集不宜如此 |
| [BixBench3](https://arxiv.org/abs/2608.25286) | 20 个研究规模计算生物学任务，从公开原始数据完成研究目标，产生 138 个指定 artifacts，再与论文发表 artifacts 确定性比较 | Hugging Face 保存任务 Parquet、cases.jsonl、每题 agent/runtime package；对象存储将 raw/metadata 与 ground truth/artifacts_grading 置于不同 release；每个对象都有 size、SHA-256、来源和类别 | inspect logs 保存 eval log、trajectory、model events 和 usage；run_manifest 固定模型、effort、镜像、数据 manifest 与生命周期 | 每个 artifact 定义路径、格式、row key、依赖、analysis depth 和 F1/CCC/Spearman 等 checks；另有 process judge，但不覆盖确定性分数 | 与本项目最接近：原始输入只读挂载、公开输出契约、隐藏 gold、逐 artifact 确定性评分、严格 schema、不可变 release、完整 run manifest | 2026 年 8 月才发布，仍属很新的预印本；20 个研究规模任务平均耗时高，不适合把所有 100–200 篇论文都做成 24 小时级任务 |
| [OpenDiscoveryTrace](https://arxiv.org/abs/2609.09203) | 跨科学任务采集过程级数据，重点不是建立 gold biomedical task，而是比较过程行为 | 每条 trajectory 是自包含 JSON，含 task、model、difficulty、outcome | 每步记录 phase、action、observation、error、revision trigger、confidence 等 | 对成功预测、错误定位、claim verification、process quality 建辅助任务 | 说明最终答案相近时，轨迹仍可揭示工具误用、统计错误和侥幸命中 | “thought”不是跨厂商稳定可得字段，也可能涉及隐私和不可比性；本项目不得把隐藏思维链作为必需数据 |

上述信息来自各项目当前公开论文、仓库和数据文件的直接核对。主要实现版本见文末“来源与核对版本”。

### 1.2 综合判断

没有任何一个现有 benchmark 可以原样复制：

- ScienceAgentBench 提供了“数据＋可执行程序＋任务专用评分”的骨架。
- PaperBench 提供了“运行、重跑、评分三环境隔离”和分层 rubric。
- HeurekaBench 提供了最重要的论文到任务策展流程。
- scBench 提供了适合单细胞技能题的紧凑任务格式和结构化轨迹。
- BixBench3 提供了最成熟的“公开输入 contract—隐藏 artifact gold—不可变 release”结构。
- CellBench 适合建立假设／分析计划赛道，但不能替代实际数据分析。
- OpenDiscoveryTrace 说明过程轨迹应被当作正式研究数据，而不是临时日志。

因此，本项目的数据格式应是这些做法的交集，而不是再发明一套庞大的平台。

---

## 2. Benchmark 的基本单位

### 2.1 四个实体

正式数据集必须区分四个实体：

| 实体 | 含义 | 稳定标识符示例 | 是否可一对多 |
|---|---|---|---|
| PaperRecord | 一篇特定版本论文及其来源记录 | paper:nature-2023-06130-4:v1 | 一篇论文可对应多个数据快照和任务 |
| DataSnapshot | 一个冻结、可校验的数据版本 | data:3ca-gavish-2023:1.0.0 | 一个数据快照可支持多个任务 |
| TaskCapsule | 一个主要科学问题及其输入、输出契约和隐藏评分规则 | task:3ca-mp-metabolism-001:1.0.0 | 同一论文可有 1–3 个任务；同一问题可有不同输入层级变体 |
| RunBundle | 一个确定系统在确定任务版本上的一次运行 | run:task-id:system-id:timestamp:trial | 每个 task×system 至少 3 次独立运行 |

这四者不得混用。尤其不得把 paper_id 当 task_id，也不得只靠目录顺序推断某条轨迹属于哪道题。

### 2.2 一题的原子性

每个 TaskCapsule 必须同时满足：

1. 只有一个主要科学问题。
2. 只有一个预先声明的主要推断单位，例如 patient、donor、sample、clone 或 cell；不得含糊使用“细胞数很大”替代生物学重复。
3. 只有一个主要 estimand 或一组逻辑上不可分割的 estimands。
4. 有一个明确的提交入口和输出契约。
5. 有至少一个不读数据就无法可靠回答的量化目标。
6. 有经独立复算确认的 gold evidence。

一个题干可以要求若干中间 artifacts，但不得把多个互不依赖的科学问题塞进同一题。若论文结论包含“识别状态、比较状态、关联预后”三层，应拆成三个 task，或明确为有依赖关系的三个 artifacts。

### 2.3 Task family

为了研究 workflow 能力而不是偶然命中，相关任务组成 family：

- 同一论文不同科学问题：共享 paper_id，不共享 task_id。
- 同一问题不同输入层级：共享 task_family_id。
- 同一患者队列或同一 accession 的派生数据：共享 leakage_group_id。
- 有前后依赖的任务：用 depends_on_task_ids 显式声明，但 leaderboard 主分应尽量允许单题独立运行。

数据切分必须按 leakage_group_id 分组，不能把同一论文、同一队列或高度派生的数据放到 train 与 test 两侧。

---

## 3. 论文纳入与结论筛选规则

### 3.1 论文纳入硬门槛

一篇论文只有同时满足以下条件，才能进入正式候选池：

1. 可信出版：已同行评议；若为预印本，只能进入 prospective/challenge 赛道，不得混入主 benchmark。
2. 身份明确：有 DOI、PMID、PubMed Central ID、bioRxiv DOI 或其他稳定标识符；记录准确版本和发布日期。
3. 无明显完整性警报：策展时检查撤稿、expression of concern、重大 correction；记录 checked_at，而不是假设状态永久不变。
4. 数据可得：至少有足以支持目标结论的公开或经正式授权可用数据。
5. 许可可执行：明确数据、代码、论文补充材料的许可或使用条款。只有“网页能下载”不等于可再分发。
6. 结论可计算验证：目标结论主要由计算分析支持；若必须依赖尚不可获得的湿实验结果，不能作为重新发现主任务。
7. 独立复算可行：策展人员能在不依赖作者私有环境的情况下得到与论文方向和量级一致的结果。
8. 伦理合规：不得将受控患者级数据、可重识别信息或原协议不允许用于模型评估的数据直接放入公开包。

### 3.2 论文优先级

建议为候选论文建立 A/B/C 级：

- A 级：同行评议；数据和代码公开；有稳定 accession／DOI；核心结果能从公开数据复算；优先进入 sealed test。
- B 级：同行评议；数据公开但代码不完整，或只提供 processed data；适合进入 dev/validation。
- C 级：只有部分数据、依赖受控数据、或复算存在实质歧义；保留为候选或方法学案例，不进入 leaderboard。

期刊影响因子不能代替上述条件。代表性应由癌种、组学、样本规模、研究设计、分析类型和结论类型共同决定。

### 3.3 每篇论文抽取什么

每篇论文先建立 Paper Card，至少抽取：

- 原始科学问题与临床／生物学背景；
- 研究设计：病例、对照、治疗、时间、队列、批次；
- 生物学重复与统计推断单位；
- 数据 accession、文件、版本、大小、格式和许可；
- 作者代码仓库、commit、容器或环境；
- 主要计算步骤及关键参数；
- 每个候选结论对应的图、表、补充表、结果段落和代码位置；
- 作者明确支持的结论与作者没有支持的外推；
- 可用负对照、替代方法和敏感性分析；
- 复算状态、偏差原因和策展决定。

### 3.4 结论必须原子化

论文中的自然语言结论必须转成 gold_claims.jsonl 的原子 claim，而不是保存一段摘要作为唯一答案。每条 claim 至少含：

| 字段 | 含义 |
|---|---|
| claim_id | 在该任务内稳定的隐藏标识 |
| subject | 结论主体，例如某 T-cell state、代谢通路或癌种 |
| relation | 富集、上调、关联、预测、分化、共现等关系 |
| object | 比较对象或结局 |
| direction | increase、decrease、positive、negative、none |
| context | 癌种、细胞类型、处理、时间点、队列 |
| estimand | 真正被估计的量 |
| expected | 数值、区间、排序、集合或方向 |
| uncertainty | 置信区间、容许范围或未确定性 |
| evidence_level | primary、supporting、exploratory |
| source_anchors | 论文图表、段落、补充材料定位 |
| reproduction_anchors | 独立复算的文件和行／对象 |
| acceptable_alternatives | 合理方法导致的可接受答案 |
| overclaim_boundary | 不得从该证据推出的更强结论 |
| status | verified、partial、disputed、deprecated |

“发现某程序与预后相关”至少要明确：在哪个癌种、哪类样本、患者还是细胞层面、方向、模型协变量、效应量和不确定性。没有这些字段，模型可能靠含糊表述得分。

### 3.5 一个结论成为任务金标准的条件

结论只有通过以下四步才可成为 gold：

1. 文献锚定：至少一处主文或补充材料证据。
2. 代码／方法锚定：能指向作者代码、方法说明或重建的确定步骤。
3. 独立复算：由未编写题干的另一名策展者，在冻结输入上重跑。
4. 敏感性界定：至少测试一个合理替代方案或关键阈值，确定可接受范围。

如果复算只得到方向一致但数值不同，应把 gold 表述为方向、排名或范围，不得伪造精确点值。如果方向也不稳定，任务应标为 disputed 并退出正式分数。

---

## 4. 从论文到任务的标准作业流程

每篇论文必须依次经过以下状态；不得从“候选论文”直接跳到“已发布题目”。

### S0 候选登记

输出 paper.json。登记 DOI/PMID、版本、期刊、研究类型、癌种、组学、数据位置、代码位置、许可和撤稿检查。

### S1 数据定位与冻结

下载或登记所有必要输入，生成 data_manifest.json。每个文件记录相对路径、大小、SHA-256、来源 URL/accession、上游版本、许可、媒体类型和角色。

必须保留上游原始文件；格式标准化产生的新文件作为 derived object 另行记录，不得覆盖原始文件。

### S2 Insight 抽取

可以用模型辅助从摘要、Results、图注和补充材料提取候选 insight，但模型输出只能是候选。两名策展者至少有一名生物医学领域人员完成：

- 是否确为论文新发现，而非背景知识；
- 是否由当前可用数据支持；
- 是否能在不展示答案的情况下问出；
- 是否具有不止一种合理分析路径；
- 是否能定义评分对象。

### S3 论文—代码—数据映射

仿照 HeurekaBench，但把中间结果结构化。为每个候选 insight 建立 mapping：

- 支持它的数据文件；
- 支持它的作者脚本／notebook／命令；
- 产生它的中间表和最终图；
- 关键样本过滤、统计模型、阈值和随机种子；
- 可能造成结果变化的未报告参数。

### S4 独立复算

策展者在一个干净环境中用公开输入重建最小分析。目标不是逐像素复制原图，而是复现该结论所需的数值、集合、方向和不确定性。

独立复算必须留下：

- reproduce.sh；
- environment.lock 或容器 digest；
- reference workflow；
- 中间 artifacts；
- stdout/stderr；
- runtime 和资源用量；
- 对作者结果的偏差说明。

### S5 题干生成

题干可以由模板和模型辅助生成，但最终由人工批准。题干不得直接复制结论句，也不得提示 gold 特有的基因、通路、阈值或排序，除非这些属于预先定义的方法指导赛道。

每个题干必须包含：

- 研究背景的最小必要信息；
- 明确的科学问题；
- 输入文件及其含义；
- 推断单位；
- 允许或禁止的外部资源；
- 资源预算；
- 预期输出文件、字段和格式；
- 需要报告的不确定性和敏感性分析；
- 不透露答案的验收说明。

### S6 三类可答性测试

1. 数据充分性测试：领域专家只看公开 task package，能完成任务。
2. 无数据基线测试：强模型不能仅凭题干和常识稳定得到 gold；否则题目不是数据驱动发现题。
3. 泄漏测试：移除或重命名任何包含答案的文件、notebook、figure、缓存、对象元数据和目录名。

### S7 Grader 开发与对抗测试

先固定 grader，再跑被测模型。禁止看完模型答案后调整 gold 或 tolerance 以“让题目合理”。

grader 必须通过：

- gold artifact 自评分为 1；
- 合理替代方法在预先定义范围内得高分；
- 已知错误方法得低分；
- 空文件、错误字段、NaN、重复行、交换标签和伪造报告不会误得高分；
- 同一个 submission 重跑得到相同分数。

### S8 双人签字与发布

至少需要：

- Domain curator：确认生物学问题、推断单位和证据边界；
- Computational curator：确认数据、代码、复算和 grader；
- Release reviewer：确认公开／隐藏分离、许可、版本和泄漏。

三者可由两人承担，但任何 task 不得由同一人独自完成题干、gold、grader 和最终审核。

---

## 5. 磁盘目录与公开／隐藏边界

### 5.1 推荐目录

以下是第一阶段的 canonical layout。它有意保持简单：文件系统＋Git＋对象存储足够支撑首版，不需要先建数据库或微服务。

    benchmark/
      VERSION
      CHANGELOG.md
      DATASET_CARD.md
      registry/
        papers.jsonl
        datasets.jsonl
        tasks_public.jsonl
        splits.json
        systems.jsonl
      schemas/
        paper.schema.json
        data-manifest.schema.json
        task.schema.json
        output-contract.schema.json
        claim.schema.json
        rubric.schema.json
        run.schema.json
        event.schema.json
        score.schema.json
      papers/
        paper_id/
          paper.json
          curation/
            claim_map.jsonl
            code_map.jsonl
            decisions.md
      datasets/
        dataset_id/
          version/
            data_manifest.json
            README.md
            data/
      tasks/
        task_id/
          public/
            task.yaml
            prompt.md
            data_manifest.public.json
            output_contract.schema.json
            README.md
          private/
            gold_claims.jsonl
            rubric.json
            gold_artifacts/
            reference_workflow/
            graders/
            adjudication.md
      runs/
        benchmark_version/
          system_id/
            task_id/
              run_id/
                run.json
                events.jsonl
                human.log
                workspace_manifest.json
                submission/
                grading/

### 5.2 物理隔离规则

必须建立三个访问层：

- Public：题干、公开数据 manifest、输出契约、开发集和示例 grader。
- Hidden：test gold claims、gold artifacts、test grader 配置和 reviewer notes；agent 容器永远不可见。
- Restricted：受控数据位置、访问审计和映射；不进入公共 release。

Private 目录在实际 leaderboard 部署中应位于不同存储桶或不同仓库，而不仅是同一仓库下的另一个文件夹。上面的目录树用于表达逻辑关系，不表示应把隐藏答案提交到公开 Git。

### 5.3 大数据规则

大数据不得直接复制到每个 task：

- task 只引用不可变 DataSnapshot。
- 数据对象按内容或稳定 accession 管理。
- agent 以只读方式挂载输入。
- 每次运行在独立可写 workspace 中产生结果。
- 数据 manifest 记录完整文件清单和 checksum。
- ZIP、tar.zst 只用于分发，不是内部 canonical schema。

---

## 6. 文件格式规范

### 6.1 格式选择总表

| 内容 | Canonical 格式 | 理由 |
|---|---|---|
| 单个任务的人工审阅配置 | YAML | 可读、适合 code review；必须经 JSON Schema 验证 |
| 论文、数据集、公开任务索引 | JSONL；发布时另导出 Parquet | 一行一个稳定对象；便于增量处理；Parquet 便于分析 |
| 机器输出契约与 schema | JSON Schema Draft 2020-12 | 严格验证字段、类型和必需项 |
| 轨迹事件 | JSONL | 追加写入、异常退出时仍能保留已完成事件 |
| 单个 run、score、rubric | JSON | 对象边界清楚，适合机器读取 |
| 表格型结果 | Parquet 为主，TSV/CSV 为交换格式 | Parquet 保留类型；CSV 仅用于简单互操作 |
| 单细胞矩阵 | h5ad；超大数据可用 Zarr | 能保存矩阵、obs、var、layers 与 embeddings；支持分块／backed 读取 |
| 基因集 | GMT ＋ genesets.json | GMT 与 GSEA/MSigDB 生态兼容；JSON 保存版本、物种和 ID 空间 |
| 序列数据 | FASTQ/BAM/CRAM/VCF 等领域标准 | 不应为 benchmark 自创二进制格式 |
| 分析记录 | ipynb 可以有，但必须同时有 reproduce.sh 或可执行脚本 | notebook 适合审阅，不应成为唯一可重跑入口 |
| 人类报告 | Markdown | 可读、可版本化 |
| 发布级 provenance | provenance.json；正式归档可生成 ro-crate-metadata.json | 首版避免把全部操作复杂化，但保留向 RO-Crate/PROV 映射的字段 |

所有 JSON Schema 应声明 [Draft 2020-12](https://json-schema.org/draft/2020-12)。单细胞 h5ad/Zarr 的使用应遵循 [AnnData 的 on-disk 结构](https://anndata.readthedocs.io/en/stable/fileformat-prose.html)，而不是把大型稀疏矩阵展开到 CSV。正式归档的研究对象可以映射到 [RO-Crate](https://www.researchobject.org/ro-crate/specification.html)。

### 6.2 为什么不使用“一张总 CSV”

CSV 可以作为 leaderboard 导出，但不得作为 source of truth，原因是：

- 无法安全表达嵌套的文件 manifest、rubric 和 artifact 依赖；
- list/dict 容易被塞成字符串，再通过 eval 解析；
- 类型、空值、版本和 schema 约束薄弱；
- 无法物理隔离题干与 gold；
- 轨迹持续追加时容易损坏整表。

### 6.3 为什么暂不建数据库

第一阶段 100–200 篇论文、约 150–300 个任务的元数据规模很小。Git 中的 JSON/YAML/JSONL 更容易 review、diff、签字和发行。只有在出现多人并发编辑冲突、复杂在线查询或上万次实时 run 时，再把这些文件索引到 SQLite/PostgreSQL；数据库仍应是索引，不是唯一真相源。

---

## 7. PaperRecord 和 DataSnapshot 的字段

### 7.1 paper.json

最低字段如下：

    schema_version: 1.0
    paper_id: nature-2023-06130-4-v1
    title: ...
    identifiers:
      doi: 10.1038/s41586-023-06130-4
      pmid: ...
    publication:
      venue: Nature
      type: peer_reviewed
      published_at: ...
      version: version_of_record
    integrity:
      checked_at: ...
      retracted: false
      expression_of_concern: false
      corrections: []
    code_sources:
      - url: ...
        commit: ...
        license: ...
    data_sources:
      - accession: ...
        version: ...
        access: public
    curation:
      status: insight_validated
      domain_curator: curator_id
      computational_curator: curator_id
      reviewed_at: ...

不得只记录论文标题和 URL。论文网页内容、代码仓库和数据 accession 都可能变化，必须保存版本或 commit。

### 7.2 data_manifest.json

每个 DataSnapshot 必须包含：

    schema_version: 1.0
    dataset_id: 3ca-gavish-2023
    version: 1.0.0
    source_accessions: [...]
    created_at: ...
    license:
      identifier: ...
      redistribution_allowed: true
    biological_scope:
      species: Homo sapiens
      disease: cancer
      assay: scRNA-seq
      tissue: ...
      unit_of_observation: cell
      unit_of_inference: patient
      reference_genome: GRCh38
      gene_id_space: HGNC_symbol
    processing_level: standardized
    files:
      - relative_path: data/expression.h5ad
        role: input
        source_role: processed_expression
        media_type: application/x-hdf5
        size_bytes: ...
        sha256: ...
        source_url: ...
        agent_visible: true
    transformations:
      - activity_id: standardize-001
        inputs: [...]
        outputs: [...]
        code_commit: ...
        container_digest: ...
    integrity:
      manifest_sha256: ...

### 7.3 生物医学数据特有的必需元数据

对于单细胞和肿瘤数据，还必须记录：

- 原始 counts 位于 X、raw 还是 layer；
- X 是否已经 log-normalized、scaled 或 centered；
- obs 中 patient、sample、tumour、treatment、timepoint、batch、cell_type 的确切列名；
- 缺失值编码；
- malignant/non-malignant 标注来源；
- 细胞和基因过滤历史；
- 基因 ID 类型及从 Ensembl 到 symbol 的版本化映射；
- 数据是否为全队列、子采样或只选定细胞类型；
- patient 数、sample 数、cell 数和 feature 数；
- 原始数据与标准化快照之间的变换。

推断单位必须独立于观察单位记录。单细胞任务中最常见且最危险的错误，是把数万个 cell 当作数万个独立生物学重复。

---

## 8. 题干如何保存

### 8.1 task.yaml 是题目的真相源

题干的结构化源文件为 public/task.yaml。prompt.md 是由 task.yaml 渲染出来、真正发送给 agent 的冻结文本；tasks_public.jsonl 和 tasks.parquet 是发布索引。不得人工分别编辑四份内容。

task.yaml 的最低结构：

    schema_version: 1.0
    benchmark_version: 0.1.0
    task_id: 3ca-mp-metabolism-001
    task_version: 1.0.0
    paper_id: nature-2023-06130-4-v1
    dataset_id: 3ca-gavish-2023
    dataset_version: 1.0.0
    task_family_id: 3ca-mp-metabolism
    leakage_group_id: 3ca-gavish-paper-and-cohort
    track: blind_rediscovery
    input_level: standardized
    domain:
      disease: pan-cancer
      modality: scRNA-seq
      analysis_types: [program_discovery, pathway_annotation]
    scientific_context: ...
    question: ...
    inference_unit: patient
    visible_inputs:
      - path: data/expression.h5ad
        description: ...
      - path: data/sample_metadata.parquet
        description: ...
      - path: data/metabolic_genes.gmt
        description: ...
    allowed_resources:
      network: disabled
      tools: [python, r]
      reference_databases: [...]
    budget:
      wall_clock_seconds: 14400
      cpu: 16
      memory_gb: 64
      gpu: none
      max_model_tokens: ...
    required_outputs:
      contract: output_contract.schema.json
      entrypoint: reproduce.sh
    reporting_requirements:
      uncertainty: required
      sensitivity_analysis: required
      negative_control: required
    public_scoring_summary:
      primary_artifact: results/programs.parquet
      metric_families: [set_recovery, rank_concordance, robustness]

### 8.2 三个任务赛道

同一科学问题可以建立不同赛道，但必须分别编号和评分：

1. Guided reproduction：提供高层方法指导，但不提供作者代码和答案。测试执行能力。
2. Blind rediscovery：只提供科学问题、数据字典和必要背景。测试方法选择、分析与解释能力。
3. External validation：给独立数据，要求验证论文结论。测试泛化，不能把未复现当作简单错误，需报告 inconclusive。

主 leaderboard 应以 blind rediscovery 为中心；guided 赛道用于诊断 agent 是不会选方法，还是不会执行方法。

### 8.3 题干不得泄漏什么

除非任务目的就是验证特定方法，否则题干不得包含：

- gold gene list、cell state 名称、目标通路名或效应方向；
- 作者图表标题中直接陈述答案的句子；
- 只有 gold workflow 才使用的特殊阈值；
- 作者 executed notebook；
- 文件名中的答案，例如 IFNB_high_genes.csv；
- 数据对象的隐藏列、unused layer 或 uns 中残留的结果；
- 通过 DOI 搜索即可直接定位答案、且任务又允许无约束网络的设置。

如果任务允许网络访问，必须记录网络策略、访问 URL 和网页快照；sealed test 应优先限制对原论文、作者代码和答案来源的访问。

### 8.4 题干必须告诉 agent 什么

隐藏答案不等于隐藏数据语义。题干必须提供足够的数据字典：

- 每个文件是什么；
- 关键列代表什么；
- counts/normalized 的状态；
- 分组变量和单位；
- 必需的输出字段；
- 可使用的时间和算力；
- 是否允许联网和安装包；
- 失败或证据不足时如何表示。

ScienceAgentBench 把目录树和数据预览加入任务，是值得保留的设计。绝不能通过让 agent 猜文件格式制造无意义难度。

---

## 9. 隐藏金标准与 Rubric

### 9.1 private/gold_claims.jsonl

每行一条原子结论，不与题干存放在同一个数据文件。对于 test split，gold 文件不发布。

### 9.2 private/rubric.json

rubric 使用 PaperBench 的“树状原子要求”思想，但主要叶节点必须对应程序化检查。建议字段：

    rubric_id
    task_id
    rubric_version
    criteria:
      - criterion_id
        parent_id
        requirement
        weight
        hard_gate
        criterion_type
        evaluator
        expected_artifact
        metric
        tolerance
        valid_alternatives
        failure_tags

criterion_type 只允许：

- schema：文件和字段是否符合契约；
- execution：是否在干净环境中成功重跑；
- data_integrity：是否使用正确数据、样本和推断单位；
- statistical：统计量、模型或不确定性是否有效；
- artifact：表、列表、排序、矩阵或图的可计算性质；
- claim：是否恢复原子科学结论；
- robustness：替代阈值、重采样、负对照；
- process：工具误用、证据链和透明度；只作辅助分。

### 9.3 不要要求逐行复刻作者代码

gold workflow 是验证参考，不是唯一正确路线。评分必须围绕科学不变量：

- 相同的目标细胞／患者集合；
- 合理一致的方向、排名、集合或分布；
- 正确的推断单位；
- 可接受的效应量范围；
- 关键负对照不显著；
- 结论不过度外推。

不同工具只要满足这些性质，就应得分。否则 benchmark 测到的是“是否猜中作者软件栈”，不是科学发现能力。

---

## 10. Agent 最终要提交什么

### 10.1 submission 目录

每次运行的最低提交物：

    submission/
      reproduce.sh
      environment.lock
      src/
      analysis.ipynb
      results/
        primary.parquet
        supporting/
      figures/
      claims.jsonl
      methods.md
      report.md
      provenance.json

具体任务不一定需要所有文件，但以下四项必须有：

1. reproduce.sh：从只读输入生成全部计分 artifacts。
2. 结构化 primary artifact：Parquet、CSV、JSON 或领域标准格式。
3. claims.jsonl：模型从结果中提出的原子结论和置信度。
4. provenance.json：输入、代码、软件、参数和输出的关系。

Notebook 可以作为人类审阅界面，但不得是唯一执行入口。图片也不得成为唯一计分对象；画图所依据的表必须同时提交。

### 10.2 agent claims.jsonl

建议每行包含：

    claim_local_id
    subject
    relation
    object
    direction
    context
    estimate
    uncertainty
    statistical_support
    evidence_artifacts
    confidence
    limitations
    status

status 允许 supported、unsupported、contradicted、inconclusive。允许 agent 说“证据不足”是必要设计；否则系统会被激励编造确定结论。

### 10.3 输出契约

public/output_contract.schema.json 必须精确规定：

- 文件相对路径；
- 文件格式；
- 必需列及类型；
- row key 和唯一性；
- 缺失值规则；
- 排序是否有意义；
- 单位；
- 允许的枚举；
- 数值范围；
- 输出版本。

例如一个差异表达题不应只要求“一段解释”，而应要求 results/de.parquet 包含 gene_id、log2fc、p_value、q_value、direction，并要求 claims.jsonl 指向对应行。

---

## 11. 模型轨迹如何保存

### 11.1 两层轨迹

每个 RunBundle 同时保留：

- events.jsonl：机器可读的逐事件记录。
- human.log：压缩后便于人类审阅的日志。

events.jsonl 是 source of truth；human.log 由它渲染。不要像部分 benchmark 那样只保留 stdout，也不要只保留聊天消息而丢失工具调用和文件变化。

### 11.2 run.json

每次运行必须固定：

    schema_version
    run_id
    task_id
    task_version
    benchmark_version
    trial_index
    system_id
    model_provider
    model_id
    model_revision
    model_parameters
    agent_scaffold
    flow_id
    flow_version
    skills:
      - name
        version
        sha256
    tools:
      - name
        version
    prompt_sha256
    input_manifest_sha256
    container_digest
    network_policy
    seed
    budgets
    timestamps
    status
    termination_reason
    usage
    cost

“model”与“system”必须区分。同一个模型配不同 scaffold、skills 或工具是不同 system，不能在 leaderboard 上用同一名称混在一起。

### 11.3 events.jsonl 每行字段

每个事件至少含：

    schema_version
    event_id
    run_id
    task_id
    sequence
    timestamp
    elapsed_ms
    actor
    event_type
    parent_event_id
    message
    tool
    arguments
    result_ref
    stdout_ref
    stderr_ref
    exit_code
    artifacts_written
    usage_delta
    error

event_type 建议限制为：

- run_started、run_finished；
- message；
- plan_summary；
- tool_call、tool_result；
- command_started、command_finished；
- file_written、file_deleted；
- checkpoint；
- error；
- submission；
- grader_started、grader_finished。

大型 stdout、图片、notebook 和二进制文件不得完整嵌入 JSONL；保存为 artifact，再在 result_ref 中记录相对路径、大小、媒体类型和 SHA-256。

### 11.4 不把隐藏思维链设为必需字段

轨迹应记录可观察行为：模型公开消息、工具参数、命令、输出、错误、文件变化、明确的计划摘要和自我修正。不得要求所有提供商暴露内部 chain-of-thought，也不得把不可见推理长度作为 leaderboard 指标。

若某模型原生提供 reasoning summary，可以作为 optional message 保存，并标记 source=model_provided_summary；不能与真正可观察工具事件混为一谈。

### 11.5 Workspace 快照

至少保存：

- 初始 workspace manifest；
- 最终 submission；
- 最终 workspace manifest；
- 失败时的最后 checkpoint；
- 每个计分 artifact 的 SHA-256。

不必每个操作都压缩一次整个 workspace。对于长任务，可以按固定时间或关键阶段保存增量 checkpoint。

---

## 12. 评分结果如何组织

### 12.1 grading 目录

    grading/
      validation.json
      reproduction.json
      criterion_scores.jsonl
      artifact_scores/
        artifact_id.json
      claim_matches.jsonl
      failure_tags.json
      score.json
      grader.log

### 12.2 三个评分层次

第一层：硬门槛，不通过则总分封顶或为零。

- 输入未被篡改；
- 输出 schema 合格；
- reproduce.sh 在干净环境中可运行；
- 未读取 hidden gold；
- 没有患者隐私或许可证违规；
- 没有用 cell 伪装 patient-level replication 等致命统计错误。

第二层：任务科学分，建议 100 分：

| 维度 | 建议权重 | 主要证据 |
|---|---:|---|
| 可重跑性与产物完整性 | 10 | 干净环境重跑、文件契约 |
| 数据选择与 QC | 15 | 样本、细胞、基因过滤和数据完整性 |
| 统计设计与不确定性 | 20 | 推断单位、模型、效应量、CI/FDR |
| 主要 artifacts 与 gold 的一致性 | 30 | 集合、排序、连续值、分布、聚类等确定性指标 |
| 科学结论恢复与证据对齐 | 15 | gold claim 匹配、方向、边界、置信度 |
| 稳健性、敏感性与负对照 | 10 | 阈值、重采样、替代方法、negative control |

第三层：运行效率与过程诊断，单独报告，不混入主科学分：

- wall-clock；
- token；
- API cost；
- CPU/GPU 小时；
- 工具调用数；
- 错误恢复次数；
- 人工介入次数；
- process failure tags。

成本可以形成 Pareto leaderboard，但不得用低成本掩盖科学错误。

### 12.3 指标选择

grader 根据 artifact 类型选择指标：

| Artifact | 推荐指标 |
|---|---|
| 无序基因／细胞状态集合 | Precision、Recall、F1、Jaccard |
| 排名基因／通路 | Spearman、Kendall、top-k overlap、rank-biased overlap |
| 连续表达／score／效应量 | CCC、Spearman、归一化 RMSE、符号一致率 |
| 差异表达表 | 方向一致率、top-k F1、效应量相关、FDR 合理性 |
| 聚类／细胞标签 | ARI、NMI、macro-F1；必要时先做 label matching |
| 细胞比例／组成 | MAE、相关、Jensen–Shannon divergence |
| 通路富集 | NES 相关、方向一致、显著集合 F1 |
| 生存模型 | C-index、time-dependent AUC、HR 方向与 CI；必须基于患者级 split |
| 数值计数 | 预注册 absolute/relative tolerance |
| 结构化假设 | 原子 claim 匹配、证据链接、可证伪性、校准 |

指标和 tolerance 必须在模型运行前写入 rubric。若不同合理工具产生差异，应使用范围、多指标或多个 gold alternatives，而不是事后挑一个对模型有利的阈值。

### 12.4 LLM judge 的上限

LLM judge 只用于：

- 将自然语言 claim 对齐到 gold claim；
- 检查解释是否超出数据；
- 辅助标注失败模式；
- 人类复核前的排序。

LLM judge 贡献不得超过主科学总分的 10%，且必须固定模型版本、prompt、temperature、输入 hash，并对一部分样本做双 judge 与人工一致性审计。确定性 artifact 分不能被 judge 覆盖。

### 12.5 score.json

最终分数对象至少含：

    score_schema_version
    run_id
    task_id
    task_version
    grader_version
    grader_container_digest
    hard_gates
    component_scores
    total_scientific_score
    deterministic_fraction
    judge_fraction
    efficiency
    failure_tags
    valid
    invalid_reason
    created_at
    input_hashes

leaderboard.csv／parquet 由 score.json 聚合生成，不得反过来成为原始评分记录。

---

## 13. 对照实验与 leaderboard 规则

### 13.1 核心对照

为直接回答导师提出的“一句话 prompt 与包含人类工作流程和工具的 agent flow 有何差异”，每个模型至少运行：

- P0 Direct：题干＋数据说明＋输出契约，不提供 workflow skills。
- P1 Agent flow：同一题干和数据，提供冻结版本的领域 workflow、skills 和工具。

可选增加：

- P2 Oracle-guided：提供正确高层方法，用来区分方法选择失败与执行失败。
- P3 Ablation：去掉某个 skill，例如统计审计或反例检查。

### 13.2 公平比较的固定项

P0 与 P1 必须相同：

- task version 和输入 hash；
- 模型及模型 revision；
- temperature、seed 策略和试验次数；
- wall-clock、token、内存、CPU/GPU；
- 网络策略；
- 基础软件；
- grader；
- 终止条件。

只有 agent flow、skills 或明确研究的变量可以改变。

### 13.3 重复与统计

- 每个 system×task 至少 3 次独立运行；高方差任务应 5 次。
- leaderboard 报告 task-level mean、median、95% bootstrap CI 和成功率。
- 统计比较以 task 为配对单位，不能把 artifact 或 cell 当独立重复。
- 同时报告平均科学分、hard-failure rate、成本和时间。
- 对模型做总体排名时，先按 task family 聚合，避免一篇论文拆很多小题后支配总榜。

### 13.4 Leaderboard 的展示

至少提供四列主结果：

1. Scientific score；
2. Reproducible success rate；
3. Median cost；
4. Median wall-clock。

另外按以下切片展示：

- 癌种；
- 单细胞／bulk／空间／多组学；
- QC、DE、program discovery、pathway、trajectory、survival；
- guided vs blind；
- input size；
- analysis depth；
- direct vs agent flow。

不建议只公布一个总分。一个模型可能擅长 QC 而在患者级统计上持续犯错。

---

## 14. 数据切分、污染与密封

### 14.1 切分单位

所有 split 必须以 leakage_group_id 为单位。以下任何一项共享，都应默认属于同一组：

- 同一论文或补充论文；
- 同一数据 accession；
- 同一患者／donor cohort；
- 同一作者 processed matrix 的不同导出；
- 同一 gold figure/table 的变体；
- 同一任务的 guided/blind 版本。

### 14.2 推荐切分

在 100–200 篇论文规模下：

- 50% public development/training：题干、部分 gold、示例轨迹和 grader 可公开，供开发 skills 和后续 SFT。
- 20% validation：题干公开、gold 由评测服务器持有，供调参与消融。
- 30% sealed test：题干可按评测时下发，gold 和 grader 配置密封。

另建立滚动 prospective set：优先选模型训练截止之后新发表、数据已释放的论文，按季度或半年加入。这样才能减轻模型记住论文答案的问题。

### 14.3 污染控制

- 每题可放非答案型 canary，但 canary 只能侦测显性复制，不能证明无污染。
- 记录论文首次公开日期、数据首次公开日期和 benchmark release 日期。
- 测试无数据模型是否能直接答对。
- 对题干做改写鲁棒性检查。
- sealed test 不公开 gold、作者结果表、reference workflow 或隐藏 rubric。
- 训练阶段只能使用明确标记为 trainable 且许可允许的 public runs；不得把 test 运行轨迹回流到训练集。

---

## 15. 版本、勘误与可撤销性

### 15.1 语义版本

benchmark、task、dataset、rubric、grader 和 schema 分别有版本。

- Patch：修正文案、日志或不改变预期答案的 grader bug。
- Minor：增加任务、指标或兼容字段；旧任务语义不变。
- Major：改变输入数据、题干实质、gold、推断单位或计分逻辑。

任何影响分数的修改都必须触发新 task/rubric/grader version，旧 leaderboard 不可与新版本无标记混合。

### 15.2 不可变 release

每次 release 必须包含：

- VERSION；
- release manifest；
- 文件 SHA-256；
- Git commit；
- 数据对象 manifest；
- schema bundle；
- release date；
- CHANGELOG；
- previous release 指针。

不得静默覆盖对象。发现错误时发布新版本，并保留旧版本 tombstone 和迁移说明。

### 15.3 问题登记

维护 issues.jsonl：

    issue_id
    task_id
    affected_versions
    reported_at
    issue_type
    evidence
    severity
    status
    resolution
    fixed_in

[ScienceAgentBench](https://github.com/OSU-NLP-Group/ScienceAgentBench) 后续增加 verified split、[BixBench](https://huggingface.co/datasets/futurehouse/BixBench) 从早期版本修订为 1.5，都说明“发布后发现题目不可答或评分漏判”是现实情况，必须被设计进治理流程。

---

## 16. 发布前硬门槛清单

每道正式任务必须全部通过：

### 论文和许可

- [ ] 论文身份、版本、DOI/PMID 已核对。
- [ ] 撤稿、concern、correction 状态有检查日期。
- [ ] 数据和代码许可已记录。
- [ ] 人体数据的公开／受控边界清楚。

### 数据

- [ ] 所有输入有相对路径、大小和 SHA-256。
- [ ] 原始与派生数据未混淆。
- [ ] 数据字典完整。
- [ ] observation unit 和 inference unit 明确。
- [ ] agent 以只读方式访问输入。

### 科学结论

- [ ] claim 已原子化。
- [ ] 有论文、代码／方法和独立复算三重锚点。
- [ ] 关键敏感性分析已完成。
- [ ] 不稳定或争议结论未作为精确 gold。

### 题干

- [ ] 一题一个主要问题。
- [ ] 只靠题干不能稳定答对。
- [ ] 不含答案型文件名、图表、notebook 或隐藏列。
- [ ] 输出契约精确且机器可验证。
- [ ] 预算和网络策略明确。

### Grader

- [ ] gold 自评满分。
- [ ] 合理替代方法通过。
- [ ] 已知错误方法失败。
- [ ] 空／坏／伪造 artifact 不会误得分。
- [ ] grader 在干净容器中可重复。
- [ ] 确定性分占主分至少 90%。

### 运行与版本

- [ ] run.json 和 events.jsonl schema 通过。
- [ ] prompt、flow、skill、工具、镜像和输入均可定位到版本/hash。
- [ ] public、hidden、restricted 物理隔离。
- [ ] leakage_group 未跨 split。
- [ ] 双人审核和 release reviewer 已签字。

任何一项“必须”未通过，任务只能留在 candidate/dev，不能进入 sealed leaderboard。

---

## 17. 结合 3CA 的首个 pilot 示例

### 17.1 推荐先做的任务

以 2023 年 3CA/Hallmarks 论文为第一批 pilot，可以构造三个层级：

#### Task A：恶性细胞程序重新发现

- 输入：冻结的恶性细胞表达 h5ad、patient/sample metadata。
- 问题：在跨肿瘤队列中识别可复现的肿瘤细胞内在表达程序。
- 主要输出：program×gene 排名表、program×sample 活性、复现率表。
- 隐藏 gold：作者 meta-programs、复算后的 program mapping、稳定性范围。
- 指标：top-k gene F1、rank correlation、program matching、跨 sample recurrence。

#### Task B：代谢相关程序识别

- 输入：同一表达快照、冻结版本代谢基因集及其 ID 映射。
- 问题：识别在多个患者或癌种中复现的代谢相关肿瘤细胞状态，并报告支持与反例。
- 主要输出：候选 program、核心基因、患者级活性、通路富集、敏感性结果。
- 隐藏 gold：论文与独立复算支持的代谢程序、方向和适用癌种。
- 指标：集合／排序一致性、NES 方向、患者级复现、负对照。

#### Task C：外部癌种验证

- 输入：与构建 gold 不同的公开癌种数据。
- 问题：验证一个在训练论文中发现的程序是否在外部队列出现。
- 主要输出：外部队列 score、效应量、置信区间和 inconclusive 判定。
- 评分：不能只比较“是否显著”；同时评估方向、效应量、校准和证据不足时的正确克制。

### 17.2 公开输入包

    public/
      task.yaml
      prompt.md
      data_manifest.public.json
      output_contract.schema.json
      data/
        expression.h5ad
        sample_metadata.parquet
        metabolic_genes.gmt
        genesets.json
        data_dictionary.md

expression.h5ad 必须明确：

- X/layers 的数值状态；
- obs 中 patient、sample、cancer_type、cell_type 的列；
- gene ID 版本；
- 哪些预处理已经由 benchmark 完成；
- 哪些步骤仍应由 agent 完成。

### 17.3 隐藏包

    private/
      gold_claims.jsonl
      rubric.json
      gold_artifacts/
        metaprograms.parquet
        program_activity.parquet
        pathway_enrichment.parquet
        sensitivity_bounds.json
      reference_workflow/
      graders/

作者原始程序与独立复算程序都应保留，但 grader 应比较科学 artifacts，而不是要求 agent 采用 NMF 的完全相同实现或完全相同随机种子。

### 17.4 与导师问题的直接对应

对每个 3CA pilot task，用同一模型运行：

- Direct：一句话科学问题＋数据和输出契约；
- Flow：数据定位／版本确认→QC→基因集校验→分析→患者级统计→敏感性→文献核对→反例→结论与不确定性报告。

主要比较：

- 是否恢复已知 meta-program／metabolic program；
- 是否使用正确推断单位；
- 是否能发现负对照或癌种异质性；
- 是否产生可重跑 artifact；
- skills 带来的分数提升是否超过成本增加。

这比单纯比较最终自然语言答案，更能回答“skills 是否重要”和“agent flow 是否比一句话 prompt 更可靠”。

---

## 18. 建设规模与分期

不要直接从零构造 200 篇正式密封任务。更稳妥的顺序：

### v0.1：格式与 grader pilot

- 5 篇 A 级论文；
- 8–12 个 task；
- 覆盖 program discovery、DE、pathway、cell state；
- 至少 2 个 3CA 任务；
- 完整跑通 public/private、trajectory、submission、grading。

验收：两名专家能只用 public package 完成；所有 gold 可独立复算；确定性评分覆盖至少 90% 主分。

### v0.5：领域覆盖

- 约 30 篇论文；
- 45–60 个任务；
- 加入 T-cell state、metabolism、survival、trajectory／clone；
- 建立 direct vs flow 的小规模模型矩阵；
- 完成首次 grader robustness 和 inter-rater audit。

### v1.0：正式 benchmark

- 100–200 篇论文；
- 每篇平均 1–3 个 task；
- public dev、validation、sealed test 和 prospective set；
- 正式 leaderboard、dataset card、schema、release manifest、issue/errata 流程。

如果 v0.1 仍频繁出现“专家也无法从公开包答题”“合理方法被 grader 判错”或“只靠论文记忆能答对”，应先修规则，不应靠扩大论文数掩盖问题。

---

## 19. 最终必须坚持的十条规则

1. 一题一个科学问题、一个主要推断单位、一个输出契约。
2. 先复算结论，再写题干；不能从论文摘要直接生成题库。
3. 题干与 gold 物理隔离，test gold 永不进入 agent 环境。
4. 每个数据文件、代码、模型、flow、skill、容器和 grader 都有版本或 hash。
5. 原始输入只读，agent 只在独立 workspace 写结果。
6. 评分以结构化 artifact 和统计性质为主，不以措辞相似度为主。
7. 正确替代方法应得分；错误推断单位和数据泄漏应成为 hard failure。
8. 轨迹记录可观察行为和 artifact，不依赖隐藏思维链。
9. split 按论文／数据／队列 family 分组，不能让同源数据跨 train-test。
10. release 不可静默修改；错误通过版本、issue、tombstone 和重算 leaderboard 处理。

---

## 20. 来源与核对版本

### 主要 benchmark

- [ScienceAgentBench 论文](https://arxiv.org/abs/2410.05080)；[官方仓库，核对 commit c26e151](https://github.com/OSU-NLP-Group/ScienceAgentBench/tree/c26e151ed601ba109dc4d35e057ff8e73fec469d)；[Hugging Face 数据集](https://huggingface.co/datasets/osunlp/ScienceAgentBench)。
- [PaperBench 论文](https://arxiv.org/abs/2504.01848)；[OpenAI 项目说明](https://openai.com/index/paperbench/)；[官方代码与数据结构](https://github.com/openai/frontier-evals/tree/main/project/paperbench)。官方代码核对 commit 51052cede8cc608f95bb00346635e03759013e5a。
- [BixBench 论文](https://arxiv.org/abs/2503.00096)；[官方仓库，核对 commit 4931118](https://github.com/Future-House/BixBench/tree/49311180bdacb324c596f2e07596c126f2004008)；[BixBench 1.5 数据集](https://huggingface.co/datasets/futurehouse/BixBench)。
- [HeurekaBench 论文](https://arxiv.org/abs/2601.01678)；[官方仓库，核对 commit 24a67f1](https://github.com/mlbio-epfl/HeurekaBench/tree/24a67f1117f1bbf737014fa196171d21f4d78862)。
- [CellVoyager / CellBench 论文](https://www.nature.com/articles/s41592-026-03029-6)；[官方仓库，核对 commit 5a61f6b](https://github.com/zou-group/CellVoyager/tree/5a61f6b36bc7e2dd2210024cbb94fb0dd1cbbc0b)。
- [scBench 论文预印本](https://arxiv.org/abs/2602.09063)；[官方仓库与任务规范，核对 commit 0bc3403](https://github.com/latchbio/scbench/tree/0bc34032bfa402dad29fc40b4cf10ea8fc03193e)。
- [BixBench3 论文预印本](https://arxiv.org/abs/2608.25286)；[公开 runner、schema 与确定性 grader，核对 commit d0e0bbb](https://github.com/EdisonScientific/BixBench3/tree/d0e0bbb41222335b1b8878f533a58466a3a782dc)。该工作在 2026 年 8 月发布，本文将其视为新近工程证据。
- [OpenDiscoveryTrace 论文](https://arxiv.org/abs/2609.09203)；[公开轨迹仓库](https://github.com/aayambansal/OpenDiscoveryTrace)；[轨迹数据集](https://huggingface.co/datasets/aayambansall/OpenDiscoveryTrace)。该资源主要支持过程轨迹设计，不作为本项目 biomedical gold 构造的主要证据。

### 数据与 provenance 规范

- [FAIR Guiding Principles](https://www.nature.com/articles/sdata201618)：强调数据、算法、工具和 workflow 的可发现、可访问、可互操作与可复用。
- [NIH Data Management and Sharing Policy](https://grants.nih.gov/grants/guide/notice-files/NOT-OD-21-013.html)；[NIH repository 选择建议](https://grants.nih.gov/grants/guide/notice-files/NOT-OD-21-016.html)：支持稳定标识符、元数据、完整性和人体数据访问边界。
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)：用于 task、run、event、output 和 score 的机器验证。
- [AnnData on-disk format](https://anndata.readthedocs.io/en/stable/fileformat-prose.html)：用于 h5ad/Zarr 单细胞输入。
- [RO-Crate 规范](https://www.researchobject.org/ro-crate/specification.html)；[Workflow Run RO-Crate](https://arxiv.org/abs/2312.07852)；[W3C PROV Overview](https://www.w3.org/TR/prov-overview/)：用于发布级研究对象和运行 provenance。
- [Data Cards](https://research.google/pubs/data-cards-purposeful-and-transparent-dataset-documentation-for-responsible-ai/)；[Datasheets for Datasets](https://arxiv.org/abs/1803.09010)：用于 DATASET_CARD、用途边界、数据来源、策展过程和风险说明。

### 本项目背景材料

- 2023 年 3CA/Hallmarks 论文：[Nature 文章](https://www.nature.com/articles/s41586-023-06130-4)；[3CA 官方代码库](https://github.com/tiroshlab/3ca)；[3CA Portal](https://www.weizmann.ac.il/sites/3CA/)。
- 本地会议记录：[会议记录稿件.md](C:/Users/User/Desktop/agentic/material/会议记录稿件.md)，尤其是从论文已知发现构造标准任务、统一 agent flow，以及一句话 prompt 与 skills workflow 对照的讨论。

---

本规则的核心不是“把更多论文转成更多问答”，而是把每个已发表发现变成一个有版本、有输入、有证据、有可观察过程、有结构化输出、有隐藏评分器、能被独立重跑的科学实验单元。只有做到这一点，第一阶段产生的 benchmark 才能同时服务第二阶段 workflow 比较和第三阶段小模型训练，而不会把论文记忆、提示工程和真正的数据驱动发现混在一起。
