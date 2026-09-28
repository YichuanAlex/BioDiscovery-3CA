# 外部组件管理

本文档记录当前项目工作流已安装、已启用和明确排除的 Skill、MCP、Hook、CLI 与隔离运行时。所有路径均相对于项目根目录 `BioDiscovery-3CA/`。

## 管理原则

- 本地科研组件只启用无需账号、OAuth、Token 或付费订阅的组件；`workflow_codex_api/` 是用户明确授权的独立 DeepSeek API 执行后端，不改变本地组件边界。
- Anthropic 源目录作为安装来源保留，运行时不直接读取源目录。
- Skill 安装后按清单和 SHA-256 校验，正文按需加载，不全部注入模型上下文。
- 匿名 MCP 在安装时执行 `initialize` 和 `tools/list`，缓存工具 schema；运行时再次校验固定端点与清单哈希。
- Python/Nextflow 依赖安装在项目隔离目录，不修改系统 Python 或主科研 Python。
- 当前自定义 JS 工作流没有安装任何执行 Hook。
- 当前 16GB Mac 的生产上下文为 49,152 tokens，其中 4,096 tokens 保留给输出；约 59K-token 的真实请求曾触发 Metal OOM。

## 快速命令

在项目根目录执行：

```bash
# 安装/校准全部本地生命科学 Skill 和隔离依赖
./workflow_codex/setup-life-sciences-macos.sh

# 只重新安装 Skill 文件与哈希清单
./workflow_codex/.runtime/macos/tools/bin/node \
  ./workflow_codex/scripts/install-anthropic-life-sciences.mjs

# 验证 Skill 依赖、CLI 和本地 Nextflow
./workflow_codex/test-life-sciences-macos.sh

# 仅卸载已安装 Skill
./workflow_codex/uninstall-life-sciences-macos.sh --skills

# 仅卸载生命科学隔离运行时
./workflow_codex/uninstall-life-sciences-macos.sh --runtimes

# 同时卸载 Skill 与隔离运行时
./workflow_codex/uninstall-life-sciences-macos.sh --all

# 安装/刷新匿名公共 MCP 工具清单
./workflow_codex/install-anonymous-http-mcp.sh

# 匿名公共 MCP
./workflow_codex/uninstall-anonymous-http-mcp.sh

# 安装/验证 ToolUniverse 本地 compact MCP
./workflow_codex/install-tooluniverse-macos.sh
./workflow_codex/test-tooluniverse-macos.sh

# 卸载 ToolUniverse 本地 MCP 及隔离环境
./workflow_codex/uninstall-tooluniverse-macos.sh

# MCP Mock 回归
source ./workflow_codex/macos-env.sh
node ./workflow_codex/codex-cli/bin/test-wingpt-http-mcp.mjs

# 工作流总回归
source ./workflow_codex/macos-env.sh
node ./workflow_codex/codex-cli/bin/test-wingpt-recovery.mjs
./workflow_codex/run-wingpt.sh --self-test --allow-shell

# DeepSeek API 副本：状态、自测和 R13
source ./workflow_codex_api/macos-env_api.sh
"$WINGPT_PYTHON" ./workflow_codex_api/scripts/macos_runtime_api.py status
./workflow_codex_api/run-wingpt_api.sh --self-test --allow-write --allow-shell
./supervisor/QA_R13/launch-qa-r13_api.sh
```

## 文件树

