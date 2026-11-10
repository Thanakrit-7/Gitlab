# Design: ภาพวงจร schematic แสดงค่าที่ใส่ในหน้า demo

วันที่: 2026-11-10
สถานะ: รออนุมัติ

## เหตุผลและเป้าหมาย

หน้า demo สำหรับห้อง lab ต้องมีภาพวงจร voltage-divider bias ที่ต่อเนื่องกับค่าที่กรอก
— ทุกครั้งที่กดคำนวณ ภาพเปลี่ยนตามจริง แสดงทั้งอินพุต (VCC, R1, R2, RC, RE, β, VBE)
และผลคำนวณ (VTH/RTH, IB, IC, IE, VB, VE, VC, VCE) ไม่ใช่รูป static

## Goals / Non-goals

- Goals: schematic วาด inline SVG จาก Python; โหนด/กิ่งติดค่าจาก `analyze()` ชุดเดียวกับตาราง;
  ค่าที่แสดงเปลี่ยนตามทุกครั้งที่คำนวณ; คมชัดทุกความละเอียดและพิมพ์ได้
- Non-goals: ไม่มีกราฟ load line; ไม่มี animation/JS; ไม่แก้ `bjt.py`; ไม่มี interactive editing
- Anti-goals: เลขในภาพขัดกับตารางผลลัพธ์ (ห้าม copy ค่าเอง — ใช้ผลจาก `analyze` เท่านั้น)

## Approaches ที่พิจารณา

1. **matplotlib → PNG ฝังหน้าเว็บ:** ไฟล์ภาพต้อง rasterize, เพิ่ม dependency หนัก, print ไม่คม — ตัดทิ้ง
2. **inline SVG จาก Python/Jinja (เลือก):** ไม่มี dependency ใหม่, vector คมทุกขนาด, ตัวเลขผูกกับผลลัพธ์โดยตรง,
   สไตล์ผสมไทย–Latin ตามหน้าเว็บได้
3. **รูป static คงที่:** ไม่ "ตรงกับค่าที่ใส่" ตามที่ขอ — ตัดทิ้ง

## Constraints

- Python stdlib + Flask ตามเดิม; `bjt.py` ห้ามแก้
- ทุกค่าที่ render มาจาก dict ผลลัพธ์ของ `analyze` (ไม่คำนวณซ้ำใน template/SVG)
- ข้อความตัวเลขทั้งหมดปลอดภัยต่อ HTML (เป็นตัวเลข/หน่วยที่เราควบคุมเอง) แต่ string อื่นต้อง escape
- กรณี Cutoff กระแสทั้งหมดแสดง 0.000; กรณี Saturation แสดงค่าตามสูตร (VC/VCE อาจติดลบตาม spec เดิม)

## Design

### โมดูลใหม่: `circuit_svg.py`

- `format_current(amps: float) -> str` — ค่า < 1e-3 A แสดงเป็น `µA` (เช่น `12.9 µA`),
  ที่เหลือเป็น `mA` (เช่น `1.286 mA`); 0 แสดง `0.000`
- `build_circuit_svg(result: dict) -> str` — pure function; รับ dict ชุดเดียวกับ `analyze`
  (`result["inputs"]`, `result["exact"]`); คืนสตริง `<svg viewBox="0 0 480 400" …>` สมบูรณ์
  (เริ่ม `<svg` จบ `</svg>`, ไม่มี doctype); ไม่มี I/O, ไม่มี global state
- Layout: ซ้ายคือวงจร ขวาคือ β ในวงกลม (อยู่ในตัวทรานซิสเตอร์):
  - ราง VCC บนสุดจากซ้ายเข้า RC แล้วต่อผ่านลง collector
  - กิ่ง R1 (บน) และ R2 (ล่าง) อนุกรมลง VCC→GND พร้อมโหนดกลาง — เขียนกำกับ `VTH`, `RTH` ชิดกิ่ง
  - ทรานซิสเตอร์ NPN กึ่งกลาง: ขีดตั้ง collector/emitter, ลูกศรชี้เข้า? (NPN ลูกศรออกที่ emitter), β ในวงกลม
  - RE ลง GND ใต้ emitter; โหนด VE; โหนด VC บน RC
  - กระแส IB เข้าเบส, IC ไหลลง collector, IE ออก emitter — ลูกศรสี accent พร้อมค่า
  - VCE: เส้นมิติแนวตั้งคร่อม C–E ทางขวา พร้อมค่า
  - β = 100.0 ในวงกลมใหญ่แทนตัวทรานซิสเตอร์เล็กน้อย ตาม mock-up ทั่วไป
- ทุกข้อความ `<text>` ระบุ `font-family` สืบทอดจาก CSS

### Templates

- `templates/_circuit.html` — partial เฉพาะ `<div class="circuit-wrap">{{ circuit_svg | safe }}</div>…`
  ใช้ `| safe` เพราะ SVG สร้างจาก Python ของเราเองและค่าเป็นตัวเลขควบคุมได้ (escape string อื่นด้วย `html.escape`)
- `templates/index.html` — `{% include "_circuit.html" %}` ในตำแหน่งท้าย `{% if result %}`
- หน้าผลลัพธ์เหมือนเดิมทุกอย่าง; SVG อยู่ใต้ตารางผลลัพธ์ / ใต้คำเตือน

### CSS

- `.circuit-wrap { overflow-x: auto; }` svg { width: 100%; max-width: 520px; height: auto; }
- คลาสสำหรับเส้น/ตัวอักษรใน SVG ผ่าน attribute ตรง ๆ (fill, stroke) — ไม่พึ่ง CSS ภายนอกสำหรับสีหลัก

### Tests (`tests/test_circuit_svg.py`, `tests/test_app.py`)

1. `build_circuit_svg` กับผลลัพธ์ของ `analyze(**BASE)` — string ที่คืนมี `<svg`, `4.655`, `VCE`, `1.286`,
   `12.0` (VCC), `β`, และมีโหนด `VB`, `VE`, `VC`, `VTH`, `RTH`; ไม่มีคำว่า `nan`/`None`
2. Cutoff case — มี `0.000` สำหรับกระแส, ไม่มี `nan`
3. Saturation case — แสดงค่าตรงกับ `analyze` (เช่นมี substring `0.246` ของ IC_sat หรือ `VCE` ติดลบ)
4. `format_current` ครอบ: 0 → `0.000`, 1.286e-3 → `mA`, 12.86e-6 → `µA`
5. Route test — POST `/calculate` แล้ว HTML ประกอบด้วย marker `class="circuit-svg"` (หรือ id) และ `4.655`
   ทั้งใน SVG และตาราง

### ขนาดงาน

เล็ก — ไฟล์ใหม่ 1, แตะ template 2, CSS 1 ก้อน, tests 1 ไฟล์ + เคสใหม่ ~5 ตัว
