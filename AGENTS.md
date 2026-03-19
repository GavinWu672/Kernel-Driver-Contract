# Kernel Driver AI Governance Rules

## Purpose

This document defines mandatory AI constraints for Windows kernel-driver work.

Kernel-driver failures can cause BSODs, memory corruption, persistent device instability, or unrecoverable hardware-state corruption. These rules are hard constraints, not suggestions.

## Required Reasoning Order

Before giving implementation guidance, the agent must reason in this order:

1. classify the missing or confirmed facts
2. identify the active lifecycle state and applicable `KSTATE-*` rules
3. decide whether implementation guidance is allowed, blocked, or limited to review notes
4. cite the governing rule ID when rejecting or constraining a recommendation

If the task skips this order, the response is not contract-compliant.

## Fact Ownership Policy

The agent must distinguish between two fact classes from `KERNEL_DRIVER_CHECKLIST.md`.

### Human-Mandatory Facts

These are hardware, platform, or lifecycle truths that the agent must not invent.

Examples:

- driver model (`WDM`, `KMDF`, `UMDF`)
- `PNP_MODEL`
- `POWER_MANAGED`
- highest reachable IRQL
- `INTERRUPT_MODEL`
- `DMA_MODEL`
- `CONFIG_SPACE_ACCESS_LEVEL`
- pool allocation policy
- verifier / SDV status when required for the claim being made

If a required human-mandatory fact is missing:

- stop implementation guidance
- ask for the missing source or fact
- state that the task is blocked by a missing human-mandatory fact

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

If an AI-verifiable fact is missing:

- the agent may perform a bounded code scan
- the result must be reported as a derived observation with source locations
- the agent must not silently treat the derived observation as a hardware truth

## State Invariant Policy

Architecture guidance is defined by state invariants, not only by abstract boundaries.

The agent must apply `docs/microsoft-architecture-principles.md` as a rule payload.

### Required KSTATE usage

When lifecycle-sensitive guidance is given, the response should cite the relevant `KSTATE-*` rule when possible.

Important examples:

- `KSTATE-001` start gates hardware visibility
- `KSTATE-003` surprise remove kills hardware access
- `KSTATE-101` low-power state blocks normal I/O assumptions
- `KSTATE-201` interrupt lifetime bounds ISR work
- `KSTATE-301` DMA ownership is state-bound
- `KSTATE-501` every stateful acquisition needs stateful teardown

If the current lifecycle state is unknown, the agent must stop and request the missing state fact instead of improvising.

## Core Constraints

- The agent must not recommend a kernel API when the current IRQL is unknown.
- The agent must not assume paged memory is safe at every IRQL.
- The agent must not recommend blocking or paged operations at `DISPATCH_LEVEL` or above.
- The agent must not recommend hardware access unless the relevant start, power, interrupt, and teardown state is explicit.
- The agent must not omit cleanup / unwind paths for allocations, locks, interrupts, DMA objects, interfaces, or IRPs.
- Any generated driver code should include explicit IRQL expectations or reviewer-visible lifecycle notes when possible.

## Response Shape Requirements

For non-trivial driver guidance, the response should include:

- rule basis
- missing fact status
- untouched safety boundaries
- verification evidence or verification gap

Minimum acceptable phrasing example:

- rule basis: `KSTATE-003` and `KD-007`
- blocked fact: `INTERRUPT_MODEL` is still human-mandatory and unresolved
- untouched boundary: no change to remove-path teardown or interrupt disconnect ordering
- verification gap: no SDV / Driver Verifier evidence supplied for this path

## IRQL, Interrupt, and Memory Safety

- `DISPATCH_LEVEL` or above must be treated as non-blocking and non-paged only unless proven otherwise.
- The agent must not recommend `KeWaitForSingleObject`, `Zw*`, or pageable code paths in elevated-IRQL paths.
- ISR and DPC guidance must also satisfy the interrupt lifetime rules in `KSTATE-201` and the non-blocking rule in `KSTATE-202`.
- Allocation guidance must specify pool intent explicitly.
- The agent must not recommend hidden ownership transfer without documenting the release path.

## IRP, PnP, and Power Safety

- The agent must not recommend synchronous waits in IRP completion paths.
- Completion, cancel, and cleanup interactions must be treated as separate review surfaces.
- The agent must not treat PnP stop, surprise remove, remove, or low-power transitions as ordinary steady-state execution.
- When request handling depends on power or PnP state, the response must say how requests are queued, failed, drained, resumed, or blocked.

## Validator Failure Policy

- A validator `HARD-STOP` result is a hard constraint. The agent must not reframe, suppress, or work around a hard-stop finding.
- A validator `ADVISORY` result must be acknowledged and documented if the change proceeds anyway.
- The agent must not claim a check passed when the validator output is unavailable or skipped.

## Scope Boundary

- This contract is a pre-merge governance and validation layer. It is not a substitute for Driver Verifier (DV), Static Driver Verifier (SDV), or HLK/WHCP certification.
- Passing all validators in this contract does not indicate DV-clean, SDV-clean, or WHQL-ready status.
- When DV/SDV/HLK results are available, those take precedence over this tool's findings.

## Unit Test Boundary Constraints

- The agent must NOT attempt to stub `ntddk.h`, `wdf.h`, `wdm.h`, or any WDK-specific header for user-mode compilation.
- User-mode unit tests must target function-level seams, not file-level compilation of driver source files.
- A valid seam is a function pointer or interface that can be substituted without modifying driver source.
- If a natural seam does not exist at the target function, the agent must recommend extracting pure business logic into a separate compilation unit, not creating synthetic WDK header stubs.
- A test build is valid only if it compiles without any WDK headers.

## Related Documents

- `KERNEL_DRIVER_CHECKLIST.md`
- `KERNEL_DRIVER_ARCHITECTURE.md`
- `FACT_INTAKE.md`
- `STATUS.md`
- `docs/microsoft-architecture-principles.md`
- `docs/microsoft-standards-mapping.md`
- `docs/unit-test-strategy.md`