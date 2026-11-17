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
    "ภาพวงจรใต้ผลลัพธ์เปลี่ยนตามโหมดที่เลือก: Voltage Divider วาด R1/R2 พร้อม RE, "
    "Fixed Bias วาด RB เดียวและลวดจาก emitter ลงกราวด์ตรง (VE = 0.000 V), "
    "Emitter Bias วาด RB เดียวพร้อม RE — เลขทุกตัวในภาพมาจากผลคำนวณชุดเดียวกับตาราง",
    "A5 ข้อความ error มาจากฝั่ง Flask (bjt.py ตรวจ RB > 0) ไม่ใช่แค่ required ของ HTML",
    "โหมดไม่รู้จัก (mode=foo): Flask คืน 400 พร้อมข้อความ \"ไม่รู้จักโหมด ...\" (ไม่ fallback เป็น Divider)",
    "ผลของ Divider ไม่เปลี่ยนจาก Lab 2 (61/61 tests เดิมผ่านทั้งหมด)",
    "การสลับโหมดใช้ dropdown + ปุ่ม \"โหลดฟอร์ม\" ให้ server render ฟอร์มของโหมดนั้นใหม่ (ไม่มี JavaScript)",
]
