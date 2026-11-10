import unittest

from bjt import InputError, validate_inputs

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


if __name__ == "__main__":
    unittest.main()
