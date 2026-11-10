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


if __name__ == "__main__":
    unittest.main()
