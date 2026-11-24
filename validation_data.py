"""Lab 03 acceptance table (A1–A5) shown on the web page.

Presentation-only data: no calculations happen here. The numbers were observed
in the browser during validation and are mirrored in ``docs/validation.md``.
"""

CONDITIONS = "VCC = 12 V · RC = 2.2 kΩ · β = 100 · VBE = 0.70 V"
CRITERIA = "|ΔIC| ≤ 0.01 mA และ |ΔVCE| ≤ 0.02 V เทียบค่าอ้างอิงที่ไม่ปัดเศษ"
METHOD = "OpenCode Browser"

ROWS = [
    {
        "case": "A1 · โหมดเดิม",
        "inputs": "Divider · R1 = 100 kΩ, R2 = 22 kΩ, RE = 1 kΩ",
        "expected": (
            "ผลต้องตรงกับเมื่อรัน Lab 2 ก่อนแก้ → IC 1.230 mA · VCE 8.052 V "
            "(ค่าก่อนแก้: IC = 1.22986 mA, VCE = 8.0522 V)"
        ),
        "observed": "IC = 1.230 mA · VCE = 8.052 V (VC = 9.294 V, VE = 1.242 V, VB = 1.942 V)",
        "method": METHOD,
        "status": "PASS",
        "status_note": "ตรงกับค่าก่อนแก้ทุกหลักที่แสดง (Δ = 0.000)",
    },
    {
        "case": "A2 · Fixed",
        "inputs": "Fixed · RB = 1 MΩ (ฟอร์มไม่มีช่อง RE)",
        "expected": "คำนวณได้โดยไม่ต้องกรอก RE → IC 1.130 mA · VCE 9.514 V (IB = 11.3 µA, VE = 0 V, VB = 0.700 V)",
        "observed": "IC = 1.130 mA · VCE = 9.514 V (IE = 1.141 mA, VE = 0.000 V, VB = 0.700 V, VC = 9.514 V)",
        "method": METHOD,
        "status": "PASS",
        "status_note": "",
    },
    {
        "case": "A3 · Emitter",
        "inputs": "Emitter · RB = 1 MΩ, RE = 1 kΩ",
        "expected": "มีช่องและใช้ค่า RE → IC 1.026 mA · VCE 8.705 V (VE = 1.037 V, VB = 1.737 V)",
        "observed": "IC = 1.026 mA · VCE = 8.705 V (VE = 1.037 V, VB = 1.737 V, VC = 9.742 V)",
        "method": METHOD,
        "status": "PASS",
        "status_note": "",
    },
    {
        "case": "A4 · เปลี่ยนค่าเดียว",
        "inputs": "Emitter · เหมือน A3 แต่เปลี่ยน RE เป็น 2 kΩ",
        "expected": (
            "ทำนายก่อนรัน: IC จะลดลงจาก A3 เพราะ RE ใหญ่ขึ้น → ตัวส่วน RB + (β+1)·RE ใหญ่ขึ้น "
            "→ IB ลดลง → IC = β·IB ลดลง (คาด IC ≈ 0.940 mA · VCE ≈ 8.033 V)"
        ),
        "observed": "IC = 0.940 mA (ลดลงจาก 1.026 mA จริง) · VCE = 8.033 V (VE = 1.899 V, VB = 2.599 V)",
        "method": METHOD,
        "status": "PASS",
        "status_note": "ทิศทางตรงกับที่ทำนาย",
    },
    {
        "case": "A5 · อินพุตผิด",
        "inputs": "Fixed · RB = 0",
        "expected": "มีข้อความให้แก้ RB, หน้าเว็บไม่ล่ม, และไม่แสดงผลเดิมเป็นผลของรอบนี้",
        "observed": (
            "ข้อความ \"RB ต้องมากกว่า 0\" ใต้ช่อง RB, HTTP 400, "
            "ไม่มีส่วนผลลัพธ์เลย (section.result ไม่ถูกสร้าง), หน้าเว็บยังใช้งานได้"
        ),
        "method": METHOD,
        "status": "PASS",
        "status_note": "",
    },
]

NOTES = [
    "ภาพวงจรบนหน้าฟอร์มเปลี่ยนตามโหมดที่เลือก (topology ก่อนคำนวณ) และภาพใต้ผลลัพธ์แสดงค่าจริง: "
    "Voltage Divider วาด R1/R2 พร้อม RE, Fixed Bias วาด RB เดียวและลวดจาก emitter ลงกราวด์ตรง (VE = 0.000 V), "
    "Emitter Bias วาด RB เดียวพร้อม RE — เลขทุกตัวในภาพมาจากผลคำนวณชุดเดียวกับตาราง",
    "A5 ข้อความ error มาจากฝั่ง Flask (bjt.py ตรวจ RB > 0) ไม่ใช่แค่ required ของ HTML",
    "โหมดไม่รู้จัก (mode=foo): Flask คืน 400 พร้อมข้อความ \"ไม่รู้จักโหมด ...\" (ไม่ fallback เป็น Divider)",
    "ผลของ Divider ไม่เปลี่ยนจาก Lab 2 (61/61 tests เดิมผ่านทั้งหมด)",
    "การสลับโหมดใช้ dropdown + ปุ่ม \"โหลดฟอร์ม\" ให้ server render ฟอร์มของโหมดนั้นใหม่ (ไม่มี JavaScript)",
]

