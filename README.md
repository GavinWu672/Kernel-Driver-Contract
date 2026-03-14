# Kernel Driver Contract

This repository is a documentation-first and runtime-integrable governance baseline for Windows kernel-driver work.

It is intended to work as an external domain contract for `ai-governance-framework`, parallel to `USB-Hub-Firmware-Architecture-Contract`.

## Included

- `contract.yaml`
- `AGENTS.md`
- `KERNEL_DRIVER_CHECKLIST.md`
- `KERNEL_DRIVER_ARCHITECTURE.md`
- `rules/kernel-driver/safety.md`
- `validators/irql_safety_validator.py`
- `docs/architecture-review.md`
- `PLAN.md`

## Integration Goal

This repository exists to validate that:

- contract discovery works for a second domain
- framework runtime hooks do not require domain-specific hardcoding
- domain repos can evolve independently while sharing the same governance seam

## Runtime Integration

Typical framework-side verification commands:

```powershell
$env:AI_GOVERNANCE_PYTHON='C:\Users\daish\AppData\Local\Python\pythoncore-3.14-64\python.exe'

& $env:AI_GOVERNANCE_PYTHON governance_tools\domain_contract_loader.py `
  --contract ..\Kernel-Driver-Contract\contract.yaml `
  --format human

& $env:AI_GOVERNANCE_PYTHON runtime_hooks\core\post_task_check.py `
  --file ..\Kernel-Driver-Contract\fixtures\post_task_response.txt `
  --risk medium `
  --oversight review-required `
  --checks-file ..\Kernel-Driver-Contract\fixtures\irql_violation.checks.json `
  --contract ..\Kernel-Driver-Contract\contract.yaml `
  --format human
```

The included post-task fixture intentionally triggers an advisory IRQL warning through `KeWaitForSingleObject` in a dispatch-level code sample.

## Next Step

The next recommended step is to connect this contract repo to a real driver codebase using:

- `FACT_INTAKE.md`
- `SOURCE_INVENTORY.md`
- `FACT_INTAKE_WORKSHEET.md`

These files are intentionally minimal and exist only to support the first real driver-repo intake, not to create a large memory platform.
