# Kernel Driver Contract Workflow

This document describes the smallest practical workflow for using this contract repository with `ai-governance-framework`.

## Goal

Use the contract repo in three stages:

1. load the domain contract
2. run governance checks against driver work
3. persist confirmed facts once a real driver repository is connected

## Stage 1: Contract Verification

Use this stage when validating that the repo still mounts cleanly as an external domain contract.

```powershell
$env:AI_GOVERNANCE_PYTHON='C:\Users\daish\AppData\Local\Python\pythoncore-3.14-64\python.exe'

& $env:AI_GOVERNANCE_PYTHON D:\ai-governance-framework\governance_tools\domain_contract_loader.py `
  --contract D:\Kernel-Driver-Contract\contract.yaml `
  --format human
```

Expected outcome:

- contract loads successfully
- `domain: kernel-driver` is reported
- external documents and validators are listed

## Stage 2: Session Bootstrap

Use this stage before starting a real driver-oriented AI coding session.

```powershell
& $env:AI_GOVERNANCE_PYTHON D:\ai-governance-framework\runtime_hooks\core\session_start.py `
  --project-root D:\Kernel-Driver-Contract `
  --plan D:\Kernel-Driver-Contract\PLAN.md `
  --rules common,kernel-driver `
  --risk medium `
  --oversight review-required `
  --contract D:\Kernel-Driver-Contract\contract.yaml `
  --format human
```

Expected outcome:

- kernel-driver domain context is injected
- `AGENTS.md`, checklist, and architecture guidance appear in the session summary
- validator preflight succeeds

## Stage 3: Pre-Task Governance Check

Use this stage to confirm the active policy surface before making changes.

```powershell
& $env:AI_GOVERNANCE_PYTHON D:\ai-governance-framework\runtime_hooks\core\pre_task_check.py `
  --project-root D:\Kernel-Driver-Contract `
  --rules common,kernel-driver `
  --risk medium `
  --oversight review-required `
  --contract D:\Kernel-Driver-Contract\contract.yaml `
  --format json
```

Expected outcome:

- `ok: true`
- external `kernel-driver` rules are active
- architecture and proposal previews remain reviewer-readable

## Stage 4: Post-Task Validation Baselines

Use the included fixtures to verify that domain validators still behave as expected.

IRQL violation baseline:

```powershell
& $env:AI_GOVERNANCE_PYTHON D:\ai-governance-framework\runtime_hooks\core\post_task_check.py `
  --file D:\Kernel-Driver-Contract\fixtures\post_task_response.txt `
  --risk medium `
  --oversight review-required `
  --checks-file D:\Kernel-Driver-Contract\fixtures\irql_violation.checks.json `
  --contract D:\Kernel-Driver-Contract\contract.yaml `
  --format human
```

Pool violation baseline:

```powershell
& $env:AI_GOVERNANCE_PYTHON D:\ai-governance-framework\runtime_hooks\core\post_task_check.py `
  --file D:\Kernel-Driver-Contract\fixtures\post_task_response.txt `
  --risk medium `
  --oversight review-required `
  --checks-file D:\Kernel-Driver-Contract\fixtures\pool_violation.checks.json `
  --contract D:\Kernel-Driver-Contract\contract.yaml `
  --format human
```

Expected outcome:

- built-in kernel-driver evidence checks pass
- advisory domain warnings appear for the violating fixtures
- compliant fixtures keep the same governance path but emit no domain warning

## Stage 5: Real Driver Intake

Use this stage only after a real driver repository is available.

Work in this order:

1. record discovered source locations in `SOURCE_INVENTORY.md`
2. fill the first confirmed facts in `FACT_INTAKE_WORKSHEET.md`
3. promote confirmed values into `memory/02_project_facts.md`
4. record decisions in `memory/03_decisions.md`
5. record real validation evidence in `memory/04_validation_log.md`

## Scope Boundary

This repository is intentionally small.

- It is a reusable external domain contract, not the driver codebase itself.
- It documents and validates governance expectations, but does not replace WDK, SDV, Driver Verifier, or code review.
- It should grow only when a real driver repository creates a concrete need.
