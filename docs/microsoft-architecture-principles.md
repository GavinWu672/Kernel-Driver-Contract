# Microsoft-Derived Kernel Driver Architecture Principles

> Purpose: reviewer-citable constraint payload derived from Microsoft's kernel-mode driver architecture guidance.
> Scope: architecture and lifecycle constraints for contract-guided reasoning.
> Not a replacement for WDK, SDV, Driver Verifier, or HLK evidence.

## Rule Format

Each rule is written as:

`[Rule ID] constraint -> violation consequence`

The consequence text describes the governance response the agent should take when the constraint cannot be satisfied from confirmed facts.

## PnP and Lifecycle Rules

### KSTATE-001 - start-gates-hardware-visibility

Constraint:
- Before the device is successfully started, translated hardware resources, interrupt objects, DMA programming surfaces, and started-only queues must be treated as unavailable.

Violation consequence:
- The agent must not recommend register access, interrupt programming, or started-only I/O setup until the started-state evidence is explicit.

### KSTATE-002 - stop-removes-operational-assumptions

Constraint:
- In stop, stop-pending, or paused states, the driver must not assume normal hardware servicing can continue.

Violation consequence:
- The agent must require an explicit queue, drain, fail, or restart policy before approving continued hardware work.

### KSTATE-003 - surprise-remove-kills-hardware-access

Constraint:
- After surprise removal, hardware access must be treated as unsafe even if cleanup is still executing.

Violation consequence:
- Any recommendation that touches registers, DMA state, or interrupt-driven work after surprise removal must be rejected as a lifecycle violation.

### KSTATE-004 - remove-kills-object-lifetime

Constraint:
- After remove completion, device objects, interfaces, symbolic links, interrupts, DMA objects, and mapped resources must be treated as invalid.

Violation consequence:
- The agent must not recommend reusing remove-invalidated objects and must require teardown evidence.

## Power Rules

### KSTATE-101 - low-power-state-blocks-normal-io

Constraint:
- In low-power device states, ordinary register programming, DMA progress assumptions, and interrupt-service assumptions are not valid unless explicitly re-established by the device's power policy.

Violation consequence:
- The agent must require a documented queue, fail, wake, or resume policy before recommending new I/O work.

### KSTATE-102 - wake-path-is-not-normal-io

Constraint:
- Wait/wake handling is a dedicated lifecycle surface and must not be treated as equivalent to normal I/O execution.

Violation consequence:
- The agent must separate wake-arming logic from normal request handling and reject designs that merge the two without explicit state reasoning.

## Interrupt and IRQL Rules

### KSTATE-201 - interrupt-lifetime-bounds-isr-work

Constraint:
- ISR, DPC, passive-level interrupt work, and interrupt-shared state are valid only while interrupt registration and the associated device resources remain active.

Violation consequence:
- The agent must reject new interrupt-driven work when disconnect, stop, surprise-remove, or remove teardown has begun.

### KSTATE-202 - elevated-irql-forbids-blocking-and-paged-assumptions

Constraint:
- ISR and DPC paths must be treated as non-blocking and non-pageable unless a narrower confirmed execution model exists.

Violation consequence:
- The agent must reject blocking waits, pageable access, or passive-only APIs in elevated-IRQL paths.

## DMA and Transfer Rules

### KSTATE-301 - dma-ownership-is-state-bound

Constraint:
- DMA common buffers, scatter/gather state, map registers, and transfer programming belong to a specific started-device lifetime.

Violation consequence:
- If stop, reset, surprise-remove, or power-down boundaries are crossed, the agent must require an explicit drain, cancel, or reinitialize policy.

### KSTATE-302 - unknown-dma-model-blocks-guidance

Constraint:
- If the active DMA or transfer model is not human-confirmed, the agent must not infer one from naming alone.

Violation consequence:
- The agent must stop and request a human-confirmed DMA fact before giving implementation guidance.

## Namespace and Security Rules

### KSTATE-401 - namespace-is-an-external-contract

Constraint:
- Named device objects, symbolic links, device interfaces, and IOCTL exposure are externally visible contract surfaces.

Violation consequence:
- The agent must not add, remove, or repurpose namespace exposure without stating compatibility and security impact.

### KSTATE-402 - access-model-must-be-explicit

Constraint:
- Device access assumptions must be tied to an explicit naming and security-descriptor model.

Violation consequence:
- If the naming or security model is unknown, the agent must treat access-control guidance as blocked.

## Cleanup and Ownership Rules

### KSTATE-501 - every-stateful-acquisition-needs-stateful-teardown

Constraint:
- Allocations, references, locks, interrupts, DMA resources, interfaces, and queue ownership must have teardown paths across normal, failed-start, stop, surprise-remove, remove, cancel, and power-down cases where applicable.

Violation consequence:
- The agent must reject recommendations that only describe happy-path release behavior.

### KSTATE-502 - error-path-cleanup-is-first-class

Constraint:
- Error-path unwind is part of the architecture contract, not a secondary concern.

Violation consequence:
- The agent must surface missing or ambiguous unwind behavior as a governance issue even when the success path looks correct.

## Review Usage

These rules are intended to be cited directly in:

- session bootstrap notes
- pre-task governance reasoning
- post-task review summaries
- human reviewer handoff comments

When a rule is triggered, quote the rule ID and then state whether the problem is:

- blocked by a missing human-mandatory fact
- derivable from code but still awaiting confirmation
- violated by the current patch or recommendation