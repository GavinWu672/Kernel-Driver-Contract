# Kernel Driver Fact Checklist

## Purpose

This checklist records driver facts that the agent must not guess.

## Required Facts

- [ ] DRIVER_TYPE: `WDM` / `WDF-KMDF` / `WDF-UMDF`
- [ ] TARGET_OS: minimum supported Windows version
- [ ] IRQL_MAX: highest IRQL reachable by this driver
- [ ] PAGED_CODE_ALLOWED: whether selected code paths are guaranteed at `PASSIVE_LEVEL`
- [ ] POOL_TYPE: `NonPagedPoolNx` / `NonPagedPool` / `PagedPool` allocation policy
- [ ] CLEANUP_PATTERN: whether cleanup / unwind path is explicitly implemented
- [ ] VERIFIER_ENABLED: whether Driver Verifier is enabled

## Additional Review Facts

- [ ] SDV_AVAILABLE: whether Static Driver Verifier outputs exist
- [ ] WDK_VERSION: active WDK toolchain version
- [ ] LOCKING_PRIMITIVES: spinlock / mutex / push lock usage model
- [ ] IRP_COMPLETION_MODEL: synchronous / asynchronous / mixed

## Rule

If a required fact is blank, the agent must stop making implementation assumptions.
