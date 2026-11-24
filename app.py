from flask import Flask, render_template, request

from bjt import InputError, analyze, emitter_bias, fixed_bias, single_bias_result
from circuit_svg import build_circuit_svg, build_mode_diagram
from plot_svg import bode_gain_db, bode_phase, transient_plot
from spice_engine import DEFAULT_CIRCUIT, SpiceError, run_simulation
from validation_data import CRITERIA, CONDITIONS, NOTES, ROWS

MODES = ("divider", "fixed", "emitter")
ANALYSES = ("analytical", "op", "ac", "tran")

MODE_LABELS = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias (แหล่งจ่ายเดียว)",
}

ANALYSIS_LABELS = {
    "analytical": "Analytical DC (Lab 3)",
    "op": "SPICE DC (.op)",
    "ac": "SPICE AC (.ac)",
    "tran": "SPICE Transient (.tran)",
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

SPICE_FIELDS = [
    ("rl", "RL", "Ω"),
    ("cin_u", "Cin", "µF"),
    ("cout_u", "Cout", "µF"),
    ("vin_mvp", "Vin amplitude", "mV peak"),
    ("freq_hz", "Frequency", "Hz"),
]

ALL_FIELDS = ("vcc", "r1", "r2", "rb", "rc", "re", "beta", "vbe", "rl", "cin_u", "cout_u", "vin_mvp", "freq_hz")

DEFAULTS = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rb": "1000000",
    "rc": "4700",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
    "rl": "10000",
    "cin_u": "10",
    "cout_u": "10",
    "vin_mvp": "10",
    "freq_hz": "1000",
}


def _parse_float(raw: dict, name: str, errors: dict):
    try:
        return float(raw.get(name, ""))
    except (TypeError, ValueError):
        errors[name] = "กรุณากรอกตัวเลข"
        return None


def create_app():
    app = Flask(__name__)

    def render_page(mode, analysis, form, result, spice, errors, circuit_svg, status=200):
        show_spice_fields = mode == "divider" and analysis in ("ac", "tran", "op")
        spice_plots = {}
        if spice and spice.get("status") == "ok":
            if spice.get("analysis") == "ac":
                pts = spice["ac"]["points"]
                spice_plots["gain"] = bode_gain_db(pts)
                spice_plots["phase"] = bode_phase(pts)
            elif spice.get("analysis") == "tran":
                spice_plots["tran"] = transient_plot(spice["tran"]["points"])
        return (
            render_template(
                "index.html",
                mode=mode,
                analysis=analysis,
                mode_label=MODE_LABELS[mode],
                mode_labels=MODE_LABELS,
                analysis_label=ANALYSIS_LABELS[analysis],
                analysis_labels=ANALYSIS_LABELS,
                fields=FIELD_SPECS[mode],
                spice_fields=SPICE_FIELDS,
                show_spice_fields=show_spice_fields,
                form=form,
                result=result,
                spice=spice,
                spice_plots=spice_plots,
                errors=errors,
                circuit_svg=circuit_svg,
                mode_diagram=build_mode_diagram(mode),
                validation_rows=ROWS,
                validation_conditions=CONDITIONS,
                validation_criteria=CRITERIA,
                validation_notes=NOTES,
            ),
            status,
        )

    @app.get("/")
    def index():
        mode = request.args.get("mode", "divider")
        analysis = request.args.get("analysis", "analytical")
        if mode not in MODES:
            mode = "divider"
        if analysis not in ANALYSES:
            analysis = "analytical"
        if mode != "divider" and analysis != "analytical":
            analysis = "analytical"
        return render_page(mode, analysis, dict(DEFAULTS), None, None, {}, None)

    @app.get("/validation")
    def validation_page():
        # Keep old route working; redirect to the combined single-page layout.
        from flask import redirect, url_for
        return redirect(url_for("index") + "#validation")

    @app.post("/calculate")
    def calculate():
        requested_mode = request.form.get("mode", "divider").strip() or "divider"
        requested_analysis = request.form.get("analysis", "analytical").strip() or "analytical"

        raw = {name: request.form.get(name, "").strip() for name in ALL_FIELDS}
        form = {name: raw[name] for name in ALL_FIELDS}

        if requested_mode not in MODES:
            errors = {"mode": f"ไม่รู้จักโหมด '{requested_mode}' — ต้องเป็น divider, fixed หรือ emitter"}
            return render_page("divider", "analytical", form, None, None, errors, None, status=400)

        mode = requested_mode
        analysis = requested_analysis if requested_analysis in ANALYSES else "analytical"
        if mode != "divider":
            analysis = "analytical"

        errors = {}
        result = None
        spice = None
        circuit_svg = None

        # parse bias fields for selected mode
        bias_values = {}
        for name, _, _ in FIELD_SPECS[mode]:
            val = _parse_float(raw, name, errors)
            if val is not None:
                bias_values[name] = val

        # parse spice fields if needed
        spice_values = {}
        if mode == "divider" and analysis in ("op", "ac", "tran"):
            for name, _, _ in SPICE_FIELDS:
                val = _parse_float(raw, name, errors)
                if val is not None:
                    spice_values[name] = val

        if not errors:
            try:
                # Always compute analytical DC for divider too? Keep Lab 3 behavior.
                if mode == "divider":
                    result = analyze(
                        bias_values["vcc"], bias_values["r1"], bias_values["r2"],
                        bias_values["rc"], bias_values["re"], bias_values["beta"],
                        bias_values["vbe"],
                    )
                elif mode == "fixed":
                    exact = fixed_bias(
                        bias_values["vcc"], bias_values["rb"], bias_values["rc"],
                        bias_values["beta"], bias_values["vbe"],
                    )
                    result = single_bias_result(
                        {"vcc": bias_values["vcc"], "rb": bias_values["rb"],
                         "rc": bias_values["rc"], "beta": bias_values["beta"],
                         "vbe": bias_values["vbe"]},
                        exact,
                    )
                else:
                    exact = emitter_bias(
                        bias_values["vcc"], bias_values["rb"], bias_values["rc"],
                        bias_values["re"], bias_values["beta"], bias_values["vbe"],
                    )
                    result = single_bias_result(
                        {"vcc": bias_values["vcc"], "rb": bias_values["rb"],
                         "rc": bias_values["rc"], "re": bias_values["re"],
                         "beta": bias_values["beta"], "vbe": bias_values["vbe"]},
                        exact,
                    )

                circuit_svg = build_circuit_svg(result)

                if mode == "divider" and analysis in ("op", "ac", "tran"):
                    circuit = {
                        "vcc": bias_values["vcc"],
                        "r1": bias_values["r1"],
                        "r2": bias_values["r2"],
                        "rc": bias_values["rc"],
                        "re": bias_values["re"],
                        "rl": spice_values["rl"],
                        "cin_u": spice_values["cin_u"],
                        "cout_u": spice_values["cout_u"],
                        "vin_mvp": spice_values["vin_mvp"],
                        "freq_hz": spice_values["freq_hz"],
                    }
                    spice = run_simulation(circuit, analysis)

            except InputError as exc:
                errors[exc.field.lower()] = str(exc)
            except SpiceError as exc:
                errors[exc.field] = exc.message
                spice = {
                    "analysis": analysis,
                    "engine": "ngspice",
                    "status": "error",
                    "error": exc.message,
                }

        status = 400 if errors else 200
        return render_page(mode, analysis, form, result, spice, errors, circuit_svg, status)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
