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

## Related Documents

- `KERNEL_DRIVER_CHECKLIST.md`
- `KERNEL_DRIVER_ARCHITECTURE.md`
- `docs/architecture-review.md`
