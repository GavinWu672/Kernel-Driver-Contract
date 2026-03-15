# Active Task

## Current Task

Maintain and extend the Kernel Driver Contract as a reusable external domain
contract for `ai-governance-framework`.

## Current Status (2026-03-15)

**Phase 1 — complete**
- `contract.yaml` discovery, session bootstrap, pre/post-task validation: working

**Phase 3 — complete**
- 5 new validators: sync_primitive, dpc_isr, pageable_section, dispatch_routine,
  static_analysis (KD-006 ~ KD-010)
- `run_validators.py`: CI/CD pipeline runner with hard-stop exit-code enforcement
- `scan_source.py`: real C/H source scanner — classifies functions by IRQL context,
  emits checks.json payloads
- Verified against `microsoft/Windows-driver-samples` pcidrv (16 files, all pass)
  and cancel/sys driver (3 handlers, 3 pageable functions detected)

**Phase 2 — blocked**
- No real driver repository connected yet
- All memory/02_project_facts.md fields still pending

## Next Action

- Connect a real driver repository and run scan_source.py against it
- Fill confirmed high-risk facts:
  - `DRIVER_TYPE`
  - `TARGET_OS`
  - `IRQL_MAX`
  - `POOL_TYPE`
  - `CLEANUP_PATTERN`
  - `VERIFIER_ENABLED`
- Add .github/workflows/kernel-driver-check.yml (Phase 4)

## Blockers

- Real driver repository path is not yet provided
- Actual IRQL model, pool allocation policy, verifier status: unknown
