# Kernel Driver Fact Intake Guide

## Purpose

This guide defines the minimum fact-intake path for connecting a real Windows kernel-driver repository to this contract repository.

Use it before filling `KERNEL_DRIVER_CHECKLIST.md`.

## Intake Principle

- Record only confirmed facts.
- Every fact should point to a concrete source artifact.
- If the source artifact is missing, keep the fact unresolved.
- Do not replace driver facts with assumptions about IRQL, pool type, cleanup ownership, DMA model, or interrupt model.

## Fact Classes

### 1. Human-Mandatory Facts

These are hardware, platform, or lifecycle truths that the agent must not invent.

Examples:

- `DRIVER_TYPE`
- `PNP_MODEL`
- `POWER_MANAGED`
- `IRQL_MAX`
- `INTERRUPT_MODEL`
- `DMA_MODEL`
- `CONFIG_SPACE_ACCESS_LEVEL`
- `POOL_TYPE`

If one of these facts is missing, the correct governance response is a blocking question at session bootstrap or fact intake time.

### 2. AI-Verifiable Facts

These are implementation facts that the agent may derive from concrete code inspection, but must still cite and surface for human confirmation.

Examples:

- `IOCTL_SURFACE_PRESENT`
- `DEVICE_NAMING_MODEL`
- `SECURITY_DESCRIPTOR_MODEL`
- `REMOVE_LOCK_USED`
- `LOCKING_PRIMITIVES`
- `IRP_COMPLETION_MODEL`
- `CLEANUP_PATTERN`

These should be reported as a fact summary with source locations, not silently assumed.

## Recommended Intake Order

### 1. Driver Model and Build Identity

Collect:

- `.vcxproj` / `.sln` / project configuration
- active driver model (`WDM`, `KMDF`, `UMDF`)
- target OS / WDK version
- PnP or legacy service model

Used to fill:

- `DRIVER_TYPE`
- `TARGET_OS`
- `WDK_VERSION`
- `PNP_MODEL`

### 2. Lifecycle and IRQL Facts

Collect:

- dispatch routines
- DPC / ISR / callback entry points
- SAL / IRQL annotations
- start / stop / remove / surprise-remove paths
- verifier or code review notes

Used to fill:

- `IRQL_MAX`
- `PAGED_CODE_ALLOWED`
- `POWER_MANAGED`
- `INTERRUPT_MODEL`

### 3. Memory, DMA, and Resource Facts

Collect:

- allocation call sites
- pool allocation wrappers
- pageable section markers
- DMA setup paths
- configuration-space access paths

Used to fill:

- `POOL_TYPE`
- `DMA_MODEL`
- `CONFIG_SPACE_ACCESS_LEVEL`

### 4. I/O, Cleanup, and Namespace Facts

Collect:

- IOCTL handlers
- device creation and naming paths
- cleanup / unload / remove paths
- IRP completion paths
- remove-lock usage
- security descriptor or SDDL setup

Used to fill:

- `IO_BUFFERING_MODEL`
- `IOCTL_SURFACE_PRESENT`
- `DEVICE_NAMING_MODEL`
- `SECURITY_DESCRIPTOR_MODEL`
- `REMOVE_LOCK_USED`
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
- actual PnP or power-management source file
- actual allocation or pool wrapper source file
- actual cleanup / IRP completion source file
- actual verifier / SDV / WDK evidence source

If fewer than these exist, keep the affected checklist fields unresolved.

## Working Companions

- `SOURCE_INVENTORY.md`
- `FACT_INTAKE_WORKSHEET.md`
- `KERNEL_DRIVER_CHECKLIST.md`