#!/usr/bin/env python3
"""
Precision measurement for scan_source.py callback role classification.

Two measurement phases:
  A. Extraction Coverage  — did the scanner find all functions that have ground truth?
  B. Classification Quality — for found functions, did it assign the right label?

Usage:
  python check_precision.py <source_file> <ground_truth_json> [--wdf-dirs dir ...]
  python check_precision.py --batch ground_truth/*.json [--wdf-dirs dir ...]

Output format:
  === Phase A: Extraction Coverage ===
  Found 9/11 ground-truth functions (81.8%)
  Missing (2): NICEvtInterruptEnable, NICEvtInterruptDisable

  === Phase B: Classification Quality (found functions only) ===
  Correct: 7/9 (77.8%)
  Misclassified (2):
    NICEvtInterruptEnable  expected=isr  got=other
    NICEvtInterruptDisable expected=isr  got=other

  Per-label metrics (precision / recall):
    isr       P=1.00  R=0.33  (TP=1 FP=0 FN=2)
    dpc       P=1.00  R=1.00  (TP=3 FP=0 FN=0)
    dispatch  P=1.00  R=1.00  (TP=3 FP=0 FN=0)
    other     P=0.83  R=1.00  (TP=5 FP=2 FN=0)
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Import scanner
# ---------------------------------------------------------------------------
try:
    import scan_source
except ImportError:
    print("ERROR: scan_source.py not found in current directory", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Scanner invocation
# ---------------------------------------------------------------------------

def _run_scanner(source_path: Path, wdf_dirs: list[Path]) -> dict:
    """
    Run scan_source on source_path and return the payload dict.
    wdf_dirs provides additional directories to build the WDF registry from.
    """
    # Build WDF registry from wdf_dirs (cross-file KMDF callback resolution)
    registry = {}
    search_dirs = list(wdf_dirs) + [source_path.parent]
    for d in search_dirs:
        if d.is_dir():
            sources = list(d.glob("**/*.h")) + list(d.glob("**/*.c"))
            registry.update(scan_source._build_wdf_registry(sources))

    analysis = scan_source._analyse_file(source_path, wdf_registry=registry)
    payload = scan_source.build_payload(analysis)
    return payload


def _get_classified_functions(payload: dict) -> dict[str, str]:
    """Return {func_name: label} from payload's classified_functions field."""
    classified = payload.get("classified_functions", {})
    result = {}
    for label, names in classified.items():
        for name in names:
            result[name] = label
    return result


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

