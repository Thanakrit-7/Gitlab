def _validate_number(value, name, allow_zero=False):
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} ต้องเป็นตัวเลข")
    minimum_ok = value >= 0 if allow_zero else value > 0
    if not minimum_ok:
        raise ValueError(f"{name} ต้องมากกว่า 0")


def _validate_positive(value, name):
    _validate_number(value, name)


def analyze_dc(voltage_v, resistance_ohm):
    """คำนวณกระแสและกำลังของวงจรตัวต้านทานเพียงตัวเดียว"""
    _validate_number(voltage_v, "แรงดัน", allow_zero=True)
    _validate_positive(resistance_ohm, "ความต้านทาน")

    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {
        "voltage_v": voltage_v,
        "resistance_ohm": resistance_ohm,
        "current_a": current_a,
        "power_w": power_w,
    }


def analyze_series(voltage_v, resistances):
    resistances = list(resistances)
    _validate_positive(voltage_v, "แรงดัน")
    if not resistances:
        raise ValueError("ต้องระบุตัวต้านทานอย่างน้อย 1 ตัว")
    for resistance in resistances:
        _validate_positive(resistance, "ความต้านทาน")

    total_resistance = sum(resistances)
    current_a = voltage_v / total_resistance
    return {
        "type": "series",
        "voltage_v": voltage_v,
        "total_resistance_ohm": total_resistance,
        "total_current_a": current_a,
        "total_power_w": voltage_v * current_a,
        "resistors": [
            {
                "resistance_ohm": resistance,
                "voltage_v": current_a * resistance,
                "current_a": current_a,
                "power_w": current_a ** 2 * resistance,
            }
            for resistance in resistances
        ],
    }


def analyze_parallel(voltage_v, resistances):
    resistances = list(resistances)
    _validate_positive(voltage_v, "แรงดัน")
    if not resistances:
        raise ValueError("ต้องระบุตัวต้านทานอย่างน้อย 1 ตัว")
    for resistance in resistances:
        _validate_positive(resistance, "ความต้านทาน")

    total_resistance = 1 / sum(1 / resistance for resistance in resistances)
    total_current_a = voltage_v / total_resistance
    resistor_results = []
    for resistance in resistances:
        current_a = voltage_v / resistance
        resistor_results.append({
            "resistance_ohm": resistance,
            "voltage_v": voltage_v,
            "current_a": current_a,
            "power_w": voltage_v * current_a,
        })

    return {
        "type": "parallel",
        "voltage_v": voltage_v,
        "total_resistance_ohm": total_resistance,
        "total_current_a": total_current_a,
        "total_power_w": voltage_v * total_current_a,
        "resistors": resistor_results,
    }


def analyze_mixed(voltage_v, branches):
    """วงจรผสมแบบแต่ละกิ่งเป็นตัวต้านทานอนุกรม กิ่งต่าง ๆ ต่อขนานกัน"""
    _validate_positive(voltage_v, "แรงดัน")
    if not branches:
        raise ValueError("ต้องระบุอย่างน้อย 1 กิ่ง")

    normalized_branches = []
    for branch in branches:
        resistances = list(branch)
        if not resistances:
            raise ValueError("แต่ละกิ่งต้องมีตัวต้านทานอย่างน้อย 1 ตัว")
        for resistance in resistances:
            _validate_positive(resistance, "ความต้านทาน")
        normalized_branches.append(resistances)

    branch_resistances = [sum(branch) for branch in normalized_branches]
    total_resistance = 1 / sum(1 / resistance for resistance in branch_resistances)
    total_current_a = voltage_v / total_resistance
    branch_results = []

    for resistances, branch_resistance in zip(normalized_branches, branch_resistances):
        branch_voltage_v = voltage_v
        branch_current_a = branch_voltage_v / branch_resistance
        resistor_results = [
            {
                "resistance_ohm": resistance,
                "voltage_v": branch_current_a * resistance,
                "current_a": branch_current_a,
                "power_w": branch_current_a ** 2 * resistance,
            }
            for resistance in resistances
        ]
        branch_results.append({
            "resistance_ohm": branch_resistance,
            "voltage_v": branch_voltage_v,
            "current_a": branch_current_a,
            "power_w": branch_voltage_v * branch_current_a,
            "resistors": resistor_results,
        })

    return {
        "type": "mixed",
        "voltage_v": voltage_v,
        "total_resistance_ohm": total_resistance,
        "total_current_a": total_current_a,
        "total_power_w": voltage_v * total_current_a,
        "branches": branch_results,
    }


