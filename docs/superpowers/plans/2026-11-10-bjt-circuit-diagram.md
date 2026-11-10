# Circuit diagram with live values Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** หน้าผลลัพธ์มีภาพ schematic วงจร voltage-divider bias ที่แสดงค่าที่กรอกและผลคำนวณจริง (SVG วาดจาก Python) เปลี่ยนตามทุกครั้งที่คำนวณ

**Architecture:** โมดูลใหม่ `circuit_svg.py` (pure function `build_circuit_svg(result)` คืนสตริง `<svg>…</svg>` จาก dict ผลลัพธ์ของ `analyze`); template include partial `_circuit.html` ใต้ส่วนผลลัพธ์; `bjt.py` ไม่แตะ

**Tech Stack:** Python stdlib, Jinja, Flask, inline SVG

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-circuit-diagram-design.md`

## Global Constraints

- `bjt.py` ห้ามแก้
- ทุกค่าตัวเลขใน SVG มาจาก `result` (dict ของ `analyze`) ห้ามคำนวณใหม่/copy ค่าเอง
- ไม่เพิ่ม dependency ใด ๆ
- ข้อความนอกเหนือจากตัวเลข/หน่วยที่เราควบคุมต้องผ่าน `html.escape`
- กรณี Cutoff กระแสแสดง `0.000`; กรณี Saturation แสดงค่าตามสูตร (อาจติดลบ) — สอดคล้อง spec เดิม
- Post-condition: ส่วนหัวข้อหน้าและตารางผลลัพธ์เดิมไม่เปลี่ยนโครงสร้าง

## Review Focus

1. **`nan`/`None` จาก dict หลุดเข้า SVG** (เช่น field ที่หาย) → ภาพต้องแสดง `0.000`/ค่าที่มี ห้ามมีคำว่า `nan` หรือ `None` — test ใน Task 1
2. **Cutoff case** กระแส 0 ทั้งหมด → ภาพต้องมี `0.000`, ไม่มีค่าติดลบปลอม — test ใน Task 1
3. **Saturation case** ค่าอาจติดลบ → ภาพต้องแสดง `VCE` ติดลบตามผลจริง (สอดคล้อง spec) — test ใน Task 1
4. **Auto-unit ของกระแส**: `12.9 µA` ต้องเลือก `µA`, `1.286 mA` ต้องเลือก `mA` — test ใน Task 1 (`format_current`)
5. **ตัวเลขในภาพต้องตรงกับตาราง 100%** (source เดียว) → ค่า `4.655` จาก `analyze` ต้องปรากฏใน SVG เช่นกัน — test ใน Task 1

---

### Task 1: `circuit_svg.py` — SVG builder + tests

**Files:**
- Create: `C:\Users\B6813208\Desktop\Gitlab\circuit_svg.py`
- Create: `C:\Users\B6813208\Desktop\Gitlab\tests\test_circuit_svg.py`

**Interfaces:**
- Consumes: dict `result` จาก `bjt.analyze` — keys `inputs` (vcc, r1, r2, rc, re, beta, vbe),
  `exact` (vth_v, rth_ohm, ib_a, ic_a, ie_a, vb_v, ve_v, vc_v, vce_v, region)
- Produces: `format_current(amps: float) -> str` และ `build_circuit_svg(result: dict) -> str`;
  คืนสตริงขึ้นต้น `<svg` viewBox `0 0 480 400` คลาสรูท `circuit-svg`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_circuit_svg.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_circuit_svg -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'circuit_svg'`

- [ ] **Step 3: Implement `circuit_svg.py`**

โมดูลประกอบด้วยตรรกะ 4 ส่วน (ผู้ implement เลือกพิกัดเอง แต่ต้องครบตาม list):

1. `format_current(amps)` — คืน `"0.000"` ถ้า amps == 0; ถ้า `amps < 1e-3` คืน f"{amps*1e6:.3f} µA";
   มิฉะนั้น f"{amps*1000:.3f} mA"
