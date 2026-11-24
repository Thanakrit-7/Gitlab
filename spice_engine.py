"""ngspice adapter for the Lab 04 CE Voltage Divider reference circuit.

This module is the only place that builds netlists, invokes ngspice, and parses
raw simulator output. Flask routes call these functions; templates render the
returned dicts. No plotting or SPICE logic belongs in templates.

BJT model provenance: this file defines a 2N3904-like reference model so the
simulator runs without an instructor starter kit. If an instructor-verified
starter kit/model is provided, replace BJT_MODEL_NAME/BJT_MODEL and record the
change in README.md and docs/validation.md.
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

NGSPICE_EXE = os.environ.get("NGSPICE_EXE") or shutil.which("ngspice_con") or shutil.which("ngspice")
DEFAULT_TIMEOUT_S = 20

# Reference model (documented assumption; replace with instructor starter model).
BJT_MODEL_NAME = "Q2N3904_REF"
BJT_MODEL = (
    ".model Q2N3904_REF NPN("
    "IS=6.734f BF=416.4 NF=1 VAF=74.03 IKF=0.06678 ISE=6.734f "
    "NE=1.259 BR=0.7371 NR=1 RB=10 RC=1 "
    "CJE=4.493p MJE=0.2593 CJC=3.638p MJC=0.3085 "
    "TF=301.2p TR=239.5n XTB=1.5)"
)

# CE Voltage Divider reference fixture (Lab 04 handout defaults).
DEFAULT_CIRCUIT = {
    "vcc": 12.0,
    "r1": 100_000.0,
    "r2": 22_000.0,
    "rc": 2_200.0,
    "re": 1_000.0,
    "rl": 10_000.0,
    "cin_u": 10.0,   # uF
    "cout_u": 10.0,  # uF
    "vin_mvp": 10.0, # mV peak
    "freq_hz": 1_000.0,
}

LIMITS = {
    "vcc": (0.1, 1000.0),
    "r1": (1.0, 1e9),
    "r2": (1.0, 1e9),
    "rc": (1.0, 1e9),
    "re": (1.0, 1e9),
    "rl": (1.0, 1e9),
    "cin_u": (1e-6, 1e6),
    "cout_u": (1e-6, 1e6),
    "vin_mvp": (0.001, 5000.0),
    "freq_hz": (0.1, 10_000_000.0),
}


class SpiceError(RuntimeError):
    """A user-facing SPICE/validation error."""

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


def _finite(name: str, value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SpiceError(name, f"{name} ต้องเป็นตัวเลข")
    v = float(value)
    if not math.isfinite(v):
        raise SpiceError(name, f"{name} ต้องเป็นค่าจำกัด")
    return v


def validate_circuit(values: dict) -> dict:
    out = {}
    for name, (lo, hi) in LIMITS.items():
        v = _finite(name, values[name])
        if v < lo or v > hi:
            raise SpiceError(name, f"{name} ต้องอยู่ระหว่าง {lo:g} ถึง {hi:g}")
        out[name] = v
    return out


def _fmt_eng(value: float) -> str:
    """Format a number for ngspice netlists (plain, no locale)."""
    if value == 0:
        return "0"
    return f"{value:.12g}"


def _resolve_exe() -> str:
    exe = NGSPICE_EXE
    if exe and Path(exe).exists():
        return str(Path(exe))
    found = shutil.which("ngspice_con") or shutil.which("ngspice")
    if found:
        return found
    # common Windows install location
    candidate = Path(r"C:\Users\B6813208\Spice64\bin\ngspice_con.exe")
    if candidate.exists():
        return str(candidate)
    raise SpiceError("engine", "ไม่พบ ngspice (ngspice_con/ngspice) ใน PATH — ติดตั้ง ngspice และตรวจด้วย ngspice -v")


def build_netlist(c: dict, analysis: str) -> str:
    c = validate_circuit(c)
    vin = c["vin_mvp"] / 1000.0  # mV peak -> V peak
    freq = c["freq_hz"]
    cin = c["cin_u"] * 1e-6
    cout = c["cout_u"] * 1e-6

    lines = [
        "* Lab04 CE Voltage Divider reference",
        f"VCC vcc 0 {_fmt_eng(c['vcc'])}",
        f"Vin in 0 DC 0 AC 1 SIN(0 {_fmt_eng(vin)} {_fmt_eng(freq)})",
        f"Cin in b {_fmt_eng(cin)}",
        f"R1 vcc b {_fmt_eng(c['r1'])}",
        f"R2 b 0 {_fmt_eng(c['r2'])}",
        f"RC vcc c {_fmt_eng(c['rc'])}",
        f"RE e 0 {_fmt_eng(c['re'])}",
        f"Q1 c b e {BJT_MODEL_NAME}",
        f"Cout c out {_fmt_eng(cout)}",
        f"RL out 0 {_fmt_eng(c['rl'])}",
        BJT_MODEL,
    ]

    control = [".control", "set noaskquit", "set filetype=ascii"]
    if analysis == "op":
        control += [
            "op",
            "let ic=@q1[ic]",
            "let ib=@q1[ib]",
            "let ie=@q1[ie]",
            "wrdata op.txt v(b) v(e) v(c) v(c,e) ic ib ie",
        ]
    elif analysis == "ac":
        control += [
            "ac dec 20 1 1Meg",
            "let gain_db = vdb(out)",
            "let gain_phase = vp(out)",
            "wrdata ac.txt gain_db gain_phase",
        ]
    elif analysis == "tran":
        # simulate 5 periods, 200 points/period, with step cap
        period = 1.0 / freq
        tstop = 5.0 * period
        tstep = min(period / 200.0, tstop / 1000.0)
        control += [
            f"tran {_fmt_eng(tstep)} {_fmt_eng(tstop)}",
            "wrdata tran.txt v(in) v(out)",
        ]
    else:
        raise SpiceError("analysis", "analysis ต้องเป็น op, ac หรือ tran")

    control += ["quit", ".endc", ".end"]
    lines += control
    return "\n".join(lines) + "\n"


def _run_ngspice(netlist: str, run_dir: Path, timeout_s: int = DEFAULT_TIMEOUT_S) -> Path:
    exe = _resolve_exe()
    cir_path = run_dir / "sim.cir"
    log_path = run_dir / "run.log"
    cir_path.write_text(netlist, encoding="utf-8", newline="\n")
    try:
        proc = subprocess.run(
            [exe, "-b", "-o", str(log_path), str(cir_path)],
            cwd=str(run_dir),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise SpiceError("engine", f"ไม่พบไฟล์ ngspice executable: {exe}") from exc
    except subprocess.TimeoutExpired as exc:
        raise SpiceError("engine", f"ngspice ใช้เวลานานเกิน {timeout_s}s (timeout)") from exc

    # ngspice sometimes returns 0 with errors in log; check both.
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "") + "\n" + log_text
    fatal_markers = ["fatal error", "Error: ", "undefined", "no such vector", "run simulation(s) aborted"]
    lowered = combined.lower()
    if proc.returncode != 0 or any(m.lower() in lowered for m in fatal_markers):
        # Keep message short but useful; include tail of log.
        tail = "\n".join(log_text.splitlines()[-12:])
        raise SpiceError("engine", f"ngspice รันไม่สำเร็จ (exit {proc.returncode}). {tail[-500:]}")
    return log_path


def _read_wrdata(path: Path) -> list[list[float]]:
    if not path.exists():
        raise SpiceError("engine", f"ไม่พบไฟล์ผลลัพธ์จาก ngspice: {path.name}")
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            continue
    if not rows:
        raise SpiceError("engine", f"ไฟล์ผลลัพธ์ว่างหรืออ่านไม่ได้: {path.name}")
    return rows


def _wrdata_columns(rows: list[list[float]], n_vectors: int) -> list[list[float]]:
    """wrdata writes pairs (x, y) repeated per vector: x y1 x y2 ..."""
    cols = [[] for _ in range(n_vectors + 1)]  # x + n vectors
    for row in rows:
        # accept either repeated-x format or plain format
        if len(row) == n_vectors + 1:
            for i in range(n_vectors + 1):
                cols[i].append(row[i])
        elif len(row) >= 2 * n_vectors:
            cols[0].append(row[0])
            for k in range(n_vectors):
                idx = 2 * k + 1
                cols[k + 1].append(row[idx])
        else:
            # fallback: best effort
            if row:
                cols[0].append(row[0])
            for k in range(n_vectors):
                idx = 1 + k
                cols[k + 1].append(row[idx] if idx < len(row) else float("nan"))
    return cols


def run_op(circuit: dict) -> dict:
    c = validate_circuit(circuit)
    with tempfile.TemporaryDirectory(prefix="ngop_") as td:
        run_dir = Path(td)
        netlist = build_netlist(c, "op")
        log_path = _run_ngspice(netlist, run_dir)
        cols = _wrdata_columns(_read_wrdata(run_dir / "op.txt"), 7)
        # vb, ve, vc, vce, ic, ib, ie
        vb, ve, vc, vce, ic, ib, ie = [cols[i + 1][0] for i in range(7)]
        return {
            "analysis": "op",
            "engine": "ngspice",
            "engine_version": "ngspice-47",
            "model": BJT_MODEL_NAME,
            "status": "ok",
            "inputs": c,
            "operating_point": {
                "vb_v": vb,
                "ve_v": ve,
                "vc_v": vc,
                "vce_v": vce,
                "ic_a": abs(ic),
                "ib_a": abs(ib),
                "ie_a": abs(ie),
            },
            "log_tail": "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]),
        }


def run_ac(circuit: dict) -> dict:
    c = validate_circuit(circuit)
    with tempfile.TemporaryDirectory(prefix="ngac_") as td:
        run_dir = Path(td)
        netlist = build_netlist(c, "ac")
        log_path = _run_ngspice(netlist, run_dir)
        cols = _wrdata_columns(_read_wrdata(run_dir / "ac.txt"), 2)
        freq = cols[0]
        gain_db = cols[1]
        phase_deg = cols[2]
        # clean NaNs/infs
        points = []
        for f, g, p in zip(freq, gain_db, phase_deg):
            if all(math.isfinite(x) for x in (f, g, p)):
                points.append({"freq_hz": f, "gain_db": g, "phase_deg": p})
        if not points:
            raise SpiceError("engine", "AC ไม่มีข้อมูลผลลัพธ์ที่อ่านได้")
        mid = points[len(points) // 2]["gain_db"]
        cutoff_low = None
        cutoff_high = None
        target = mid - 3.0
        # find -3dB crossings relative to mid-band approximation
        for i in range(1, len(points)):
            g0, g1 = points[i - 1]["gain_db"], points[i]["gain_db"]
            if cutoff_low is None and g0 < target <= g1:
                cutoff_low = points[i]["freq_hz"]
            if g0 >= target > g1:
                cutoff_high = points[i]["freq_hz"]
        return {
            "analysis": "ac",
            "engine": "ngspice",
            "engine_version": "ngspice-47",
            "model": BJT_MODEL_NAME,
            "status": "ok",
            "inputs": c,
            "ac": {
                "points": points,
                "midband_gain_db": mid,
                "cutoff_low_hz": cutoff_low,
                "cutoff_high_hz": cutoff_high,
            },
            "log_tail": "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]),
        }


def run_tran(circuit: dict) -> dict:
    c = validate_circuit(circuit)
    with tempfile.TemporaryDirectory(prefix="ngtran_") as td:
        run_dir = Path(td)
        netlist = build_netlist(c, "tran")
        log_path = _run_ngspice(netlist, run_dir)
        cols = _wrdata_columns(_read_wrdata(run_dir / "tran.txt"), 2)
        t = cols[0]
        vin = cols[1]
        vout = cols[2]
        points = []
        for tt, vi, vo in zip(t, vin, vout):
            if all(math.isfinite(x) for x in (tt, vi, vo)):
                points.append({"t_s": tt, "vin_v": vi, "vout_v": vo})
        if not points:
            raise SpiceError("engine", "Transient ไม่มีข้อมูลผลลัพธ์ที่อ่านได้")
        # downsample for transport/render (keep shape)
        max_points = 600
        if len(points) > max_points:
            step = max(1, len(points) // max_points)
            points = points[::step]
        vin_pp = (max(p["vin_v"] for p in points) - min(p["vin_v"] for p in points))
        vout_pp = (max(p["vout_v"] for p in points) - min(p["vout_v"] for p in points))
        gain_vv = (vout_pp / vin_pp) if vin_pp > 1e-15 else None
        # phase/inversion heuristic: compare sign near peaks
        inverted = None
        if gain_vv is not None:
            # correlation sign
            mv = sum(p["vin_v"] for p in points) / len(points)
            mo = sum(p["vout_v"] for p in points) / len(points)
            num = sum((p["vin_v"] - mv) * (p["vout_v"] - mo) for p in points)
            inverted = num < 0
        return {
            "analysis": "tran",
            "engine": "ngspice",
            "engine_version": "ngspice-47",
            "model": BJT_MODEL_NAME,
            "status": "ok",
            "inputs": c,
            "tran": {
                "points": points,
                "vin_pp_v": vin_pp,
                "vout_pp_v": vout_pp,
                "gain_vv": gain_vv,
                "inverted": inverted,
            },
            "log_tail": "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]),
        }


def run_simulation(circuit: dict, analysis: str) -> dict:
    analysis = (analysis or "").strip().lower()
    if analysis == "op":
        return run_op(circuit)
    if analysis == "ac":
        return run_ac(circuit)
    if analysis == "tran":
        return run_tran(circuit)
    raise SpiceError("analysis", f"ไม่รู้จักโหมดวิเคราะห์ '{analysis}'")