```text
BioDiscovery-3CA/
├── EXTERNAL_COMPONENTS.md                         # 本文档
├── anthropics-knowledge-work-plugins/
│   └── bio-research/                              # 上游源目录，不由运行时直接加载
│       ├── .claude-plugin/plugin.json
│       ├── .mcp.json
│       └── skills/
│           ├── start/
│           ├── single-cell-rna-qc/
│           ├── scvi-tools/
│           ├── nextflow-development/
│           ├── instrument-data-to-allotrope/
│           └── scientific-problem-selection/
├── anthropics-life-sciences/                      # 上游源目录，不由运行时直接加载
│   ├── .claude-plugin/marketplace.json
│   ├── clinical-trial-protocol-skill/
│   ├── single-cell-rna-qc/
│   ├── scvi-tools/
│   ├── nextflow-development/
│   ├── instrument-data-to-allotrope/
│   ├── scientific-problem-selection/
│   └── */.claude-plugin/plugin.json               # MCP 定义来源；认证型未安装
├── workflow_codex_api/                            # DeepSeek API 独立源码副本
│   ├── README_api.md                              # API 配置、隔离边界与测试
│   ├── macos-env_api.sh                           # 凭据加载及 API 参数
│   ├── run-wingpt_api.sh                          # API 总入口
│   ├── .secrets/deepseek_api_key                  # 600 权限；Git 忽略；不进入清单
│   ├── .runtime_api/                              # 独立 checkpoint、会话和状态
│   ├── codex-cli/bin/
│   │   ├── codex_api.js                           # API CLI 入口
│   │   ├── wingpt_api.js                          # DeepSeek thinking/tool 编排
│   │   ├── test-deepseek-api-adapter_api.mjs      # 鉴权与 reasoning 连续性
│   │   └── test-wingpt-recovery_api.mjs            # API 恢复入口
│   └── scripts/
│       ├── macos_runtime_api.py                   # API canary 与有界恢复
│       └── test_macos_runtime_api.py              # API runtime 单测
└── workflow_codex/
    ├── macos-context-profile.json                 # 16GB Mac 上下文实测配置
    ├── setup-macos.sh                             # 工作流总安装入口
    ├── setup-life-sciences-macos.sh               # Skill 依赖安装入口
    ├── test-life-sciences-macos.sh                # Skill/CLI 冒烟测试
    ├── uninstall-life-sciences-macos.sh           # Skill/运行时卸载入口
    ├── install-anonymous-http-mcp.sh               # 匿名 MCP 安装入口
    ├── uninstall-anonymous-http-mcp.sh             # 匿名 MCP 卸载入口
    ├── install-tooluniverse-macos.sh               # ToolUniverse 本地安装入口
    ├── test-tooluniverse-macos.sh                  # ToolUniverse 真实冒烟
    ├── uninstall-tooluniverse-macos.sh             # ToolUniverse 卸载入口
    ├── components/
    │   └── tooluniverse/
    │       ├── workflow-install.json               # MCPB 来源、哈希与运行配置
    │       ├── workflow-tool-schema.json           # compact 5 工具 schema 与哈希
    │       ├── manifest.json
    │       ├── pyproject.toml
    │       └── src/                                # MCPB 安全解包源码
    ├── scripts/
    │   ├── install-anthropic-life-sciences.mjs    # Skill 复制、去重、哈希
    │   ├── install-anonymous-http-mcp.mjs          # MCP 探测与 schema 缓存
    │   ├── uninstall-anonymous-http-mcp.mjs
    │   ├── life-sciences-scverse-requirements.txt
    │   ├── life-sciences-allotrope-requirements.txt
    │   └── nextflow-smoke.nf
    ├── skills/
    │   └── anthropic-life-sciences/
    │       ├── manifest.json                       # Skill 来源、哈希、运行时
    │       ├── README.md
    │       ├── start/
    │       ├── single-cell-rna-qc/
    │       ├── scvi-tools/
    │       ├── nextflow-development/
    │       ├── instrument-data-to-allotrope/
    │       ├── scientific-problem-selection/
    │       └── clinical-trial-protocol-skill/
    ├── codex-cli/bin/
    │   ├── wingpt.js                              # Skill/MCP 注册与阶段路由
    │   ├── wingpt-http-mcp.js                     # HTTP MCP JSON/SSE 客户端
    │   ├── wingpt-tooluniverse-mcp.js             # ToolUniverse stdio 客户端
    │   ├── test-wingpt-http-mcp.mjs
    │   ├── test-tooluniverse-mcp.mjs
    │   └── test-wingpt-recovery.mjs
    ├── tools/
    │   ├── tool43CA/                              # 既有 3CA CLI/MCP/Skill
    │   └── research-quality/                      # 既有科研分析/验证工具
    └── .runtime/
        ├── anonymous-http-mcp/
        │   └── manifest.json                      # 5 个端点、31 个工具的缓存清单
        └── macos/
            ├── python/                            # 主科研 Python/MLX 环境
            ├── tools/                             # Node、Tectonic、Poppler
            └── life-sciences/
                ├── scverse/                       # scVI/scRNA Python 3.12
                ├── allotrope/                     # Allotrope Python 3.11
                ├── nextflow/                      # OpenJDK 17 + Nextflow
                ├── locks/                         # pip freeze/Conda explicit
                └── smoke/                         # 本地冒烟测试输出
            ├── tooluniverse/                      # ToolUniverse Python 3.12
            └── tooluniverse-home/                 # 隔离 HOME/XDG
```

