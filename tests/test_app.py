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


if __name__ == "__main__":
    unittest.main()
