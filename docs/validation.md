# ตารางตรวจ Lab 04 — B1–B8 (BJT CE Amplifier Simulator v1)

เว็บ: http://127.0.0.1:5000/ (Flask)  
วิธีตรวจจริง: **OpenCode Browser / Playwright MCP-style browser tools** (navigate, evaluate/fetch, snapshot, read DOM values) บนหน้าเว็บจริงที่รันจาก Flask local  
Engine: **ngspice-47** (`ngspice_con.exe`, KLU), ติดตั้งที่ `C:\Users\B6813208\Spice64\bin\`  
BJT model: **Q2N3904_REF** (นิยามใน `spice_engine.py` เป็น reference model; ไม่ใช่ starter kit จากผู้สอน — หากผู้สอนแจก model ให้เปลี่ยนและบันทึก provenance ใหม่)

> หมายเหตุความซื่อสัตย์: ผล SPICE ในตารางนี้มาจากการรัน ngspice จริงผ่าน `spice_engine.py` (subprocess, no shell). กราฟและตัวเลขไม่ได้ hard-code. ผล Analytical (bjt.py) เป็นอีกชุดหนึ่ง — อาจต่างจาก SPICE ได้เพราะสมมติฐานคนละแบบ.

## B1–B8

| Case | Method | Input | Expected / Reference | Observed (Browser) | Evidence | Status |
|---|---|---|---|---|---|---|
| **B1 · Regression** | Browser fetch POST `/calculate` (โหมด analytical) | Divider: VCC=12,R1=47k,R2=10k,RC=4.7k,RE=1k,β=100,VBE=0.7 · Fixed: VCC=12,RB=1M,RC=2.2k,β=100,VBE=0.7 · Emitter: VCC=12,RB=1M,RC=2.2k,RE=1k,β=100,VBE=0.7 | Divider: IC=1.286 mA, VCE=4.655 V (Lab 3). Fixed: IC=1.130 mA, VCE=9.514 V. Emitter: IC=1.026 mA, VCE=8.705 V. สลับโหมดได้ | Divider: IC=**1.286 mA**, VCE=**4.655 V**, Active. Fixed: IC=**1.130 mA**, VCE=**9.514 V**. Emitter: IC=**1.026 mA**, VCE=**8.705 V** | Browser DOM values via evaluate/fetch; HTTP 200; analytical labels visible | **PASS** |
| **B2 · DC SPICE** | Browser POST `/calculate` analysis=op | CE Divider ref: VCC=12,R1=100k,R2=22k,RC=2.2k,RE=1k,RL=10k,Cin=10u,Cout=10u,source 10mV 1kHz | แสดง VB/VE/VC/VCE/IC จาก ngspice output จริง พร้อม engine/model/status | VB=**1.942 V**, VE=**1.242 V**, VC=**9.294 V**, VCE=**8.052 V**, IC=**1.230 mA**, IB=**12.299 µA**, IE=**1.242 mA**. Engine: **ngspice ngspice-47**, Model: **Q2N3904_REF**, Status: **ok** | Browser DOM + `ngspice-47`/`Q2N3904_REF`/`Status: ok` present | **PASS** |
| **B3 · Change RE** | Browser POST op, RE=1k then RE=2k | เปลี่ยน RE ค่าเดียว | Operating point ต้องเปลี่ยน ไม่ค้างค่าเดิม | RE=1k: VCE=**8.052 V**. RE=2k: VCE=**9.192 V** (เปลี่ยนจริง) | Two browser responses compared | **PASS** |
| **B4 · AC** | Browser POST analysis=ac | CE ref เดิม, .ac dec 20 1..1Meg | Bode magnitude/phase มีแกน/หน่วย และค่าจากรันจริง | Mid-band gain: **4.89 dB**. มีกราฟ **Bode Magnitude (ngspice .ac)**, **Bode Phase (ngspice .ac)**, แกน Frequency (Hz)/Gain (dB)/Phase (deg) | Browser DOM: hasGain/hasPhase true, mid-band value shown | **PASS** |
| **B5 · Transient** | Browser POST analysis=tran | 10 mV peak, 1 kHz, 5 periods | Vin/Vout vs time มีป้ายเวลา/แรงดัน; สัญญาณกลับเฟส CE | Vin pp: **19.9992 mV**, Vout pp: **35.1156 mV**, Gain: **1.756 V/V**, Phase: **inverted (~180°)**. กราฟ Transient มีแกน Time (ms), Voltage (V), legend Vin/Vout | Browser DOM values and plot labels | **PASS** |
| **B6 · Change Source** | Browser POST tran, เปลี่ยน amplitude แล้ว frequency | เปลี่ยน amplitude/frequency แล้ว Run ซ้ำ | Waveform เปลี่ยนตามค่า ไม่ hard-code | 10mV 1kHz: Vout pp **35.1156 mV**. 20mV 1kHz: Vout pp **70.2312 mV** (เปลี่ยนตาม amplitude). 10mV 2kHz: run สำเร็จ, waveform ถูกสร้างใหม่สำหรับ 2kHz (ช่วงเวลา 5 คาบ=2.5ms) | Three browser responses compared | **PASS** |
| **B7 · Invalid / Fail** | Browser POST analysis=op, RE=0 | RE=0 หรือ engine ไม่พร้อม | แจ้ง error ได้ ไม่ค้าง ไม่ส่งผลสำเร็จปลอม | HTTP **400**, ข้อความ **"RE ต้องมากกว่า 0"**, ไม่มี `Status: ok` ของ SPICE | Browser DOM; status 400 | **PASS** |
| **B8 · UI** | Browser snapshot/evaluate + responsive CSS | Desktop/mobile viewport, เปลี่ยนโหมด | กราฟ/หน่วย/ปุ่มอ่านง่าย ไม่ตัดเนื้อหาสำคัญ | Desktop (~764px ใน browser pane): ไม่มี horizontal scroll, grid 2 คอลัมน์, diagram/plots แสดงได้. มี `@media (max-width:560px)` ให้ grid เป็น 1 คอลัมน์; table-wrap มี overflow-x. ตรวจ mobile จริงด้วย Playwright viewport เต็มควรทำซ้ำก่อนส่งถ้ามีโอกาส | Browser evaluate layout info; CSS responsive rules present | **PASS (with note)** |

## หมายเหตุ B1–B8

- B1 ยืนยัน Lab 3 regression ครบ 3 โหมด; ค่าตรงกับชุดอ้างอิงเดิม
- B2/B3/B4/B5/B6 เป็นผลจาก `ngspice` จริงผ่าน `spice_engine.py` (subprocess `['ngspice_con','-b','-o',log,cir]`, `shell=False`, timeout)
- B4 แสดงค่า mid-band gain และกราฟ Bode; cutoff -3dB จะแสดง "not determined in sweep range" หาก sweep ไม่ครอบคลุม
- B7 ทดสอบ validation ฝั่ง server; กรณี engine ไม่พร้อมได้จัดการด้วย `SpiceError` และไม่คืน `Status: ok`
- B8 ตรวจ layout โดย evaluate/CSS; ไม่ได้จับ screenshot mobile viewport แยกผ่าน Playwright MCP เต็มรูปแบบในรอบนี้ (บันทึกตามจริง)

## Lab 03 A1–A5 (คงไว้เป็นประวัติ)

ตาราง A1–A5 เดิมของ Lab 3 อยู่ใน git history และถูกรวมไว้ในหน้า `/validation` (Lab 03). ผล Divider/Fixed/Emitter A1–A5 ยังผ่าน regression ตาม B1.
