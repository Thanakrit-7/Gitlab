"""Render the BJT common-emitter bias circuit as an inline SVG.

Pure functions only: no I/O, no globals. ``build_circuit_svg`` draws the
selected mode with the values produced by ``bjt`` so the picture can never
disagree with the result table. ``build_mode_diagram`` draws the same topology
without numbers, for the form page (before anything is calculated).

``mode`` is inferred from the keys present in ``inputs`` when not given.
"""

import html

ACCENT = "#0b6e4f"
INK = "#1f2933"
MUTED = "#5f6b7a"
WIRE = "#1f2933"

ARIA_LABELS = {
    "divider": "วงจร Voltage Divider Bias พร้อมค่าที่คำนวณได้",
    "fixed": "วงจร Fixed Bias พร้อมค่าที่คำนวณได้",
    "emitter": "วงจร Emitter Bias (แหล่งจ่ายเดียว) พร้อมค่าที่คำนวณได้",
}

TOPOLOGY_ARIA = {
    "divider": "วงจร Voltage Divider Bias",
    "fixed": "วงจร Fixed Bias",
    "emitter": "วงจร Emitter Bias (แหล่งจ่ายเดียว)",
}


def _esc(text):
    return html.escape(str(text), quote=True)


def _ohms(value):
    return f"{value:.0f}" if float(value).is_integer() else f"{value:.10g}"


def format_current(amps):
    if amps == 0:
        return "0.000"
    if amps < 1e-3:
        return f"{amps * 1e6:.3f} µA"
    return f"{amps * 1000:.3f} mA"


def build_circuit_svg(result, mode=None):
    inputs = result["inputs"]
    exact = result["exact"]

    if mode is None:
        mode = "divider" if "r1" in inputs else ("emitter" if "re" in inputs else "fixed")

    return _render(mode, inputs, exact, with_values=True)


def build_mode_diagram(mode):
    """Topology-only diagram (component names, no calculated numbers)."""
    return _render(mode, None, None, with_values=False)


