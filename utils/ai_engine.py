def analyze_student(student_data):
    marks = float(student_data.get("Sem6_Total", 0) or 0)
    attendance = float(student_data.get("Attendance", 0))
    avg_marks = float(student_data.get("Average", 0) or 0)

    if avg_marks <= 0 and marks > 0:
        avg_marks = round(marks / 5, 2)

    if attendance < 70 or avg_marks < 60:
        risk = "High"
    elif attendance < 80:
        risk = "Medium"
    else:
        risk = "Low"

    performance_score = round((marks / 500) * 10, 2)

    return {
        "risk_level": risk,
        "performance_score": performance_score,
        "average_marks": avg_marks,
        "attendance": attendance,
    }
