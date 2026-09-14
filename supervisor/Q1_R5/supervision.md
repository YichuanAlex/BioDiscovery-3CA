# Q1 R5 until-complete 自主工作流监督

## 边界

- 工作流：`C:\Users\User\Desktop\agentic\workflow_codex`。
- 研究目录：`C:\Users\User\Desktop\agentic\3CA\Q1_R5`。
- 监督目录：`C:\Users\User\Desktop\agentic\supervisor\Q1_R5`。
- 只有项目内 Qwen3.5-4B 编写研究代码、下载数据、执行分析和撰写报告。监督者不选择数据集、不提供统计方法/参考数字、不写或修改研究产物、不发送研究纠错提示。
- R1–R4 和标准 Codex 产物不输入 Qwen3.5-4B；项目内经来源与哈希验证的公开原始字节缓存可以复用，但模型必须自行记录来源、哈希和复用事实。

## R4 证据驱动的启动前修复

- `--max-rounds 0` 取消自主模型轮次上限；旧的无动作/无进展阈值改为有日志的 loop recovery，不再结束任务。
- 外层启动器对可恢复的模型服务/网络/检查点中断持续恢复同一任务，不再限制三次。
- catalog/web 预算护栏和工具错误会冷却对应工具一个响应，其他工具仍可用；冷却后自动恢复。
- 路径本身不是 PowerShell 动作；空输出且无工作区变化的 exit 0 不算进展或完成验证。
- Skill 名被明确标注为说明入口，不是函数工具。

完整工程测试、冻结哈希和正式启动时间在启动后追加。本文件的启动前内容不代表研究完成。

## 启动前验证与正式启动

2026-09-12 完成 Node 语法、PowerShell 5.1 解析、until-complete/预算冷却/path-only shell 永久回归和完整 `test-Qwen3.5-4B.ps1`，全部退出 0。本次完整测试因宿主无交互式终端而对 Computer Use 输入动作标记 SKIP；运行时、应用枚举和观察通过，Computer Use 模块未修改，R4 启动前的真实动作闭环证据单独保留。详见 `engineering-validation.md`。

R5 于 2026-09-12 18:31:49 +08:00 从空的 `C:\Users\User\Desktop\agentic\3CA\Q1_R5` 启动。运行器 PID 404、Node 子进程 PID 20288；命令行实际包含 `--autonomous --max-rounds 0`。manifest 明确 `run_until_complete=true`、`max_rounds=0`，提示 SHA-256 为 `a0324f0ad73ac0fea171463a30ade153db2d6b20df967c3f0e3a357b3296eb9a`。11 个关键文件及哈希保存在 `run-manifest.json` 和 `frozen-workflow`；首轮复核哈希差异 0。运维重启 0、研究干预 0。

只读 heartbeat `Qwen3.5-4B-q1-r5` 每 15 分钟运行 `audit-r5.mjs`，无实质变化时不通知；它不得修改任务/工作流、追加研究提示或手动重启，完成或不可恢复终态后暂停。

首个非终态快照为 5 次模型响应、5/5 thinking 开启且 5/5 实际返回 reasoning、6 个工具结果、0 失败、0 护栏、0 loop recovery、任务文件 0。进程存活、runner-result 不存在，当前只是启动成功，不是任务完成。

## 无限轮次现场验证（非终态）

R5 已运行到 51 个 checkpoint 轮次，超过 R4 在 48 轮写入 `needs_attention` 并退出的位置；进程仍存活、runner-result 不存在、status=`running`。当前 51/51 thinking 开启且 51/51 实际返回 reasoning，55 个工具结果、5 个失败、32 个护栏、26 个 loop breaker、2 个 loop recovery，冻结文件哈希差异 0，研究干预 0。两次旧“连续无进展”阈值均转换为 loop recovery，未结束 session，证明 `--max-rounds 0` 的运行时分支而非仅配置文本生效。

当前研究文件仍为 0。模型在冷却后调用过 `get_study`，但随后重复空目录列表、主页和不兼容的 PowerShell 命令；无限模式防止人工时长/轮次截断，却不能单独保证 4B 模型形成有效研究策略。监督者没有修改冻结引擎或给出研究纠错，后续由活跃的 `Qwen3.5-4B-q1-r5` heartbeat 继续只读审计。

初版 R5 审计曾把同时带可见文本的 assistant 响应对应的 `response_item` 与 `event_msg` 重复计数，出现 responses 大于 checkpoint rounds。原始 JSONL 没有重复模型请求；只读审计已限定以 `event_msg` 的 assistant_response 计数，修正后 rounds/thinking/reasoning 为 51/51/51。此修改只影响 supervisor 汇总，不触及运行中的工作流或研究目录。
