import math


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

    for field, value in (
        ("VCC", vcc),
        ("R1", r1),
        ("R2", r2),
        ("RC", rc),
        ("RE", re),
    ):
        if value <= 0:
            raise InputError(field, f"{field} ต้องมากกว่า 0")

    if beta < 1:
        raise InputError("beta", "beta ต้องมีค่าอย่างน้อย 1")

    if not (0 < vbe < vcc):
        raise InputError("VBE", "VBE ต้องมากกว่า 0 และน้อยกว่า VCC")
