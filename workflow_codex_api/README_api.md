# DeepSeek API 工作流

该目录是 `workflow_codex/` 的独立 API 副本。原本地模型工作流不受影响；API 版使用 DeepSeek OpenAI 兼容接口，并通过 `_api` 后缀入口启动。

## 入口

```text
run-wingpt_api.sh
└── macos-env_api.sh
    └── scripts/macos_runtime_api.py
        └── codex-cli/bin/codex_api.js
            └── codex-cli/bin/wingpt_api.js
```

## 默认配置

- Provider：`deepseek-api`
- Model：`deepseek-v4-pro`
- Base URL：`https://api.deepseek.com`
- Thinking：启用
- Reasoning effort：`max`
- 模型文档上下文：1,000,000 tokens
- 工作流上下文预算：1,000,000 tokens
- 单次最大输出：65,536 tokens
- API 请求超时：900 秒

工作流保留原有严格科研阶段、单响应单工具、核心结果合同、PDF 构建、validator 和 `complete_task` 门禁。启动前真实 canary 会同时验证普通 chat、thinking 工具调用和工具结果后的 `reasoning_content` 连续回放。

## 单次启动

- `report_build`、`bundle_validation` 和 `completion` 由本地阶段机确定性执行，不再额外依赖模型选择正确工具。
- 已识别的双核心报告修复由保存的权威 core JSON 和核验文献确定性重建。
- 报告修复压缩会保留最近 8 条有界消息，避免读取结果在下一轮前丢失。
- API 请求内部重试 3 次；外层 checkpoint 对可恢复中断按同版本最多 3 次、全程最多 5 次自动恢复。
- 每个正式轮次可设置独立 `CODEX_HOME`，将生产 session、checkpoint 和测试探针完全隔离。
- 正式运行开始后，监督者只读取日志、checkpoint 和产物，不停止、恢复或热修进程。

## 凭据

默认从 `.secrets/deepseek_api_key` 读取，也可在启动前设置 `DEEPSEEK_API_KEY`。密钥目录被 `.gitignore` 排除，文件权限应为 `600`。源码、checkpoint、会话和运行清单不得保存密钥正文。

如需轮换密钥：

```bash
umask 077
read -s DEEPSEEK_API_KEY
printf '%s\n' "$DEEPSEEK_API_KEY" > .secrets/deepseek_api_key
chmod 600 .secrets/deepseek_api_key
unset DEEPSEEK_API_KEY
```

## 运行

```bash
source ./macos-env_api.sh
./run-wingpt_api.sh --self-test --allow-write --allow-shell
```

R14 单次启动入口：

```bash
../supervisor/QA_R14/launch-qa-r14_api.sh
```

## 隔离边界

- API checkpoint、会话和附件：`.runtime_api/codex-home/`
- API 健康状态：`.runtime_api/api.json`
- 公共原始缓存：只复用 `../workflow_codex/.threeca/cache/`
- Python、Node、Java、Nextflow：复用 `../workflow_codex/.runtime/macos/`
- 不启动或终止 MLX 服务，不读取本地模型权重。

## 测试

```bash
source ./macos-env_api.sh
env -u PYTHONHOME "$WINGPT_PYTHON" -m unittest scripts/test_macos_runtime_api.py
../workflow_codex/.runtime/macos/tools/bin/node codex-cli/bin/test-wingpt-recovery_api.mjs
./run-wingpt_api.sh --self-test --allow-write --allow-shell
```

API adapter/recovery 测试会强制使用临时 `CODEX_HOME`，不会在正式 `.runtime_api` session 目录产生探针记录。
