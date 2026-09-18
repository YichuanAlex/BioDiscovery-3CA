# 本地 WiNGPT Workflow

本项目支持 Windows/vLLM 与 Apple Silicon macOS/MLX 两条本地运行路径。模型、工具和会话状态均保存在项目目录内，不调用全局 Codex/agent。

## macOS / MLX

当前 Mac 入口使用项目同级的 `model/Qwen3.5-4B-MLX-4bit`，复用 Conda `py312` 中的 MLX，并把科研 Python、Node、Tectonic 和 Poppler 固定在 `.runtime/macos`。`macos-env.sh` 会清除宿主 `PYTHONHOME`/`PYTHONPATH`，避免其他应用内置 Python 污染项目解释器。

```bash
cd '/Users/bytedance/Downloads/BioDiscovery-3CA/workflow_codex'

# 首次安装或重建项目运行时
./setup-macos.sh

# 启动、检查和停止本地 MLX 服务
./start-wingpt-server.sh start
./start-wingpt-server.sh status
./start-wingpt-server.sh stop

# 交互模式
./run-wingpt.sh
./run-wingpt.sh --allow-write --allow-shell

# 本地模型、文件、工具协议、联网与 shell 冒烟测试
./run-wingpt.sh --self-test --allow-shell
```

Mac 自主任务示例：

```bash
./run-wingpt.sh \
  --workspace '/absolute/path/to/new-task' \
  --allow-write \
  --allow-shell \
  --autonomous \
  --max-rounds 0 \
  --prompt-file '/absolute/path/to/prompt.txt' \
  --require-artifact 'results/core_analysis/core_result.json' \
  --require-artifact 'report/main.tex' \
  --require-artifact 'report/main.pdf' \
  --require-artifact 'results/summary.json' \
  --require-artifact 'results/analysis_manifest.json' \
  --require-artifact 'README.md'
```

Mac 默认上下文为 32,768 tokens、单次输出上限为 4,096 tokens，可通过 `WINGPT_CONTEXT_TOKENS` 与 `WINGPT_MAX_TOKENS` 调整；不要直接套用 Windows 16 GB GPU 上验证过的 262,144 配置。在线来源请求默认使用 120 秒 socket 超时，可用 `WINGPT_NETWORK_TIMEOUT` 调整；TLS 校验、来源白名单和 SHA-256 核验不会关闭。

## Windows / vLLM

Windows 项目的历史目录是：

```text
C:\Users\User\Desktop\agentic\workflow_codex
```

它通过本地 vLLM 使用 `C:\Users\User\Desktop\agentic\model\Qwen3.5-4B` 中的 `Qwen3.5-4B`（历史 WiNGPT 入口文件名保留兼容），不调用电脑中安装的 `codex` 命令，也不会自动扫描或写回 `C:\Users\User\.codex`、`C:\Users\User\.agents` 或 `%LOCALAPPDATA%\OpenAI\Codex`。只有当用户在提示中明确给出外部附件路径时，程序才会读取该源文件并复制一份到本项目；运行时状态、3CA 缓存和研究来源缓存均保存在本项目内。

## 安装和测试

```powershell
Set-Location 'C:\Users\User\Desktop\agentic\workflow_codex'
& '.\tools\tool43CA\install.ps1'
& '.\test-WiNGPT.ps1'
```

完整测试包含：路径隔离、当前 Qwen 模型、文件工具、联网工具、3CA CLI/MCP、research-quality CLI/MCP、Ruff、Reactome 基因集、PubMed/Crossref 元数据、合成单细胞代谢聚类回归和科研产物闸门。联网冒烟最多六轮，要求一次实际检索及带来源的可见答复，超限/停滞不算通过。测试脚本使用 UTF-8 BOM 兼容 Windows PowerShell 5 的中文文本；长任务提示通过 `--prompt-file` 显式 UTF-8 读取，不依赖 shell 的中文字面量编码。

## 交互使用

```powershell
# 普通交互；已包含文件读取、联网、3CA 和 research-quality 工具
& '.\run-WiNGPT.ps1'

# 额外允许写文件和执行 PowerShell
& '.\run-WiNGPT.ps1' --allow-write --allow-shell

# 在另一个明确目录完成任务；模型、工具和会话状态仍来自 workflow_codex
& '.\run-WiNGPT.ps1' --workspace 'C:\Users\User\Desktop\agentic\3CA\Q1' --allow-write --allow-shell
```

输入 `/clear` 清空对话，输入 `/exit` 退出。

## 有界自主执行与恢复

```powershell
# task-prompt.txt 为用户的完整任务；任务目录应存在且是新工作区
& '.\run-WiNGPT.ps1' --workspace 'C:\path\to\new-task' --allow-write --allow-shell --autonomous --prompt-file 'C:\path\to\task-prompt.txt' --require-artifact 'report/main.pdf'

# 取消人工模型轮次上限，持续到 complete_task 验证完成
& '.\run-WiNGPT.ps1' --workspace 'C:\path\to\new-task' --allow-write --allow-shell --autonomous --max-rounds 0 --prompt-file 'C:\path\to\task-prompt.txt' --require-artifact 'report/main.pdf'

# 同一任务中断后读取项目内检查点；不会盲目重放缺少结果的修改
& '.\run-WiNGPT.ps1' --workspace 'C:\path\to\new-task' --allow-write --allow-shell --autonomous --resume
```

