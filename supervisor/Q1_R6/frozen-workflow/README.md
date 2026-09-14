# 本地 Qwen3.5-4B Workflow

本项目的唯一目录是：

```text
C:\Users\User\Desktop\agentic\workflow_codex
```

它通过本地 vLLM 使用 `Qwen3.5-4B`，不调用电脑中安装的 `codex` 命令，也不会自动扫描或写回 `C:\Users\User\.codex`、`C:\Users\User\.agents` 或 `%LOCALAPPDATA%\OpenAI\Codex`。只有当用户在提示中明确给出外部附件路径时，程序才会读取该源文件并复制一份到本项目；运行时状态、3CA 缓存和 Computer Use 运行时均保存在本项目内。

## 安装和测试

```powershell
Set-Location 'C:\Users\User\Desktop\agentic\workflow_codex'
& '.\tools\tool43CA\install.ps1'
& '.\test-Qwen3.5-4B.ps1'
```

完整测试包含：路径隔离、Qwen3.5-4B 模型、文件工具、联网工具、3CA CLI/MCP，以及 Computer Use 的应用枚举、启动、窗口选择、观察、按键动作和动作后观察。Windows 桌面已锁定时，输入动作会明确标记为 `SKIP`；解锁后重新运行即可强制验证真实动作，测试不会尝试越过登录界面。

也可单独强制执行 Computer Use 动作闭环测试：

```powershell
& 'C:\Program Files\nodejs\node.exe' '.\tools\computer-use\test-computer-use.mjs' --require-action
```

## 交互使用

```powershell
# 普通交互；已包含文件读取、联网、Computer Use 和 3CA 工具
& '.\run-Qwen3.5-4B.ps1'

# 额外允许写文件和执行 PowerShell
& '.\run-Qwen3.5-4B.ps1' --allow-write --allow-shell

# 在另一个明确目录完成任务；模型、工具和会话状态仍来自 workflow_codex
& '.\run-Qwen3.5-4B.ps1' --workspace 'C:\Users\User\Desktop\agentic\3CA\Q1' --allow-write --allow-shell
```

输入 `/clear` 清空对话，输入 `/exit` 退出。Computer Use 的状态变更动作会在控制台逐次请求确认。

## 有界自主执行与恢复

```powershell
# task-prompt.txt 为用户的完整任务；任务目录应存在且是新工作区
& '.\run-Qwen3.5-4B.ps1' --workspace 'C:\path\to\new-task' --allow-write --allow-shell --autonomous --prompt-file 'C:\path\to\task-prompt.txt' --require-artifact 'report/main.pdf'

# 取消人工模型轮次上限，持续到 complete_task 验证完成
& '.\run-Qwen3.5-4B.ps1' --workspace 'C:\path\to\new-task' --allow-write --allow-shell --autonomous --max-rounds 0 --prompt-file 'C:\path\to\task-prompt.txt' --require-artifact 'report/main.pdf'

# 同一任务中断后读取项目内检查点；不会盲目重放缺少结果的修改
& '.\run-Qwen3.5-4B.ps1' --workspace 'C:\path\to\new-task' --allow-write --allow-shell --autonomous --resume
```

自主模式使用 `task_checkpoint` 保存阶段和下一项实际行动，只有经过工具验证的非空产物才能提交 `complete_task`。默认单次最多 240 轮（`--max-rounds` 范围 1–500）；`--max-rounds 0` 仅用于自主模式，取消人工模型轮次上限。该模式遇到连续无动作、护栏或工具错误时记录 `loop_recovery`，丢弃近期重复策略，并从原任务、检查点和已保存的来源证据继续；本地模型的暂时连接、超时、429/5xx 和检查点瞬态错误由外层启动器持续恢复同一任务，即使失败当刻只能读到旧的 `running` 检查点也不会另建任务。手动停止、操作系统关机、进程被外部杀死或不可恢复的配置/程序错误仍会留下明确失败证据，不能从软件层面伪称绝对不会中断。自主模式的每次模型请求都发送 `enable_thinking=true`；与原始任务无关的 Computer Use 不会暴露给自主科研任务，交互桌面任务不受影响。`completed_candidate` 仅为产物和执行证据合格，内容与科学正确性仍需独立检查。工作摘要与近期证据用于缩减上下文，原始 JSONL 不删减。任务检查点位于本项目 `.runtime\codex-home\tasks`，运行中不要另开第二个同工作区执行器。

