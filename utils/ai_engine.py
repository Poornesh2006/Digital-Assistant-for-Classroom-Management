def _coerce_float(student_data, key, label, minimum=0, maximum=None):
    raw_value = student_data.get(key, 0)
    try:
        parsed = float(raw_value or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a valid number.") from exc

    if parsed < minimum:
        raise ValueError(f"{label} must be at least {minimum}.")
    if maximum is not None and parsed > maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}.")
    return parsed


def analyze_student(student_data):
    name = str(student_data.get("Name", "")).strip()
    register_number = str(student_data.get("RegisterNumber", "")).strip().upper()
    if not name:
        raise ValueError("Student name is required for AI analysis.")
    if not register_number:
        raise ValueError("Register number is required for AI analysis.")

    marks = _coerce_float(student_data, "Sem6_Total", "Total marks", minimum=0, maximum=500)
    attendance = _coerce_float(student_data, "Attendance", "Attendance", minimum=0, maximum=100)
    avg_marks = _coerce_float(student_data, "Average", "Average marks", minimum=0, maximum=100)

    if avg_marks <= 0 and marks > 0:
        avg_marks = round(marks / 5, 2)

    if avg_marks < 50 or attendance < 70:
        risk = "High Risk"
    elif avg_marks < 65:
        risk = "Moderate Risk"
    else:
        risk = "Low Risk"

    performance_score = round((marks / 500) * 10, 2)

    return {
        "risk_level": risk,
        "performance_score": performance_score,
        "average_marks": avg_marks,
        "attendance": attendance,
    }