## 已安装 Skill

| Skill | 功能 | 安装相对路径 | 规范来源 |
| --- | --- | --- | --- |
| `start` | 生物研究组件导航 | `workflow_codex/skills/anthropic-life-sciences/start/` | `anthropics-knowledge-work-plugins/bio-research/skills/start/` |
| `single-cell-rna-qc` | scRNA-seq QC、MAD 过滤与图表 | `workflow_codex/skills/anthropic-life-sciences/single-cell-rna-qc/` | `anthropics-knowledge-work-plugins/bio-research/skills/single-cell-rna-qc/` |
| `scvi-tools` | scVI/scANVI/totalVI/PeakVI/MultiVI 等 | `workflow_codex/skills/anthropic-life-sciences/scvi-tools/` | `anthropics-knowledge-work-plugins/bio-research/skills/scvi-tools/` |
| `nextflow-development` | nf-core/Nextflow 流程与样本表 | `workflow_codex/skills/anthropic-life-sciences/nextflow-development/` | `anthropics-knowledge-work-plugins/bio-research/skills/nextflow-development/` |
| `instrument-data-to-allotrope` | 仪器文件转 ASM JSON/CSV | `workflow_codex/skills/anthropic-life-sciences/instrument-data-to-allotrope/` | `anthropics-knowledge-work-plugins/bio-research/skills/instrument-data-to-allotrope/` |
| `scientific-problem-selection` | 科研选题与风险决策框架 | `workflow_codex/skills/anthropic-life-sciences/scientific-problem-selection/` | `anthropics-knowledge-work-plugins/bio-research/skills/scientific-problem-selection/` |
| `clinical-trial-protocol-skill` | 临床试验方案与样本量辅助 | `workflow_codex/skills/anthropic-life-sciences/clinical-trial-protocol-skill/` | `anthropics-life-sciences/clinical-trial-protocol-skill/` |

重复项处理：两个上游目录中重名的 5 个 Skill 只安装一份，优先采用 `bio-research` 版本；所有来源、文件字节数和 SHA-256 记录在 `workflow_codex/skills/anthropic-life-sciences/manifest.json`。

运行时只把有界索引放入系统提示。模型通过以下内建工具按需读取：

- `load_skill`
- `read_skill_resource`

## 已启用匿名 MCP

这些 MCP 均通过匿名 `initialize` 与 `tools/list` 实测，不需要账号、订阅或 Token。模型工具名使用 `<prefix>__<tool>`，避免跨服务器重名。

### PubMed

- 端点：`https://pubmed.mcp.claude.com/mcp`
- 前缀：`pubmed__`
- 工具：`search_articles`、`get_article_metadata`、`find_related_articles`、`lookup_article_by_citation`、`convert_article_ids`、`get_full_text_article`、`get_copyright_status`