自主模式使用 `task_checkpoint` 保存阶段和下一项实际行动，只有经过工具验证的非空产物才能提交 `complete_task`。自主模式默认 `--max-rounds 0`，持续到完成验收；仍可显式传入任意正整数，仅用于人为要求的有界测试，不再设 500 轮上限。该模式遇到连续无动作、护栏或工具错误时记录 `loop_recovery`，丢弃近期重复策略，并从原任务、检查点和已保存的来源证据继续；这些恢复阈值不会终止 until-complete 任务。本地模型的暂时连接、超时、429/5xx 和检查点瞬态错误由外层启动器持续恢复同一任务。手动停止、操作系统关机、进程被外部杀死或不可恢复的配置/程序错误仍会留下明确失败证据，不能从软件层面伪称绝对不会中断。自主模式的每次模型请求都发送 `enable_thinking=true`。研究任务若要求 `analysis_manifest.json`，`complete_task` 会核对实体粒度、真实聚类标签、基线与随机种子、来源哈希、文献元数据、图件及 PDF/TeX 新旧关系；通过仍不等于生物学结论已经由独立复核接受。工作摘要与近期证据用于适配模型物理上下文，完整来源引用、验证证据、实际工具结果和原始 JSONL 持久保存。任务检查点位于本项目 `.runtime\codex-home\tasks`，运行中不要另开第二个同工作区执行器。

Windows 11 Insider build 26200 上，正式启动器固定使用项目内的 Node 24.21.0（libuv 1.52.1），避开 Node 24.15.0 的 Windows TCP-connect `0xC0000409` 原生崩溃；同时保留 `--no-maglev`，规避此前实际观察到的独立 V8 Maglev FailFast。若以后更换到已验证不受影响的 Node/Windows 组合，再以长程回归证据移除此兼容参数。

自主模式使用本地 vLLM/Qwen 的原生 function-call 协议，并以 `tool_choice=required` 要求每次只完成一个实际工具行动；这条路径已用真实服务验证。取消整段 `structured_outputs.json` 动作生成，避免长 PowerShell JSON 在输出上限处截断并反复污染上下文；兼容路径若仍收到截断的旧式 JSON，会立即丢弃残片并要求用一个简短原生调用重试。执行入口继续检查必填参数、类型和当前可用工具，缺少文件内容时不会先创建目录。日志保存服务原始响应和真实 reasoning。

3CA catalog 与公开网页检索不再有每任务请求次数上限，计数仅作为审计指标，工具不会因达到旧的 8/3 次阈值而消失。完全相同的发现类请求允许在新证据或精炼策略需要时重试；相同的写入、Shell、下载与验收调用仍防止盲目重放，失败工具只临时隐藏一个响应。3CA `download_asset` 的模型接口不再暴露猜测式大小参数，CLI/MCP 默认下载与安全解压上限均为 0（无限制）；`crawl_site` 默认遍历全部可发现页面。长 catalog 返回保持为可解析的压缩 JSON，完整公开缓存与 manifest 保留在磁盘。仅包含数据路径的 PowerShell 输入会被明确拒绝；空输出、无工作区变化的 exit 0 不再算作进展或完成验证。

在 until-complete 模式中，即使搜索或 shell 每次都有新输出，连续 12 个工具轮次没有工作区修改仍会触发上下文恢复，但不会退出任务或禁止发现工具；恢复不能替代科学规划。实际工具返回中的研究 ID、完整标题、资产来源/哈希、观察和验证证据不再按固定条目数从检查点删除；每次模型请求只投影最近的必要索引，以适配 65,536-token 的物理上下文，完整记录仍可从检查点、manifest、工作区和 JSONL 读取。PowerShell、模型 API、3CA 与 research-quality 桥不设人工执行总时限，来源请求不设本工作流固定 socket 超时；实际网络/远端服务和操作系统仍可能返回错误，错误重试与检查点恢复保留。公网文本读取仍保留私网/localhost 阻断和有限内存保护，避免 SSRF 或单页响应耗尽进程。启动器只读取当前工作区的检查点，并持有操作系统独占文件锁，进程退出后自动释放，避免并行运行同一任务。

## 会话记录

每次启动都会在本项目自己的运行目录生成一份 JSONL 会话卷宗：

```text
.runtime\codex-home\sessions\YYYY\MM\DD\rollout-*.jsonl
```

