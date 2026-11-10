from flask import Flask, render_template

DEFAULTS = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "100",
    "vbe": "0.7",
}


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html", form=DEFAULTS, result=None, errors={})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
