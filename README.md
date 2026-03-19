# Kernel Driver Contract

A reusable domain contract for Windows kernel-driver work inside `ai-governance-framework`.

This repo is no longer only a scanner demo. It now defines:

- kernel-driver AI behavior constraints
- state-machine-oriented architecture invariants
- human-mandatory versus AI-verifiable driver facts
- validator-backed safety rules
- intake and workflow guidance for connecting a real driver repo


The current lifecycle-oriented architecture guidance and `KSTATE-*` rule surface were refined with reference to `Kernel-Mode Driver Architecture Design Guide (Microsoft).pdf`. They should be read as a contract-friendly distillation of that guidance, not as an official Microsoft certification or standards substitute.
It remains a governance and validation layer, not a replacement for WDK, SDV, Driver Verifier, or HLK.

## Current Shape

The contract is built from six document surfaces plus validator-backed rules:

- `KERNEL_DRIVER_CHECKLIST.md`
  - fact model split into `Human-Mandatory Facts` and `AI-Verifiable Facts`
- `KERNEL_DRIVER_ARCHITECTURE.md`
  - state invariants for PnP, power, interrupt, DMA, namespace, and teardown boundaries
- `docs/microsoft-architecture-principles.md`
  - Microsoft-derived constraint payload with review-citable rule IDs such as `KSTATE-003`
- `docs/microsoft-standards-mapping.md`
  - traceability map against Driver Verifier, SDV, SAL, and HLK intent
- `FACT_INTAKE.md`
  - intake policy for resolving hardware and lifecycle facts without guessing

The runtime contract entrypoint is `contract.yaml`.

## Why This Exists

The main AI failure mode in kernel work is not only bad syntax. It is incorrect lifecycle reasoning.

Typical failures include:

- touching hardware before start completion
- assuming interrupts or DMA remain valid during stop or surprise removal
- inventing DMA, interrupt, or config-space facts that were never confirmed
- treating power transitions as ordinary request-handling paths
- describing cleanup only on the success path

This contract pushes the model toward explicit lifecycle and ownership reasoning instead of prompt-level guesswork.

## State Invariant Model

`KERNEL_DRIVER_ARCHITECTURE.md` treats architecture as state invariants, not only abstract boundaries.

Core invariants include:

- PnP state controls hardware visibility
- low-power states limit legal work
- interrupt and DPC paths are valid only within active resource lifetime
- DMA ownership is tied to a specific started-device lifetime
- namespace and security surfaces are external contract surfaces
- teardown requirements apply to normal, failed-start, stop, surprise-remove, remove, cancel, and power-down paths

If the current lifecycle state is unknown, the correct response is to stop and request the missing fact.

## Fact Model

`KERNEL_DRIVER_CHECKLIST.md` separates facts into two classes.

### Human-Mandatory Facts

These must come from project files, hardware contracts, design notes, or reviewer-confirmed sources.

Examples:

- `DRIVER_TYPE`
- `PNP_MODEL`
- `POWER_MANAGED`
- `IRQL_MAX`
- `INTERRUPT_MODEL`
- `DMA_MODEL`
- `CONFIG_SPACE_ACCESS_LEVEL`
- `POOL_TYPE`

Missing human-mandatory facts should block implementation guidance.

### AI-Verifiable Facts

These may be derived from code, but must still be surfaced with source locations for human confirmation.

Examples:

- `IOCTL_SURFACE_PRESENT`
- `DEVICE_NAMING_MODEL`
- `SECURITY_DESCRIPTOR_MODEL`
- `REMOVE_LOCK_USED`
- `LOCKING_PRIMITIVES`
- `IRP_COMPLETION_MODEL`
- `CLEANUP_PATTERN`

## Rule Surfaces

### KD Rules

The validator-backed safety rules live in `rules/kernel-driver/safety.md` and are enforced by the validators under `validators/`.

Current hard-stop set in `contract.yaml`:

- `KD-002`
- `KD-003`
- `KD-006`
- `KD-007`
- `KD-010`

The rule surface also includes `KD-011` for the user-mode unit-test seam policy, but it is not currently listed in the contract hard-stop set.

These cover IRQL safety, blocking behavior, synchronization, static-analysis expectations, plus the documented test-boundary policy.

For review guidance on partially extracted helpers that only test a subset of a larger driver function, see docs/unit-test-strategy.md.

### KSTATE Rules

`docs/microsoft-architecture-principles.md` adds architecture and lifecycle rules in this format:

`[Rule ID] constraint -> violation consequence`

Examples:

- `KSTATE-001` start gates hardware visibility
- `KSTATE-003` surprise remove kills hardware access
- `KSTATE-101` low-power state blocks normal I/O assumptions
- `KSTATE-301` DMA ownership is state-bound
- `KSTATE-501` every stateful acquisition needs stateful teardown

These are designed to be cited directly in session bootstrap, pre-task reasoning, post-task review, and reviewer handoff notes.

## Quick Start

Validate that the contract loads:

```powershell
python governance_tools/domain_contract_loader.py --contract E:\BackUp\Git_EE\Kernel-Driver-Contract\contract.yaml --format human
```

Run a runtime bootstrap against the contract:

```powershell
python runtime_hooks/core/session_start.py `
  --project-root E:\BackUp\Git_EE\Kernel-Driver-Contract `
  --plan E:\BackUp\Git_EE\Kernel-Driver-Contract\PLAN.md `
  --rules common,kernel-driver `
  --risk medium `
  --oversight review-required `
  --contract E:\BackUp\Git_EE\Kernel-Driver-Contract\contract.yaml `
  --format human
```

Run a post-task fixture baseline:

```powershell
python runtime_hooks/core/post_task_check.py `
  --file E:\BackUp\Git_EE\Kernel-Driver-Contract\fixtures\post_task_response.txt `
  --risk medium `
  --oversight review-required `
  --checks-file E:\BackUp\Git_EE\Kernel-Driver-Contract\fixtures\irql_violation.checks.json `
  --contract E:\BackUp\Git_EE\Kernel-Driver-Contract\contract.yaml `
  --format human
```

## Real Driver Intake

When connecting a real driver repo, work in this order:

1. record source artifacts in `SOURCE_INVENTORY.md`
2. resolve human-mandatory facts in `FACT_INTAKE_WORKSHEET.md`
3. produce AI-verifiable fact summaries with source locations
4. promote confirmed values into `KERNEL_DRIVER_CHECKLIST.md`
5. record stable facts and decisions under `memory/`

Do not mark the contract as grounded in a real driver repo until hardware and lifecycle facts are actually sourced.

## Scope Boundary

This repository is intentionally narrow.

- It is a domain contract, not the production driver codebase.
- It improves pre-task and post-task governance, not token-level interception.
- It complements WDK, SDV, Driver Verifier, and HLK instead of replacing them.
- It should grow only when real driver evidence forces a concrete new requirement.
