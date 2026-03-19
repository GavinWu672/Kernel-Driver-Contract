# Kernel Driver Architecture State Invariants

## Purpose

This document defines the state invariants and resource-visibility boundaries that an AI agent must not violate when reasoning about Windows kernel-driver changes.

For kernel drivers, architecture boundaries are not only layering guidance. They are lifecycle constraints tied to PnP state, power state, interrupt state, DMA ownership, and object lifetime.

If the current state is unknown, the agent must stop making implementation claims and request the missing state fact.

## Invariant 1 - PnP State Controls Resource Visibility

### Device Added but Not Started

- The device object can exist before hardware resources are translated and connected.
- Memory-mapped registers, interrupts, DMA adapters, and started-only queues must be treated as not yet visible.
- Code in this state must not touch hardware registers, queue started-only I/O, or assume interrupts are connected.

### Device Started

- Hardware resources may be mapped and interrupts may be connected only after successful start completion.
- Access to BARs, translated resources, interrupt objects, and DMA resources is valid only within the started lifetime.
- Started-state ownership must be paired with an explicit stop, surprise-remove, or remove teardown path.

### Device Stopped or Stop-Pending

- The driver must treat the device as unable to service new hardware work until restart is complete.
- New hardware programming, DMA setup, and interrupt-dependent flows must be blocked or drained.
- Any remaining queued I/O must follow a documented paused, failed, or requeue model.

### Surprise Removed or Removed

- After surprise removal, the driver must treat hardware access as unsafe even if cleanup is still in progress.
- After remove completion, device extensions, interfaces, symbolic links, interrupts, DMA objects, and mapped resources must be treated as no longer valid.
- The agent must not recommend touching registers, forwarding new hardware work, or reusing remove-invalidated objects after these states.

## Invariant 2 - Power State Limits Legal Work

### D0 Working State

- Normal device programming is allowed only when the device is in a working power state and the required resources are still owned.

### Low-Power Device States

- When the device is sleeping or powering down, the driver must not assume register access, DMA progress, or interrupt delivery remain valid.
- Requests arriving in low-power states require an explicit queue, fail, or wake coordination policy.
- Power transitions must preserve a reviewer-visible ownership model for outstanding IRPs, timers, DPCs, and wake paths.

### Wait/Wake and Wake-Capable Devices

- Wake capability is a separate lifecycle surface, not a blanket permission to access the device while powered down.
- The agent must distinguish wake-arming logic from ordinary I/O or register programming.

## Invariant 3 - Interrupt and DPC Paths Must Respect Lifetime and IRQL

### ISR / DPC Visibility

- ISR and DPC code must assume non-blocking, non-pageable execution.
- Interrupt handlers may read or acknowledge device state only while the interrupt registration and resource lifetime are still valid.

### Interrupt Disconnect Boundary

- Once interrupt teardown begins, ISR, DPC, passive-level interrupt work items, and related shared state must be treated as draining or invalid.
- The agent must not recommend new interrupt-driven work after disconnect or surprise-removal boundaries.

## Invariant 4 - DMA and Transfer Ownership Are State-Bound

- DMA common buffers, scatter/gather transactions, map registers, and programmed transfers belong to a specific started-device lifetime.
- If start, stop, reset, surprise-remove, or power-down boundaries are crossed, the agent must require an explicit drain, cancel, or reinitialize path.
- If the active DMA model is unknown, the agent must stop and request a human-confirmed fact.

## Invariant 5 - Device Object, Namespace, and Security Surfaces Are Contracted Interfaces

- Named device objects, symbolic links, interfaces, and IOCTL exposure are part of the driver's externally visible contract.
- The agent must not casually add or remove namespace exposure without stating the security and compatibility impact.
- Device access assumptions must be tied to an explicit naming and security-descriptor model.

## Invariant 6 - Cleanup and Lifetime Rules Apply to Every State Transition

- Every state transition that acquires resources must have a matching teardown path.
- Cleanup is not limited to unload; it must exist for failed start, stop, surprise remove, remove, cancel, and power-down paths where applicable.
- Error-path teardown, not only happy-path teardown, must remain reviewable.

## Reviewer Questions

For any non-trivial driver change, the review should be able to answer:

- What is the current PnP state when this code runs?
- Are hardware registers, interrupts, DMA objects, and queues actually visible in that state?
- What changes if the device is stopped, removed, or powered down while this path is active?
- Which objects remain valid, and who owns their teardown?
- Which facts are human-confirmed versus inferred from code structure?

## Related Rule Payload

See `docs/microsoft-architecture-principles.md` for reviewer-citable constraint rules derived from Microsoft's kernel driver architecture guidance.