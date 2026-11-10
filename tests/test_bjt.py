import unittest

from bjt import InputError, exact_operating_point, validate_inputs

BASE = dict(vcc=12.0, r1=47000.0, r2=10000.0, rc=4700.0, re=1000.0,
            beta=100.0, vbe=0.7)


class TestValidation(unittest.TestCase):
    def assert_field(self, field, **overrides):
        with self.assertRaises(InputError) as ctx:
            validate_inputs(**{**BASE, **overrides})
        self.assertEqual(ctx.exception.field, field)

    def test_accepts_valid_inputs(self):
        validate_inputs(**BASE)

    def test_rejects_zero_vcc(self):
        self.assert_field("VCC", vcc=0)

    def test_rejects_negative_resistor(self):
        self.assert_field("R1", r1=-1)

    def test_rejects_beta_below_one(self):
        self.assert_field("beta", beta=0.5)

    def test_accepts_beta_one(self):
        validate_inputs(**{**BASE, "beta": 1.0})

    def test_rejects_vbe_equal_to_vcc(self):
        self.assert_field("VBE", vbe=12.0)

    def test_rejects_vbe_zero(self):
        self.assert_field("VBE", vbe=0)

    def test_rejects_string(self):
        self.assert_field("VCC", vcc="12")

    def test_rejects_nan(self):
        self.assert_field("VCC", vcc=float("nan"))

    def test_rejects_infinity(self):
        self.assert_field("R2", r2=float("inf"))


class TestExactOperatingPoint(unittest.TestCase):
    def test_textbook_example(self):
        result = exact_operating_point(**BASE)
        self.assertAlmostEqual(result["vth_v"], 2.1052631578947367, places=9)
        self.assertAlmostEqual(result["rth_ohm"], 8245.61403508772, places=6)
        self.assertAlmostEqual(result["ib_a"], 1.2863337080456077e-05, delta=1e-12)
        self.assertAlmostEqual(result["ic_a"], 1.2863337080456078e-03, delta=1e-12)
        self.assertAlmostEqual(result["ie_a"], 1.299197045126064e-03, delta=1e-12)
        self.assertAlmostEqual(result["vb_v"], 1.9991970451260639, places=9)
        self.assertAlmostEqual(result["ve_v"], 1.299197045126064, places=9)
        self.assertAlmostEqual(result["vc_v"], 5.954231572185644, places=9)
        self.assertAlmostEqual(result["vce_v"], 4.65503452705958, places=9)
        self.assertEqual(result["region"], "active")
        self.assertEqual(result["warnings"], [])

    def test_large_beta_stays_finite(self):
        result = exact_operating_point(**{**BASE, "beta": 1000.0})
        self.assertEqual(result["region"], "active")
        self.assertGreater(result["ic_a"], 0)
        self.assertLess(result["vce_v"], 12.0)

    def test_beta_one_stays_finite(self):
        result = exact_operating_point(**{**BASE, "beta": 1.0})
        self.assertEqual(result["region"], "active")
        self.assertGreater(result["ib_a"], 0)


class TestRegion(unittest.TestCase):
    def test_cutoff_when_vth_below_vbe(self):
        result = exact_operating_point(
            vcc=12.0, r1=47000.0, r2=1000.0, rc=4700.0, re=1000.0,
            beta=100.0, vbe=0.7)
        self.assertEqual(result["region"], "cutoff")
        self.assertIn("cutoff", result["warnings"])
        self.assertEqual(result["ib_a"], 0.0)
        self.assertEqual(result["ic_a"], 0.0)
        self.assertEqual(result["ie_a"], 0.0)
        self.assertEqual(result["ve_v"], 0.0)
        self.assertAlmostEqual(result["vb_v"], 0.25, places=9)
        self.assertAlmostEqual(result["vc_v"], 12.0, places=9)
        self.assertAlmostEqual(result["vce_v"], 12.0, places=9)
        self.assertIsNone(result["ic_sat_a"])

    def test_cutoff_boundary_when_vth_equals_vbe(self):
        result = exact_operating_point(
            vcc=12.0, r1=16142.857142857143, r2=1000.0, rc=4700.0,
            re=1000.0, beta=100.0, vbe=0.7)
        self.assertEqual(result["region"], "cutoff")
        self.assertEqual(result["ib_a"], 0.0)

    def test_saturation_when_vce_below_vce_sat(self):
        result = exact_operating_point(**{**BASE, "rc": 47000.0})
        self.assertEqual(result["region"], "saturation")
        self.assertIn("saturation", result["warnings"])
        self.assertLess(result["vce_v"], 0.2)
        self.assertAlmostEqual(result["ic_sat_a"], 0.00024583333333333336,
                               delta=1e-12)


if __name__ == "__main__":
    unittest.main()
