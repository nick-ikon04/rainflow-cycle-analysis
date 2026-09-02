"""Deterministic demonstration of two rainflow-counting modes.

This is the publication version of ``task_0.py`` from 2026-05-15.  The
calculation itself is preserved, while result export and a non-interactive CLI
were added so both modes can be reproduced in CI or from a terminal.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


METHODS = ("rainflow_4point", "rainflow_3point_demo")


def turning_points(signal: np.ndarray) -> np.ndarray:
    """Return turning-point indices, including both endpoints."""
    values = np.asarray(signal, dtype=float)
    derivative = np.diff(values)
    derivative[derivative == 0] = 1e-12
    sign_changes = np.diff(np.sign(derivative))
    indices = np.where(sign_changes != 0)[0] + 1
    return np.unique(np.r_[0, indices, len(values) - 1])


def rainflow_4point(tp_values, tp_indices=None):
    """Stack-based four-point rainflow count.

    Each record is ``(range, mean, count, start_index, end_index)``.  Closed
    cycles have count 1.0; residual cycles have count 0.5.
    """
    tp_values = np.asarray(tp_values, dtype=float)
    if tp_indices is None:
        tp_indices = np.arange(len(tp_values))

    stack_values: list[float] = []
    stack_indices: list[int] = []
    cycles: list[tuple[float, float, float, int, int]] = []

    def add_cycle(value_1, value_2, index_1, index_2, count):
        cycles.append(
            (
                abs(value_2 - value_1),
                0.5 * (value_1 + value_2),
                count,
                int(index_1),
                int(index_2),
            )
        )

    for value, index in zip(tp_values, tp_indices):
        stack_values.append(float(value))
        stack_indices.append(int(index))

        while len(stack_values) >= 4:
            a, b, c, d = stack_values[-4:]
            index_a, index_b, index_c, index_d = stack_indices[-4:]
            range_ab = abs(a - b)
            range_bc = abs(b - c)
            range_cd = abs(c - d)

            if range_bc <= range_ab and range_bc <= range_cd:
                count = 0.5 if len(stack_values) == 4 else 1.0
                add_cycle(b, c, index_b, index_c, count)
                del stack_values[-3:-1]
                del stack_indices[-3:-1]
            else:
                break

    for index in range(len(stack_values) - 1):
        add_cycle(
            stack_values[index],
            stack_values[index + 1],
            stack_indices[index],
            stack_indices[index + 1],
            0.5,
        )

    return cycles


def rainflow_3point_demo(tp_values, tp_indices=None):
    """Educational simplified three-point mode.

    This mode is included for comparison and is not claimed to be an ASTM
    E1049 reference implementation.
    """
    values = list(map(float, tp_values))
    indices = list(range(len(values))) if tp_indices is None else list(tp_indices)
    cycles: list[tuple[float, float, float, int, int]] = []

    def add_cycle(value_1, value_2, index_1, index_2, count):
        cycles.append(
            (
                abs(value_2 - value_1),
                0.5 * (value_1 + value_2),
                count,
                int(index_1),
                int(index_2),
            )
        )

    changed = True
    while changed and len(values) >= 3:
        changed = False
        position = 0
        while position <= len(values) - 3:
            x_value, y_value, z_value = values[position : position + 3]
            x_index, y_index, z_index = indices[position : position + 3]
            if abs(x_value - y_value) <= abs(y_value - z_value):
                add_cycle(x_value, y_value, x_index, y_index, 1.0)
                del values[position : position + 2]
                del indices[position : position + 2]
                changed = True
                position = max(position - 1, 0)
            else:
                position += 1

    for position in range(len(values) - 1):
        add_cycle(
            values[position],
            values[position + 1],
            indices[position],
            indices[position + 1],
            0.5,
        )
    return cycles


def build_rainflow_intervals(cycles):
    """Convert cycle tuples to unique interval records."""
    unique = {}
    for cycle_range, mean, count, start_index, end_index in cycles:
        left = int(min(start_index, end_index))
        right = int(max(start_index, end_index))
        duration = right - left
        if duration < 2:
            continue
        key = (left, right, float(count))
        record = {
            "start": left,
            "end": right,
            "duration": duration,
            "range": float(cycle_range),
            "mean": float(mean),
            "count": float(count),
        }
        if key not in unique or record["range"] > unique[key]["range"]:
            unique[key] = record
    return list(unique.values())


def select_non_overlapping_max_intervals(intervals):
    """Select longest non-overlapping intervals and return them by start."""
    ordered = sorted(
        intervals,
        key=lambda item: (item["duration"], item["range"], item["count"]),
        reverse=True,
    )
    selected = []
    for candidate in ordered:
        intersects = any(
            not (
                candidate["end"] <= current["start"]
                or candidate["start"] >= current["end"]
            )
            for current in selected
        )
        if not intersects:
            selected.append(candidate)
    return sorted(selected, key=lambda item: item["start"])


def generate_variable_saw_signal(cycle_lengths, seed=11, noise_std=0.009):
    """Build a deterministic noisy sawtooth signal."""
    random = np.random.default_rng(seed)
    parts = []
    for length in cycle_lengths:
        time = np.arange(length, dtype=float) / length
        amplitude = 1.0 + random.uniform(-0.08, 0.08)
        offset = random.uniform(-0.03, 0.03)
        segment = offset + amplitude * time
        segment += random.normal(0.0, noise_std, size=length)
        parts.append(segment)
    return np.concatenate(parts)


def plot_selected_intervals(signal, selected_intervals, output_path: Path):
    """Save a chart of selected intervals."""
    x_values = np.arange(len(signal))
    fig, axis = plt.subplots(figsize=(14, 6))
    axis.plot(x_values, signal, color="0.7", lw=1.2, label="Signal")
    axis.scatter(x_values, signal, s=7, color="0.55", alpha=0.35, label="Samples")
    colors = plt.get_cmap("tab20")
    y_span = float(signal.max() - signal.min())

    for rank, interval in enumerate(selected_intervals, start=1):
        color = colors((rank - 1) % 20)
        interval_slice = slice(interval["start"], interval["end"])
        cycle_kind = "full" if interval["count"] == 1.0 else "half"
        axis.axvspan(
            interval["start"], interval["end"], color=color, alpha=0.18, ec=color
        )
        axis.plot(
            x_values[interval_slice],
            signal[interval_slice],
            color=color,
            lw=2.8,
            label=f"#{rank}: {cycle_kind}, length={interval['duration']}",
        )
        midpoint = (interval["start"] + interval["end"]) // 2
        y_position = np.max(signal[interval_slice]) + 0.04 * y_span
        axis.text(midpoint, y_position, f"#{rank}", color=color, ha="center", weight="bold")

    axis.set(
        title="Sawtooth signal: maximum non-overlapping rainflow intervals",
        xlabel="Sample index",
        ylabel="Amplitude",
    )
    axis.grid(alpha=0.25)
    axis.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def run_analysis(method: str, output_dir: Path):
    """Run one method and save the summary, cycles, intervals and chart."""
    if method not in METHODS:
        raise ValueError(f"Unknown method: {method}")

    cycle_lengths = [58, 60, 56, 124, 59, 57, 146, 61, 55, 132, 58, 149, 60]
    signal = generate_variable_saw_signal(cycle_lengths)
    turning_point_indices = turning_points(signal)
    method_function = rainflow_4point if method == "rainflow_4point" else rainflow_3point_demo
    cycles = method_function(signal[turning_point_indices], turning_point_indices)
    intervals = build_rainflow_intervals(cycles)
    selected = select_non_overlapping_max_intervals(intervals)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "method": method,
        "signal_samples": int(len(signal)),
        "turning_points": int(len(turning_point_indices)),
        "rainflow_cycles": int(len(cycles)),
        "equivalent_cycles": float(sum(cycle[2] for cycle in cycles)),
        "selected_non_overlapping_intervals": int(len(selected)),
        "seed": 11,
        "noise_std": 0.009,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with (output_dir / "cycles.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["range", "mean", "count", "start", "end"])
        writer.writerows(cycles)

    with (output_dir / "selected_intervals.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=["start", "end", "duration", "range", "mean", "count"]
        )
        writer.writeheader()
        writer.writerows(selected)

    plot_selected_intervals(signal, selected, output_dir / "selected_intervals.png")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary, cycles, selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", choices=METHODS, default="rainflow_4point")
    parser.add_argument("--output-dir", type=Path, default=None)
    arguments = parser.parse_args()
    output_dir = arguments.output_dir or Path("results") / arguments.method
    run_analysis(arguments.method, output_dir)


if __name__ == "__main__":
    main()