3CA catalog 检索每个会话最多执行八次；同一工作区版本下完全相同的工具调用只执行一次，JSON 参数键顺序不同也视为同一调用。相同调用第二次被护栏拒绝后，只把该工具从下一次模型响应中临时隐藏一轮；catalog/web 预算拒绝和真实工具错误同样冷却对应工具一轮，随后自动恢复，避免永久阻断合法验证。长 catalog 返回保持为可解析的压缩 JSON，包含总条目数、实际返回条目数和收窄过滤提示。达到检索上限后，`search_studies` 不再出现在后续工具列表中，但模型仍可使用 `get_study`、`plan_asset`、`download_asset`、文件和 PowerShell 等工具继续任务。仅包含数据路径的 PowerShell 输入会被明确拒绝；空输出、无工作区变化的 exit 0 不再算作进展或完成验证。

在 until-complete 模式中，即使搜索或 shell 每次都有新输出，连续 12 个工具轮次没有工作区修改仍会触发上下文恢复，不因此退出任务；恢复不能替代科学规划。catalog/web 预算跨 resume 保存，不会因进程恢复重置。启动器只读取当前工作区的检查点，并持有操作系统独占文件锁，进程退出后自动释放，避免并行运行同一任务。上下文证据索引最多 12000 字符，验证证据只保留最近 32 项。识别桌面任务前先剔除本地路径，路径中的 `Desktop` 不会误启用 Computer Use；恢复时依据原始任务判断。

## 会话记录

每次启动都会在本项目自己的运行目录生成一份 JSONL 会话卷宗：

```text
.runtime\codex-home\sessions\YYYY\MM\DD\rollout-*.jsonl
```

记录采用 Codex rollout 的 JSONL 外壳（`session_meta`、`response_item`、`event_msg`），并在 `payload.workflow` 中保留本 workflow 的轮次、原始可见 API 回复、工具参数、完整工具返回值、`/clear`/`/exit` 控制事件和结束原因。官方 Codex 使用 `CODEX_HOME` 作为状态根目录；本 workflow 将其隔离到 `.runtime\codex-home`，会话仍按 `sessions\YYYY\MM\DD\rollout-*.jsonl` 保存。提示中明确写出的外部本地文件会被复制到 `attachments\<UUID>\<filename>`，并同时记录 `source`、项目内 `path`、大小和 `input_file` 引用；给模型的上下文会把外部路径替换成项目相对路径，避免模型访问工作区外。URL 只记录引用，不会擅自下载。Computer Use 返回的截图会记录其项目内捕获文件路径。记录器只保存 API 返回的可见内容和工具数据，不会伪造或泄露模型未返回的隐藏思维链；此前已经结束的会话也无法从本地模型服务倒推恢复。

会话记录严格位于 `workflow_codex\.runtime\codex-home`，不会写入电脑中安装的 Codex 的 `%USERPROFILE%\.codex`。

新的日志保存完整模型 API 返回信封，以及实际返回的 `reasoning_content`、`reasoning`、`reasoning_details`。每个 assistant 轮次分别记录 `reasoning_requested`、`generation.thinking_enabled` 与 `reasoning_present`：前两项表示请求确实开启，最后一项只表示服务实际返回了 reasoning，不能伪造为 `true`。实际本地 reasoning 文本另记为 `response_item` 的 `reasoning_text`，来源明确为 `local-vllm`；不会把它冒充 OpenAI 摘要，也不会补造未返回的思维过程。旧会话未保存的 reasoning 无法倒推补全。恢复会话仍以 `session_meta` 为首条事件。PowerShell 长命令每 30 秒记录进度；超过 6000 字符的工具输出保留首尾并写明截断，提示改用过滤条件或落盘，避免只有尾部使模型丢失结果结构。API 重试、引擎自动续行、上下文压缩、恢复与完成候选均留存事件。

Computer Use 的 Windows helper 还需要一次 `app-server` 策略握手；`codex-local.cmd` 和项目根目录的 `app-server` 是本 workflow 的最小本地实现，确保不会回退查找系统 `codex`。它只返回本地 Qwen3.5-4B/Computer Use 所需的策略，不承载聊天模型请求。

## tool43CA 独立入口

```powershell
# CLI
& '.\tools\tool43CA\run-cli.ps1' --version
& '.\tools\tool43CA\run-cli.ps1' --pretty search lung

# MCP stdio 服务（供独立 MCP 客户端连接）
& '.\tools\tool43CA\run-mcp.ps1'
```

CLI、MCP 和 Skill 的文件分别位于：

```text
tools\tool43CA\CLI
tools\tool43CA\MCP
tools\tool43CA\SKILL\threeca-access
```

## 服务控制

```powershell
& '.\start-Qwen3.5-4B-server.ps1'
& '.\start-Qwen3.5-4B-server.ps1' -Stop
```
