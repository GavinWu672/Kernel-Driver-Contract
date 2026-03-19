# Kernel Driver Contract 1.0 Alpha Gate

## Purpose

This file defines the minimum release gate for calling `Kernel-Driver-Contract` a credible `1.0 alpha`.

The goal is not perfection. The goal is a reviewable early-release bar with:

- one real adopter path
- real lifecycle facts
- real verifier evidence
- a clear v1 scope boundary

## Current Judgment

- Current state: `controlled pilot candidate`
- Not yet ready to call `1.0 alpha`

## Alpha Exit Criteria

All items in this section should be complete before changing the repo status to `1.0 alpha`.

### 1. Real Driver Intake

- [ ] One real pure-KMDF driver repository has been connected through the contract workflow.
- [ ] `SOURCE_INVENTORY.md` contains concrete artifact paths from that repo.
- [ ] Human-mandatory facts are resolved for the pilot repo.
- [ ] AI-verifiable facts are surfaced with source locations rather than hidden assumptions.
- [ ] Confirmed facts are promoted into `KERNEL_DRIVER_CHECKLIST.md` and durable memory artifacts.

### 2. Real Validation Evidence

- [ ] At least one real Driver Verifier artifact is recorded.
- [ ] At least one real SDV or WDK diagnostics artifact is recorded.
- [ ] Validation evidence is referenced from `memory/04_validation_log.md`.
- [ ] The evidence is tied to the same pilot repo used for fact intake.

### 3. Real Task Replay

- [ ] One real coding or review task has been run against actual driver code rather than only fixtures.
- [ ] The recorded response shows use of fact ownership reasoning.
- [ ] The recorded response cites relevant `KSTATE-*` and/or `KD-*` rules where applicable.
- [ ] The replay leaves a reviewer-readable trail of what was blocked, inferred, and still unverified.

### 4. Release-Facing Scope

- [ ] README and STATUS clearly say `KMDF-first`.
- [ ] README and STATUS clearly say WDM function-pointer cast support is out of scope for v1.
- [ ] Accepted alpha limitations are listed explicitly.
- [ ] The Microsoft-guide lineage note remains visible without overstating equivalence to official standards.

### 5. Adoption Surface

- [ ] Pre-commit / hook guidance is usable by an adopter repo.
- [ ] Contract loading and runtime bootstrap remain reproducible.
- [ ] The repo can be handed to a reviewer without private verbal context.

## Accepted Alpha Limitations

These are allowed in `1.0 alpha` if all exit criteria above are satisfied.

- WDM function-pointer cast blind spot remains v2 work.
- Spinlock heuristic false positives remain documented for legacy NDIS-heritage KMDF patterns.
- Deeper AST or dataflow analysis remains out of scope.
- The repo is still an early governance contract, not a certification-ready driver validation stack.

## Current Blockers

- [ ] No real driver project facts have been promoted from an adopter repo.
- [ ] No real Driver Verifier evidence has been recorded.
- [ ] No real SDV or WDK diagnostics have been recorded.
- [ ] No real adopter-task replay has been documented as evidence.

## Recommended Next Sequence

1. Connect one real pure-KMDF driver repo.
2. Complete human-mandatory fact intake first.
3. Ingest one real verifier or SDV artifact.
4. Run one real task replay and preserve the review trail.
5. Re-evaluate `STATUS.md` after the evidence is recorded.
