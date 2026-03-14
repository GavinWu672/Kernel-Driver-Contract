# Kernel Driver Fact Intake Guide

## Purpose

This guide defines the minimum fact-intake path for connecting a real Windows kernel-driver repository to this contract repository.

Use it before filling `KERNEL_DRIVER_CHECKLIST.md`.

## Intake Principle

- Record only confirmed facts.
- Every fact should point to a concrete source artifact.
- If the source artifact is missing, keep the fact unresolved.
- Do not replace driver facts with assumptions about IRQL, pool type, or cleanup ownership.

## Recommended Intake Order

### 1. Driver Model And Build Identity

Collect:

- `.vcxproj` / `.sln` / project configuration
- active driver model (`WDM`, `KMDF`, `UMDF`)
- target OS / WDK version

Used to fill:

- `DRIVER_TYPE`
- `TARGET_OS`
- `WDK_VERSION`

### 2. IRQL Facts

Collect:

- dispatch routines
- DPC / ISR / callback entry points
- SAL / IRQL annotations
- verifier or code review notes

Used to fill:

- `IRQL_MAX`
- `PAGED_CODE_ALLOWED`
- IRQL-sensitive path ownership

### 3. Memory And Pool Facts

Collect:

- allocation call sites
- pool allocation wrappers
- pageable section markers
- verifier or static-analysis notes

Used to fill:

- `POOL_TYPE`
- pageable versus non-pageable policy

### 4. Cleanup And IRP Facts

Collect:

- cleanup / unload / remove paths
- IRP completion paths
- unwind labels or release helpers

Used to fill:

- `CLEANUP_PATTERN`
- `IRP_COMPLETION_MODEL`

### 5. Validation Tooling Facts

Collect:

- Driver Verifier status
- SDV results
- WDK / PREfast diagnostics

Used to fill:

- `VERIFIER_ENABLED`
- `SDV_AVAILABLE`

## Minimum Artifact Checklist

Before claiming the contract is connected to a real driver repo, try to gather:

- actual driver project file
- actual dispatch / callback source file
- actual allocation or pool wrapper source file
- actual cleanup / IRP completion source file
- actual verifier / SDV / WDK evidence source

If fewer than these exist, keep the affected checklist fields unresolved.

## Working Companions

- `SOURCE_INVENTORY.md`
- `FACT_INTAKE_WORKSHEET.md`
