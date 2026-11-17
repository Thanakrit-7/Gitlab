เครื่องคำนวณวงจรไฟฟ้ากระแสตรง (DC) รองรับวงจรอนุกรม ขนาน และผสม โดยใช้ Python

## การใช้งาน

```powershell
python .\electrical.py
```

โปรแกรมจะถามค่าแรงดัน รูปแบบวงจร และค่าตัวต้านทาน จากนั้นแสดงความต้านทานรวม กระแส กำลัง และค่าของตัวต้านทานแต่ละตัว

สำหรับวงจรผสม ให้แต่ละกิ่งเป็นตัวต้านทานอนุกรม แล้วต่อกิ่งทั้งหมดแบบขนานกัน ตัวอย่าง 2 กิ่งที่กิ่งละ 2 ตัวต้านทาน: `10, 20` และ `30, 60`

## เว็บแอปคำนวณจุดทำงาน DC ของ BJT

Flask web app สำหรับคำนวณจุดทำงาน DC ของทรานซิสเตอร์ BJT แบบ NPN ในวงจร
Common-Emitter เลือกวงจรได้สามแบบ

- **Voltage Divider Bias** (Lab 2) — `R1`, `R2`, `RC`, `RE`
- **Fixed Bias** — `RB` ต่อจาก `VCC` ไป Base, Emitter ต่อลงกราวด์ตรง (`VE = 0`)
- **Emitter Bias** (แหล่งจ่ายเดียว) — `RB` ต่อจาก `VCC` ไป Base และ `RE` ต่อจาก Emitter ลงกราวด์

### ติดตั้ง

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### รัน

```powershell
.\.venv\Scripts\python.exe app.py
```

เปิด http://127.0.0.1:5000

### เลือกโหมดและอินพุต

เลือกโหมดจาก dropdown "เลือกวงจร" ด้านบนฟอร์ม แล้วกด "โหลดฟอร์ม" — หน้าจะโหลดใหม่และแสดง
เฉพาะฟิลด์ของโหมดนั้น (ไม่มี JavaScript)

- ทุกโหมด: `VCC` (V), `RC` (Ω), `β`, `VBE` (V)
- Voltage Divider: `R1`, `R2` (Ω), `RE` (Ω)
- Fixed: `RB` (Ω)
- Emitter: `RB`, `RE` (Ω)

### สมการที่ใช้ (Python)

- Fixed: `IB = (VCC − VBE) / RB`, `VE = 0`, `VB = VBE`
- Emitter: `IB = (VCC − VBE) / (RB + (β + 1)·RE)`
- Divider: `IB = (VTH − VBE) / (RTH + (β + 1)·RE)`, `VTH = VCC·R2/(R1+R2)`, `RTH = R1·R2/(R1+R2)`
- ร่วมกัน: `IC = β·IB`, `IE = (β + 1)·IB`, `VE = IE·RE`, `VB = VE + VBE`, `VC = VCC − IC·RC`, `VCE = VC − VE`

### ผลลัพธ์

- จุดทำงาน DC: `VTH`, `RTH`, `IB`, `IC`, `IE`, `VB`, `VE`, `VC`, `VCE` พร้อมหน่วย
- สถานะการทำงาน: Active / Cutoff / Saturation พร้อมคำเตือน
- (เฉพาะ Divider) ตารางเปรียบเทียบวิธีแม่นยำ (Thevenin) กับวิธีประมาณ (ไม่คิดกระแสเบส)
- สลับโหมด URL: `http://127.0.0.1:5000/?mode=fixed` (หรือ `emitter` / `divider`)

### ตัวอย่าง (Voltage Divider)

`VCC=12, R1=47000, R2=10000, RC=4700, RE=1000, β=100, VBE=0.7`

ได้ `IC = 1.286 mA`, `VCE = 4.655 V` และทำงานในย่าน Active

### ตัวอย่าง (Fixed Bias)

`VCC=12, RB=1000000, RC=2200, β=100, VBE=0.7` → `IC = 1.130 mA`, `VCE = 9.514 V`

### ตัวอย่าง (Emitter Bias)

`VCC=12, RB=1000000, RC=2200, RE=1000, β=100, VBE=0.7` → `IC = 1.026 mA`, `VCE = 8.705 V`

### ตรวจ Lab 03 (A1–A5)

ดู `docs/validation.md` หรือเปิดหน้าเว็บ **http://127.0.0.1:5000/validation** (มีลิงก์ "ตารางตรวจ A1–A5" ด้านบนทุกหน้า)
— ตรวจผ่าน Browser (เลือกโหมด กรอก แล้วอ่านผล) ตามตารางของนักศึกษา

### เทสต์

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```