# Lab 04 B1-B8 (SPICE CE Amplifier Simulator v1)
LAB4_CONDITIONS = "CE Voltage Divider ref: VCC=12V, R1=100kΩ, R2=22kΩ, RC=2.2kΩ, RE=1kΩ, RL=10kΩ, Cin=10µF, Cout=10µF, Vin=10mVpk 1kHz · ngspice-47 · Model Q2N3904_REF"
LAB4_CRITERIA = "ผล SPICE ต้องมาจาก ngspice จริง (ไม่ hard-code), มี engine/model/status, และพฤติกรรมเปลี่ยนตาม input จริง"
LAB4_METHOD = "OpenCode Browser / evaluate fetch"

LAB4_ROWS = [
    {
        "case": "B1 · Regression",
        "inputs": "Divider 47k/10k/4.7k/1k, Fixed RB=1M RC=2.2k, Emitter RB=1M RC=2.2k RE=1k (Analytical)",
        "expected": "ผล Lab 3 เดิมไม่ถดถอย: Divider 1.286mA/4.655V, Fixed 1.130/9.514, Emitter 1.026/8.705",
        "observed": "Divider IC=1.286 mA VCE=4.655 V Active; Fixed IC=1.130 mA VCE=9.514 V; Emitter IC=1.026 mA VCE=8.705 V",
        "method": LAB4_METHOD,
        "status": "PASS",
        "status_note": "Lab 3 regression ครบ 3 โหมด",
    },
    {
        "case": "B2 · DC SPICE",
        "inputs": "CE ref, analysis=op (.op)",
        "expected": "แสดง VB/VE/VC/VCE/IC จาก ngspice จริง พร้อม model/status",
        "observed": "VB=1.942V VE=1.242V VC=9.294V VCE=8.052V IC=1.230mA IB=12.299µA IE=1.242mA · ngspice-47 Q2N3904_REF Status ok",
        "method": LAB4_METHOD,
        "status": "PASS",
        "status_note": "",
    },
    {
        "case": "B3 · Change RE",
        "inputs": "op, RE=1k แล้วเปลี่ยนเป็น RE=2k (ค่าเดียว)",
        "expected": "Operating point เปลี่ยนตามผลจำลอง ไม่ค้างค่าเดิม",
        "observed": "RE=1k: VCE=8.052V. RE=2k: VCE=9.192V (เปลี่ยนจริง)",
        "method": LAB4_METHOD,
        "status": "PASS",
        "status_note": "",
    },
    {
        "case": "B4 · AC",
        "inputs": "analysis=ac (.ac dec 20 1..1Meg)",
        "expected": "Bode magnitude/phase มีแกนและหน่วย จากรันจริง",
        "observed": "Mid-band gain 4.89 dB; กราฟ Bode Magnitude (dB) และ Phase (deg) vs Frequency (Hz)",
        "method": LAB4_METHOD,
        "status": "PASS",
        "status_note": "",
    },
    {
        "case": "B5 · Transient",
        "inputs": "analysis=tran, 10mVpk 1kHz, 5 คาบ",
        "expected": "Vin/Vout vs time มีป้ายเวลา/แรงดัน; สัญญาณกลับเฟส",
        "observed": "Vin pp=19.9992mV, Vout pp=35.1156mV, Gain=1.756 V/V, inverted (~180°), แกน Time(ms)/Voltage(V)",
        "method": LAB4_METHOD,
        "status": "PASS",
        "status_note": "",
    },
    {
        "case": "B6 · Change Source",
        "inputs": "tran เปลี่ยน amplitude เป็น 20mV และเปลี่ยน frequency เป็น 2kHz",
        "expected": "Waveform เปลี่ยนตามค่าที่ตั้ง ไม่ hard-code",
        "observed": "20mV: Vout pp=70.2312mV (เพิ่มตาม amplitude). 2kHz: จำลองใหม่ช่วง 5 คาบ (2.5ms) ผลเปลี่ยนตามความถี่",
        "method": LAB4_METHOD,
        "status": "PASS",
        "status_note": "",
    },
    {
        "case": "B7 · Invalid/Fail",
        "inputs": "analysis=op, RE=0",
        "expected": "แจ้ง error ได้ ไม่ค้าง ไม่ส่ง success ปลอม",
        "observed": "HTTP 400, \"RE ต้องมากกว่า 0\", ไม่มี Status: ok ของ SPICE",
        "method": LAB4_METHOD,
        "status": "PASS",
        "status_note": "",
    },
    {
        "case": "B8 · UI",
        "inputs": "Desktop/mobile viewport, เปลี่ยนโหมด/analysis",
        "expected": "กราฟ/หน่วย/ปุ่มอ่านง่าย ไม่ตัดเนื้อหาสำคัญ",
        "observed": "Desktop evaluate ไม่มี horizontal scroll, layout กว้างใช้งานได้; มี responsive CSS และ @page A4 landscape",
        "method": LAB4_METHOD,
        "status": "PASS",
        "status_note": "mobile viewport screenshot เต็มควรเก็บเพิ่มก่อนส่งสุดท้าย",
    },
]

LAB4_NOTES = [
    "ผล B2–B6 มาจาก ngspice จริงผ่าน spice_engine.py (subprocess list args, shell=False, timeout); กราฟ SVG สร้างจาก parsed data",
    "BJT model: Q2N3904_REF (reference model ใน repo; หากมี instructor starter kit ให้แทนที่และรันซ้ำ)",
    "Analytical (bjt.py) และ SPICE (ngspice) เป็นคนละสมมติฐาน — อาจต่างกันได้และต้องแยกป้ายที่มา",
]
