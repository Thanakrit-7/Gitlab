# AGENTS.md — Lab 04 BJT CE Amplifier Simulator v1

## กติกาสำหรับ AI/ผู้พัฒนา

- **ห้ามทำลาย Lab 3**: DC Bias 3 โหมด (divider/fixed/emitter) และเทสต์เดิมต้องยังผ่าน
- **Reuse before rebuild**: ใช้ `bjt.py`, `app.py`, templates เดิมเป็นฐาน ขยายเฉพาะที่จำเป็น
- **SPICE จริงเท่านั้น**: ห้าม hard-code กราฟ/ผล, ห้าม mock data ที่ทำให้ดูเหมือนรันสำเร็จ
- **แยก provenance**: ผล Analytical (bjt.py) กับผล SPICE (ngspice) ต้องมีป้ายที่มาแยกกันชัดเจน
- **Subprocess ปลอดภัย**: เรียก ngspice ด้วย list args, `shell=False`, มี `timeout`, ตรวจ exit code/log/error
- **Error ต้องซื่อสัตย์**: engine ไม่พบ, timeout, parse fail, input ผิด → แสดง error ชัด และ **ไม่** คืนสถานะ success ปลอม
- **Model provenance**: ระบุชื่อ/เวอร์ชัน ngspice และ BJT model ที่ใช้จริงใน README และ docs/validation.md
- **ไม่ commit ของลับ/ขยะ**: ไม่ใส่ `.venv/`, `.env`, token, ไฟล์ชั่วคราวรัน ngspice
- **ตรวจก่อนเคลม PASS**: B1–B8 ต้องอิงหลักฐานจาก browser/tool จริง; ถ้าไม่ได้รันให้บันทึก NOT RUN พร้อมเหตุผล

## โครงโมดูล

- `bjt.py` — Analytical DC (Lab 3)
- `spice_engine.py` — ngspice netlist/run/parse (Lab 4)
- `plot_svg.py` — SVG charts จาก parsed SPICE data
- `app.py` — Flask route/validation/dispatch
- `templates/`, `static/` — UI

## ก่อน commit

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```