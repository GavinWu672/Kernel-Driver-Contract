#!/usr/bin/env python3
"""
Hard-stop validator for synchronization primitive IRQL mismatches.

Rules enforced:
  KD-006  sync-primitive-irql

IRQL requirements:
  PASSIVE_LEVEL only : KeWaitForMutexObject, ExAcquireFastMutex,
                       ExAcquireFastMutexUnsafe, ExReleaseFastMutex,
                       ExReleaseFastMutexUnsafe
  <= APC_LEVEL       : ExAcquirePushLockExclusive, ExAcquirePushLockShared,
                       ExReleasePushLock*, KeWaitForSingleObject (with mutex),
                       KeReleaseMutex
  DISPATCH_LEVEL     : KeAcquireSpinLock, KeReleaseSpinLock (correct at DISPATCH)

Violations detected in dispatch-level / DPC / ISR code paths:
  - PASSIVE_LEVEL-only mutex APIs
  - APC_LEVEL-only push-lock APIs
  - ExAcquireFastMutex family at DISPATCH_LEVEL
"""

import re

from governance_tools.validator_interface import DomainValidator, ValidatorResult

# APIs that require PASSIVE_LEVEL — illegal at DISPATCH_LEVEL or in DPC/ISR
_PASSIVE_ONLY = [
    "KeWaitForMutexObject",
    "ExAcquireFastMutex",
    "ExAcquireFastMutexUnsafe",
    "ExReleaseFastMutex",
    "ExReleaseFastMutexUnsafe",
]

# APIs that require <= APC_LEVEL — illegal at DISPATCH_LEVEL or in DPC/ISR
_APC_ONLY = [
    "ExAcquirePushLockExclusive",
    "ExAcquirePushLockShared",
    "ExReleasePushLockExclusive",
    "ExReleasePushLockShared",
    "ExReleasePushLock",
    "KeReleaseMutex",
]

_ALL_FORBIDDEN = _PASSIVE_ONLY + _APC_ONLY

_IRQL_TAG_PATTERNS = [
    # explicit IRQL comment hints in the code snippet
    re.compile(r"DISPATCH_LEVEL", re.IGNORECASE),
    re.compile(r"KIRQL\s+\w+\s*=\s*DISPATCH_LEVEL", re.IGNORECASE),
    re.compile(r"KeRaiseIrql\s*\(", re.IGNORECASE),
    re.compile(r"KeAcquireSpinLock", re.IGNORECASE),
]


def _is_dispatch_context(code: str) -> bool:
    """Heuristic: returns True if the snippet appears to run at DISPATCH_LEVEL."""
    return any(p.search(code) for p in _IRQL_TAG_PATTERNS)


class SyncPrimitiveValidator(DomainValidator):

    @property
    def rule_ids(self) -> list[str]:
        return ["kernel-driver", "KD-006"]

    def validate(self, payload: dict) -> ValidatorResult:
        checks = payload.get("checks", {})
        code = (
            payload.get("dispatch_level_code")
            or payload.get("dpc_code")
            or checks.get("dispatch_level_code")
            or checks.get("dpc_code")
            or checks.get("driver_code")
            or checks.get("diff_text")
            or ""
        )

        # Only flag when we have evidence of a DISPATCH_LEVEL or higher context,
        # OR when the payload explicitly carries a dispatch/dpc code key.
        in_dispatch = (
            "dispatch_level_code" in payload
            or "dispatch_level_code" in checks
            or "dpc_code" in payload
            or "dpc_code" in checks
            or _is_dispatch_context(code)
        )

        violations: list[str] = []
        warnings: list[str] = []

        for api in _ALL_FORBIDDEN:
            if re.search(rf"\b{re.escape(api)}\b", code):
                level = "PASSIVE_LEVEL" if api in _PASSIVE_ONLY else "APC_LEVEL"
                msg = (
                    f"KD-SYNC-001: '{api}' requires <= {level} "
                    f"but was detected in a DISPATCH_LEVEL context"
                )
                if in_dispatch:
                    violations.append(msg)
                else:
                    warnings.append(
                        f"KD-SYNC-002: '{api}' requires <= {level}; "
                        "verify IRQL at call site"
                    )

        return ValidatorResult(
            ok=len(violations) == 0,
            rule_ids=self.rule_ids,
            violations=violations,
            warnings=warnings,
            evidence_summary=(
                f"Checked {len(_ALL_FORBIDDEN)} sync primitives; "
                f"dispatch context={'yes' if in_dispatch else 'unknown'}"
            ),
            metadata={"mode": "hard-stop" if in_dispatch else "advisory"},
        )
