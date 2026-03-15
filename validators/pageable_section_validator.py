#!/usr/bin/env python3
"""
Advisory validator for pageable section annotation correctness.

Rules enforced:
  KD-008  paged-code-annotation

Checks:
  1. Functions annotated with #pragma alloc_text(PAGE, ...) must contain
     a PAGED_CODE() call at entry.
  2. Functions NOT in a PAGE section must not contain PAGED_CODE() if they
     are clearly dispatch-level (heuristic: contain KeAcquireSpinLock or
     are named with common non-pageable patterns).
  3. Raw 'PAGED_CODE()' without a matching alloc_text pragma is flagged as
     an annotation gap.

Limitations:
  - This validator operates on text snippets, not full compilation units.
  - Full correctness requires cross-file analysis; this validator is advisory.
"""

import re

from governance_tools.validator_interface import DomainValidator, ValidatorResult

_ALLOC_TEXT_PAGE = re.compile(
    r"#\s*pragma\s+alloc_text\s*\(\s*PAGE\s*,\s*(\w+)\s*\)", re.IGNORECASE
)
_FUNC_DEF = re.compile(
    r"\b(\w+)\s*\([^)]*\)\s*\{", re.MULTILINE
)
_PAGED_CODE_CALL = re.compile(r"\bPAGED_CODE\s*\(\s*\)")

# Patterns that indicate a clearly non-pageable context
_NONPAGEABLE_HINTS = re.compile(
    r"\b(KeAcquireSpinLock|KeRaiseIrql|DISPATCH_LEVEL|KeSynchronizeExecution)\b"
)

# Broad function-definition opener: captures the function name
_FUNC_OPENER = re.compile(
    r"""
    ^(?:[\w\s\*]+?)          # return type (non-greedy)
    \b(\w+)\s*               # function name (captured)
    \([^)]*\)                # parameter list
    (?:\s*\w+)*\s*           # optional SAL / calling-convention suffixes
    \{                       # opening brace
    """,
    re.VERBOSE | re.MULTILINE,
)


def _iter_function_bodies(code: str):
    """Yield (func_name, body_text) for each top-level function in code."""
    for m in _FUNC_OPENER.finditer(code):
        name = m.group(1)
        brace_start = m.end() - 1
        depth = 0
        for i, ch in enumerate(code[brace_start:], brace_start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    yield name, code[brace_start: i + 1]
                    break


def _functions_in_page_section(code: str) -> set[str]:
    return set(_ALLOC_TEXT_PAGE.findall(code))


def _has_paged_code_macro(func_body: str) -> bool:
    return bool(_PAGED_CODE_CALL.search(func_body))


def _extract_function_body(code: str, func_name: str) -> str | None:
    """
    Very naive brace-counting extraction for a named function.
    Returns the text from the opening '{' to the matching '}'.
    """
    pattern = re.compile(
        rf"\b{re.escape(func_name)}\b[^{{]*\{{", re.MULTILINE
    )
    m = pattern.search(code)
    if not m:
        return None
    start = m.end() - 1  # position of '{'
    depth = 0
    for i, ch in enumerate(code[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return code[start : i + 1]
    return None


class PageableSectionValidator(DomainValidator):

    @property
    def rule_ids(self) -> list[str]:
        return ["kernel-driver", "KD-008"]

    def validate(self, payload: dict) -> ValidatorResult:
        checks = payload.get("checks", {})
        code = (
            checks.get("driver_code")
            or checks.get("diff_text")
            or payload.get("driver_code")
            or ""
        )

        warnings: list[str] = []
        violations: list[str] = []

        paged_funcs = _functions_in_page_section(code)

        # Check 1: functions declared in PAGE section must have PAGED_CODE()
        for func in paged_funcs:
            body = _extract_function_body(code, func)
            if body is None:
                # Body not present in snippet — can't verify, skip silently
                continue
            if not _has_paged_code_macro(body):
                warnings.append(
                    f"KD-PAGE-001: '{func}' is in PAGE section (alloc_text) "
                    "but lacks PAGED_CODE() at entry"
                )

        # Check 2: PAGED_CODE() and non-pageable hints in the SAME function body.
        # Checking file-level causes false positives when pageable and
        # non-pageable functions coexist in the same translation unit.
        for func_name, body in _iter_function_bodies(code):
            if _PAGED_CODE_CALL.search(body) and _NONPAGEABLE_HINTS.search(body):
                violations.append(
                    f"KD-PAGE-002: '{func_name}' contains both PAGED_CODE() and "
                    "non-pageable IRQL hints (KeAcquireSpinLock / DISPATCH_LEVEL) "
                    "in the same function body. This will bugcheck at runtime."
                )

        # Check 3: PAGED_CODE() without any alloc_text(PAGE, ...) pragma in snippet
        if _PAGED_CODE_CALL.search(code) and not paged_funcs:
            warnings.append(
                "KD-PAGE-003: PAGED_CODE() found but no 'alloc_text(PAGE, ...)' "
                "pragma detected in this snippet; verify section placement"
            )

        return ValidatorResult(
            ok=len(violations) == 0,
            rule_ids=self.rule_ids,
            violations=violations,
            warnings=warnings,
            evidence_summary=(
                f"Pageable functions declared: {len(paged_funcs)}; "
                f"PAGED_CODE() present: {bool(_PAGED_CODE_CALL.search(code))}"
            ),
            metadata={"mode": "advisory"},
        )
