# Kernel Driver AI Governance Rules

## Purpose

This document defines mandatory AI constraints for Windows kernel-driver work.

Kernel-driver failures can cause BSODs, memory corruption, or persistent device instability. These rules are hard constraints, not suggestions.

## Core Constraints

- The agent must not recommend a kernel API when the current IRQL is unknown.
- The agent must not assume paged memory is safe at every IRQL.
- The agent must not recommend blocking or paged operations at `DISPATCH_LEVEL` or above.
- The agent must not omit cleanup / unwind paths for allocations, locks, or IRPs.
- Any generated driver code should include explicit IRQL expectations or annotations when possible.

## No-Assumption Policy

The agent must not assume any of the following without a concrete source:

- driver model (`WDM`, `KMDF`, `UMDF`)
- highest reachable IRQL
- pool allocation policy
- pageable-code guarantees
- cleanup / completion ownership
- verifier / SDV status

If any required fact is missing:

- stop implementation guidance
- ask for the missing source or fact

## IRQL Safety

- `DISPATCH_LEVEL` or above must be treated as non-blocking and non-paged only unless proven otherwise.
- The agent must not recommend `KeWaitForSingleObject`, `Zw*`, or pageable code paths in elevated IRQL paths.
- The agent must explicitly call out IRQL-sensitive APIs when reviewing code.

## Memory And Cleanup Safety

- Allocation guidance must specify pool intent explicitly.
- Resource acquisition must always be paired with cleanup / unwind reasoning.
- The agent must not recommend hidden ownership transfer without documenting the release path.

## IRP Path Safety

- The agent must not recommend synchronous waits in IRP completion paths.
- Completion, cancel, and cleanup interactions must be treated as separate review surfaces.

## Validator Failure Policy

- A validator `HARD-STOP` result is a hard constraint. The agent must not reframe, suppress, or work around a hard-stop finding.
- A validator `ADVISORY` result must be acknowledged and documented if the change proceeds anyway.
- The agent must not claim a check passed when the validator output is unavailable or skipped.

## Scope Boundary

- This contract is a pre-merge static pattern checker. It is not a substitute for Driver Verifier (DV), Static Driver Verifier (SDV), or HLK/WHCP certification.
- Passing all validators in this contract does not indicate DV-clean, SDV-clean, or WHQL-ready status.
- When DV/SDV/HLK results are available, those take precedence over this tool's findings.

## Unit Test Boundary Constraints

- The agent must NOT attempt to stub `ntddk.h`, `wdf.h`, `wdm.h`, or any WDK-specific
  header for user-mode compilation. These headers have unavoidable kernel-mode structural
  dependencies that cannot be satisfied outside a WDK build environment.

- User-mode unit tests must target function-level seams, not file-level compilation of
  driver source files. Attempting to compile a full driver `.c` file in user mode by
  providing synthetic WDK header stubs is a prohibited approach.

- A valid seam is a function pointer or interface that can be substituted without
  modifying driver source (e.g., `BUS_INTERFACE_STANDARD.GetBusData`).

- If a natural seam does not exist at the target function, the agent must recommend
  extracting pure business logic into a separate compilation unit, NOT creating synthetic
  WDK header stubs.

- A test build is valid only if it compiles without any WDK headers. If a WDK header is
  required for compilation, the test boundary is drawn at the wrong level.

- See `docs/unit-test-strategy.md` for the decision tree and canonical test structure.

## Related Documents

- `KERNEL_DRIVER_CHECKLIST.md`
- `KERNEL_DRIVER_ARCHITECTURE.md`
- `STATUS.md`
- `docs/microsoft-standards-mapping.md`
- `docs/unit-test-strategy.md`
