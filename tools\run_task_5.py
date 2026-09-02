"""Run the original task_5 visualization and save reproducible artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

import task_5  # noqa: E402


def source_peaks_and_valleys():
    source_values = [2, -14, 10, 0, 13, -9, 11, -8, 8, -9, 15, -4, 10, 0, 13, 0]
    negated = [-value for value in source_values]
    source_points = list(enumerate(negated[1:], start=2))
    return source_points[0::2], source_points[1::2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPOSITORY_ROOT / "results" / "task_5",
    )
    arguments = parser.parse_args()
    arguments.output_dir.mkdir(parents=True, exist_ok=True)

    output_figure = arguments.output_dir / "rainfall_flow_visualization.png"

    def save_current_figure():
        figure = plt.gcf()
        figure.set_size_inches(14, 8)
        figure.tight_layout()
        figure.savefig(output_figure, dpi=160)
        plt.close(figure)

    original_show = plt.show
    plt.show = save_current_figure
    try:
        task_5.main()
    finally:
        plt.show = original_show

    peaks, valleys = source_peaks_and_valleys()
    processed = task_5.process_peaks(peaks, valleys)
    case_counts = Counter(case_name for case_name, _ in processed)
    summary = {
        "implementation": "task_5.py",
        "input_points": 15,
        "starting_peaks": len(peaks),
        "valleys": len(valleys),
        "generated_flows": len(processed),
        "termination_cases": dict(sorted(case_counts.items())),
    }
    (arguments.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
