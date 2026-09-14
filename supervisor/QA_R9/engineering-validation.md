# QA_R9 engineering validation

- Local model: `Qwen3.5-4B`, model root `/mnt/c/Users/User/Desktop/agentic/model/Qwen3.5-4B`.
- Model-native context: `text_config.max_position_embeddings=262144`.
- vLLM service: `/v1/models` reports `max_model_len=262144`; startup log reports GPU KV capacity 411,206 tokens.
- Real long-context inference: 70,025 prompt tokens plus 2 completion tokens succeeded, exceeding the former 65,536 limit.
- Workflow context budget: 262,144; generation budget: 8,192; compaction trigger: 245,760; retained target: 229,376.
- Workspace read/write/shell/checkpoint tools remain available at every research stage; write-path guards remain active.
- Same phase/workspace recovery ceiling: 12; build and validator failure ceilings: 12.
- Project-local Node: 24.21.0 / libuv 1.52.1.
- Full `test-wingpt.ps1`: passed after restoring all active workflow filenames.
- `test-wingpt-recovery.mjs`: passed after the final manifest fact-injection change; all recovery and bounded-context checks passed in 143 seconds.

`FULL_TEST_EXIT_CODE=0`
`RECOVERY_TEST_EXIT_CODE=0`

