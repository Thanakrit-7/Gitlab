"""Server-side SVG charts for Lab 04 (no JS dependencies).

Charts are generated from parsed ngspice data only.
"""

from __future__ import annotations

import html
import math


def _esc(v):
    return html.escape(str(v), quote=True)


def _nice_ticks(vmin, vmax, n=5):
    if not math.isfinite(vmin) or not math.isfinite(vmax):
        return [0.0]
    if vmax == vmin:
        vmax = vmin + 1.0
    span = vmax - vmin
    step = span / max(n - 1, 1)
    mag = 10 ** math.floor(math.log10(step)) if step > 0 else 1
    norm = step / mag
    if norm <= 1:
        nice = 1
    elif norm <= 2:
        nice = 2
    elif norm <= 5:
        nice = 5
    else:
        nice = 10
    step = nice * mag
    start = math.floor(vmin / step) * step
    ticks = []
    x = start
    for _ in range(20):
        if x > vmax + step * 0.5:
            break
        ticks.append(x)
        x += step
    return ticks or [vmin, vmax]


def _fmt(v):
    av = abs(v)
    if av >= 1000 or (0 < av < 0.01):
        return f"{v:.3g}"
    if float(v).is_integer():
        return f"{int(v)}"
    return f"{v:.4g}"


def line_chart(series, *, x_label, y_label, title, width=760, height=320, x_log=False, y_ticks=None):
    """series: [{name,color,points:[(x,y),...]}]"""
    pad_l, pad_r, pad_t, pad_b = 64, 20, 36, 52
    iw, ih = width - pad_l - pad_r, height - pad_t - pad_b

    all_pts = [(x, y) for s in series for x, y in s["points"] if math.isfinite(x) and math.isfinite(y)]
    if not all_pts:
        return '<div class="plot-empty">ไม่มีข้อมูลสำหรับวาดกราฟ</div>'

    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if x_log:
        xs_pos = [x for x in xs if x > 0]
        xmin = min(xs_pos) if xs_pos else 1.0
        xmax = max(xs_pos) if xs_pos else 10.0
    if ymin == ymax:
        ymin -= 1
        ymax += 1
    # small padding
    ypad = (ymax - ymin) * 0.08
    ymin -= ypad
    ymax += ypad

    def sx(x):
        if x_log:
            x = max(x, xmin)
            return pad_l + (math.log10(x) - math.log10(xmin)) / max(math.log10(xmax) - math.log10(xmin), 1e-9) * iw
        return pad_l + (x - xmin) / max(xmax - xmin, 1e-9) * iw

    def sy(y):
        return pad_t + ih - (y - ymin) / max(ymax - ymin, 1e-9) * ih

    yticks = y_ticks or _nice_ticks(ymin, ymax, 6)
    xticks = []
    if x_log:
        p = 10 ** math.floor(math.log10(xmin))
        while p <= xmax * 1.01:
            for m in [1, 2, 5]:
                v = m * p
                if xmin <= v <= xmax * 1.01:
                    xticks.append(v)
            p *= 10
    else:
        xticks = _nice_ticks(xmin, xmax, 6)

    parts = [f'<svg class="plot-svg" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{_esc(title)}">']
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fcfdfe"/>')
    parts.append(f'<text x="{width/2}" y="22" text-anchor="middle" font-size="13" font-weight="700" fill="#183954">{_esc(title)}</text>')

    # grid + y ticks
    for t in yticks:
        y = sy(t)
        if y < pad_t - 2 or y > pad_t + ih + 2:
            continue
        parts.append(f'<line x1="{pad_l}" y1="{y:.2f}" x2="{pad_l+iw}" y2="{y:.2f}" stroke="#dbe7ee" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l-8}" y="{y+4:.2f}" text-anchor="end" font-size="11" fill="#567">{_esc(_fmt(t))}</text>')
    # x ticks
    for t in xticks:
        x = sx(t)
        if x < pad_l - 2 or x > pad_l + iw + 2:
            continue
        parts.append(f'<line x1="{x:.2f}" y1="{pad_t}" x2="{x:.2f}" y2="{pad_t+ih}" stroke="#edf3f7" stroke-width="1"/>')
        parts.append(f'<text x="{x:.2f}" y="{pad_t+ih+20}" text-anchor="middle" font-size="11" fill="#567">{_esc(_fmt(t))}</text>')

    # axes
    parts.append(f'<rect x="{pad_l}" y="{pad_t}" width="{iw}" height="{ih}" fill="none" stroke="#9bb1c1"/>')
    parts.append(f'<text x="{pad_l+iw/2}" y="{height-10}" text-anchor="middle" font-size="12" fill="#355">{_esc(x_label)}</text>')
    parts.append(f'<text transform="translate(18 {pad_t+ih/2}) rotate(-90)" text-anchor="middle" font-size="12" fill="#355">{_esc(y_label)}</text>')

    # series
    for s in series:
        pts = [(x, y) for x, y in s["points"] if math.isfinite(x) and math.isfinite(y)]
        if x_log:
            pts = [(x, y) for x, y in pts if x > 0]
        if not pts:
            continue
        d = " ".join(("M" if i == 0 else "L") + f"{sx(x):.2f},{sy(y):.2f}" for i, (x, y) in enumerate(pts))
        parts.append(f'<path d="{d}" fill="none" stroke="{_esc(s["color"])}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>')

    # legend
    lx = pad_l + 10
    ly = pad_t + 14
    for i, s in enumerate(series):
        x = lx + i * 150
        parts.append(f'<line x1="{x}" y1="{ly}" x2="{x+22}" y2="{ly}" stroke="{_esc(s["color"])}" stroke-width="2.5"/>')
        parts.append(f'<text x="{x+28}" y="{ly+4}" font-size="11.5" fill="#234">{_esc(s["name"])}</text>')

    parts.append('</svg>')
    return "".join(parts)


def bode_gain_db(points):
    return line_chart(
        [{"name": "|Vout/Vin| (dB)", "color": "#0c7d88", "points": [(p["freq_hz"], p["gain_db"]) for p in points]}],
        x_label="Frequency (Hz)", y_label="Gain (dB)", title="Bode Magnitude (ngspice .ac)", x_log=True,
    )


def bode_phase(points):
    return line_chart(
        [{"name": "Phase (deg)", "color": "#a65a2c", "points": [(p["freq_hz"], p["phase_deg"]) for p in points]}],
        x_label="Frequency (Hz)", y_label="Phase (deg)", title="Bode Phase (ngspice .ac)", x_log=True,
    )


def transient_plot(points):
    return line_chart(
        [
            {"name": "Vin", "color": "#0c8e83", "points": [(p["t_s"] * 1000.0, p["vin_v"]) for p in points]},
            {"name": "Vout", "color": "#c77a35", "points": [(p["t_s"] * 1000.0, p["vout_v"]) for p in points]},
        ],
        x_label="Time (ms)", y_label="Voltage (V)", title="Transient Response (ngspice .tran)",
    )