2. `_fmt(value, unit="")` — helper ชุดเดียวกับหน้า: f"{value:.3f}" สำหรับ V, f"{value:.0f}" สำหรับ Ω (หรือ 1 ตำแหน่งสำหรับ kΩ? ใช้ Ω เต็มตาม input ที่แสดง)
3. `build_circuit_svg(result)` — layout แนวตรง ตามสเปก:
   - `<svg class="circuit-svg" viewBox="0 0 480 400" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="วงจร Voltage Divider Bias">`
   - ราง VCC บน, เส้น RC ลง collector, ทรานซิสเตอร์ (วงจรเส้นตรง: C บน, E ล่าง ลูกศรชี้ลงออก), β ในวงกลมเหนือตัว
   - กิ่ง R1/R2 ซ้ายสุด โหนดกลางเขียน `VTH = … V`, `RTH = … Ω`
   - กระแส: `IB = … µA` เข้าเบส (ลูกศร), `IC = …` เข้า collector, `IE = …` ออก emitter — สี accent (#0b6e4f)
   - โหนด: `VB`, `VE` (ใต้ RE เหนือ GND), `VC` เหนือ collector พร้อมค่า; เส้นมิติแนวตั้งคร่อม C–E ทางขวา ปิดท้ายด้วย `VCE = … V`
   - ทุกข้อความเป็น `<text>`; เส้นเป็น `<line>/<path>`; ค่าที่นำมาแปะ escape ด้วย `html.escape` ทุกครั้งที่เป็น string ที่ไม่ใช่เลขที่เราฟอร์แมตเอง
   - Cutoff: `format_current(0)` ให้ `0.000` อยู่แล้ว — ไม่มีเงื่อนไขพิเศษเพิ่ม
   - Saturation: แสดงค่าตรงกับ dict (เช่น VCE ติดลบ) ไม่ต้องปรับ layout
4. คืนสตริงสมบูรณ์ ไม่มี doctype

- [ ] **Step 4: Run tests**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_circuit_svg -v`
Expected: PASS 9 ตัว

- [ ] **Step 5: Commit**

```bash
$git add circuit_svg.py tests/test_circuit_svg.py
& $git commit -m "feat: render BJT circuit schematic as SVG with live values"
```

---

### Task 2: Template + CSS — ฝัง SVG ใต้ผลลัพธ์

**Files:**
- Create: `C:\Users\B6813208\Desktop\Gitlab\templates\_circuit.html`
- Modify: `C:\Users\B6813208\Desktop\Gitlab\templates\index.html`
- Modify: `C:\Users\B6813208\Desktop\Gitlab\static\style.css`
- Test: `C:\Users\B6813208\Desktop\Gitlab\tests\test_app.py`

**Interfaces:**
- Consumes: `build_circuit_svg` จาก Task 1; `create_app()` ส่ง `circuit_svg=build_circuit_svg(result)` เข้าไปใน render เฉพาะเมื่อ `result` ไม่เป็น None
- Produces: หน้าผลลัพธ์มีบล็อกภาพวงจรใต้ส่วนผลลัพธ์เดิม ไม่แตะโครงสร้างเดิม

- [ ] **Step 1: Write the failing test**

เพิ่มใน `tests/test_app.py` (class `TestCircuitDiagram`):

```python
class TestCircuitDiagram(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_result_page_embeds_svg(self):
        response = self.client.post("/calculate", data={
            "vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
            "re": "1000", "beta": "100", "vbe": "0.7"})
        html = response.get_data(as_text=True)
        self.assertIn("circuit-svg", html)
        self.assertIn("<svg", html)
        self.assertIn("4.655", html)

    def test_invalid_submission_has_no_svg(self):
        response = self.client.post("/calculate", data={
            "vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
            "re": "1000", "beta": "abc", "vbe": "0.7"})
        self.assertNotIn("circuit-svg", response.get_data(as_text=True))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m unittest tests.test_app.TestCircuitDiagram -v`
Expected: FAIL — หน้าผลลัพธ์ยังไม่มี `circuit-svg`

- [ ] **Step 3: แก้ `app.py`**

ใน `calculate()` เมื่อ `result` เป็น truthy ให้คำนวณ `circuit = build_circuit_svg(result)`;
ส่งเข้า `render_template(...)` ทั้ง GET (ไม่มี result → ไม่ต้องส่ง) และ POST พร้อม `circuit_svg=circuit`

- [ ] **Step 4: สร้าง `templates/_circuit.html`**

```html
<div class="circuit-wrap">
  {{ circuit_svg | safe }}
</div>
```

และใน `templates/index.html` หลัง `{% if %}{% elif %}` บล็อกคำเตือนท้ายผลลัพธ์:
`{% include "_circuit.html" %}` ใต้ `</section>` ของ result (ก่อน `{% endif %}` ปิด if result)
หรือเป็นส่วนหนึ่งของ section ผลลัพธ์ท้ายสุด — เลือกจุดที่อ่านง่ายที่สุดในบล็อกไฟล์จริง

- [ ] **Step 5: แก้ `static/style.css`**

```css
.circuit-wrap { margin: 18px 0 4px; overflow-x: auto; }
.circuit-svg { width: 100%; max-width: 520px; height: auto; display: block; margin: 0 auto; }
```

- [ ] **Step 6: Run tests**

Run: `.\.venv\Scripts\python.exe -m unittest discover -v`
Expected: PASS ทั้งหมด (รวมเทสต์ใหม่ 2 + Task 1 9)

- [ ] **Step 7: ตรวจด้วยตาใน browser**

รัน `.\.venv\Scripts\python.exe app.py` แล้วเปิด http://127.0.0.1:5000 → กรอกเคส Active
(12 / 47000 / 10000 / 4700 / 1000 / 100 / 0.7) ตรวจว่าภาพแสดง VB≈1.999, VE≈1.299,
VC≈5.954, VCE≈4.655, IB≈12.863 µA, และ Cutoff (R2=1000) แสดง 0.000

- [ ] **Step 8: Commit**

```bash
$git add app.py templates/_circuit.html templates/index.html static/style.css tests/test_app.py
& $git commit -m "feat: embed circuit diagram under result"
```
