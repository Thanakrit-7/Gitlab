# BJT Common-Emitter DC Bias Web App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Flask web app that computes, validates, and explains the DC operating point of a voltage-divider-biased NPN common-emitter stage, and compares it with an independent approximate calculation.

**Architecture:** Pure engineering functions live in `bjt.py` with no Flask import. `app.py` is a thin application factory that parses the form, calls `bjt.analyze`, and renders one Jinja page. Templates and one stylesheet handle presentation; `unittest` suites cover the math and the routes.

**Tech Stack:** Python 3.12, Flask 3.x, Jinja2, stdlib `unittest`, hand-written CSS.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-dc-bias-design.md`

## Global Constraints

- Python 3.12; runtime dependency is only `Flask>=3.0,<4`; tests use stdlib `unittest` (no pytest).
- All engineering formulas live in `bjt.py`. `app.py` must contain no electrical formula.
- `VCE_SAT = 0.2` volts is a module constant, not a form field.
- UI copy is Thai; engineering symbols stay Latin (`VCC`, `R1`, `R2`, `RC`, `RE`, `β`, `VBE`, `IB`, `IC`, `IE`, `VCE`).
- Do not modify `electrical.py` or `test_electrical.py`; the CLI calculator must keep working.
- `git` is not on `PATH`. In every shell, set:
  `$git = "C:\Users\B6813208\AppData\Local\Programs\Git\cmd\git.exe"`
- Run tests from the repository root as `python -m unittest ...`.
- Commit after every task. Use the message given in the task.
- Reference values (hand-computed from the spec's equations) for
  `VCC=12, R1=47000, R2=10000, RC=4700, RE=1000, β=100, VBE=0.7`:

| Quantity | Exact | Approximate |
|---|---|---|
| `VTH` | 2.1052631578947367 V | same |
| `RTH` | 8245.61403508772 Ω | same |
| `IB` | 1.2863337080456077e-05 A | 1.3913496612819175e-05 A |
| `IC` | 1.2863337080456078e-03 A | 1.4052631578947367e-03 A |
| `IE` | 1.299197045126064e-03 A | 1.4052631578947367e-03 A |
| `VB` | 1.9991970451260639 V | 2.1052631578947367 V |
| `VE` | 1.299197045126064 V | 1.4052631578947368 V |
| `VC` | 5.954231572185644 V | 5.395263157894737 V |
| `VCE` | 4.65503452705958 V | 3.99 V |

## Review Focus

1. **Non-finite numeric text** (`nan`, `inf`) in any field must be rejected with a field error, never produce NaN/inf results. Test in Task 1, surfaced by the route in Task 8.
2. **A missing form field** (key absent, not just empty) must return 400 with a message, never a 500. Test in Task 8.
3. **`VTH` exactly equal to `VBE`** must classify as cutoff with zero currents, never a negative `IB`. Test in Task 3.
4. **HTML/JavaScript typed into a field** must come back escaped, never executable. Test in Task 8.
5. **`β = 1` and very large `β` (1000)** must stay finite and produce no division by zero. Tests in Tasks 1 and 2.

---

### Task 1: Validation and repository cleanup

**Files:**
- Create: `bjt.py`
- Create: `tests/__init__.py` (empty)
- Create: `tests/test_bjt.py`
- Delete: the two untracked files whose names contain `verify DC circuit results` and `start DC circuit calculator`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `class InputError(ValueError)` with attributes `field: str` and message text.
  - `validate_inputs(vcc, r1, r2, rc, re, beta, vbe) -> None` raising `InputError` on the first bad field.

- [ ] **Step 1: Remove the junk files and confirm the tree is clean**

```powershell
Get-ChildItem -File | Where-Object { $_.Name -match 'verify DC circuit results|start DC circuit calculator' } | Remove-Item
$git = "C:\Users\B6813208\AppData\Local\Programs\Git\cmd\git.exe"
& $git status --short
```

Expected: only `docs/superpowers/...` entries appear as untracked.

- [ ] **Step 2: Write the failing validation tests**

```python
# tests/test_bjt.py
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
```

- [ ] **Step 3: Run the tests and confirm they fail**

Run: `python -m unittest tests.test_bjt -v`
Expected: `ModuleNotFoundError: No module named 'bjt'`.

- [ ] **Step 4: Implement `InputError` and `validate_inputs`**

`bjt.py` imports only `math`. `_finite_number(value, field)` raises
`InputError(field, f"{field} ต้องเป็นตัวเลข")` when the value is not an
`int`/`float` (reject `bool`) and
`InputError(field, f"{field} ต้องเป็นค่าจำกัด")` when `math.isfinite` is false.

`validate_inputs` checks, in order: `VCC`, `R1`, `R2`, `RC`, `RE` must be
`> 0` (`"{field} ต้องมากกว่า 0"`); `beta >= 1`
(`"beta ต้องมีค่าอย่างน้อย 1"`); `0 < VBE < VCC`
(`"VBE ต้องมากกว่า 0 และน้อยกว่า VCC"`).

- [ ] **Step 5: Run the tests and confirm they pass**

Run: `python -m unittest tests.test_bjt -v`
Expected: 10 tests, `OK`.

- [ ] **Step 6: Commit**

```powershell
$git = "C:\Users\B6813208\AppData\Local\Programs\Git\cmd\git.exe"
& $git add bjt.py tests/__init__.py tests/test_bjt.py docs/superpowers
& $git commit -m "feat: validate BJT bias inputs"
```

---

### Task 2: Exact operating point for the active region

**Files:**
- Modify: `bjt.py`
- Test: `tests/test_bjt.py`

**Interfaces:**
- Consumes: `validate_inputs`.
- Produces: `exact_operating_point(vcc, r1, r2, rc, re, beta, vbe) -> dict` with keys
  `vth_v`, `rth_ohm`, `ib_a`, `ic_a`, `ie_a`, `vb_v`, `ve_v`, `vc_v`, `vce_v`,
  `region` (string), `warnings` (list of strings), `ic_sat_a` (`float | None`).

- [ ] **Step 1: Write the failing tests**

```python
from bjt import exact_operating_point


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
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m unittest tests.test_bjt.TestExactOperatingPoint -v`
Expected: `ImportError: cannot import name 'exact_operating_point'`.

- [ ] **Step 3: Implement the exact equations**

Implement the spec's "Exact (Thevenin)" equations. For this task return
`region="active"`, `warnings=[]`, `ic_sat_a=None` unconditionally; Task 3 adds
classification. `validate_inputs` runs first.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m unittest tests.test_bjt -v`
Expected: all tests `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add bjt.py tests/test_bjt.py
& $git commit -m "feat: compute exact BJT operating point"
```

