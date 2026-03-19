# Kernel Driver Fact Checklist

## Purpose

This checklist records driver facts that the agent must not guess.

The fields are split into two groups:

- Human-mandatory facts: hardware, platform, or lifecycle truths that the agent must not invent.
- AI-verifiable facts: implementation facts that the agent may derive from code, but must still cite a source and present for human review.

If a human-mandatory fact is unresolved, the agent must stop implementation guidance and ask for the missing source.

## Human-Mandatory Facts

- [ ] DRIVER_TYPE: `WDM` / `WDF-KMDF` / `WDF-UMDF`
- [ ] TARGET_OS: minimum supported Windows version
- [ ] WDK_VERSION: active WDK toolchain version
- [ ] PNP_MODEL: `legacy` / `PnP`
- [ ] POWER_MANAGED: `yes` / `no`
- [ ] IRQL_MAX: highest IRQL reachable by this driver
- [ ] INTERRUPT_MODEL: `none` / `line-based` / `MSI` / `MSI-X` / `passive-level`
- [ ] DMA_MODEL: `none` / `PIO` / `packet DMA` / `common-buffer DMA` / `scatter-gather DMA` / `mixed`
- [ ] CONFIG_SPACE_ACCESS_LEVEL: `PASSIVE-only` / `DISPATCH-capable` / `unknown`
- [ ] PAGED_CODE_ALLOWED: whether selected code paths are guaranteed at `PASSIVE_LEVEL`
- [ ] POOL_TYPE: `NonPagedPoolNx` / `NonPagedPool` / `PagedPool` allocation policy
- [ ] VERIFIER_ENABLED: whether Driver Verifier is enabled
- [ ] SDV_AVAILABLE: whether Static Driver Verifier outputs exist

## AI-Verifiable Facts

- [ ] IO_BUFFERING_MODEL: `buffered` / `direct` / `neither` / `mixed`
- [ ] IOCTL_SURFACE_PRESENT: `yes` / `no`
- [ ] DEVICE_NAMING_MODEL: `unnamed` / `NT name` / `DOS symbolic link` / `device interface only` / `mixed`
- [ ] SECURITY_DESCRIPTOR_MODEL: `default` / `SDDL` / `custom` / `unknown`
- [ ] REMOVE_LOCK_USED: `yes` / `no`
- [ ] LOCKING_PRIMITIVES: spinlock / mutex / push lock / interrupt lock usage model
- [ ] IRP_COMPLETION_MODEL: `synchronous` / `asynchronous` / `mixed`
- [ ] CLEANUP_PATTERN: whether cleanup / unwind path is explicit and reviewable

## Source Discipline

- Every populated field must point to a concrete source artifact or code location.
- Human-mandatory facts should come from project files, INF/installation assets, hardware contracts, design notes, or confirmed reviewer input.
- AI-verifiable facts should come from concrete code scans and must be reported as derived observations, not hidden assumptions.

## Rule

- If a human-mandatory fact is blank, the agent must stop making implementation assumptions.
- If an AI-verifiable fact is blank, the agent may propose a bounded code scan to derive it, then surface the result for human confirmation.