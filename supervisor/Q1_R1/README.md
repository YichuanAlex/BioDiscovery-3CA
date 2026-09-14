# Q1 supervision archive

## Scope and paths

- Local workflow: `C:\Users\User\Desktop\agentic\workflow_codex`
- Research artifacts: `C:\Users\User\Desktop\agentic\3CA\Q1`
- Supervision artifacts: this directory
- The legacy `C:\Users\User\Desktop\agentic\workflow\_codex` does not exist; the run did not create or redirect it.

The user-supplied standard Codex project/rollout is a read-only reference. The global Codex installation, home, CLI, MCP registrations, and skills are not used by the local task runner. Ordinary installed Python and MiKTeX programs are reused without changing their installation.

## Evidence index

| File/directory | Contents |
|---|---|
| `prompt.txt` | User research prompt supplied to the workflow |
| `supervision.md` | Chronological interventions, rejected claims, runtime fixes, and verification scope |
| `reference-baseline.json` | Reference output inventory and numerical acceptance baseline |
| `logs/` | Full copies of every saved Q1 workflow JSONL session |
| `tool-timeline.csv` | Every returned tool call, arguments, timestamps, status, and excerpt |
| `session-audit.json` | Session hashes, event counts, pending-call snapshot, and status counts |
| `sources/` | Source text/structured study responses extracted from actual tool results |
| `analysis-audit.json` | Independently checked sparse inputs, recomputed metrics, table populations, figure hashes |
| `report-audit.json` | Generated only after bibliography, source hashes, compilation/text/value checks pass |
| `figure-qa.md` | Panel-by-panel evidence and visual checks, including units and variability definitions |
| `writing-plan.md` | Report argument, evidence boundaries, and drafting plan |
| `pdf-qa/` | Rendered final-report pages and visual acceptance evidence |
| `final-*-output.txt` | Explicitly captured final verification output |

`verification-transcript.txt` is an earlier PowerShell transcript with incomplete native-output capture. Use the explicit final output files for those checks, not that transcript alone.

## Independent rerunnable checks

```powershell
Set-Location -LiteralPath 'C:\Users\User\Desktop\agentic\supervisor\Q1'
python .\audit_q1.py
python .\test_tar_guard.py
python .\audit_report.py
python .\audit_sessions.py
```

The analysis check uses the installed Python environment recorded in the task's requirements. The report check requires a compiled report and available Poppler. A script PASS does not replace manual inspection of the actual figure/PDF pages. Session auditing snapshots active logs; run it again after the final `/exit`.

## Interpretation and assistance boundaries

- The first independently generated main analysis failed review. With the user's reference authorization, the workflow reused an audited **code baseline only**, adapted its raw-input location, and recomputed the statistics and figures from independently downloaded files. A shared export helper subsequently enforced a 6 pt font floor.
- Reference downloaded files, precomputed result tables, figures, report/PDF, and prose were not copied. Report prose is newly drafted by the local workflow with explicit supervisor corrections.
- Exact agreement with reference metrics is a code-assisted regression reproduction, not independent discovery or proof that the 4B model reasons at Codex level.
- Tool exit 0, saved state, and assistant completion text are not semantic acceptance. Scientific claims, counts, references, and rendered pages are checked separately.
- Raw logs preserve observable model API responses and tool events. Private, unavailable internal reasoning from the standard Codex run is not inferred or reconstructed.
- Bounded API/loop recovery and saved state reduce interruption risk; they do not guarantee every future model response or arbitrary task is correct.