---

### Task 3: Region classification and warnings

**Files:**
- Modify: `bjt.py`
- Test: `tests/test_bjt.py`

**Interfaces:**
- Produces: `VCE_SAT = 0.2`; `exact_operating_point` now returns
  `region` in `{"active", "cutoff", "saturation"}` and warning codes in
  `warnings` (`"cutoff"`, `"saturation"`); `ic_sat_a` is set on saturation.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m unittest tests.test_bjt.TestRegion -v`
Expected: `test_cutoff...` fails because region is `"active"`.

- [ ] **Step 3: Implement classification**

After `validate_inputs`, compute `vth_v` and `rth_ohm`. If `vth_v <= vbe`,
return zeros with `region="cutoff"`, `warnings=["cutoff"]`,
`vb_v=vth_v`, `vc_v=vcc`, `vce_v=vcc`, `ic_sat_a=None`. Otherwise compute the
exact values; if `vce_v < VCE_SAT`, set `region="saturation"`,
`warnings=["saturation"]`, and
`ic_sat_a=(vcc - VCE_SAT) / (rc + re)`; else `region="active"`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m unittest tests.test_bjt -v`
Expected: all tests `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add bjt.py tests/test_bjt.py
& $git commit -m "feat: classify BJT operating region"
```

---

### Task 4: Approximate calculation and comparison

**Files:**
- Modify: `bjt.py`
- Test: `tests/test_bjt.py`

**Interfaces:**
- Produces:
  - `approximate_operating_point(vcc, r1, r2, rc, re, beta, vbe) -> dict` with
    `vth_v`, `rth_ohm`, `ib_a`, `ic_a`, `ie_a`, `vb_v`, `ve_v`, `vc_v`, `vce_v`.
  - `compare(exact: dict, approximate: dict) -> dict` with keys `"ic"` and
    `"vce"`, each holding `{"exact", "approximate", "delta", "percent"}` where
    `delta = approximate - exact` and `percent = delta / exact * 100`
    (`0.0` when `exact == 0`).

- [ ] **Step 1: Write the failing tests**

