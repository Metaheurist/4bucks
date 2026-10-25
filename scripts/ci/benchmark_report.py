#!/usr/bin/env python3
"""Render pytest-benchmark JSON as a Markdown table and optionally gate on regressions.

Usage:
  python scripts/ci/benchmark_report.py --current bench.json [--baseline base.json]
                                        [--max-ratio 3.0] [--summary PATH] [--fail-on-regression]

A benchmark regresses when its mean is more than --max-ratio times the baseline mean.
Shared CI runners are noisy, so the default ratio is deliberately loose: it catches
algorithmic slowdowns, not single-digit percentage drift.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def load_means(path: Path) -> dict[str, float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {b["name"]: float(b["stats"]["mean"]) for b in data.get("benchmarks", [])}


def fmt_us(seconds: float) -> str:
    return f"{seconds * 1e6:,.1f} us"


def build_report(
    current: dict[str, float],
    baseline: dict[str, float] | None,
    max_ratio: float,
) -> tuple[str, list[str]]:
    regressions: list[str] = []
    lines = ["## Benchmark results", ""]
    if baseline is None:
        lines += [
            "_No baseline from `main` yet - showing absolute timings only._",
            "",
            "| Benchmark | Mean |",
            "|-----------|------|",
        ]
        for name in sorted(current):
            lines.append(f"| `{name}` | {fmt_us(current[name])} |")
        return "\n".join(lines) + "\n", regressions

    lines += [
        f"Compared with the latest `main` baseline. Regression gate: mean > **{max_ratio:g}x** baseline.",
        "",
        "| Benchmark | Mean | Baseline | Ratio | Status |",
        "|-----------|------|----------|-------|--------|",
    ]
    for name in sorted(current):
        cur = current[name]
        base = baseline.get(name)
        if base is None or base <= 0:
            lines.append(f"| `{name}` | {fmt_us(cur)} | - | - | new |")
            continue
        ratio = cur / base
        if ratio > max_ratio:
            status = "REGRESSION"
            regressions.append(f"{name}: {ratio:.2f}x baseline")
        elif ratio < 0.8:
            status = "faster"
        else:
            status = "ok"
        lines.append(f"| `{name}` | {fmt_us(cur)} | {fmt_us(base)} | {ratio:.2f}x | {status} |")
    return "\n".join(lines) + "\n", regressions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--max-ratio", type=float, default=3.0)
    parser.add_argument("--summary", type=Path, help="Append Markdown here (defaults to $GITHUB_STEP_SUMMARY)")
    parser.add_argument("--fail-on-regression", action="store_true")
    args = parser.parse_args()

    current = load_means(args.current)
    baseline = load_means(args.baseline) if args.baseline and args.baseline.is_file() else None
    report, regressions = build_report(current, baseline, args.max_ratio)
    print(report)

    summary = args.summary or (Path(os.environ["GITHUB_STEP_SUMMARY"]) if os.environ.get("GITHUB_STEP_SUMMARY") else None)
    if summary:
        with summary.open("a", encoding="utf-8") as fh:
            fh.write(report)

    if regressions:
        print("Regressions:\n  " + "\n  ".join(regressions), file=sys.stderr)
        if args.fail_on_regression:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
