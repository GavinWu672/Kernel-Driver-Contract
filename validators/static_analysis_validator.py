#!/usr/bin/env python3
"""
Hard-stop validator that parses Driver Verifier, SDV, and WDK/SAL
static-analysis output from the fixture payload.

Rules enforced:
  KD-010  static-analysis-clean

Input contract (payload keys searched in order):
  payload["static_analysis"]        — dict or list (preferred structured form)
  payload["diagnostics"]            — list[str] (legacy text lines)
  payload["checks"]["diagnostics"]  — list[str] (checks sub-object)
  payload["checks"]["diff_text"]    — free-text fallback

Structured form (payload["static_analysis"]):
  {
    "driver_verifier": {
      "defects": [...],          # list of defect strings; empty = clean
      "passed": true/false
    },
    "sdv": {
      "rule_violations": [...],  # list of violated SDV rule names
      "passed": true/false
    },
    "sal": {
      "warnings": [...],         # list of SAL warning strings
      "passed": true/false
    }
  }

Text form (payload["diagnostics"] or checks["diagnostics"]):
  Each string is scanned for failure keywords; passing strings are ignored.

Failure keywords (case-insensitive):
  "defect", "violation", "failed", "error", "bugcheck", "assertion failed",
  "rule violation", "sal warning", "c28", "c26"
"""

import re
from typing import Any

from governance_tools.validator_interface import DomainValidator, ValidatorResult

_FAILURE_PATTERNS = re.compile(
    r"\b(defect|violation|failed|error|bugcheck|assertion\s+failed|"
    r"rule\s+violation|sal\s+warning|C28\d+|C26\d+)\b",
    re.IGNORECASE,
)

# Lines that mention "passed" without failure keywords are treated as clean
_PASS_PATTERN = re.compile(r"\bpassed\b", re.IGNORECASE)


def _scan_text_lines(lines: list[str]) -> list[str]:
    """Return violation strings from a list of diagnostic text lines."""
    found: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if _FAILURE_PATTERNS.search(line):
            found.append(f"KD-SA-001: Static analysis defect: {line}")
    return found


def _parse_structured(sa: dict[str, Any]) -> list[str]:
    """Parse the structured static_analysis dict."""
    violations: list[str] = []

    # Driver Verifier
    dv = sa.get("driver_verifier", {})
    if not dv.get("passed", True):
        for d in dv.get("defects", []):
            violations.append(f"KD-SA-002: Driver Verifier defect: {d}")
        if not dv.get("defects"):
            violations.append("KD-SA-002: Driver Verifier reported failure (no defect list)")

    # SDV
    sdv = sa.get("sdv", {})
    if not sdv.get("passed", True):
        for r in sdv.get("rule_violations", []):
            violations.append(f"KD-SA-003: SDV rule violation: {r}")
        if not sdv.get("rule_violations"):
            violations.append("KD-SA-003: SDV reported failure (no rule list)")

    # SAL / WDK annotation analysis
    sal = sa.get("sal", {})
    if not sal.get("passed", True):
        for w in sal.get("warnings", []):
            violations.append(f"KD-SA-004: SAL/WDK warning: {w}")
        if not sal.get("warnings"):
            violations.append("KD-SA-004: SAL analysis reported failure (no warning list)")

    return violations


class StaticAnalysisValidator(DomainValidator):

    @property
    def rule_ids(self) -> list[str]:
        return ["kernel-driver", "KD-010"]

    def validate(self, payload: dict) -> ValidatorResult:
        checks = payload.get("checks", {})
        violations: list[str] = []

        # --- Structured form (highest priority) ---
        if "static_analysis" in payload:
            violations.extend(_parse_structured(payload["static_analysis"]))

        # --- Text diagnostics list ---
        diag_lines: list[str] = (
            payload.get("diagnostics")
            or checks.get("diagnostics")
            or []
        )
        if isinstance(diag_lines, list):
            violations.extend(_scan_text_lines(diag_lines))

        # --- Free-text fallback in diff_text ---
        diff = checks.get("diff_text", "")
        if diff and not diag_lines and "static_analysis" not in payload:
            violations.extend(_scan_text_lines(diff.splitlines()))

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_violations: list[str] = []
        for v in violations:
            if v not in seen:
                seen.add(v)
                unique_violations.append(v)

        has_any_sa_input = bool(
            "static_analysis" in payload or diag_lines or diff
        )

        warnings: list[str] = []
        if not has_any_sa_input:
            warnings.append(
                "KD-SA-005: No static analysis output provided "
                "(Driver Verifier / SDV / SAL); KD-010 cannot be verified"
            )

        return ValidatorResult(
            ok=len(unique_violations) == 0,
            rule_ids=self.rule_ids,
            violations=unique_violations,
            warnings=warnings,
            evidence_summary=(
                "Static analysis inputs: "
                f"structured={'yes' if 'static_analysis' in payload else 'no'}, "
                f"diagnostics={len(diag_lines)} lines"
            ),
            metadata={"mode": "hard-stop"},
        )