```python
from bjt import approximate_operating_point, compare


class TestApproximate(unittest.TestCase):
    def test_approximate_values(self):
        result = approximate_operating_point(**BASE)
        self.assertAlmostEqual(result["vb_v"], 2.1052631578947367, places=9)
        self.assertAlmostEqual(result["ve_v"], 1.4052631578947368, places=9)
        self.assertAlmostEqual(result["ie_a"], 0.0014052631578947367, delta=1e-12)
        self.assertAlmostEqual(result["ic_a"], 0.0014052631578947367, delta=1e-12)
        self.assertAlmostEqual(result["ib_a"], 1.3913496612819175e-05, delta=1e-12)
        self.assertAlmostEqual(result["vc_v"], 5.395263157894737, places=9)
        self.assertAlmostEqual(result["vce_v"], 3.99, places=9)

    def test_compare_deltas(self):
        exact = exact_operating_point(**BASE)
        approx = approximate_operating_point(**BASE)
        result = compare(exact, approx)
        self.assertAlmostEqual(result["ic"]["delta"], 0.00011892944984912891,
                               delta=1e-12)
        self.assertAlmostEqual(result["ic"]["percent"], 9.245614035087712,
                               places=9)
        self.assertAlmostEqual(result["vce"]["delta"], -0.6650345270595794,
                               delta=1e-9)
        self.assertAlmostEqual(result["vce"]["percent"], -14.286350040880539,
                               places=9)

    def test_compare_avoids_division_by_zero(self):
        zero = {"ic_a": 0.0, "vce_v": 0.0}
        result = compare(zero, zero)
        self.assertEqual(result["ic"]["percent"], 0.0)
        self.assertEqual(result["vce"]["percent"], 0.0)
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m unittest tests.test_bjt.TestApproximate -v`
Expected: `ImportError`.

- [ ] **Step 3: Implement**

Implement the spec's "Approximate" equations (`VB = VTH`, then
`VE = VB - VBE`, `IE = VE / RE`, `IC = IE`, `IB = IE / (1 + beta)`,
`VC = VCC - IC * RC`, `VCE = VC - VE`). `compare` reads `ic_a` and `vce_v`
from both dicts.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m unittest tests.test_bjt -v`
Expected: all tests `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add bjt.py tests/test_bjt.py
& $git commit -m "feat: compare exact and approximate bias results"
```

---

### Task 5: `analyze` orchestration

**Files:**
- Modify: `bjt.py`
- Test: `tests/test_bjt.py`

**Interfaces:**
- Produces: `analyze(vcc, r1, r2, rc, re, beta, vbe) -> dict` with keys
  `"inputs"` (the seven values), `"exact"`, `"approximate"`, `"comparison"`,
  and `"approx_near_saturation"` (`bool`, `True` only when the exact region is
  active and the approximate `vce_v` is below `VCE_SAT`).
  `"approximate"` and `"comparison"` are `None` unless `exact["region"] == "active"`.

- [ ] **Step 1: Write the failing tests**

```python
from bjt import analyze


class TestAnalyze(unittest.TestCase):
    def test_active_returns_comparison(self):
        result = analyze(**BASE)
        self.assertEqual(result["inputs"]["vcc"], 12.0)
        self.assertEqual(result["exact"]["region"], "active")
        self.assertIsNotNone(result["approximate"])
        self.assertIsNotNone(result["comparison"])

    def test_cutoff_skips_comparison(self):
        result = analyze(vcc=12.0, r1=47000.0, r2=1000.0, rc=4700.0,
                         re=1000.0, beta=100.0, vbe=0.7)
        self.assertEqual(result["exact"]["region"], "cutoff")
        self.assertIsNone(result["approximate"])
        self.assertIsNone(result["comparison"])

    def test_saturation_skips_comparison(self):
        result = analyze(**{**BASE, "rc": 47000.0})
        self.assertEqual(result["exact"]["region"], "saturation")
        self.assertIsNone(result["approximate"])
        self.assertIsNone(result["comparison"])

    def test_flags_approximation_near_saturation(self):
        result = analyze(**{**BASE, "rc": 7800.0})
        self.assertEqual(result["exact"]["region"], "active")
        self.assertTrue(result["approx_near_saturation"])

    def test_does_not_flag_comfortably_active_result(self):
        self.assertFalse(analyze(**BASE)["approx_near_saturation"])

    def test_invalid_input_raises(self):
        with self.assertRaises(InputError):
            analyze(**{**BASE, "beta": 0.5})
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python -m unittest tests.test_bjt.TestAnalyze -v`
Expected: `ImportError`.

- [ ] **Step 3: Implement**

`analyze` validates, computes `exact_operating_point`, and only when the
region is `"active"` computes `approximate_operating_point` and `compare`.
Otherwise both are `None`. Set `approx_near_saturation` to
`approximate["vce_v"] < VCE_SAT` when the region is active, else `False`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `python -m unittest tests.test_bjt -v`
Expected: all tests `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add bjt.py tests/test_bjt.py
& $git commit -m "feat: orchestrate BJT bias analysis"
```

---

### Task 6: Flask skeleton, page, and stylesheet

**Files:**
- Create: `requirements.txt`
- Create: `app.py`
- Create: `templates/base.html`
- Create: `templates/index.html`
- Create: `static/style.css`
- Create: `tests/test_app.py`

**Interfaces:**
- Consumes: `bjt.analyze`, `bjt.InputError`.
- Produces: `create_app() -> Flask` and module-level `app`; `GET /` renders
  `index.html` with `form` (dict of seven raw strings), `result=None`,
  `errors={}`.

- [ ] **Step 1: Install Flask in a local virtual environment**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "Flask>=3.0,<4"
```

