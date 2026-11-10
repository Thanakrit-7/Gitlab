# BJT Common-Emitter DC Bias Calculator — Design

- **Date:** 2026-11-10
- **Course:** ENG29 2121
- **Status:** Draft for approval

## Intent

A short lab needs a working, demonstrable web application that computes the DC
operating point of a voltage-divider-biased NPN common-emitter stage and shows
that the answer is trustworthy. The app is the deliverable; the comparison
against an independent calculation is the evidence that the engineering logic
is correct.

## Goals

- Accept `VCC, R1, R2, RC, RE, beta, VBE` from a web form.
- Compute `VTH, RTH, IB, IC, IE, VB, VE, VC, VCE` with units.
- Validate every input and reject unusable values with a clear message.
- Classify the operating region (active / cutoff / saturation) and warn when
  the transistor is outside the active region.
- Show the exact Thevenin result beside an independent approximate result and
  the difference between them.
- Keep engineering logic in a pure Python module with no Flask imports.
- Run on localhost and be committed to GitHub the same day.

## Non-goals

- AC analysis, gain, input/output impedance, frequency response.
- Transient or time-domain simulation.
- A schematic editor or arbitrary netlist solver.
- FETs, PNP devices, Darlington pairs, or multi-stage amplifiers.
- Databases, authentication, deployment, or user accounts.
- Plotting a DC load line (nice for a report, but not needed to demonstrate
  the operating point).

## Anti-goals

- Producing a number silently when the inputs are physically impossible.
- Reporting an operating point without saying which region it is in.
- Hiding the comparison behind a debug flag or a separate page.
- Letting Flask routes contain engineering formulas.

## Constraints

- Python 3.12 is installed; Flask is not yet installed.
- Tests use the standard-library `unittest` runner, matching the existing
  `test_electrical.py`, so no extra test dependency is required.
- The existing CLI calculator (`electrical.py`, `test_electrical.py`) is
  unrelated and must keep working unchanged.
- The repository already exists at `C:\Users\B6813208\Desktop\Gitlab` with
  remote `https://github.com/Thanakrit-7/Gitlab.git` and identity
  `Thanakrit <codebank77@gmail.com>`.
- `git` is not on `PATH`; use
  `C:\Users\B6813208\AppData\Local\Programs\Git\cmd\git.exe`.
- UI text is Thai; engineering symbols stay in standard notation (`VCC`, `R1`,
  `β`, `VBE`, `IC`, `VCE`).
- No CSS or JavaScript framework; one hand-written stylesheet.

## Circuit

NPN common-emitter stage with voltage-divider bias:

```
            VCC
             |
            R1
             |
   VCC -- RC-+-- C
             |
            R2        B --/\/\/-- E
             |                 |
            GND               RE
                              |
                             GND
```

`R1` is the upper divider resistor (VCC to base), `R2` the lower divider
resistor (base to ground), `RC` the collector resistor, `RE` the emitter
resistor.

## Engineering method

### Exact (Thevenin) — primary result