### bioRxiv/medRxiv

- 端点：`https://hcls.mcp.claude.com/biorxiv/mcp`
- 前缀：`biorxiv__`
- 工具：`search_preprints`、`get_preprint`、`get_categories`、`search_published_preprints`、`search_by_funder`、`get_content_statistics`、`get_usage_statistics`

### ClinicalTrials.gov

- 端点：`https://hcls.mcp.claude.com/clinical_trials/mcp`
- 前缀：`clinicaltrials__`
- 工具：`search_trials`、`get_trial_details`、`search_by_sponsor`、`search_investigators`、`analyze_endpoints`、`search_by_eligibility`

### ChEMBL

- 端点：`https://hcls.mcp.claude.com/chembl/mcp`
- 前缀：`chembl__`
- 工具：`compound_search`、`get_bioactivity`、`target_search`、`get_mechanism`、`drug_search`、`get_admet`

### Open Targets

- 端点：`https://mcp.platform.opentargets.org/mcp`
- 前缀：`opentargets__`
- 工具：`get_open_targets_graphql_schema`、`get_type_dependencies`、`search_entities`、`query_open_targets_graphql`、`batch_query_open_targets_graphql`

MCP 安装相对路径：

- 客户端：`workflow_codex/codex-cli/bin/wingpt-http-mcp.js`
- 安装器：`workflow_codex/scripts/install-anonymous-http-mcp.mjs`
- 缓存清单：`workflow_codex/.runtime/anonymous-http-mcp/manifest.json`
- 回归测试：`workflow_codex/codex-cli/bin/test-wingpt-http-mcp.mjs`

## 已安装 CLI 与运行时

| 组件 | 用途 | 相对路径 |
| --- | --- | --- |
| 项目 Node.js | WiNGPT 与安装脚本 | `workflow_codex/.runtime/macos/tools/bin/node` |
| Tectonic | LaTeX/PDF 构建 | `workflow_codex/.runtime/macos/tools/bin/tectonic` |
| Poppler | PDF 渲染与检查 | `workflow_codex/.runtime/macos/tools/bin/pdftoppm` 等 |
| 3CA CLI | 3CA 数据搜索、下载与核验 | `workflow_codex/tools/tool43CA/CLI/` |
| Research Quality CLI | Reactome、单细胞核心、报告与验证 | `workflow_codex/tools/research-quality/` |
| scverse Python 3.12 | Scanpy、scvi-tools、Torch、MuData、scVelo | `workflow_codex/.runtime/macos/life-sciences/scverse/bin/python` |
| Allotrope Python 3.11 | allotropy、pandas、openpyxl、pdfplumber | `workflow_codex/.runtime/macos/life-sciences/allotrope/bin/python` |
| OpenJDK 17 | Nextflow JVM | `workflow_codex/.runtime/macos/life-sciences/nextflow/lib/jvm/` |
| Nextflow 25.04.8 | 本地 DSL2/nf-core 流程 | `workflow_codex/.runtime/macos/life-sciences/nextflow/bin/nextflow` |
| ToolUniverse Python 3.12 | 本地 compact stdio MCP，后台加载科学工具目录 | `workflow_codex/.runtime/macos/tooluniverse/bin/python` |

## ToolUniverse 本地 MCP

ToolUniverse MCPB 版本 1.0.15 已从项目自带文件安全解包并安装，不需要账号或订阅。为控制上下文，只注册 compact 模式的 5 个入口：

- `tooluniverse__list_tools`
- `tooluniverse__grep_tools`
- `tooluniverse__get_tool_info`
- `tooluniverse__execute_tool`
- `tooluniverse__find_tools`

安装相对路径：

