from flask import Flask, render_template, request

from bjt import InputError, analyze, emitter_bias, fixed_bias, single_bias_result
from circuit_svg import build_circuit_svg

MODES = ("divider", "fixed", "emitter")

MODE_LABELS = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias (แหล่งจ่ายเดียว)",
}

FIELD_SPECS = {
    "divider": [
        ("vcc", "VCC", "V"),
        ("r1", "R1", "Ω"),
        ("r2", "R2", "Ω"),
        ("rc", "RC", "Ω"),
        ("re", "RE", "Ω"),
        ("beta", "β", ""),
        ("vbe", "VBE", "V"),
    ],
    "fixed": [
        ("vcc", "VCC", "V"),
        ("rb", "RB", "Ω"),
        ("rc", "RC", "Ω"),
        ("beta", "β", ""),
        ("vbe", "VBE", "V"),
    ],
    "emitter": [
        ("vcc", "VCC", "V"),
        ("rb", "RB", "Ω"),
        ("rc", "RC", "Ω"),
        ("re", "RE", "Ω"),
        ("beta", "β", ""),
        ("vbe", "VBE", "V"),
    ],
}

ALL_FIELDS = ("vcc", "r1", "r2", "rb", "rc", "re", "beta", "vbe")

DEFAULTS = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rb": "1000000",
    "rc": "4700",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
}


def create_app():
    app = Flask(__name__)

    def render_page(mode, form, result, errors, circuit_svg, status=200):
        return (
            render_template(
                "index.html",
                mode=mode,
                mode_label=MODE_LABELS[mode],
                mode_labels=MODE_LABELS,
                fields=FIELD_SPECS[mode],
                form=form,
                result=result,
                errors=errors,
                circuit_svg=circuit_svg,
            ),
            status,
        )

    @app.get("/")
    def index():
        mode = request.args.get("mode", "divider")
        if mode not in MODES:
            mode = "divider"
        return render_page(mode, dict(DEFAULTS), None, {}, None)

    @app.post("/calculate")
    def calculate():
        requested_mode = request.form.get("mode", "divider").strip() or "divider"

        raw = {name: request.form.get(name, "").strip()
               for name in ALL_FIELDS}
        raw["mode"] = requested_mode
        form = {name: raw[name] for name in ALL_FIELDS}

        if requested_mode not in MODES:
            errors = {"mode": f"ไม่รู้จักโหมด '{requested_mode}' — ต้องเป็น divider, fixed หรือ emitter"}
            return render_page("divider", form, None, errors, None, status=400)

        mode = requested_mode
        fields = FIELD_SPECS[mode]

        values = {}
        errors = {}
        for name, _, _ in fields:
            try:
                values[name] = float(raw[name])
            except ValueError:
                errors[name] = "กรุณากรอกตัวเลข"

        result = None
        circuit_svg = None
        if not errors:
            try:
                if mode == "divider":
                    result = analyze(values["vcc"], values["r1"], values["r2"],
                                     values["rc"], values["re"], values["beta"],
                                     values["vbe"])
                elif mode == "fixed":
                    exact = fixed_bias(values["vcc"], values["rb"], values["rc"],
                                       values["beta"], values["vbe"])
                    result = single_bias_result(
                        {"vcc": values["vcc"], "rb": values["rb"],
                         "rc": values["rc"], "beta": values["beta"],
                         "vbe": values["vbe"]},
                        exact,
                    )
                else:  # emitter
                    exact = emitter_bias(values["vcc"], values["rb"], values["rc"],
                                         values["re"], values["beta"],
                                         values["vbe"])
                    result = single_bias_result(
                        {"vcc": values["vcc"], "rb": values["rb"],
                         "rc": values["rc"], "re": values["re"],
                         "beta": values["beta"], "vbe": values["vbe"]},
                        exact,
                    )
                circuit_svg = build_circuit_svg(result)
            except InputError as exc:
                errors[exc.field.lower()] = str(exc)

        status = 400 if errors else 200
        return render_page(mode, form, result, errors, circuit_svg, status)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
