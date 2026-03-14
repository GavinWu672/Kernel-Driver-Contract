# Validation Log

## Completed

- External contract loading verified from `ai-governance-framework`
- `session_start` context injection verified
- `pre_task_check` external `kernel-driver` rule activation verified
- first `post_task_check` advisory IRQL fixture verified
- compliant `post_task_check` IRQL fixture verified

## Latest Verified Flow

- `domain_contract_loader.py --contract ..\Kernel-Driver-Contract\contract.yaml --format human`
- `session_start.py --project-root ..\Kernel-Driver-Contract --contract ..\Kernel-Driver-Contract\contract.yaml --format human`
- `pre_task_check.py --project-root ..\Kernel-Driver-Contract --contract ..\Kernel-Driver-Contract\contract.yaml --format json`
- `post_task_check.py --file ..\Kernel-Driver-Contract\fixtures\post_task_response.txt --checks-file ..\Kernel-Driver-Contract\fixtures\irql_violation.checks.json --contract ..\Kernel-Driver-Contract\contract.yaml --format json`
- `post_task_check.py --file ..\Kernel-Driver-Contract\fixtures\post_task_response.txt --checks-file ..\Kernel-Driver-Contract\fixtures\irql_compliant.checks.json --contract ..\Kernel-Driver-Contract\contract.yaml --format json`

## Observed Result

- built-in kernel-driver evidence gate passed
- domain validator produced `KD-IRQL-001` for `KeWaitForSingleObject`
- result remained reviewer-consumable through advisory warnings
- compliant fixture produced no IRQL domain violation while preserving the same built-in evidence baseline

## Pending Evidence

- real Driver Verifier output
- real SDV / WDK diagnostics
- real driver project facts from a connected repository
