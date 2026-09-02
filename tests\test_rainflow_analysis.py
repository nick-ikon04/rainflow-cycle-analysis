import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rainflow_analysis import (  # noqa: E402
    generate_variable_saw_signal,
    rainflow_3point_demo,
    rainflow_4point,
    turning_points,
)


class RainflowAnalysisTests(unittest.TestCase):
    def test_turning_points_include_endpoints(self):
        signal = np.array([0.0, 1.0, 0.0, -1.0, 0.0])
        np.testing.assert_array_equal(turning_points(signal), [0, 1, 3, 4])

    def test_seeded_signal_is_deterministic(self):
        lengths = [8, 10, 9]
        first = generate_variable_saw_signal(lengths)
        second = generate_variable_saw_signal(lengths)
        np.testing.assert_allclose(first, second)

    def test_both_modes_return_positive_ranges_and_valid_counts(self):
        signal = np.array([0.0, 2.0, -1.0, 3.0, 0.0])
        indices = turning_points(signal)
        for method in (rainflow_4point, rainflow_3point_demo):
            cycles = method(signal[indices], indices)
            self.assertTrue(cycles)
            self.assertTrue(all(cycle[0] >= 0 for cycle in cycles))
            self.assertTrue(all(cycle[2] in {0.5, 1.0} for cycle in cycles))


if __name__ == "__main__":
    unittest.main()
