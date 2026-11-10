import unittest

from bjt import analyze
from circuit_svg import build_circuit_svg, format_current

BASE = dict(vcc=12.0, r1=47000.0, r2=10000.0, rc=4700.0, re=1000.0,
            beta=100.0, vbe=0.7)


class TestFormatCurrent(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(format_current(0.0), "0.000")

    def test_milliamp(self):
        self.assertEqual(format_current(1.286e-3), "1.286 mA")

    def test_microamp(self):
        self.assertEqual(format_current(12.86e-6), "12.860 µA")


class TestBuildCircuitSvg(unittest.TestCase):
    def setUp(self):
        self.result = analyze(**BASE)
        self.svg = build_circuit_svg(self.result)

    def test_svg_envelope(self):
        self.assertTrue(self.svg.startswith("<svg"))
        self.assertIn('viewBox="0 0 480 400"', self.svg)
        self.assertIn("circuit-svg", self.svg)
        self.assertTrue(self.svg.rstrip().endswith("</svg>"))

    def test_shows_input_and_result_values(self):
        for token in ("12.0", "47000", "10000", "4700", "1000", "100",
                      "VCC", "R1", "R2", "RC", "RE", "β", "VBE",
                      "VTH", "RTH", "IB", "IC", "IE", "VB", "VE", "VC", "VCE"):
            self.assertIn(token, self.svg)
        self.assertIn("4.655", self.svg)
        self.assertIn("1.286 mA", self.svg)

    def test_no_leaked_python_sentinels(self):
        self.assertNotIn("nan", self.svg.lower())
        self.assertNotIn("None", self.svg)

    def test_cutoff_shows_zero_currents(self):
        result = analyze(vcc=12.0, r1=47000.0, r2=1000.0, rc=4700.0,
                         re=1000.0, beta=100.0, vbe=0.7)
        svg = build_circuit_svg(result)
        self.assertIn("0.000", svg)
        self.assertNotIn("nan", svg.lower())

    def test_saturation_shows_negative_vce(self):
        result = analyze(**{**BASE, "rc": 47000.0})
        svg = build_circuit_svg(result)
        expected = f"{result['exact']['vce_v']:.3f}"
        self.assertLess(result["exact"]["vce_v"], 0)
        self.assertIn(expected, svg)

    def test_values_match_analyze_output(self):
        svg = build_circuit_svg(analyze(**BASE))
        exact = analyze(**BASE)["exact"]
        self.assertIn(f"{exact['vce_v']:.3f}", svg)
        self.assertIn(format_current(exact["ic_a"]), svg)


if __name__ == "__main__":
    unittest.main()
