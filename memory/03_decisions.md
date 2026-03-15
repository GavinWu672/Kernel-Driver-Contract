# Decisions

## Accepted Decisions

- The repository remains documentation-first.
- The repository must also remain consumable as an external domain contract for `ai-governance-framework`.
- Kernel-driver validation starts advisory-first at the domain-validator layer even when individual rules are conceptually stronger.
- The first maturity target is a stable low-level governance seam, not a full driver-analysis platform.

## Pending Decisions

- Whether IRQL annotations should become a hard requirement or remain advisory at the contract level
- Which real driver repository should be used as the first fact-intake target

## 2026-03-15

- `KD-002` and `KD-003` are now recorded as `hard_stop_rules` in `contract.yaml`
  so framework-side enforcement routing can treat IRQL misuse as a blocking outcome.
- Pool allocation guidance remains advisory for now, so `KD-005` is intentionally left out of `hard_stop_rules`.