`requirements.txt` contains exactly `Flask>=3.0,<4`.

- [ ] **Step 2: Write the failing test**

```python
# tests/test_app.py
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
```

- [ ] **Step 3: Run the test and confirm it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app -v`
Expected: `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 4: Implement the app and templates**

`app.py`: `create_app()` builds the Flask app, defines `GET /` returning
`render_template("index.html", form=DEFAULTS, result=None, errors={})`, then
returns it. `DEFAULTS` is
`{"vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700", "re": "1000", "beta": "100", "vbe": "0.7"}`.
At module level set `app = create_app()`; under `__main__` run
`app.run(host="127.0.0.1", port=5000)` with no debug reloader.

`templates/base.html`: Thai `<title>`, a header, `{% block content %}`, links
`static/style.css` via `url_for`.

`templates/index.html`: extends base; a form with `method="post"`,
`action="{{ url_for('calculate') }}"`, seven number inputs (`step="any"`,
`name` equal to the dict keys, `value="{{ form.vcc }}"` etc.), and a submit
button labelled `คำนวณ`. Leave a `{% block results %}` placeholder section for
Task 7. Every field shows `{{ errors.vcc }}` in a `class="field-error"` span
when present.

`static/style.css`: system font, centered `max-width: 720px` card, two-column
field grid that collapses under 560 px, warning box in amber, error text in
red. No external assets.

- [ ] **Step 5: Run the test and confirm it passes**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app -v`
Expected: `OK`.

- [ ] **Step 6: Commit**

```powershell
& $git add requirements.txt app.py templates static tests/test_app.py
& $git commit -m "feat: add Flask page for BJT bias calculator"
```

---

### Task 7: Results and comparison on the page

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `bjt.analyze`.
- Produces: `POST /calculate` endpoint; valid input returns `200` and renders
  the result block.

- [ ] **Step 1: Write the failing test**

```python
class TestCalculate(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_valid_input_shows_operating_point(self):
        response = self.client.post("/calculate", data={
            "vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
            "re": "1000", "beta": "100", "vbe": "0.7"})
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("1.286", html)      # IC in mA
        self.assertIn("4.655", html)      # VCE in V
        self.assertIn("Active", html)
        self.assertIn("9.2", html)        # IC percent difference
```

- [ ] **Step 2: Run the test and confirm it fails**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app.TestCalculate -v`
Expected: `404`.

- [ ] **Step 3: Implement the route and result markup**

`POST /calculate` reads `request.form.get(name, "").strip()` for the seven
fields, parses with `float`, and calls `analyze`. On success render
`index.html` with `form=raw`, `result=result`, `errors={}`, status 200.

Result markup (inside `{% if result %}`):
- Region badge using a Jinja map:
  `active → "Active — ทำงานในย่านขยายสัญญาณ"`,
  `cutoff → "Cutoff — ทรานซิสเตอร์ไม่นำกระแส"`,
  `saturation → "Saturation — ทรานซิสเตอร์อิ่มตัว"`.
- Values: `VCE`, `IC`, `IE`, `VB`, `VE`, `VC`, `IB`, `VTH`, `RTH`, with
  `"%.3f"|format(...)` and units V / mA / µA / Ω.
- `{% if result.comparison %}`: a table with rows IC and VCE showing exact,
  approximate, `delta`, and `percent` (`"%.1f"|format(...)` + `%`).
- `{% if result.exact.warnings %}`: an amber box listing Thai text for each
  code (`cutoff`, `saturation`), and on saturation the `IC_sat` limit in mA.
- `{% if result.approx_near_saturation %}`: a short note that the approximate
  method already puts `VCE` below `VCE(sat)` even though the exact result is
  active.
- Never print raw `warnings` codes to the user.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app -v`
Expected: all tests `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add app.py templates/index.html tests/test_app.py
& $git commit -m "feat: render BJT operating point and comparison"
```

---

### Task 8: Validation errors, missing fields, and escaping

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Test: `tests/test_app.py`

**Interfaces:**
- Produces: invalid input returns `400`, keeps the submitted values, and shows
  a Thai message per field.

- [ ] **Step 1: Write the failing tests**

```python
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
                "re": "1000", "beta": "100"}          # vbe omitted
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
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app.TestErrors -v`
Expected: at least `test_non_numeric_returns_400` fails with `500`.

- [ ] **Step 3: Implement error handling**

In `POST /calculate`, collect `errors: dict[str, str]`:
- empty or unparsable value → `"กรุณากรอกตัวเลข"` for that field;
- `InputError` from `analyze` → `errors[exc.field.lower()] = str(exc)`
  (the engineering module names fields in uppercase, the form in lowercase);
- if any error, re-render `index.html` with `form=raw`, `result=None`,
  `errors=errors`, status `400`.

Do not catch `Exception` broadly; only `InputError` and `ValueError` from
`float()`. Jinja autoescaping handles the echo; never use `|safe`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.\.venv\Scripts\python.exe -m unittest discover -v`
Expected: all tests `OK`.

