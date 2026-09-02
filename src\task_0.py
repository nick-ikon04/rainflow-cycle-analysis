import argparse
import numpy as np
import matplotlib.pyplot as plt


def turning_points(x):
    """
    Return indices of turning points (local maxima/minima) + endpoints.
    Basic derivative sign-change method.
    """
    x = np.asarray(x)
    dx = np.diff(x)

    # Remove flat segments by nudging zeros (simple approach)
    dx2 = dx.copy()
    dx2[dx2 == 0] = 1e-12

    sign = np.sign(dx2)
    sdiff = np.diff(sign)

    # Turning points where sign changes
    idx = np.where(sdiff != 0)[0] + 1

    # Include endpoints
    idx = np.unique(np.r_[0, idx, len(x) - 1])
    return idx


def rainflow_4point(tp_values, tp_indices=None):
    """
    Stack-based 4-point rainflow.
    Returns list of cycles: (range, mean, count, i_start, i_end)
    count = 1.0 for full cycle, 0.5 for half cycle
    """
    tp_values = np.asarray(tp_values, dtype=float)
    if tp_indices is None:
        tp_indices = np.arange(len(tp_values))

    stack_v = []
    stack_i = []
    cycles = []

    def add_cycle(v1, v2, i1, i2, count):
        rng = abs(v2 - v1)
        mean = 0.5 * (v1 + v2)
        cycles.append((rng, mean, count, i1, i2))

    for v, idx in zip(tp_values, tp_indices):
        stack_v.append(v)
        stack_i.append(idx)

        # Try to close cycles while possible
        while len(stack_v) >= 4:
            A, B, C, D = stack_v[-4], stack_v[-3], stack_v[-2], stack_v[-1]
            iA, iB, iC, iD = stack_i[-4], stack_i[-3], stack_i[-2], stack_i[-1]

            R_AB = abs(A - B)
            R_BC = abs(B - C)
            R_CD = abs(C - D)

            # If the inner range is not bigger than both adjacent ranges -> closed cycle
            if (R_BC <= R_AB) and (R_BC <= R_CD):
                # If B-C touches the beginning of the stack, count as half-cycle
                count = 0.5 if len(stack_v) == 4 else 1.0
                add_cycle(B, C, iB, iC, count)

                # Remove B and C
                del stack_v[-3:-1]
                del stack_i[-3:-1]
            else:
                break

    # Residual half cycles from remaining stack
    for k in range(len(stack_v) - 1):
        add_cycle(stack_v[k], stack_v[k + 1], stack_i[k], stack_i[k + 1], 0.5)

    return cycles


def rainflow_3point_demo(tp_values, tp_indices=None):
    """
    Educational simplified 3-point approach.
    """
    tp_values = list(map(float, tp_values))
    if tp_indices is None:
        tp_indices = list(range(len(tp_values)))
    else:
        tp_indices = list(tp_indices)

    cycles = []

    def add_cycle(v1, v2, i1, i2, count):
        rng = abs(v2 - v1)
        mean = 0.5 * (v1 + v2)
        cycles.append((rng, mean, count, i1, i2))

    changed = True
    while changed and len(tp_values) >= 3:
        changed = False
        j = 0
        while j <= len(tp_values) - 3:
            X, Y, Z = tp_values[j], tp_values[j + 1], tp_values[j + 2]
            iX, iY, iZ = tp_indices[j], tp_indices[j + 1], tp_indices[j + 2]

            R_XY = abs(X - Y)
            R_YZ = abs(Y - Z)

            if R_XY <= R_YZ:
                add_cycle(X, Y, iX, iY, 1.0)

                # Remove X and Y, keep Z as new neighbor
                del tp_values[j:j + 2]
                del tp_indices[j:j + 2]
                changed = True

                # Step back to re-check neighborhood
                j = max(j - 1, 0)
            else:
                j += 1

    # Residual half cycles
    for k in range(len(tp_values) - 1):
        add_cycle(tp_values[k], tp_values[k + 1], tp_indices[k], tp_indices[k + 1], 0.5)

    return cycles


def build_rainflow_intervals(cycles):
    """
    Convert rainflow cycles to interval records for plotting/selection.
    """
    intervals = []
    seen = {}
    for rng, mean, count, i_start, i_end in cycles:
        left = int(min(i_start, i_end))
        right = int(max(i_start, i_end))
        duration = right - left
        if duration < 2:
            continue

        key = (left, right, float(count))
        record = {
            "start": left,
            "end": right,
            "duration": duration,
            "range": float(rng),
            "mean": float(mean),
            "count": float(count),
        }
        # Keep only the strongest variant for duplicated interval keys.
        if key not in seen or record["range"] > seen[key]["range"]:
            seen[key] = record

    intervals = list(seen.values())
    return intervals


def select_non_overlapping_max_intervals(intervals):
    """
    Pick the largest non-overlapping intervals.
    Sorting by duration first guarantees nested/smaller overlaps are skipped.
    """
    ordered = sorted(
        intervals,
        key=lambda x: (x["duration"], x["range"], x["count"]),
        reverse=True,
    )
    selected = []
    for cand in ordered:
        intersects = any(
            not (cand["end"] <= cur["start"] or cand["start"] >= cur["end"])
            for cur in selected
        )
        if not intersects:
            selected.append(cand)

    selected.sort(key=lambda x: x["start"])
    return selected


