# Active Task

## Current Task

Maintain the Kernel Driver Contract as a reusable external domain contract for `ai-governance-framework`.

## Current Status

- `contract.yaml` discovery works
- `session_start` context injection works
- `pre_task_check` external rule activation works
- `post_task_check` can execute the first advisory IRQL validation fixture
- `post_task_check` can execute advisory pool-allocation validation
- minimal fact-intake workflow exists through `FACT_INTAKE.md`, `SOURCE_INVENTORY.md`, and `FACT_INTAKE_WORKSHEET.md`
- operational usage docs exist through `WORKFLOW.md` and `VALIDATION_REQUIREMENTS.md`

## Next Action

- connect the contract repo to a real driver codebase
- fill the first confirmed high-risk facts:
  - `DRIVER_TYPE`
  - `TARGET_OS`
  - `IRQL_MAX`
  - `POOL_TYPE`
  - `CLEANUP_PATTERN`
  - `VERIFIER_ENABLED`

## Blockers

- real driver repository path is not yet connected
- actual project file / solution path is unknown
- actual IRQL model is unknown
- actual pool allocation policy is unknown
- actual verifier / SDV status is unknown