- [ ] **Step 5: Commit**

```powershell
& $git add app.py templates/index.html tests/test_app.py
& $git commit -m "feat: validate form input and keep values on error"
```

---

### Task 9: README, full verification, demo, and push

**Files:**
- Modify: `README.md`
- Test: full suite

**Interfaces:**
- Consumes: everything above.
- Produces: documented run instructions; verified localhost demo; pushed commit.

- [ ] **Step 1: Update `README.md`**

Add a Thai section `## เว็บแอปคำนวณจุดทำงาน DC ของ BJT` with: what it does,
install (`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`), run
(`.\.venv\Scripts\python.exe app.py` → `http://127.0.0.1:5000`), test
(`python -m unittest discover -v`), the seven inputs, and the example values
from the Global Constraints table. Keep the existing CLI section intact.

- [ ] **Step 2: Run the whole suite**

Run: `.\.venv\Scripts\python.exe -m unittest discover -v`
Expected: every test `OK`, zero failures/errors.

- [ ] **Step 3: Verify the CLI still works**

Run: `python -m unittest test_electrical -v`
Expected: 4 tests `OK`.

- [ ] **Step 4: Run the localhost demo and check all three regions**

```powershell
$proc = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "app.py" -PassThru
Start-Sleep -Seconds 3
$active = Invoke-WebRequest -Uri http://127.0.0.1:5000/calculate -Method Post -Body @{vcc=12;r1=47000;r2=10000;rc=4700;re=1000;beta=100;vbe=0.7} -UseBasicParsing
$cutoff = Invoke-WebRequest -Uri http://127.0.0.1:5000/calculate -Method Post -Body @{vcc=12;r1=47000;r2=1000;rc=4700;re=1000;beta=100;vbe=0.7} -UseBasicParsing
$sat = Invoke-WebRequest -Uri http://127.0.0.1:5000/calculate -Method Post -Body @{vcc=12;r1=47000;r2=10000;rc=47000;re=1000;beta=100;vbe=0.7} -UseBasicParsing
$active.StatusCode; $active.Content -match '1.286'; $cutoff.Content -match 'Cutoff'; $sat.Content -match 'Saturation'
Stop-Process -Id $proc.Id
```

Expected: `200`, `True`, `True`, `True`. If port 5000 is busy, run with
`$env:FLASK_RUN_PORT` is not used here — instead change the port in `app.py`
to 5001 and note it in the README, then repeat.

- [ ] **Step 5: Commit and push**

```powershell
$git = "C:\Users\B6813208\AppData\Local\Programs\Git\cmd\git.exe"
& $git add README.md
& $git commit -m "docs: document BJT bias web app"
& $git push origin main
```

Expected: push succeeds. If authentication fails, report the exact error and
leave the local commit in place.

---

## Self-Review

- **Spec coverage:** inputs (Task 6), exact output with units (Tasks 2, 7),
  validation (Tasks 1, 8), region warnings (Tasks 3, 7), independent
  comparison (Tasks 4, 7), separated logic/routes/templates/CSS/tests (Tasks
  1–8), localhost + GitHub (Task 9). No gaps.
- **Step scan:** every step names one action and one checkable result.
- **Type consistency:** `exact_operating_point` returns `ic_a`, `vce_v`,
  `region`, `warnings`, `ic_sat_a`; `compare` reads `ic_a` and `vce_v` from
  both dicts; templates read `result.exact.ic_a` and `result.comparison.ic.*`.
  Names match across Tasks 2–8.
- **Review Focus:** each of the five lines has a test in the task that owns
  the code (Tasks 1, 2, 3, 8).