def _read_positive_float(prompt):
    while True:
        try:
            value = float(input(prompt).strip())
            if value <= 0:
                print("กรุณากรอกค่าที่มากกว่า 0")
                continue
            return value
        except ValueError:
            print("กรุณากรอกตัวเลข")


def _read_resistances(prompt):
    while True:
        try:
            values = [float(value.strip()) for value in input(prompt).split(",")]
            if not values or any(value <= 0 for value in values):
                print("กรุณากรอกตัวต้านทานที่มากกว่า 0 คั่นด้วยเครื่องหมายจุลภาค")
                continue
            return values
        except ValueError:
            print("กรุณากรอกตัวเลขและคั่นด้วยเครื่องหมายจุลภาค เช่น 10, 20")


def _print_resistors(resistors, indent=""):
    for index, resistor in enumerate(resistors, start=1):
        print(
            f"{indent}R{index}: {resistor['resistance_ohm']:.6g} Ω, "
            f"{resistor['voltage_v']:.6g} V, "
            f"{resistor['current_a']:.6g} A, "
            f"{resistor['power_w']:.6g} W"
        )


def print_result(result):
    print("\nผลการคำนวณ")
    print(f"แรงดัน: {result['voltage_v']:.6g} V")
    print(f"ความต้านทานรวม: {result['total_resistance_ohm']:.6g} Ω")
    print(f"กระแสรวม: {result['total_current_a']:.6g} A")
    print(f"กำลังรวม: {result['total_power_w']:.6g} W")

    if result["type"] == "mixed":
        for branch_index, branch in enumerate(result["branches"], start=1):
            print(
                f"\nกิ่งที่ {branch_index}: "
                f"R={branch['resistance_ohm']:.6g} Ω, "
                f"I={branch['current_a']:.6g} A"
            )
            _print_resistors(branch["resistors"], indent="  ")
    else:
        print("\nรายละเอียดตัวต้านทาน")
        _print_resistors(result["resistors"])


def main():
    print("เครื่องคำนวณวงจร DC")
    voltage_v = _read_positive_float("แรงดันแหล่งจ่าย (V): ")

    print("\nเลือกแบบวงจร")
    print("1. ตัวต้านทานอนุกรม")
    print("2. ตัวต้านทานขนาน")
    print("3. วงจรผสม (กิ่งอนุกรมต่อขนานกัน)")

    while True:
        circuit_type = input("ตัวเลือก 1-3: ").strip()
        if circuit_type in {"1", "2", "3"}:
            break
        print("กรุณาเลือก 1, 2 หรือ 3")

    if circuit_type == "1":
        resistances = _read_resistances("กรอกตัวต้านทานอนุกรม (Ω, คั่นด้วยจุลภาค): ")
        result = analyze_series(voltage_v, resistances)
    elif circuit_type == "2":
        resistances = _read_resistances("กรอกตัวต้านทานขนาน (Ω, คั่นด้วยจุลภาค): ")
        result = analyze_parallel(voltage_v, resistances)
    else:
        while True:
            try:
                branch_count = int(input("จำนวนกิ่งขนาน: ").strip())
                if branch_count > 0:
                    break
            except ValueError:
                pass
            print("กรุณากรอกจำนวนเต็มที่มากกว่า 0")

        branches = []
        for branch_index in range(1, branch_count + 1):
            resistances = _read_resistances(
                f"ตัวต้านทานในกิ่งที่ {branch_index} (Ω, คั่นด้วยจุลภาค): "
            )
            branches.append(resistances)
        result = analyze_mixed(voltage_v, branches)

    print_result(result)


if __name__ == "__main__":
    main()