def generate_variable_saw_signal(cycle_lengths, seed=7, noise_std=0.01):
    """
    Build a piecewise linear sawtooth signal with slight amplitude/offset variation.
    The sequence must contain 4 clearly longest cycles.
    """
    rng = np.random.default_rng(seed)
    parts = []

    for length in cycle_lengths:
        t = np.arange(length, dtype=float) / length
        amp = 1.0 + rng.uniform(-0.08, 0.08)
        offset = rng.uniform(-0.03, 0.03)
        segment = offset + amp * t
        segment += rng.normal(0.0, noise_std, size=length)
        parts.append(segment)

    return np.concatenate(parts)


def detect_saw_cycles(signal):
    """
    Detect sawtooth cycles by finding sharp negative resets.
    Returns list of dicts: {'start', 'end', 'length'}.
    """
    x = np.asarray(signal)
    dx = np.diff(x)

    # Robust threshold: reset drop is much larger than regular slope/noise.
    amp_span = np.percentile(x, 95) - np.percentile(x, 5)
    drop_threshold = -0.45 * amp_span
    reset_idx = np.where(dx < drop_threshold)[0]

    boundaries = np.r_[0, reset_idx + 1, len(x)]
    cycles = []
    for i in range(len(boundaries) - 1):
        start = int(boundaries[i])
        end = int(boundaries[i + 1])
        length = end - start
        if length >= 3:
            cycles.append({"start": start, "end": end, "length": length})

    return cycles


def plot_selected_intervals(signal, selected_intervals):
    x = np.arange(len(signal))
    plt.figure(figsize=(14, 6))
    plt.plot(x, signal, color="0.7", lw=1.2, label="Сигнал")
    plt.scatter(x, signal, s=7, color="0.55", alpha=0.35, label="Точки сигналу")

    cmap = plt.get_cmap("tab20")
    y_span = signal.max() - signal.min()

    for idx, c in enumerate(selected_intervals, start=1):
        color = cmap((idx - 1) % 20)
        sl = slice(c["start"], c["end"])
        cycle_kind = "цикл" if c["count"] == 1.0 else "півцикл"

        plt.axvspan(c["start"], c["end"], color=color, alpha=0.18, ec=color, lw=1.0)
        plt.plot(
            x[sl],
            signal[sl],
            color=color,
            lw=2.8,
            label=f"#{idx}: {cycle_kind}, довж={c['duration']}",
        )
        plt.scatter(x[sl], signal[sl], s=10, color=color, alpha=0.9)

        mid = (c["start"] + c["end"]) // 2
        y_mid = np.max(signal[sl]) + 0.04 * y_span
        plt.text(
            mid,
            y_mid,
            f"#{idx}",
            color=color,
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.title("Пилкоподібний сигнал: максимальні неперетинні інтервали rainflow")
    plt.xlabel("Індекс відліку")
    plt.ylabel("Амплітуда")
    plt.grid(alpha=0.25)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig("task_0_max_non_overlapping_intervals.png", dpi=160)
    plt.show()


def choose_rainflow_method(cli_method):
    """
    Return chosen rainflow method from CLI or interactive terminal prompt.
    """
    if cli_method in {"rainflow_4point", "rainflow_3point_demo"}:
        return cli_method

    print("Оберіть метод rainflow:")
    print("  1) rainflow_4point")
    print("  2) rainflow_3point_demo")
    choice = input("Введіть 1 або 2 [1]: ").strip()
    return "rainflow_3point_demo" if choice == "2" else "rainflow_4point"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Генерація пилкоподібного сигналу, пошук циклів і вибір rainflow-методу."
    )
    parser.add_argument(
        "--method",
        choices=["rainflow_4point", "rainflow_3point_demo"],
        default=None,
        help="Метод rainflow для розрахунку за turning points.",
    )
    args = parser.parse_args()

    # Exactly 4 longest cycles are embedded in this signal.
    cycle_lengths = [58, 60, 56, 124, 59, 57, 146, 61, 55, 132, 58, 149, 60]
    signal = generate_variable_saw_signal(cycle_lengths, seed=11, noise_std=0.009)

    # Existing 3 functions are still used for processing context.
    method_name = choose_rainflow_method(args.method)
    tp_idx = turning_points(signal)
    method_fn = rainflow_4point if method_name == "rainflow_4point" else rainflow_3point_demo
    rf_cycles = method_fn(signal[tp_idx], tp_idx)
    rf_intervals = build_rainflow_intervals(rf_cycles)
    selected = select_non_overlapping_max_intervals(rf_intervals)

    print(
        f"Поворотні точки: {len(tp_idx)}, "
        f"вибрано метод: {method_name}, знайдено rainflow-циклів: {len(rf_cycles)}"
    )
    print(f"Максимальні неперетинні інтервали: {len(selected)}")
    for i, c in enumerate(selected, start=1):
        cycle_kind = "цикл" if c["count"] == 1.0 else "півцикл"
        print(
            f"  {i:2d}) {cycle_kind:8s} start={c['start']:4d}, end={c['end']:4d}, "
            f"L={c['duration']:3d}, range={c['range']:6.3f}"
        )

    plot_selected_intervals(signal, selected)