```
VTH = VCC * R2 / (R1 + R2)
RTH = R1 * R2 / (R1 + R2)
IB  = (VTH - VBE) / (RTH + (1 + beta) * RE)
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = IE * RE
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

### Approximate (ignores base current) — independent calculation

```
VB  ~= VTH
VE  = VB - VBE
IE  = VE / RE
IC  ~= IE
IB  = IE / (1 + beta)
VC  = VCC - IC * RC
VCE = VC - VE
```

The result page shows both, plus `delta IC`, `delta VCE`, and percentage
differences. The approximation is expected to differ by a few percent on
typical lab values; the comparison makes the cost of ignoring `IB` visible.

The comparison is shown only when the exact result is in the active region.
In cutoff the approximation would report a negative emitter voltage, and in
saturation the two methods describe different limiting behaviour, so the
comparison would mislead rather than inform.

Near the saturation boundary the exact result can still be active while the
approximation's `VCE` falls below `VCE_sat`. The page keeps the exact region
label and adds a one-line note that the approximation is already in
saturation, so the two displayed results do not appear to contradict each
other.

### Region rules

- **Cutoff** when `VTH <= VBE`: no base current flows. Report
  `IB = IC = IE = 0`, `VE = 0`, `VB = VTH`, `VC = VCC`, `VCE = VCC`.
- **Saturation** when the exact `VCE < VCE_sat`, with
  `VCE_sat = 0.2 V` as a documented module constant. Report the computed
  values and add a warning that includes the saturated current limit
  `IC_sat = (VCC - VCE_sat) / (RC + RE)`.
- **Active** otherwise.

## Validation

Rejected with a field-level Thai message; the form keeps the user's values.
The engineering module raises `InputError(field, message)` (a `ValueError`
subclass) so the route can attach the message to the right form field.

| Field | Rule |
|-------|------|
| `VCC` | number, `> 0` |
| `R1, R2, RC, RE` | number, `> 0` |
| `beta` | number, `>= 1` |
| `VBE` | number, `0 < VBE < VCC` |
| any field | required, parseable as a float (accepts `4.7`, `4700`, `1e3`) |

`VTH <= VBE` is not a validation error; it is a valid cutoff condition and is
reported as a region warning.

## Approaches considered

1. **Single-file Flask app** — math, routes, and HTML in one `app.py`.
   Fastest to write, but violates the lab requirement that engineering logic,
   routes, templates, CSS, and tests are separate. Rejected.
2. **Layered app** (chosen) — pure `bjt.py`, thin `app.py` factory, Jinja
   templates, one stylesheet, `unittest` suites. Meets every separation
   requirement with the least structure that still reads as a real app.
3. **Blueprint package** — `app/` package with blueprints, form objects, a
   service layer, and a repository. Correct for a larger product, but adds
   indirection a one-page lab does not need. Rejected as over-engineering.

## File layout

```
bjt.py                      # pure engineering logic, no Flask
app.py                      # create_app(), routes, error handling
templates/base.html         # shared shell
templates/index.html        # form + results + comparison
static/style.css            # layout, cards, warning styles
tests/test_bjt.py           # engineering unit tests
tests/test_app.py           # Flask route tests
requirements.txt            # Flask
README.md                   # add web-app section
docs/superpowers/specs/...  # this document
```

`tests/` gets an `__init__.py` so `python -m unittest discover` works from the
repository root.

## UI sketch

```
+--------------------------------------------------------------+
|  ตัวคำนวณจุดทำงาน DC ของ BJT (Common-Emitter)                |
+--------------------------------------------------------------+
|  VCC [ 12  ] V      R1 [ 47000 ] Ω    R2 [ 10000 ] Ω         |
|  RC  [ 4700] Ω      RE [ 1000  ] Ω    β  [ 100   ]           |
|  VBE [ 0.7 ] V                                               |
|                        [ คำนวณ ]                              |
+--------------------------------------------------------------+
|  สถานะ: ทำงานในย่าน Active                                   |
|  VCE = 4.655 V   IC = 1.286 mA   IE = 1.299 mA               |
|  VB  = 1.999 V   VE = 1.299 V    VC = 5.954 V                |
|  IB  = 12.863 µA                                             |
+--------------------------------------------------------------+
|  เปรียบเทียบกับวิธีประมาณ (ไม่คิดกระแสเบส)                    |
|  ค่า      | วิธีแม่นยำ | วิธีประมาณ | ต่างกัน | %ต่าง          |
|  IC (mA)  |   1.286    |   1.405    |  0.119  |  9.2%          |
|  VCE (V)  |   4.655    |   3.990    | -0.665  | 14.3%          |
+--------------------------------------------------------------+
|  [!] คำเตือน: ...                                            |
+--------------------------------------------------------------+
```

Invalid input re-renders the same page with the offending fields marked and a
message under each one. The response status is `400`.

## Tests

Engineering (`tests/test_bjt.py`):

- Textbook example above matches hand-calculated values to `1e-6`.
- Approximate method matches hand-calculated values.
- Comparison returns correct deltas and percentages.
- An active result whose approximation lands below `VCE_sat` sets the
  near-saturation note; a comfortably active result does not.
- Cutoff example (`VTH < VBE`) returns zero currents and `VCE = VCC`.
- Saturation example returns the saturation flag and `IC_sat`.
- Validation: zero, negative, non-numeric, `beta < 1`, `VBE >= VCC` each raise
  `ValueError` naming the field.
- `beta = 1` is accepted (boundary).

Routes (`tests/test_app.py`):

- `GET /` returns `200` and contains the form fields.
- `POST /calculate` with valid values returns `200`, the region label, and the
  comparison table.
- `POST /calculate` with a bad value returns `400` and an error message, and
  echoes the other values back.
- `POST /calculate` with a saturation case shows the warning.
- The app never returns a stack trace for bad input.

## Demo and commit

- `python -m pip install -r requirements.txt`
- `python app.py` serves `http://127.0.0.1:5000`.
- `python -m unittest discover -v` passes.
- Manual browser check of one active, one cutoff, and one saturation case.
- Commit the app, tests, design, and README update; push to `origin main`.

## Left to the builder

- Exact CSS spacing, colors, and responsive breakpoints.
- Thai wording of labels, help text, and error messages (meaning is fixed
  above; phrasing is not).
- Display rounding: volts to 3 decimals, currents to 3 decimals in mA/µA,
  percentages to 1 decimal.
- Whether the form uses `POST` redirect `GET` or renders results directly
  (direct render is acceptable and simpler).
- Whether `IC_sat` is shown only on saturation or always as a reference line.

## Acceptance criteria

1. All engineering tests and route tests pass.
2. The textbook example returns `IC = 1.286 mA`, `VCE = 4.655 V`, region
   `active`, within rounding.
3. A cutoff input and a saturation input each show the correct region and a
   warning.
4. Invalid input produces a readable error, not a traceback.
5. The page loads at localhost with no external network dependencies.
6. Work is committed and pushed to GitHub.
