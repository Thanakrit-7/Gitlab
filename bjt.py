import math

VCE_SAT = 0.2

MAX_VOLTAGE = 10_000.0
MAX_RESISTANCE = 1_000_000_000.0
MAX_BETA = 1_000_000.0


class InputError(ValueError):
    """Invalid circuit input, carrying the form field it belongs to."""

    def __init__(self, field, message):
        super().__init__(message)
        self.field = field


def _finite_number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(field, f"{field} ต้องเป็นตัวเลข")
    if not math.isfinite(value):
        raise InputError(field, f"{field} ต้องเป็นค่าจำกัด")
    return float(value)


def validate_inputs(vcc, r1, r2, rc, re, beta, vbe):
    vcc = _finite_number(vcc, "VCC")
    r1 = _finite_number(r1, "R1")
    r2 = _finite_number(r2, "R2")
    rc = _finite_number(rc, "RC")
    re = _finite_number(re, "RE")
    beta = _finite_number(beta, "beta")
    vbe = _finite_number(vbe, "VBE")

    checks = (
        ("VCC", vcc, MAX_VOLTAGE, "V"),
        ("R1", r1, MAX_RESISTANCE, "Ω"),
        ("R2", r2, MAX_RESISTANCE, "Ω"),
        ("RC", rc, MAX_RESISTANCE, "Ω"),
        ("RE", re, MAX_RESISTANCE, "Ω"),
    )
    for field, value, limit, unit in checks:
        if value <= 0:
            raise InputError(field, f"{field} ต้องมากกว่า 0")
        if value > limit:
            raise InputError(field, f"{field} ต้องไม่เกิน {limit:,.0f} {unit}")

    if beta < 1:
        raise InputError("beta", "beta ต้องมีค่าอย่างน้อย 1")
    if beta > MAX_BETA:
        raise InputError("beta", f"beta ต้องไม่เกิน {MAX_BETA:,.0f}")

    if not (0 < vbe < vcc):
        raise InputError("VBE", "VBE ต้องมากกว่า 0 และน้อยกว่า VCC")


def exact_operating_point(vcc, r1, r2, rc, re, beta, vbe):
    validate_inputs(vcc, r1, r2, rc, re, beta, vbe)

    vth_v = vcc * r2 / (r1 + r2)
    rth_ohm = r1 * r2 / (r1 + r2)

    if vth_v <= vbe:
        return {
            "vth_v": vth_v,
            "rth_ohm": rth_ohm,
            "ib_a": 0.0,
            "ic_a": 0.0,
            "ie_a": 0.0,
            "vb_v": vth_v,
            "ve_v": 0.0,
            "vc_v": vcc,
            "vce_v": vcc,
            "region": "cutoff",
            "warnings": ["cutoff"],
            "ic_sat_a": None,
        }

    ib_a = (vth_v - vbe) / (rth_ohm + (1 + beta) * re)
    ic_a = beta * ib_a
    ie_a = (1 + beta) * ib_a
    ve_v = ie_a * re
    vb_v = ve_v + vbe
    vc_v = vcc - ic_a * rc
    vce_v = vc_v - ve_v

    region = "active"
    warnings = []
    ic_sat_a = None
    if vce_v < VCE_SAT:
        region = "saturation"
        warnings = ["saturation"]
        ic_sat_a = (vcc - VCE_SAT) / (rc + re)

    return {
        "vth_v": vth_v,
        "rth_ohm": rth_ohm,
        "ib_a": ib_a,
        "ic_a": ic_a,
        "ie_a": ie_a,
        "vb_v": vb_v,
        "ve_v": ve_v,
        "vc_v": vc_v,
        "vce_v": vce_v,
        "region": region,
        "warnings": warnings,
        "ic_sat_a": ic_sat_a,
    }


def approximate_operating_point(vcc, r1, r2, rc, re, beta, vbe):
    validate_inputs(vcc, r1, r2, rc, re, beta, vbe)

    vth_v = vcc * r2 / (r1 + r2)
    rth_ohm = r1 * r2 / (r1 + r2)
    vb_v = vth_v
    ve_v = vb_v - vbe
    ie_a = ve_v / re
    ic_a = ie_a
    ib_a = ie_a / (1 + beta)
    vc_v = vcc - ic_a * rc
    vce_v = vc_v - ve_v

    return {
        "vth_v": vth_v,
        "rth_ohm": rth_ohm,
        "ib_a": ib_a,
        "ic_a": ic_a,
        "ie_a": ie_a,
        "vb_v": vb_v,
        "ve_v": ve_v,
        "vc_v": vc_v,
        "vce_v": vce_v,
    }


def compare(exact, approximate):
    def entry(exact_value, approximate_value):
        delta = approximate_value - exact_value
        percent = delta / exact_value * 100 if exact_value else 0.0
        return {
            "exact": exact_value,
            "approximate": approximate_value,
            "delta": delta,
            "percent": percent,
        }

    return {
        "ic": entry(exact["ic_a"], approximate["ic_a"]),
        "vce": entry(exact["vce_v"], approximate["vce_v"]),
    }


def analyze(vcc, r1, r2, rc, re, beta, vbe):
    exact = exact_operating_point(vcc, r1, r2, rc, re, beta, vbe)
    approximate = None
    comparison = None
    approx_near_saturation = False

    if exact["region"] == "active":
        approximate = approximate_operating_point(vcc, r1, r2, rc, re, beta, vbe)
        comparison = compare(exact, approximate)
        approx_near_saturation = approximate["vce_v"] < VCE_SAT

    return {
        "inputs": {
            "vcc": vcc,
            "r1": r1,
            "r2": r2,
            "rc": rc,
            "re": re,
            "beta": beta,
            "vbe": vbe,
        },
        "exact": exact,
        "approximate": approximate,
        "comparison": comparison,
        "approx_near_saturation": approx_near_saturation,
    }
