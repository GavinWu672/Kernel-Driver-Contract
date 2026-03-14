# Kernel Driver Architecture Boundaries

## Purpose

This document defines the non-negotiable architecture boundaries for kernel-driver changes.

## Boundary 1 - IRQL Boundary

- Every reviewed or generated function should state the expected entry IRQL when possible.
- Code reachable at `DISPATCH_LEVEL` or above must avoid blocking and pageable behavior.
- IRQL transitions must be explicit review points.

## Boundary 2 - Memory Boundary

- Pageable and non-pageable access must not be mixed carelessly across elevated IRQL paths.
- Allocation intent must be explicit and matched to execution context.

## Boundary 3 - IRP Boundary

- IRP completion paths must not introduce synchronous waiting.
- Completion ownership, cancel interactions, and completion status propagation must be reviewable.

## Boundary 4 - Cleanup Boundary

- Any allocation, reference acquisition, or lock acquisition must have a corresponding cleanup / unwind path.
- Error paths must be reviewed with the same rigor as happy paths.

## Evidence Expectations

Relevant changes should be reviewed against:

- IRQL annotations or review notes
- Driver Verifier / SDV / WDK diagnostics
- cleanup / unwind path review
- pool allocation review