记录采用 Codex rollout 的 JSONL 外壳（`session_meta`、`response_item`、`event_msg`），并在 `payload.workflow` 中保留本 workflow 的轮次、原始可见 API 回复、工具参数、完整工具返回值、`/clear`/`/exit` 控制事件和结束原因。官方 Codex 使用 `CODEX_HOME` 作为状态根目录；本 workflow 将其隔离到 `.runtime\codex-home`，会话仍按 `sessions\YYYY\MM\DD\rollout-*.jsonl` 保存。提示中明确写出的外部本地文件会被复制到 `attachments\<UUID>\<filename>`，并同时记录 `source`、项目内 `path`、大小和 `input_file` 引用；给模型的上下文会把外部路径替换成项目相对路径，避免模型访问工作区外。URL 只记录引用，不会擅自下载。记录器只保存 API 返回的可见内容和工具数据，不会伪造或泄露模型未返回的隐藏思维链；此前已经结束的会话也无法从本地模型服务倒推恢复。

会话记录严格位于 `workflow_codex\.runtime\codex-home`，不会写入电脑中安装的 Codex 的 `%USERPROFILE%\.codex`。

新的日志保存完整模型 API 返回信封，以及实际返回的 `reasoning_content`、`reasoning`、`reasoning_details`。每个 assistant 轮次分别记录 `reasoning_requested`、`generation.thinking_enabled` 与 `reasoning_present`：前两项表示请求确实开启，最后一项只表示服务实际返回了 reasoning，不能伪造为 `true`。实际本地 reasoning 文本另记为 `response_item` 的 `reasoning_text`，来源明确为 `local-vllm`；不会把它冒充 OpenAI 摘要，也不会补造未返回的思维过程。旧会话未保存的 reasoning 无法倒推补全。恢复会话仍以 `session_meta` 为首条事件。PowerShell 长命令每 30 秒记录进度；超过 6000 字符的工具输出保留首尾并写明截断，提示改用过滤条件或落盘，避免只有尾部使模型丢失结果结构。API 重试、引擎自动续行、上下文压缩、恢复与完成候选均留存事件。

## tool43CA 独立入口

```powershell
# CLI
& '.\tools\tool43CA\run-cli.ps1' --version
& '.\tools\tool43CA\run-cli.ps1' --pretty search lung

# MCP stdio 服务（供独立 MCP 客户端连接）
& '.\tools\tool43CA\run-mcp.ps1'
```

## research-quality 独立入口

八个函数工具与 CLI/MCP 共用实现。数据准备必须使用实际缓存 extracted_path；TPM 不冒称 counts。原始重复基因符号在核心中按计数求和、保存源行映射；原始特征行数与汇总符号数分开报告。代码审计、真实多种子标签/对照/混杂结果、来源与引用核验、TeX/PDF 同步检查覆盖科学验收，不能把工具通过等同于离散生物学状态已成立。

```powershell
& '.\tools\research-quality\run-cli.ps1' --workspace 'C:\path\to\task' --pretty reactome-metabolic-genes
& '.\tools\research-quality\run-cli.ps1' --workspace 'C:\path\to\task' --pretty pubmed-search 'single-cell metabolism'
& '.\tools\research-quality\run-cli.ps1' --workspace 'C:\path\to\task' --pretty verify-doi '10.x/...'
& '.\tools\research-quality\run-cli.ps1' --workspace 'C:\path\to\task' --pretty audit-analysis-code 'analysis.py'
& '.\tools\research-quality\run-cli.ps1' --workspace 'C:\path\to\task' --pretty prepare-3ca-dataset 'actual 3CA cached extracted_path'
& '.\tools\research-quality\run-cli.ps1' --workspace 'C:\path\to\task' --pretty analyze-metabolic-states --expression-path 'data/counts.mtx' --cells-path 'data/cells.csv' --genes-path 'data/genes.txt' --metabolic-genes-path 'sources/reactome/metabolism.txt'
& '.\tools\research-quality\run-cli.ps1' --workspace 'C:\path\to\task' --pretty validate
& '.\tools\research-quality\run-mcp.ps1' -Workspace 'C:\path\to\task'
```

CLI、MCP 和 Skill 的文件分别位于：

```text
tools\tool43CA\CLI
tools\tool43CA\MCP
tools\tool43CA\SKILL\threeca-access
```

## 服务控制

```powershell
& '.\start-WiNGPT-server.ps1'
& '.\start-WiNGPT-server.ps1' -Stop
```

重复调用回用原实际结果，给模型的单项展示有长度边界，并明确标注原会话、原调用 ID、时间及未重新执行；不把回用当成新验证或新进展。恢复及 resume 保留记录，缺少结果的历史调用仍不盲目重放副作用。资产来源完整保存在检查点和会话，模型请求只展示近期有限索引，不按展示窗口删除历史资产；这只是机械记忆，不代选数据集，也不校验生物学结论。

`inspect_dataset` 的共享 CLI 实现区分文件、目录及不存在路径；目录仅返回最多 100 个浅层实际名称、不跟随符号链接，长清单仍以有截断标记的可解析 JSON 返回。目录存在不是矩阵内容验证，必须检查实际返回的文件名。CLI、MCP、函数工具共用此实现。

Qwen 服务直接加载指定本地目录，文本任务使用 language-model-only，原生工具解析器 qwen3_coder、reasoning 解析器 qwen3；自主任务使用原生函数调用并保留真实 reasoning。当前硬件下上下文长度为 262144，未启用视觉模块，也未修改权重或全局已安装的 agent。