def _render(mode, inputs, exact, with_values):
    if mode not in ARIA_LABELS:
        raise ValueError(f"unknown mode: {mode}")

    is_divider = mode == "divider"
    is_fixed = mode == "fixed"
    marker_id = "arr" if with_values else "arr-topo"

    def ohms_label(name, key):
        if not with_values:
            return name
        return f"{name} = {_esc(_ohms(inputs[key]))} Ω"

    if with_values:
        vcc_label = "VCC = " + _esc(f"{inputs['vcc']:.2f}") + " V"
    else:
        vcc_label = "VCC"

    if with_values:
        beta = f"{inputs['beta']:.1f}"
        vbe = f"{inputs['vbe']:.2f}"
        vth = f"{exact['vth_v']:.3f} V"
        rth = f"{exact['rth_ohm']:.1f} Ω"
        vb = f"{exact['vb_v']:.3f} V"
        ve = f"{exact['ve_v']:.3f} V"
        vc = f"{exact['vc_v']:.3f} V"
        vce = f"{exact['vce_v']:.3f} V"
        ib = format_current(exact["ib_a"])
        ic = format_current(exact["ic_a"])
        ie = format_current(exact["ie_a"])

    zigzag_r1 = "120,48 111,62 129,76 111,90 129,104 111,118 129,132 120,146"
    zigzag_r2 = "120,246 111,258 129,270 111,282 129,294 111,306 129,318 120,330"
    zigzag_rc = "340,48 331,58 349,68 331,78 349,88 331,98 340,106"
    zigzag_re = "340,282 331,292 349,302 331,312 349,322 331,332 340,340"

    aria = ARIA_LABELS[mode] if with_values else TOPOLOGY_ARIA[mode]
    svg_class = "circuit-svg" if with_values else "mode-diagram-svg"

    parts = [
        f'<svg class="{svg_class}" viewBox="0 0 480 400" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{aria}">',
        f'<defs><marker id="{marker_id}" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{ACCENT}"/>'
        f'</marker></defs>',

        # VCC rail
        f'<line x1="40" y1="30" x2="440" y2="30" stroke="{WIRE}" stroke-width="2"/>',
        f'<text x="44" y="20" font-size="12" fill="{MUTED}">{vcc_label}</text>',
    ]

    if is_divider:
        # R1 branch
        parts += [
            f'<line x1="120" y1="30" x2="120" y2="48" stroke="{WIRE}" stroke-width="2"/>',
            f'<polyline points="{zigzag_r1}" fill="none" stroke="{WIRE}" stroke-width="2" '
            f'stroke-linejoin="round"/>',
            f'<line x1="120" y1="146" x2="120" y2="228" stroke="{WIRE}" stroke-width="2"/>',
            f'<text x="100" y="100" font-size="11.5" fill="{INK}" text-anchor="end">'
            f'{ohms_label("R1", "r1")}</text>',

            # R2 branch to ground
            f'<line x1="120" y1="228" x2="120" y2="246" stroke="{WIRE}" stroke-width="2"/>',
            f'<polyline points="{zigzag_r2}" fill="none" stroke="{WIRE}" stroke-width="2" '
            f'stroke-linejoin="round"/>',
            f'<line x1="120" y1="330" x2="120" y2="356" stroke="{WIRE}" stroke-width="2"/>',
            f'<text x="100" y="295" font-size="11.5" fill="{INK}" text-anchor="end">'
            f'{ohms_label("R2", "r2")}</text>',
        ]
    else:
        # Single RB from VCC to base (Fixed / Emitter bias)
        parts += [
            f'<circle cx="120" cy="30" r="3.5" fill="{WIRE}"/>',
            f'<line x1="120" y1="30" x2="120" y2="48" stroke="{WIRE}" stroke-width="2"/>',
            f'<polyline points="{zigzag_r1}" fill="none" stroke="{WIRE}" stroke-width="2" '
            f'stroke-linejoin="round"/>',
            f'<line x1="120" y1="146" x2="120" y2="200" stroke="{WIRE}" stroke-width="2"/>',
            f'<text x="100" y="100" font-size="11.5" fill="{INK}" text-anchor="end">'
            f'{ohms_label("RB", "rb")}</text>',
        ]

    # Base wire from bias network node to transistor base
    parts += [
        f'<circle cx="120" cy="200" r="3.5" fill="{WIRE}"/>',
        f'<line x1="120" y1="200" x2="284" y2="200" stroke="{WIRE}" stroke-width="2"/>',
        f'<path d="M120,200 L280,200" fill="none" stroke="{ACCENT}" '
        f'stroke-width="1.6" marker-end="url(#{marker_id})"/>',
    ]
    if with_values:
        parts += [
            f'<text x="130" y="216" font-size="11.5" fill="{INK}">VB = {_esc(vb)}</text>',
            f'<text x="130" y="230" font-size="11.5" fill="{ACCENT}">IB = {_esc(ib)}</text>',
        ]
    if is_divider and with_values:
        parts += [
            f'<text x="130" y="168" font-size="11.5" fill="{MUTED}">VTH = {_esc(vth)}</text>',
            f'<text x="130" y="182" font-size="11.5" fill="{MUTED}">RTH = {_esc(rth)}</text>',
        ]

    # RC branch
    parts += [
        f'<circle cx="340" cy="30" r="3.5" fill="{WIRE}"/>',
        f'<line x1="340" y1="30" x2="340" y2="48" stroke="{WIRE}" stroke-width="2"/>',
        f'<polyline points="{zigzag_rc}" fill="none" stroke="{WIRE}" stroke-width="2" '
        f'stroke-linejoin="round"/>',
        f'<line x1="340" y1="106" x2="340" y2="124" stroke="{WIRE}" stroke-width="2"/>',
        f'<text x="356" y="72" font-size="11.5" fill="{INK}">'
        f'{ohms_label("RC", "rc")}</text>',

        # NPN transistor: enclosing circle + vertical bar + 45-degree leads
        f'<circle cx="284" cy="200" r="26" fill="#fcfdfe" stroke="{WIRE}" '
        f'stroke-width="2"/>',
        f'<line x1="284" y1="180" x2="284" y2="220" stroke="{WIRE}" stroke-width="5"/>',
        f'<path d="M340,124 L284,180" fill="none" stroke="{WIRE}" stroke-width="2"/>',
        f'<path d="M340,124 L288,176" fill="none" stroke="{ACCENT}" '
        f'stroke-width="1.6" marker-end="url(#{marker_id})"/>',
        f'<path d="M284,220 L340,276" fill="none" stroke="{WIRE}" stroke-width="2"/>',
        f'<path d="M284,220 L332,268" fill="none" stroke="{ACCENT}" '
        f'stroke-width="1.6" marker-end="url(#{marker_id})"/>',
        f'<text x="318" y="192" font-size="12" font-weight="700" fill="{INK}">'
        f'Q1 NPN</text>',
    ]
    if with_values:
        parts += [
            f'<text x="318" y="207" font-size="10.5" fill="{MUTED}">'
            f'(β = {_esc(beta)})</text>',
            f'<circle cx="340" cy="124" r="3.5" fill="{WIRE}"/>',
            f'<text x="332" y="114" font-size="11.5" fill="{INK}" text-anchor="end">'
            f'VC = {_esc(vc)}</text>',
            f'<text x="252" y="146" font-size="11.5" fill="{ACCENT}" text-anchor="end">'
            f'IC = {_esc(ic)}</text>',
        ]

    # Emitter node
    parts += [
        f'<circle cx="340" cy="276" r="3.5" fill="{WIRE}"/>',
    ]
    if with_values:
        parts += [
            f'<text x="348" y="272" font-size="11.5" fill="{INK}">VE = {_esc(ve)}</text>',
            f'<text x="348" y="258" font-size="11.5" fill="{ACCENT}">IE = {_esc(ie)}</text>',
        ]

    if is_fixed:
        # Emitter grounded directly — straight wire down to the rail
        parts += [
            f'<line x1="340" y1="276" x2="340" y2="356" stroke="{WIRE}" stroke-width="2"/>',
        ]
    else:
        # RE branch to ground (Divider / Emitter)
        parts += [
            f'<line x1="340" y1="276" x2="340" y2="282" stroke="{WIRE}" stroke-width="2"/>',
            f'<polyline points="{zigzag_re}" fill="none" stroke="{WIRE}" stroke-width="2" '
            f'stroke-linejoin="round"/>',
            f'<line x1="340" y1="340" x2="340" y2="356" stroke="{WIRE}" stroke-width="2"/>',
            f'<text x="356" y="316" font-size="11.5" fill="{INK}">'
            f'{ohms_label("RE", "re")}</text>',
        ]

    if with_values:
        parts += [
            # Beta / VBE annotations, clear of the emitter lead
            f'<text x="272" y="246" font-size="11.5" font-weight="700" fill="{INK}" '
            f'text-anchor="end">β = {_esc(beta)}</text>',
            f'<text x="272" y="262" font-size="10.5" fill="{MUTED}" '
            f'text-anchor="end">VBE = {_esc(vbe)} V</text>',

            # VCE vertical dimension line spanning collector node to emitter node
            f'<line x1="446" y1="124" x2="446" y2="276" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<line x1="440" y1="124" x2="452" y2="124" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<line x1="440" y1="276" x2="452" y2="276" stroke="{ACCENT}" stroke-width="1.6"/>',
            f'<text transform="rotate(-90 462 200)" x="462" y="200" font-size="11" '
            f'font-weight="700" fill="{ACCENT}" text-anchor="middle">'
            f'VCE = {_esc(vce)}</text>',
        ]

    parts += [
        # Ground rail + symbol
        f'<line x1="40" y1="356" x2="440" y2="356" stroke="{WIRE}" stroke-width="2"/>',
        f'<line x1="250" y1="356" x2="250" y2="366" stroke="{WIRE}" stroke-width="2"/>',
        f'<line x1="228" y1="366" x2="272" y2="366" stroke="{WIRE}" stroke-width="2"/>',
        f'<line x1="236" y1="372" x2="264" y2="372" stroke="{WIRE}" stroke-width="2"/>',
        f'<line x1="244" y1="378" x2="256" y2="378" stroke="{WIRE}" stroke-width="2"/>',
        f'<text x="284" y="374" font-size="11.5" fill="{MUTED}">GND</text>',

        "</svg>",
    ]
    return "".join(parts)
