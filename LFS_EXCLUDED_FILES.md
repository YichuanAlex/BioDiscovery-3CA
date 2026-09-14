# Files excluded from the GitHub upload because Git LFS is insufficient

Date: 2026-09-14  
Local project root: `C:\Users\User\Desktop\agentic`  
GitHub repository: `YichuanAlex/BioDiscovery-3CA`

The local project contains 34 files larger than GitHub's 100 MiB regular-Git limit. Together they occupy approximately 63.736 GiB. The GitHub Free plan currently provides 10 GiB of included Git LFS storage and limits each LFS file to 2 GB. Twenty-three of these files individually exceed 2 GB. One additional 12.2 MiB file, `model/Qwen3.5-4B/tokenizer.json`, is covered by the model directory's existing Git LFS attributes and is therefore also excluded under the repository owner's instruction not to upload LFS-tracked content when the full LFS set cannot be accommodated.

Following the repository owner's instruction, no large-file content is uploaded when the available Git LFS capacity is insufficient. These files remain unchanged on the local machine. They are not deleted, ignored by `.gitignore`, committed as broken LFS pointers, or included in the GitHub repository.

The `.gitignore` file intentionally contains no ignore patterns. The remaining 36,449 files are included in the Git commit.

Official GitHub limits consulted:

- [About Git Large File Storage](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage)
- [Git Large File Storage billing](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)
- [Repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits)

## Excluded files

| Size (MiB) | Local relative path |
|---:|---|
| 5,082.5 | `model/Qwen3.5-4B/model.safetensors-00001-of-00002.safetensors` |
| 3,805.6 | `model/Qwen3.5-4B/model.safetensors-00002-of-00002.safetensors` |
| 3,183.4 | `workflow_codex/.threeca/cache/downloads/91df9076d4cc/extracted/Data_Bischoff2021_Lung.tar` |
| 3,169.2 | `workflow_codex/.threeca/cache/downloads/91df9076d4cc/extracted/inner/Data_Bischoff2021_Lung/Exp_data_UMIcounts.mtx` |
| 3,169.2 | `3CA/Q1_R11/data/Exp_data_UMIcounts.mtx` |
| 3,169.2 | `workflow_codex/.threeca/cache/downloads/91df9076d4cc/Data_Bischoff2021_Lung.extracted/Data_Bischoff2021_Lung/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/QA_R9/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `workflow_codex/.threeca/cache/downloads/b4d828443422/Data_Choudhury2022_Brain.extracted/Data_Choudhury2022_Brain/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `workflow_codex/.runtime/3ca-staging-smoke/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/QA_R8/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/QA_R6/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/QA_R5/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/QA_R7/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/QA_R3/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/Q1_R12/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/Q1_R13/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/QA_R4/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/Q1_R15/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/Q1_R14/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/QA_R1/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/QA_R10/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `3CA/Q1_R17/inputs/Exp_data_UMIcounts.mtx` |
| 2,287.7 | `workflow_codex/.threeca/cache/downloads/b4d828443422/Data_Choudhury2022_Brain/Exp_data_UMIcounts.mtx` |
| 1,107.7 | `workflow_codex/.threeca/cache/downloads/724c0b240626/Data_Bassez2021_Breast.tar.gz` |
| 726.3 | `workflow_codex/.threeca/cache/downloads/91df9076d4cc/Data_Bischoff2021_Lung.tar.gz` |
| 613.7 | `workflow_codex/.threeca/cache/downloads/cb435bb85809/Data_Tirosh2016_Brain.extracted/Data_Tirosh2016_Brain/Exp_data_TPM.mtx` |
| 562.4 | `3CA/Q1_R1/data/Data_Tirosh2016_Skin/Exp_data_TPM.mtx` |
| 528.8 | `workflow_codex/.threeca/cache/downloads/b4d828443422/Data_Choudhury2022_Brain.tar.gz` |
| 242.5 | `workflow_codex/.threeca/cache/downloads/cb435bb85809/Data_Tirosh2016_Brain.tar.gz` |
| 229.3 | `workflow_codex/.threeca/cache/downloads/8421bc21e274/Data_Azizi2018_Breast.tar.gz` |
| 223.3 | `3CA/Q1_R1/data/Data_Tirosh2016_Skin.tar.gz` |
| 223.3 | `workflow_codex/.runtime/codex-home/attachments/405795c0-dc39-4f66-a1e6-c3bfac06f6c7/Data_Tirosh2016_Skin.tar.gz` |
| 223.3 | `workflow_codex/.threeca/cache/downloads/2cd2280ff535/Data_Tirosh2016_Skin.tar.gz` |
| 114.8 | `workflow_codex/tools/tool43CA/.venv/Lib/site-packages/llvmlite/binding/llvmlite.dll` |
| 12.2 | `model/Qwen3.5-4B/tokenizer.json` (covered by existing Git LFS attributes) |

## Restoration notes

To reconstruct a complete local environment, recover model weights from their licensed upstream model distribution and reacquire 3CA archives from their official study assets. Verify every recovered file against the hashes and provenance already recorded in the corresponding local run manifests before using it for scientific analysis.
