import unittest
from electrical import analyze_dc, analyze_series, analyze_parallel


class TestDCAnalyzer(unittest.TestCase):
    def test_known_values(self):
        result = analyze_dc(12, 6)
        self.assertAlmostEqual(result["current_a"], 2.0)
        self.assertAlmostEqual(result["power_w"], 24.0)

    def test_zero_voltage(self):
        result = analyze_dc(0, 10)
        self.assertAlmostEqual(result["current_a"], 0.0)
        self.assertAlmostEqual(result["power_w"], 0.0)

    def test_series_circuit(self):
        result = analyze_series(12, [4, 8])
        self.assertAlmostEqual(result["total_resistance_ohm"], 12.0)
        self.assertAlmostEqual(result["total_current_a"], 1.0)

    def test_parallel_circuit(self):
        result = analyze_parallel(12, [6, 3])
        self.assertAlmostEqual(result["total_resistance_ohm"], 2.0)
        self.assertAlmostEqual(result["total_current_a"], 6.0)


if __name__ == "__main__":
    unittest.main()