import unittest

from app import create_app


class TestIndex(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_index_renders_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for label in ("VCC", "R1", "R2", "RC", "RE", "β", "VBE"):
            self.assertIn(label, html)


class TestCalculate(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_valid_input_shows_operating_point(self):
        response = self.client.post("/calculate", data={
            "vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
            "re": "1000", "beta": "100", "vbe": "0.7"})
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("1.286", html)
        self.assertIn("4.655", html)
        self.assertIn("Active", html)
        self.assertIn("9.2", html)


class TestErrors(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def post(self, **overrides):
        data = {"vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
                "re": "1000", "beta": "100", "vbe": "0.7"}
        data.update(overrides)
        return self.client.post("/calculate", data=data)

    def test_non_numeric_returns_400(self):
        response = self.post(beta="abc")
        self.assertEqual(response.status_code, 400)
        self.assertIn("กรุณากรอกตัวเลข", response.get_data(as_text=True))

    def test_missing_field_returns_400_not_500(self):
        data = {"vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
                "re": "1000", "beta": "100"}
        response = self.client.post("/calculate", data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("กรุณากรอกตัวเลข", response.get_data(as_text=True))

    def test_out_of_range_names_the_field(self):
        response = self.post(beta="0.5")
        self.assertEqual(response.status_code, 400)
        self.assertIn("อย่างน้อย 1", response.get_data(as_text=True))

    def test_values_are_echoed_back(self):
        html = self.post(beta="abc").get_data(as_text=True)
        self.assertIn('value="47000"', html)

    def test_html_in_input_is_escaped(self):
        html = self.post(vcc="<script>alert(1)</script>").get_data(as_text=True)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_nan_is_rejected(self):
        response = self.post(vcc="nan")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
