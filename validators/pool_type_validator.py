#!/usr/bin/env python3
"""
Advisory validator for kernel-driver pool allocation intent.
"""

import re

from governance_tools.validator_interface import DomainValidator, ValidatorResult


class PoolTypeValidator(DomainValidator):
    LEGACY_ALLOCATORS = [
        "ExAllocatePoolWithTag",
        "ExAllocatePool",
    ]

    @property
    def rule_ids(self) -> list[str]:
        return ["kernel-driver", "KD-005"]

    def validate(self, payload: dict) -> ValidatorResult:
        checks = payload.get("checks", {})
        driver_code = (
            checks.get("driver_code")
            or checks.get("diff_text")
            or ""
        )
        matched_apis = []
        for api in self.LEGACY_ALLOCATORS:
            if re.search(rf"\b{re.escape(api)}\b", driver_code):
                matched_apis.append(api)
        warnings = [
            f"KD-POOL-001: '{api}' does not make pool intent explicit; prefer NonPagedPoolNx/PagedPool-aware allocation guidance"
            for api in matched_apis
        ]
        return ValidatorResult(
            ok=len(warnings) == 0,
            rule_ids=self.rule_ids,
            warnings=warnings,
            evidence_summary=f"Checked {len(self.LEGACY_ALLOCATORS)} legacy pool allocation APIs",
            metadata={"mode": "advisory"},
        )
