# R2 自主工作流监督

## 执行边界

- 工作流：`C:\Users\User\Desktop\agentic\workflow_codex`（用户最新确认的现存根目录）。
- 新研究目录：`C:\Users\User\Desktop\agentic\3CA\Q1_R2`。
- 本监督目录：`C:\Users\User\Desktop\agentic\supervisor\Q1_R2`。
- 旧归档位于 `3CA\Q1_R1` 和 `supervisor\Q1_R1`，不移动、不改写。用户明确要求直接使用上述既有 `Q1_R2` 目录，不创建 `Q1\_R2` 层级。
- 只有本地 Qwen3.5-4B 编写、运行和修改研究代码、分析与报告。监督者修改工作流工程、保存原始提示与版本/测试证据、启动任务，并只读观察与验收；不代写研究产物、不追加研究纠错提示、不复制 R1/标准 Codex 解法给模型。
- 本轮允许经来源/哈希验证的公开原始下载缓存复用，不允许旧分析结果/报告复用。研究能否自主达到标准以本轮真实工具与文件证据衡量。

## 优化前基线

R1 记录包含大量人工续行/纠错、参考分析代码复用和部分监督者改稿，未最终验收。因此不能把 R1 当作完全自主的小模型成功案例，也不能把复现同样数字作为独立推理能力证据。标准 Codex 产物仅供监督者事后比较，不作为 R2 的解法输入。

## 启动前检查

- 完整集成测试通过，包括真实 Computer Use 动作闭环、本地模型 tool-call 协议、文件/网络/附件/日志、MCP 工具枚举与一次调用、隔离与环境恢复。
- 模拟模型配合真实工具的自主恢复、提前完成拒绝、嵌套路径、reasoning 保存、未知修改结果的恢复不重放、预算用尽非零退出检查通过。
- 真实 Qwen3.5-4B 自主工程探针三轮完成：写入 7 字节 `AUTO_OK`，执行验证，引用实际调用 id 提交完成候选；文件读回与哈希核查通过。探针不包含任何 Q1 研究解法，未作人工续行。
- 冷启动并发和所有工具全部参数分支没有穷尽测试；授权 shell 不是 OS 沙箱。不能以这些工程通过声称研究质量达到 Codex。

## 监督方式

`audit-r2.mjs` 只读工作区和本轮 isolated rollout，镜像完整日志、产生工具全量参数/返回时间线与状态快照，区分引擎自动续行和实际用户追加输入。不得推断未返回 reasoning。runner 完成只作为候选，另做来源、计算复现、引用、图表/公式/表格一致性和 PDF 视觉验收。运行中冻结工作流；发现缺陷记录，不临时帮模型修研究代码。若引擎停止或预算用尽，照实标记，不用手动解法掩盖失败。

## 正式启动

2026-09-12 17:08:14 +08:00；运行器 PID 6320。启动时研究目录为空，版本与原始提示已冻结，详见 run-manifest.json / frozen-workflow。监督自动化 Qwen3.5-4B-r2，每 15 分钟被动核查；只通知重要变化，不向模型发送研究纠错或手动重启。日志和执行结果见 logs/worker.stdout.log、logs/worker.stderr.log、runner-result.json（结束后生成）与 audit.json。冻结后观察到的引擎问题不得直接修进本轮。

## 首次执行中止与基础设施恢复重试

首次运行 17:08:31 退出，研究工具调用 0、研究文件 0。实际 model_response 中保存了 reasoning，之后的独立 reasoning 项/检查点写入失败，故不宣称完整记录。错误为 ENOSPC，错误处理再次保存失败造成二次异常，旧 running 状态失真；audit 以 runner_failed 为准。C: 尚有约 99.8 GB，同目录工程写入连续三次通过，环境根因未知；未删用户文件。暂停监督。

首次运行结束后修复引擎的有界持久化重试和二次异常保护，注入 ENOSPC 回归通过，隔离检查通过。首次冻结副本、日志、结果不覆盖。第二次作为明确标注的基础设施恢复重试，仍使用同一原始用户提示、空研究目录和仅含初始目标的上次已提交检查点，不植入研究解法。使用 run-manifest-attempt2.json / frozen-workflow-attempt2 / worker-attempt2 日志及 runner-result-attempt2.json。人工研究干预保持 0，但人工运维重启为 1；不把两次拼成“全程自主未中断”，不以该恢复证明长程能力。

## 第三次运行的终态

- 第二次启动失败的根因是 Windows PowerShell 5.1 将单个 `--resume` 字符串按字符展开；修复为显式字符串数组并以真实参数 Probe 验证后，第三次于 2026-09-12 17:16:08 +08:00 启动，运行器 PID 23736。人工运维恢复累计 2 次，研究内容干预仍为 0。
- 第三次实际运行 31 轮，得到 54 个工具返回，其中 1 个失败；31 个模型响应中 16 次 thinking 开启且返回实际 reasoning，后续 15 次 thinking 被旧恢复逻辑关闭且没有返回 reasoning。审计汇总显示 17 个 reasoning 响应，是因为还包含首次启动在持久化失败前保存的 1 条。模型停留在 initialization，检查点 next_action 仍为探索 3CA catalog。
- 模型先广泛重复 `search_studies`，随后通过 PowerShell 多次运行同一条 `threeca.exe search "10x"`。第二次真实命令仍返回超长结果，后续相同调用被重复保护拦截；模型没有改用过滤参数、保存输出、选择研究对象或创建文件。连续 8 轮无验证进展后，引擎按设计以 `Autonomous recovery exhausted without verified progress` 停止。
- 结束时间为 2026-09-12 17:21:38 +08:00；`runner-result-attempt3.json` 为失败，checkpoint 为 `needs_attention`，研究文件和要求产物均为 0，semantic acceptance 为 `not_accepted`。不再人工重启，不把工具数量或 reasoning 数量冒充任务完成。监督 heartbeat 已暂停。
- 原始第三次 rollout 为 `workflow_codex\.runtime\codex-home\sessions\2026\09\12\rollout-2026-09-12T17-16-09-d41e4aa6-b5c.jsonl`；其首条元数据顺序不规范的事实保留并由 audit 标记，不重排原始日志。完整工具时间线、镜像日志和最终快照见本目录 `tool-timeline.csv`、`logs` 与 `audit.json`。

## 终态后的工程修复（不属于 R2 冻结版本）

R2 结束后才修改当前工作流：自主模式的工具错误/引擎续行不再关闭 thinking，每次请求显式记录 `reasoning_requested`、`thinking_enabled` 与实际 `reasoning_present`；恢复事件移到首条 `session_meta` 之后；超长 PowerShell/3CA 返回改为保留首尾及显式截断标记，上下文缩减也限制单条文本。冻结的 attempt3、副本、原始日志和研究目录均未修改。

真实 Qwen3.5-4B 工程探针独立完成 `write_file -> run_powershell -> complete_task`。其 3/3 次请求均为 thinking requested/enabled，3/3 次均实际返回 reasoning 并生成独立 reasoning 项；首条事件为 session_meta。完整功能测试随后退出 0。该结果只验收修正后的开关和记录链，不改变 R2 研究失败结论，也不证明长程研究达到 Codex。