def _measure(
    source_path: Path,
    ground_truth: dict,
    wdf_dirs: list[Path],
) -> dict:
    """
    Run scanner and compare against ground truth.
    Returns a structured result dict.
    """
    payload = _run_scanner(source_path, wdf_dirs)
    scanned: dict[str, str] = _get_classified_functions(payload)

    gt_functions: dict[str, dict] = ground_truth.get("functions", {})

    # --- Phase A: Extraction Coverage ---
    found = [fn for fn in gt_functions if fn in scanned]
    missing = [fn for fn in gt_functions if fn not in scanned]

    # --- Phase B: Classification Quality (found functions only) ---
    correct = []
    misclassified = []  # list of (func, expected, got)

    for fn in found:
        expected = gt_functions[fn]["label"]
        got = scanned[fn]
        if expected == got:
            correct.append(fn)
        else:
            misclassified.append((fn, expected, got))

    # --- Per-label metrics ---
    all_labels = sorted({gt_functions[fn]["label"] for fn in gt_functions})

    label_metrics: dict[str, dict] = {}
    for label in all_labels:
        # TP: found and correctly classified as this label
        tp = sum(1 for fn in found if gt_functions[fn]["label"] == label and scanned[fn] == label)
        # FP: scanned says this label, but ground truth differs (for found GT functions)
        fp = sum(1 for fn in found if scanned[fn] == label and gt_functions[fn]["label"] != label)
        # FN: ground truth is this label, but scanner got it wrong or missed it
        fn_count = sum(
            1 for fn in gt_functions
            if gt_functions[fn]["label"] == label and (fn not in scanned or scanned[fn] != label)
        )
        precision = tp / (tp + fp) if (tp + fp) > 0 else None
        recall = tp / (tp + fn_count) if (tp + fn_count) > 0 else None
        label_metrics[label] = {
            "tp": tp, "fp": fp, "fn": fn_count,
            "precision": precision,
            "recall": recall,
        }

    return {
        "source": str(source_path),
        "scope": ground_truth.get("scope", ""),
        "phase_a": {
            "gt_total": len(gt_functions),
            "found": len(found),
            "missing": missing,
            "coverage": len(found) / len(gt_functions) if gt_functions else 1.0,
        },
        "phase_b": {
            "found_total": len(found),
            "correct": len(correct),
            "misclassified": misclassified,
            "accuracy": len(correct) / len(found) if found else 1.0,
        },
        "per_label": label_metrics,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _fmt_opt(value) -> str:
    if value is None:
        return "  N/A"
    return f"{value:.2f}"


def _print_result(result: dict, verbose: bool = False) -> bool:
    """Print human-readable report. Returns True if all checks pass."""
    source = result["source"]
    scope = result["scope"]
    pa = result["phase_a"]
    pb = result["phase_b"]
    pl = result["per_label"]

    print(f"\n{'=' * 60}")
    print(f"File:  {source}")
    if scope:
        print(f"Scope: {scope}")
    print(f"{'=' * 60}")

    # Phase A
    print(f"\n--- Phase A: Extraction Coverage ---")
    print(f"  Found {pa['found']}/{pa['gt_total']} ground-truth functions ({_fmt_pct(pa['coverage'])})")
    if pa["missing"]:
        print(f"  Missing ({len(pa['missing'])}): {', '.join(pa['missing'])}")

    # Phase B
    print(f"\n--- Phase B: Classification Quality (found functions only) ---")
    if pb["found_total"] == 0:
        print("  No found functions to evaluate.")
    else:
        print(f"  Correct: {pb['correct']}/{pb['found_total']} ({_fmt_pct(pb['accuracy'])})")
        if pb["misclassified"]:
            print(f"  Misclassified ({len(pb['misclassified'])}):")
            for fn, expected, got in pb["misclassified"]:
                print(f"    {fn:<45} expected={expected:<10} got={got}")

    # Per-label
    print(f"\n--- Per-label Metrics ---")
    header = f"  {'Label':<12}  {'Prec':>6}  {'Recall':>6}  TP  FP  FN"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for label, m in sorted(pl.items()):
        print(
            f"  {label:<12}  {_fmt_opt(m['precision']):>6}  {_fmt_opt(m['recall']):>6}"
            f"  {m['tp']:>2}  {m['fp']:>2}  {m['fn']:>2}"
        )

    all_pass = (pa["coverage"] == 1.0 and pb["accuracy"] == 1.0)
    status = "PASS" if all_pass else "FAIL"
    print(f"\n  Overall: {status}")
    return all_pass


def _print_batch_summary(results: list[dict]) -> None:
    """Print aggregate numbers across all files."""
    total_gt = sum(r["phase_a"]["gt_total"] for r in results)
    total_found = sum(r["phase_a"]["found"] for r in results)
    total_correct = sum(r["phase_b"]["correct"] for r in results)

    # Aggregate per-label across all files
    agg: dict[str, dict] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for r in results:
        for label, m in r["per_label"].items():
            agg[label]["tp"] += m["tp"]
            agg[label]["fp"] += m["fp"]
            agg[label]["fn"] += m["fn"]

    print(f"\n{'=' * 60}")
    print("BATCH SUMMARY")
    print(f"{'=' * 60}")
    cov = total_found / total_gt if total_gt else 1.0
    acc = total_correct / total_found if total_found else 1.0
    print(f"  Extraction coverage:      {total_found}/{total_gt} ({_fmt_pct(cov)})")
    print(f"  Classification accuracy:  {total_correct}/{total_found} ({_fmt_pct(acc)})")
    print(f"\n  Aggregate per-label:")
    header = f"    {'Label':<12}  {'Prec':>6}  {'Recall':>6}  TP  FP  FN"
    print(header)
    print("    " + "-" * (len(header) - 4))
    for label, m in sorted(agg.items()):
        tp, fp, fn = m["tp"], m["fp"], m["fn"]
        p = tp / (tp + fp) if (tp + fp) > 0 else None
        r = tp / (tp + fn) if (tp + fn) > 0 else None
        print(
            f"    {label:<12}  {_fmt_opt(p):>6}  {_fmt_opt(r):>6}"
            f"  {tp:>2}  {fp:>2}  {fn:>2}"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source", nargs="?", help="Source .c/.h file to scan")
    p.add_argument("ground_truth", nargs="?", help="Ground truth JSON file")
    p.add_argument(
        "--batch",
        metavar="GT_JSON",
        nargs="+",
        help="Run against multiple ground truth files (source path taken from 'source' field in JSON)",
    )
    p.add_argument(
        "--wdf-dirs",
        metavar="DIR",
        nargs="+",
        default=[],
        help="Additional directories to scan for WDF forward declarations",
    )
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON result")
    p.add_argument("--verbose", action="store_true", help="Show per-function detail")
    return p.parse_args()


def main():
    args = _parse_args()
    wdf_dirs = [Path(d) for d in args.wdf_dirs]

    results = []

    if args.batch:
        for gt_path_str in args.batch:
            gt_path = Path(gt_path_str)
            gt = json.loads(gt_path.read_text())
            # Source path is relative to repo root (where this script lives)
            source_path = Path(gt["source"])
            if not source_path.exists():
                print(f"SKIP: {source_path} not found", file=sys.stderr)
                continue
            result = _measure(source_path, gt, wdf_dirs)
            results.append(result)
    else:
        if not args.source or not args.ground_truth:
            print("ERROR: provide <source> and <ground_truth>, or use --batch", file=sys.stderr)
            sys.exit(1)
        gt = json.loads(Path(args.ground_truth).read_text())
        result = _measure(Path(args.source), gt, wdf_dirs)
        results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    all_pass = True
    for r in results:
        ok = _print_result(r, verbose=args.verbose)
        all_pass = all_pass and ok

    if len(results) > 1:
        _print_batch_summary(results)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
