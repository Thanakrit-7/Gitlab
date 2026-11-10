from flask import Flask, render_template, request

from bjt import InputError, analyze

DEFAULTS = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
}

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html", form=DEFAULTS, result=None, errors={})

    @app.post("/calculate")
    def calculate():
        raw = {name: request.form.get(name, "").strip() for name in FIELDS}
        values = {}
        errors = {}
        for name in FIELDS:
            try:
                values[name] = float(raw[name])
            except ValueError:
                errors[name] = "กรุณากรอกตัวเลข"
        result = None
        if not errors:
            try:
                result = analyze(**values)
            except InputError as exc:
                errors[exc.field.lower()] = str(exc)
        status = 400 if errors else 200
        return (
            render_template("index.html", form=raw, result=result, errors=errors),
            status,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
