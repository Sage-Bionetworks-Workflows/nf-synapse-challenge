<!-- Last reviewed: 2026-03 -->

## Project

Nextflow DSL2 workflow for evaluating scientific challenge submissions hosted on Synapse. Supports two pipeline types: data-to-model (participants submit prediction files) and model-to-data (participants submit Docker containers). Owned by the DPE team (@Sage-Bionetworks-Workflows/dpe), scheduled via [orca-recipes](https://github.com/Sage-Bionetworks-Workflows/orca-recipes), and executed on Seqera Platform (Tower) or locally.

## Stack

- Nextflow >=19.04.0 (DSL2 enabled)
- Python 3 (scripts in `bin/`)
- Docker (container execution + Docker-in-Docker for M2D)
- `synapseclient` — Synapse Python client for file/submission operations
- `challengeutils` v4.2.0 — CLI for submission status and annotation management
- Ubuntu 22.04 base image (see `Dockerfile`)
- No linters, formatters, or type checkers configured

## Commands

```bash
# Data-to-model with comma-separated submission IDs
nextflow run main.nf --entry data_to_model -profile local --submissions 9741046,9741047

# Data-to-model with manifest CSV
nextflow run main.nf --entry data_to_model -profile local --manifest assets/data_to_model_manifest.csv

# Model-to-data with submissions
nextflow run main.nf --entry model_to_data -profile local --submissions 9741046,9741047

# Run with a pre-configured challenge profile
nextflow run main.nf -profile olfactory25_challenge_task1
```

See README.md for full setup and Seqera Platform instructions.

## Data Models

**Submission channel tuple** — the core data structure flowing between processes:
```
tuple val(submission_id), path(predictions), env(status), path("results.json")
```
All process outputs that chain into downstream steps must maintain this 4-element tuple shape. The `status` field is captured from script stdout via `env()`.

**Manifest CSV** — simple format with a single `submission_id` column (see `assets/`).

**results.json** — JSON key-value pairs written by validation/scoring scripts. `ANNOTATE_SUBMISSION` runs `challengeutils annotate-submission -f` to read this file and attach its contents as Synapse submission annotations.

**Synapse annotations** — key-value metadata attached to submissions. The `email_with_score` param ("yes"/"no") controls whether scores are included in participant emails. Non-score annotations (e.g., `current_rank`) are always excluded from the email context in `send_email.py`.

## Conventions

- **Process aliasing**: When including the same process multiple times, use aliases (e.g., `SEND_EMAIL as SEND_EMAIL_BEFORE`, `UPDATE_SUBMISSION_STATUS as UPDATE_SUBMISSION_STATUS_AFTER_VALIDATE`). Each alias creates a distinct Nextflow task.
- **Sync signals**: Processes that produce no meaningful output emit `val "ready"` as a synchronization token for downstream dependencies.
- **Status capture**: Validation/scoring scripts print status to stdout, captured via `env(status)` in the Nextflow tuple. This drives pass/fail routing.
- **maxForks = 1**: Used on `CREATE_FOLDERS` — Synapse cannot handle concurrent folder creation reliably.
- **File name sanitization**: `download_submission.py` replaces non-alphanumeric chars (except `.`, `-`, `_`) with underscores — because Nextflow breaks on spaces in file paths.
- **Python scripts in `bin/`**: Keep small and single-purpose with specific input/output contracts. This is a core design philosophy (see ORCA-312).
- **Profile-per-challenge**: Each challenge gets its own profile block in `nextflow.config` with pre-set params. Required params: `entry`, `view_id`, `project_name`, `groundtruth_id` (D2M) or `data_folder_id` (M2D).
- **Submission ID sourcing**: Always pass `submission_id` from the prior process output, never re-read from the original submission channel — parallel channel consumption can cause mismatches.

## Architecture

```
main.nf                          -- Entry dispatcher (--entry data_to_model | model_to_data)
├── workflows/DATA_TO_MODEL.nf   -- D2M pipeline: download → validate → score → annotate → email
├── workflows/MODEL_TO_DATA.nf   -- M2D pipeline: create_folders → stage_data → run_docker → upload → validate → score → annotate → email
├── subworkflows/                 -- CREATE_SUBMISSION_CHANNEL (parses --submissions or --manifest)
├── modules/                     -- Reusable Nextflow processes (one per .nf file)
└── bin/                         -- Python helper scripts executed inside containers
```

**Container strategy**: Each process step runs in a specific versioned container:
- `sagebionetworks/synapsepythonclient:v4.0.0` — Synapse file operations
- `sagebionetworks/challengeutils:v4.2.0` — status updates, annotations
- `params.challenge_container` — organizer-provided container for validation/scoring
- `ghcr.io/sage-bionetworks-workflows/nf-synapse-challenge:latest` — M2D Docker orchestration (runs Docker-in-Docker)

## Constraints

- **Never use the original submission channel for downstream submission IDs.** Always use the submission_id from the prior process output. Mixing channels caused email/submission mismatches (PR #53).
- **`groundtruth_id` must point to a single Synapse File entity, not a Folder.** Team agreement between DPE and CnB — predictions and groundtruth have a 1:1 relationship (PR #50).
- **Do not call `get_annotations` before determining email type (BEFORE vs AFTER).** New submissions have no annotations yet, so this call fails for SEND_EMAIL_BEFORE (PR #52).
- **Validate entity type before any file operations.** Submissions can be any Synapse entity type (File, Docker, Project). Attempting file operations on non-file submissions crashes the pipeline (PR #59).
- **`SYNAPSE_AUTH_TOKEN` must be configured as a Nextflow secret.** Required for all Synapse API operations. Set in Seqera Platform workspace or local environment.
- **Docker socket mounting is required for M2D.** Configured globally in `nextflow.config` and via `aws.batch.volumes` for AWS Batch execution.

## Testing

No automated unit or integration tests exist (ORCA-312 identifies this as a gap). Testing is done manually:
1. Run the pipeline in the Seqera Platform dev workspace (`example-dev-project`)
2. Use prototype profiles (`data_to_model_prototype`, `model_to_data_prototype`) with known test submissions
3. Verify: Tower run completes, emails are correct, Synapse annotations are applied
4. PRs must include Problem/Solution/Testing sections per the PR template

## Related Systems

- **[orca-recipes](https://github.com/Sage-Bionetworks-Workflows/orca-recipes)** — Airflow DAGs that schedule and trigger this workflow on a recurring basis
- **Synapse** (synapse.org) — Data platform hosting challenge projects, submission queues, file storage, and participant notifications
- **Seqera Platform** (Tower) — Workflow execution platform; dev workspace at `tower-dev.sagebionetworks.org`, prod at `tower.sagebionetworks.org`
- **GHCR** — Container registry for workflow and challenge evaluation images; CI publishes on push to main or version tags
- **Jira**: DPE board for implementation tickets, ORCA board for workflow/architecture epics
