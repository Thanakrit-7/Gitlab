เครื่องคำนวณวงจรไฟฟ้ากระแสตรง (DC) รองรับวงจรอนุกรม ขนาน และผสม โดยใช้ Python

## การใช้งาน (CLI เดิม)

```powershell
python .\electrical.py
```

โปรแกรมจะถามค่าแรงดัน รูปแบบวงจร และค่าตัวต้านทาน จากนั้นแสดงความต้านทานรวม กระแส กำลัง และค่าของตัวต้านทานแต่ละตัว

---

# Lab 04 — BJT CE Amplifier Simulator v1

ต่อยอดจาก Lab 3 (Flask BJT DC Bias Web App) โดยคง DC Bias 3 โหมดเดิม (Voltage Divider / Fixed / Emitter) และเพิ่มการจำลอง **Common-Emitter Voltage Divider reference** ด้วย **ngspice จริง**: DC `.op`, AC `.ac`, Transient `.tran`

## โครงสร้างสำคัญ

- `app.py` — Flask routes, validation, dispatch Analytical / SPICE
- `bjt.py` — สูตร Analytical DC bias เดิม (Lab 3) **ห้ามเปลี่ยนพฤติกรรมเดิม**
- `spice_engine.py` — สร้าง netlist, รัน `ngspice_con -b`, parse ผลจริง, timeout/error handling (`shell=False`)
- `plot_svg.py` — สร้างกราฟ SVG จากข้อมูล ngspice ที่ parse แล้ว (ไม่มี mock/hard-code)
- `circuit_svg.py` — ภาพวงจรตามโหมด
- `templates/index.html`, `static/style.css` — UI
- `docs/validation.md` — ตาราง B1–B8 พร้อมหลักฐาน
- `tests/` — เทสต์เดิม Lab 2/3 ต้องผ่าน

## ติดตั้ง

### 1) Python venv

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2) ngspice (จำเป็นสำหรับ SPICE mode)

ติดตั้ง ngspice ให้เรียกได้จาก terminal เดียวกับที่รัน Flask:

```powershell
ngspice_con --version
# หรือ
ngspice -v
```

โปรเจกต์นี้ทดสอบกับ:
- **ngspice-47** (Windows 64-bit console, KLU)  
- Binary: `C:\Users\B6813208\Spice64\bin\ngspice_con.exe` (เพิ่มใน User PATH)

ดาวน์โหลดทางการ: https://ngspice.sourceforge.io/download.html (ngspice-47_64.7z)

> ถ้า `ngspice_con` ไม่อยู่ใน PATH ให้ตั้ง env `NGSPICE_EXE` ชี้ไปที่ executable ก่อนรัน Flask

## รัน

```powershell
.\.venv\Scripts\python.exe app.py
```

เปิด http://127.0.0.1:5000

## วิธีใช้ Lab 4

1. เลือกโหมดวงจร (Divider/Fixed/Emitter) — **Fixed/Emitter ใช้ Analytical เดิมเหมือน Lab 3**
2. ถ้าเลือก **Voltage Divider** จะเลือก Analysis ได้:
   - `Analytical DC (Lab 3)` — สูตรเดิม
   - `SPICE DC (.op)` — ngspice operating point จริง
   - `SPICE AC (.ac)` — Bode magnitude/phase
   - `SPICE Transient (.tran)` — Vin/Vout vs time
3. กรอกพารามิเตอร์วงจรและแหล่งสัญญาณ (RL, Cin, Cout, Vin amplitude mV peak, Frequency Hz) แล้วกด **Run Simulation**
4. ผล SPICE จะแสดงป้าย **Engine/Model/Status** และ log tail; กราฟสร้างจากข้อมูล parse จริง

## วงจรอ้างอิง CE (Lab 4 v1)

- VCC=12V, R1=100kΩ, R2=22kΩ, RC=2.2kΩ, RE=1kΩ, RL=10kΩ, Cin=10µF, Cout=10µF
- Source: 10 mV peak, 1 kHz (SIN)
- BJT model: `Q2N3904_REF` (นิยามใน `spice_engine.py`)

**Provenance note:** ไม่มี instructor-verified starter kit ในเครื่องตอนพัฒนา — model นี้เป็น reference model ที่ระบุชัดเจนเพื่อให้รันซ้ำได้ หากผู้สอนแจก starter kit/model ให้แทนที่และอัปเดต README + `docs/validation.md`

## เทสต์

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

ผลล่าสุดที่รัน: **61 tests, OK** (หลังเพิ่ม Lab 4 integration; เทสต์เดิมทั้งหมดยังผ่าน)

## Validation (B1–B8)

ดู `docs/validation.md` — บันทึก B1–B8, วิธีตรวจ, ค่าที่เห็นจริง, สถานะ, หมายเหตุ

สรุปผลรันจริง: B1 PASS, B2 PASS, B3 PASS, B4 PASS, B5 PASS, B6 PASS, B7 PASS, B8 PASS (with note เรื่อง mobile viewport capture)

## UI (Impeccable)

ติดตั้ง Impeccable skill ในโปรเจกต์แล้ว (`npx impeccable install --providers=opencode --scope=project --yes`) และใช้แนวทาง critique/polish: จัดกลุ่ม input, แสดง engine/model/status/provenance ชัด, กราฟมีแกนและหน่วย, error state ไม่แสดง success ปลอม. การเปลี่ยน UI ไม่แตะสูตรใน `bjt.py`.

## ข้อจำกัด / สมมติฐาน

- SPICE รองรับเฉพาะ CE Voltage Divider reference circuit (Lab 4 v1) — Fixed/Emitter ยังเป็น Analytical
- ค่า SPICE กับ Analytical อาจต่างกันเพราะใช้ BJT model/สมมติฐานคนละแบบ
- ไม่มี CE bypass capacitor ใน baseline
- กราฟเป็น SVG server-side จาก parsed data (ไม่ใช้ Chart.js CDN)
- B8 mobile viewport capture เต็มรูปแบบควรทำซ้ำด้วย Playwright MCP viewport ก่อนส่งสุดท้ายหากมีเวลา

## AI / ผู้พัฒนา

- AI ช่วย: วางโครง integration, เขียน `spice_engine.py`/`plot_svg.py`, แก้ app/template/css, รันเทสต์และ browser checks
- ผู้พัฒนาตรวจ: สมมติฐาน model, ความถูกต้องของค่า/หน่วย, ผล B1–B8 เทียบค่าจริง, ความปลอดภัย subprocess (`shell=False`, timeout), และไม่ให้ผล SPICE ปลอมหลุดเป็น success
