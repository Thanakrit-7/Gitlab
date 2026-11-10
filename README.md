เครื่องคำนวณวงจรไฟฟ้ากระแสตรง (DC) รองรับวงจรอนุกรม ขนาน และผสม โดยใช้ Python

## การใช้งาน

```powershell
python .\electrical.py
```

โปรแกรมจะถามค่าแรงดัน รูปแบบวงจร และค่าตัวต้านทาน จากนั้นแสดงความต้านทานรวม กระแส กำลัง และค่าของตัวต้านทานแต่ละตัว

สำหรับวงจรผสม ให้แต่ละกิ่งเป็นตัวต้านทานอนุกรม แล้วต่อกิ่งทั้งหมดแบบขนานกัน ตัวอย่าง 2 กิ่งที่กิ่งละ 2 ตัวต้านทาน: `10, 20` และ `30, 60`

## เว็บแอปคำนวณจุดทำงาน DC ของ BJT

Flask web app สำหรับคำนวณจุดทำงาน DC ของทรานซิสเตอร์ BJT แบบ NPN ในวงจร
Common-Emitter แบบ Voltage Divider Bias

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

### อินพุต

`VCC` (V), `R1` (Ω), `R2` (Ω), `RC` (Ω), `RE` (Ω), `β`, `VBE` (V)

### ผลลัพธ์

- จุดทำงาน DC: `VTH`, `RTH`, `IB`, `IC`, `IE`, `VB`, `VE`, `VC`, `VCE` พร้อมหน่วย
- สถานะการทำงาน: Active / Cutoff / Saturation พร้อมคำเตือน
- ตารางเปรียบเทียบวิธีแม่นยำ (Thevenin) กับวิธีประมาณ (ไม่คิดกระแสเบส)
  พร้อมส่วนต่างและเปอร์เซ็นต์

### ตัวอย่าง

`VCC=12, R1=47000, R2=10000, RC=4700, RE=1000, β=100, VBE=0.7`

ได้ `IC = 1.286 mA`, `VCE = 4.655 V` และทำงานในย่าน Active

### เทสต์

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```
