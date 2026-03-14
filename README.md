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
```