- 原始 MCPB：`anthropics-life-sciences/tooluniverse/tooluniverse.mcpb`
- 安装源码：`workflow_codex/components/tooluniverse/`
- 安装记录：`workflow_codex/components/tooluniverse/workflow-install.json`
- 工具 schema 缓存：`workflow_codex/components/tooluniverse/workflow-tool-schema.json`
- 隔离环境：`workflow_codex/.runtime/macos/tooluniverse/`
- stdio 适配器：`workflow_codex/codex-cli/bin/wingpt-tooluniverse-mcp.js`
- Mock/真实测试：`workflow_codex/codex-cli/bin/test-tooluniverse-mcp.mjs`

运行边界：

- 不配置或转发任何 API key、Token、账号环境变量。
- 单次请求和结果均有 16 KiB 边界。
- 默认调用超时 45 秒，超时和主进程退出时清理子进程。
- ToolUniverse 目录中存在名为 `extended_hooks.py` 的库代码，但当前工作流没有把它注册为执行 Hook。

锁定和复现信息位于：

```text
workflow_codex/.runtime/macos/life-sciences/locks/
├── scverse-pip-freeze.txt
├── scverse-conda-explicit.txt
├── allotrope-pip-freeze.txt
├── allotrope-conda-explicit.txt
└── nextflow-conda-explicit.txt
```

## Hook 状态

当前自定义 JS 工作流没有安装或启用任何外部 Hook。仓库源码和第三方 Python 包中名称包含 `hook` 的文件不代表运行时 Hook 已注册。

| 类型 | 状态 | 配置路径 |
| --- | --- | --- |
| 启动 Hook | 未安装 | 无 |
| 工具前置/后置 Hook | 未安装 | 无 |
| 会话结束 Hook | 未安装 | 无 |
| 外部 MCP Hook | 未安装 | 无 |

## 运行恢复边界

- 配置证据：`workflow_codex/macos-context-profile.json`
- 运行管理器：`workflow_codex/scripts/macos_runtime.py`
- 回归测试：`workflow_codex/scripts/test_macos_runtime.py`
- 健康检查同时验证 `/v1/models` 和最小 `/v1/chat/completions` canary。
- 检测受管 MLX 日志中的 Metal OOM，或受管服务 canary 失败时，只重启 `server.json` 中经过命令行身份核验的 PID。
- 同一 checkpoint/version 最多恢复 3 次，单次 runner 总计最多恢复 5 次；超过限制写入 `needs_attention`，不再无限重启。
- 严格科研阶段只广告阶段明确列出的工具。31 个匿名 HTTP MCP 和 ToolUniverse 不会旁路进入核心、报告、构建、验证或完成阶段。

## 明确未安装

以下组件需要账号、OAuth、Token、机构权限或付费订阅，因此仅保留在上游源目录，没有注册到当前工作流：

- BioRender
- Synapse
- Wiley Scholar Gateway
- Consensus
- Cortellis
- AdisInsight
- 10x Genomics Cloud
- Owkin
- Medidata
- Benchling

旧的 `mcp.deepsense.ai` bioRxiv、ClinicalTrials 和 ChEMBL 地址在本机 POST 探测中返回 403；当前使用的是通过匿名实测的 `hcls.mcp.claude.com` 地址。

## 完整卸载说明

1. 先停止正在运行的 QA/研究任务，避免任务仍引用组件。
2. 执行：

```bash
./workflow_codex/uninstall-anonymous-http-mcp.sh
./workflow_codex/uninstall-tooluniverse-macos.sh
./workflow_codex/uninstall-life-sciences-macos.sh --all
```

3. 源目录默认保留，便于重新安装：

```text
anthropics-knowledge-work-plugins/bio-research/
anthropics-life-sciences/
```

4. 如需重新安装：

```bash
./workflow_codex/setup-life-sciences-macos.sh
./workflow_codex/install-anonymous-http-mcp.sh
./workflow_codex/install-tooluniverse-macos.sh
```

5. 重装后执行全部验证命令，确认 Skill 清单、匿名 MCP 清单、CLI 和主工作流均通过。
