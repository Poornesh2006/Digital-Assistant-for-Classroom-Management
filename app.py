import os
import random
import re
import math
from datetime import datetime
from functools import wraps
from io import BytesIO

import matplotlib
import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from flask import Flask, flash, redirect, render_template, request, send_file, session, url_for
from sklearn.linear_model import LogisticRegression

# Render charts on server without GUI.
matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = Flask(__name__,
            template_folder="templates",
            static_folder="static")
app.secret_key = "supersecretkey"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = "database/students.csv"
STUDENTS_PATH = os.path.join(BASE_DIR, DATABASE_PATH)
COURSES_PATH = os.path.join(DATA_DIR, "courses.csv")
SEMESTERS_PATH = os.path.join(DATA_DIR, "semesters.csv")
UPLOAD_FOLDER = "static/images/students"
EXPORT_FOLDER = "exports/pdf"
ACTIVITY_LOG_PATH = os.path.join(BASE_DIR, "activity_log.txt")

DEFAULT_COURSES = [
    ("22AI037", "TIME SERIES ANALYSIS AND FORECASTING"),
    ("22AI501", "ARTIFICIAL INTELLIGENCE"),
    ("22AI502", "COMPUTER NETWORKS"),
    ("22AI503", "MACHINE LEARNING"),
    ("22AI504", "CLOUD COMPUTING"),
]

DEPARTMENTS = [
    "Biomedical Engineering",
    "Civil Engineering",
    "Computer Science & Design",
    "Computer Science & Engineering",
    "Electrical & Electronics Engineering",
    "Electronics & Communication Engineering",
    "Electronics & Instrumentation Engineering",
    "Information Science & Engineering",
    "Mechanical Engineering",
    "Mechatronics Engineering",
    "Agricultural Engineering",
    "Artificial Intelligence and Data Science",
    "Artificial Intelligence and Machine Learning",
    "Biotechnology",
    "Computer Science & Business Systems",
    "Computer Technology",
    "Food Technology",
    "Fashion Technology",
    "Information Technology",
    "Textile Technology",
]

FACULTY_USERS = {
    "admin": "admin123",
    "faculty1": "faculty123",
}

SEMESTER_TOTAL_COLS = [f"Sem{i}_Total" for i in range(1, 7)]
SEMESTER_ATT_COLS = [f"Sem{i}_Attendance" for i in range(1, 7)]


def login_required(route_func):
    """Decorator to protect faculty-only routes."""

    @wraps(route_func)
    def wrapper(*args, **kwargs):
        if not (session.get("user") or session.get("logged_in")):
            flash("Please login to continue.", "error")
            return redirect(url_for("login"))
        return route_func(*args, **kwargs)

    return wrapper


def _ensure_data_dir() -> None:
    """Create data directory if missing."""
    os.makedirs(DATA_DIR, exist_ok=True)


def _safe_read_csv(path: str, dtype=None) -> pd.DataFrame | None:
    """
    Read a CSV safely.
    Returns None if file is missing/empty/corrupt so callers can recreate defaults.
    """
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path, dtype=dtype)
    except (EmptyDataError, ParserError, UnicodeDecodeError, FileNotFoundError):
        return None


def ensure_courses_file() -> None:
    """Ensure courses CSV exists, has valid headers, and has starter data when empty."""
    _ensure_data_dir()
    df = _safe_read_csv(COURSES_PATH, dtype=str)

    if df is None or df.empty:
        pd.DataFrame(DEFAULT_COURSES, columns=["CourseCode", "CourseName"]).to_csv(COURSES_PATH, index=False)
        return

    for col in ["CourseCode", "CourseName"]:
        if col not in df.columns:
            df[col] = ""

    df = df[["CourseCode", "CourseName"]].fillna("")
    df["CourseCode"] = df["CourseCode"].astype(str).str.strip().str.upper()
    df["CourseName"] = df["CourseName"].astype(str).str.strip()
    df = df[df["CourseCode"] != ""].drop_duplicates(subset=["CourseCode"], keep="first")

    # If sanitization removed all rows, reseed defaults.
    if df.empty:
        df = pd.DataFrame(DEFAULT_COURSES, columns=["CourseCode", "CourseName"])

    df.to_csv(COURSES_PATH, index=False)


def load_courses() -> pd.DataFrame:
    """Load course catalog from CSV safely."""
    ensure_courses_file()
    df = pd.read_csv(COURSES_PATH, dtype=str).fillna("")
    df["CourseCode"] = df["CourseCode"].str.strip().str.upper()
    df["CourseName"] = df["CourseName"].str.strip()
    df = df[df["CourseCode"] != ""]
    df = df.drop_duplicates(subset=["CourseCode"], keep="first")
    return df[["CourseCode", "CourseName"]].reset_index(drop=True)


def save_courses(df: pd.DataFrame) -> None:
    """Persist course catalog to CSV."""
    _ensure_data_dir()
    df = df[["CourseCode", "CourseName"]].copy()
    df.to_csv(COURSES_PATH, index=False)


def get_course_info() -> list[tuple[str, str]]:
    """Return course list as (code, name) tuples."""
    courses_df = load_courses()
    return list(courses_df.itertuples(index=False, name=None))


def get_course_codes() -> list[str]:
    """Return list of active course codes."""
    return [code for code, _ in get_course_info()]


def student_columns(course_codes: list[str]) -> list[str]:
    """Return dynamic student CSV columns with department."""
    return ["Name", "Department", "CurrentSemester"] + SEMESTER_TOTAL_COLS + SEMESTER_ATT_COLS + course_codes + ["Attendance"]


def generate_sample_students_df(course_codes: list[str]) -> pd.DataFrame:
    """Generate sample students with marks, attendance, and semester tracking."""
    rng = random.Random(42)

    first_names = [
        "Aarav", "Vivaan", "Aditya", "Arjun", "Krish", "Ishaan", "Reyansh", "Ayaan", "Rohan", "Siddharth",
        "Diya", "Ananya", "Aadhya", "Ira", "Meera", "Saanvi", "Kavya", "Priya", "Nithya", "Anika",
        "Harsh", "Naveen", "Karthik", "Varun", "Rahul", "Surya", "Pranav", "Ritvik", "Abhinav", "Dev",
    ]
    last_names = [
        "Kumar", "Sharma", "Iyer", "Nair", "Reddy", "Patel", "Singh", "Gupta", "Mishra", "Yadav",
        "Bhat", "Rao", "Menon", "Das", "Joshi", "Verma", "Chauhan", "Saxena", "Kulkarni", "Pillai",
        "Agarwal", "Jain", "Malhotra", "Srinivasan", "Narayanan", "Rajan", "Bhaskar", "Venkatesh", "Dubey", "Chawla",
    ]

    records = []
    name_index = 0

    # 10 sample students per department for a predictable demo dataset.
    for dept in DEPARTMENTS:
        for _ in range(10):
            first = first_names[name_index % len(first_names)]
            last = last_names[(name_index * 3) % len(last_names)]
            name = f"{first} {last}"
            name_index += 1

            row = {
                "Name": name,
                "Department": dept,
                "CurrentSemester": 6,
                "Attendance": rng.randint(60, 98),
            }

            sem_totals, sem_atts = _generate_semester_totals_and_attendance(row["Attendance"])
            for i, col in enumerate(SEMESTER_TOTAL_COLS):
                row[col] = sem_totals[i]
            for i, col in enumerate(SEMESTER_ATT_COLS):
                row[col] = sem_atts[i]

            for code in course_codes:
                row[code] = rng.randint(40, 95)

            records.append(row)

    return pd.DataFrame(records, columns=student_columns(course_codes))


def _normalize_department(value: str) -> str:
    """Map department text to the canonical list (case-insensitive), with fallback."""
    cleaned = str(value).strip()
    if not cleaned:
        return DEPARTMENTS[0]

    lookup = {dept.lower(): dept for dept in DEPARTMENTS}
    return lookup.get(cleaned.lower(), DEPARTMENTS[0])


def _safe_slug(value: str) -> str:
    """Return filesystem-safe slug."""
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip()).strip("_").lower() or "student"


def _generate_semester_totals_and_attendance(base_attendance: float | int | None = None) -> tuple[list[int], list[int]]:
    """Generate realistic semester totals and attendance for Sem1-Sem6."""
    rng = random.Random()

    sem_totals = []
    start = rng.randint(320, 420)
    for _ in range(6):
        drift = rng.randint(-28, 36)
        current = max(300, min(500, (sem_totals[-1] if sem_totals else start) + drift))
        sem_totals.append(int(current))

    sem_attendance = []
    seed_att = int(base_attendance) if base_attendance is not None else rng.randint(68, 92)
    for _ in range(6):
        drift = rng.randint(-6, 7)
        current_att = max(60, min(98, (sem_attendance[-1] if sem_attendance else seed_att) + drift))
        sem_attendance.append(int(current_att))

    return sem_totals, sem_attendance


def _apply_semester_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure semester tracking columns exist and contain valid values."""
    working = df.copy()

    if "CurrentSemester" not in working.columns:
        working["CurrentSemester"] = 6
    working["CurrentSemester"] = pd.to_numeric(working["CurrentSemester"], errors="coerce").fillna(6).astype(int)
    working["CurrentSemester"] = working["CurrentSemester"].clip(lower=1, upper=8)

    for col in SEMESTER_TOTAL_COLS + SEMESTER_ATT_COLS:
        if col not in working.columns:
            working[col] = None

    for idx in working.index:
        totals_missing = any(pd.isna(working.at[idx, col]) for col in SEMESTER_TOTAL_COLS)
        atts_missing = any(pd.isna(working.at[idx, col]) for col in SEMESTER_ATT_COLS)
        if totals_missing or atts_missing:
            att_seed = working.at[idx, "Attendance"] if "Attendance" in working.columns else None
            sem_totals, sem_atts = _generate_semester_totals_and_attendance(att_seed)
            for i, col in enumerate(SEMESTER_TOTAL_COLS):
                working.at[idx, col] = sem_totals[i]
            for i, col in enumerate(SEMESTER_ATT_COLS):
                working.at[idx, col] = sem_atts[i]

    for col in SEMESTER_TOTAL_COLS:
        working[col] = pd.to_numeric(working[col], errors="coerce").fillna(350).astype(int).clip(lower=300, upper=500)
    for col in SEMESTER_ATT_COLS:
        working[col] = pd.to_numeric(working[col], errors="coerce").fillna(75).astype(int).clip(lower=60, upper=98)

    return working


def sync_students_with_courses() -> pd.DataFrame:
    """Align student CSV with current active courses and department column."""
    _ensure_data_dir()
    course_codes = get_course_codes()
    required_cols = student_columns(course_codes)

    df = _safe_read_csv(STUDENTS_PATH)
    if df is None or df.empty:
        df = generate_sample_students_df(course_codes)
        df.to_csv(STUDENTS_PATH, index=False)
        return df

    df = _apply_semester_columns(df)

    for col in required_cols:
        if col not in df.columns:
            if col == "Department":
                df[col] = DEPARTMENTS[0]
            else:
                df[col] = None

    # Keep only supported columns.
    df = df[required_cols].copy()

    # Ensure department values are valid and not blank.
    df["Department"] = df["Department"].apply(_normalize_department)

    df.to_csv(STUDENTS_PATH, index=False)
    return df


def load_students() -> pd.DataFrame:
    """Load students from CSV using dynamic course columns."""
    return sync_students_with_courses()


def save_students(df: pd.DataFrame) -> None:
    """Persist students to CSV with dynamic columns."""
    _ensure_data_dir()
    df = _apply_semester_columns(df)
    required_cols = student_columns(get_course_codes())
    for col in required_cols:
        if col not in df.columns:
            if col == "Department":
                df[col] = DEPARTMENTS[0]
            else:
                df[col] = None
    df[required_cols].to_csv(STUDENTS_PATH, index=False)


def _ensure_activity_log_file() -> None:
    """Create activity log file if it does not exist."""
    if not os.path.exists(ACTIVITY_LOG_PATH):
        with open(ACTIVITY_LOG_PATH, "w", encoding="utf-8"):
            pass


def log_activity(action: str, username: str | None = None, details: str | None = None) -> None:
    """
    Append timestamped activity event.
    Supports both simple and detailed logging.
    """
    _ensure_activity_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if username or details:
        user_part = username or "System"
        details_part = details or ""
        line = f"{timestamp} | {user_part} | {action} | {details_part}\n"
    else:
        line = f"{timestamp} | {action}\n"

    with open(ACTIVITY_LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(line)


def read_activity_logs() -> list[dict[str, str]]:
    """Read activity log file into structured rows."""
    _ensure_activity_log_file()

    rows: list[dict[str, str]] = []
    with open(ACTIVITY_LOG_PATH, "r", encoding="utf-8") as log_file:
        for line in log_file:
            entry = line.rstrip("\n").strip()
            if not entry:
                continue

            # New format: timestamp | username | action | details
            parts = [p.strip() for p in entry.split("|")]
            if len(parts) >= 4:
                rows.append(
                    {
                        "timestamp": parts[0],
                        "username": parts[1],
                        "action": parts[2],
                        "details": " | ".join(parts[3:]),
                    }
                )
                continue

            # Simple format: timestamp | action
            if len(parts) == 2:
                rows.append(
                    {
                        "timestamp": parts[0],
                        "username": "System",
                        "action": parts[1],
                        "details": "",
                    }
                )
                continue

            # Legacy tab-separated format.
            tab_parts = entry.split("\t")
            if len(tab_parts) == 4:
                rows.append(
                    {
                        "timestamp": tab_parts[0],
                        "username": tab_parts[1],
                        "action": tab_parts[2],
                        "details": tab_parts[3],
                    }
                )
    return list(reversed(rows))


def _student_analytics_df() -> pd.DataFrame:
    """Compute cross-page analytics for risk, API, trend, improvement, and department rank."""
    df = load_students().copy()
    if df.empty:
        return pd.DataFrame()

    for col in ["Sem1_Total", "Sem4_Total", "Sem5_Total", "Sem6_Total", "Sem6_Attendance", "Attendance", "CurrentSemester"]:
        if col not in df.columns:
            df[col] = 0

    df["Name"] = df["Name"].astype(str).str.strip()
    df["Department"] = df["Department"].astype(str).apply(_normalize_department)
    df["CurrentSemester"] = pd.to_numeric(df["CurrentSemester"], errors="coerce").fillna(6).astype(int)
    df["Sem1_Total"] = pd.to_numeric(df["Sem1_Total"], errors="coerce").fillna(0)
    df["Sem4_Total"] = pd.to_numeric(df["Sem4_Total"], errors="coerce").fillna(0)
    df["Sem5_Total"] = pd.to_numeric(df["Sem5_Total"], errors="coerce").fillna(0)
    df["Sem6_Total"] = pd.to_numeric(df["Sem6_Total"], errors="coerce").fillna(0)
    fallback_att = pd.to_numeric(df["Attendance"], errors="coerce").fillna(0)
    df["Sem6_Attendance"] = pd.to_numeric(df["Sem6_Attendance"], errors="coerce").fillna(fallback_att)

    df["AtRisk"] = (df["Sem6_Attendance"] < 75) | (df["Sem6_Total"] < 250)
    df["PerformanceIndex"] = (((df["Sem6_Total"] / 500.0) * 0.7) + ((df["Sem6_Attendance"] / 100.0) * 0.3)) * 10.0
    df["PerformanceIndex"] = df["PerformanceIndex"].round(1)

    df["ImprovementPct"] = df.apply(
        lambda row: round(((row["Sem6_Total"] - row["Sem1_Total"]) / row["Sem1_Total"]) * 100, 2) if row["Sem1_Total"] else 0.0,
        axis=1,
    )
    df["ImprovementText"] = df["ImprovementPct"].apply(
        lambda value: f"Improved by {abs(value):.0f}%" if value >= 0 else f"Decreased by {abs(value):.0f}%"
    )

    df["TrendStatus"] = df.apply(
        lambda row: _student_directory_status(int(row["Sem4_Total"]), int(row["Sem5_Total"]), int(row["Sem6_Total"])),
        axis=1,
    )

    df["DepartmentRank"] = (
        df.groupby("Department")["Sem6_Total"].rank(method="dense", ascending=False).fillna(0).astype(int)
    )
    df["DepartmentCount"] = df.groupby("Department")["Name"].transform("count").fillna(0).astype(int)

    def _insight(row: pd.Series) -> str:
        if row["TrendStatus"] == "Improving" and row["Sem6_Attendance"] >= 85:
            return "Student shows consistent academic growth."
        if row["Sem6_Attendance"] < 75:
            return "Attendance needs improvement."
        if row["TrendStatus"] == "Stable":
            return "Performance trend is unstable."
        return "Performance is acceptable with scope for stronger consistency."

    df["Insight"] = df.apply(_insight, axis=1)
    return df


def calculate_grade(avg: float) -> str:
    """Return grade from average marks."""
    if avg >= 75:
        return "A"
    if avg >= 50:
        return "B"
    return "C"


def prepare_data(df: pd.DataFrame, course_codes: list[str]) -> pd.DataFrame:
    """Clean data and add Total, Average, Grade, Weak Student."""
    if df.empty:
        return pd.DataFrame(columns=student_columns(course_codes) + ["Total", "Average", "Grade", "Weak Student"])

    clean_df = df.copy()

    for col in course_codes + ["Attendance"]:
        clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

    clean_df["Department"] = clean_df["Department"].astype(str).apply(_normalize_department)
    clean_df = clean_df.dropna(subset=["Name", "Department"] + course_codes + ["Attendance"])

    if course_codes:
        clean_df["Total"] = clean_df[course_codes].sum(axis=1)
        clean_df["Average"] = (clean_df["Total"] / len(course_codes)).round(2)
    else:
        clean_df["Total"] = 0
        clean_df["Average"] = 0

    clean_df["Grade"] = clean_df["Average"].apply(calculate_grade)
    clean_df["Weak Student"] = clean_df["Average"] < 50
    return clean_df


def add_prediction(df: pd.DataFrame) -> pd.DataFrame:
    """Add pass/fail prediction from Logistic Regression."""
    pred_df = df.copy()

    if pred_df.empty:
        pred_df["Prediction"] = []
        return pred_df

    X = pred_df[["Average", "Attendance"]]
    y = ((pred_df["Average"] >= 50) & (pred_df["Attendance"] >= 75)).astype(int)

    if y.nunique() < 2:
        pred_df["Prediction"] = y.map({1: "Pass", 0: "Fail"})
        return pred_df

    model = LogisticRegression(random_state=42)
    model.fit(X, y)
    y_pred = model.predict(X)
    pred_df["Prediction"] = pd.Series(y_pred, index=pred_df.index).map({1: "Pass", 0: "Fail"})
    return pred_df


def _student_directory_status(sem4: int, sem5: int, sem6: int) -> str:
    """Return trend status for the student directory view."""
    if sem6 > sem5 > sem4:
        return "Improving"
    if sem6 < sem5 < sem4:
        return "Declining"
    return "Stable"


def _student_performance_badge(sem6_total: int) -> tuple[str, str]:
    """Return display badge text and CSS class for Sem6 total."""
    if sem6_total >= 400:
        return "Excellent", "performance-excellent"
    if sem6_total >= 300:
        return "Good", "performance-good"
    if sem6_total >= 250:
        return "Average", "performance-average"
    return "At Risk", "performance-risk"


def _build_students_directory_df() -> pd.DataFrame:
    """Build enriched directory dataframe with rank, trend, and performance metadata."""
    base_df = _student_analytics_df()
    if base_df.empty:
        return pd.DataFrame(
            columns=[
                "Name",
                "Department",
                "CurrentSemester",
                "Sem6_Total",
                "Sem6_Attendance",
                "TrendStatus",
                "PerformanceBadge",
                "PerformanceClass",
                "PerformanceIndex",
                "ImprovementPct",
                "ImprovementText",
                "AtRisk",
                "Rank",
                "IsWeak",
                "IsTopper",
            ]
        )

    badge_series = base_df["Sem6_Total"].apply(_student_performance_badge)
    base_df["PerformanceBadge"] = badge_series.apply(lambda item: item[0])
    base_df["PerformanceClass"] = badge_series.apply(lambda item: item[1])

    ranked_df = base_df.sort_values(["Sem6_Total", "Name"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
    ranked_df["Rank"] = ranked_df.index + 1
    ranked_df["IsWeak"] = ranked_df["Sem6_Total"] < 250
    ranked_df["IsTopper"] = ranked_df["Rank"] == 1
    ranked_df["AtRisk"] = ranked_df["AtRisk"].astype(bool)
    return ranked_df


def _create_profile_charts(student_name: str, semester_totals: list[int], semester_attendance: list[int]) -> dict[str, str]:
    """Generate student profile charts and return static-relative file paths."""
    profile_dir = os.path.join(BASE_DIR, UPLOAD_FOLDER)
    os.makedirs(profile_dir, exist_ok=True)

    slug = _safe_slug(student_name)
    sem_labels = [f"Sem{i}" for i in range(1, 7)]

    perf_file = f"{slug}_performance_trend.png"
    perf_path = os.path.join(profile_dir, perf_file)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(sem_labels, semester_totals, marker="o", linewidth=2.2, color="#4f46e5")
    ax.set_title("Performance Trend")
    ax.set_xlabel("Semester")
    ax.set_ylabel("Total Marks (out of 500)")
    ax.set_ylim(250, 520)
    ax.grid(alpha=0.25, linestyle="--")
    plt.tight_layout()
    fig.savefig(perf_path, dpi=120)
    plt.close(fig)

    att_file = f"{slug}_attendance_trend.png"
    att_path = os.path.join(profile_dir, att_file)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(sem_labels, semester_attendance, marker="o", linewidth=2.2, color="#10b981")
    ax.set_title("Attendance Trend")
    ax.set_xlabel("Semester")
    ax.set_ylabel("Attendance (%)")
    ax.set_ylim(55, 100)
    ax.grid(alpha=0.25, linestyle="--")
    plt.tight_layout()
    fig.savefig(att_path, dpi=120)
    plt.close(fig)

    pie_file = f"{slug}_semester_contribution.png"
    pie_path = os.path.join(profile_dir, pie_file)
    plt.figure(figsize=(6, 6))
    plt.pie(
        semester_totals,
        labels=sem_labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=["#4f46e5", "#7c3aed", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"],
        textprops={"fontsize": 12},
    )
    plt.title(
        "Semester Contribution to Overall Performance",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    plt.axis("equal")
    plt.tight_layout()
    plt.savefig(pie_path, dpi=120)
    plt.close()

    return {
        "performance_chart": f"images/students/{perf_file}",
        "attendance_chart": f"images/students/{att_file}",
        "contribution_chart": f"images/students/{pie_file}",
    }


@app.route("/", methods=["GET", "POST"])
def login():
    """Faculty login page."""
    if session.get("user") or session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        is_default_admin = username == "admin" and password == "admin"
        is_faculty_user = username in FACULTY_USERS and FACULTY_USERS[username] == password

        if is_default_admin or is_faculty_user:
            session["user"] = username
            session["logged_in"] = True
            session["username"] = username
            log_activity("Faculty logged in", username=username, details="Successful login")
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid login credentials", "error")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard with department cards and full student overview."""
    if "user" not in session and not session.get("logged_in"):
        return redirect(url_for("login"))
    course_info = get_course_info()
    course_codes = [code for code, _ in course_info]

    students_df = load_students()
    processed_df = add_prediction(prepare_data(students_df, course_codes))
    analytics_df = _student_analytics_df()
    risky_students_count = int(analytics_df["AtRisk"].sum()) if not analytics_df.empty else 0

    weak_students = processed_df[processed_df["Weak Student"]].to_dict(orient="records")

    department_cards = []
    for dept in DEPARTMENTS:
        dept_df = processed_df[processed_df["Department"] == dept]
        department_cards.append(
            {
                "name": dept,
                "total": len(dept_df),
                "weak": int(dept_df["Weak Student"].sum()) if not dept_df.empty else 0,
            }
        )

    return render_template(
        "dashboard.html",
        username=session.get("username", "Faculty"),
        students=processed_df.to_dict(orient="records"),
        weak_students=weak_students,
        risky_students_count=risky_students_count,
        course_info=course_info,
        department_cards=department_cards,
    )


@app.route("/department/<path:department_name>")
@login_required
def department_view(department_name):
    """Department-wise student list with search and weak student count."""
    selected_department = department_name.strip()
    if selected_department not in DEPARTMENTS:
        flash("Department not found.", "error")
        return redirect(url_for("dashboard"))

    course_info = get_course_info()
    course_codes = [code for code, _ in course_info]

    students_df = load_students()
    processed_df = add_prediction(prepare_data(students_df, course_codes))
    dept_df = processed_df[processed_df["Department"] == selected_department].copy()

    query = request.args.get("q", "").strip().lower()
    if query:
        dept_df = dept_df[dept_df["Name"].astype(str).str.lower().str.contains(query)]

    weak_count = int(dept_df["Weak Student"].sum()) if not dept_df.empty else 0

    # Department-specific summary metrics requested for this route.
    if dept_df.empty:
        dept_avg_attendance = 0
        dept_high_attendance = 0
        dept_low_attendance = 0
    else:
        dept_avg_attendance = round(float(dept_df["Attendance"].mean()), 2)
        dept_high_attendance = round(float(dept_df["Attendance"].max()), 2)
        dept_low_attendance = round(float(dept_df["Attendance"].min()), 2)

    return render_template(
        "department.html",
        username=session.get("username", "Faculty"),
        department_name=selected_department,
        students=dept_df.to_dict(orient="records"),
        total_students=len(dept_df),
        weak_students_count=weak_count,
        dept_avg_attendance=dept_avg_attendance,
        dept_high_attendance=dept_high_attendance,
        dept_low_attendance=dept_low_attendance,
        query=request.args.get("q", "").strip(),
        course_info=course_info,
    )


@app.route("/add-student", methods=["GET", "POST"])
@login_required
def add_student():
    """Add student form and append record to CSV."""
    course_info = get_course_info()
    course_codes = [code for code, _ in course_info]

    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            department = request.form.get("department", "").strip()
            attendance = float(request.form.get("attendance", "0"))

            if department not in DEPARTMENTS:
                department = DEPARTMENTS[0]

            course_marks = {}
            for code in course_codes:
                course_marks[code] = float(request.form.get(code, "0"))

            if not name:
                flash("Student name is required.", "error")
                return redirect(url_for("add_student"))

            if any(v < 0 or v > 100 for v in list(course_marks.values()) + [attendance]):
                flash("Marks and attendance must be between 0 and 100.", "error")
                return redirect(url_for("add_student"))

            existing = load_students()
            new_row_data = {"Name": name, "Department": department}
            new_row_data.update(course_marks)
            new_row_data["Attendance"] = attendance

            new_row = pd.DataFrame([new_row_data])
            save_students(pd.concat([existing, new_row], ignore_index=True))
            log_activity("Added student", username=session.get("username", "Faculty"), details=name)

            flash("Student added successfully.", "success")
            return redirect(url_for("dashboard"))
        except ValueError:
            flash("Please enter valid numeric values.", "error")
            return redirect(url_for("add_student"))

    return render_template(
        "add_student.html",
        username=session.get("username", "Faculty"),
        course_info=course_info,
        departments=DEPARTMENTS,
    )


@app.route("/student/<path:student_name>", endpoint="student_profile")
@login_required
def student_profile(student_name):
    """Student profile dashboard with semester-wise performance analysis."""
    students_df = load_students()
    analytics_df = _student_analytics_df()

    # Use exact match first; fallback to case-insensitive match.
    selected = students_df[students_df["Name"] == student_name]
    if selected.empty:
        selected = students_df[students_df["Name"].astype(str).str.lower() == student_name.lower()]

    if selected.empty:
        return "Student not found", 404

    student = selected.iloc[0].copy()
    student_name_value = str(student["Name"]).strip()
    analytic_row = analytics_df[analytics_df["Name"].astype(str).str.lower() == student_name_value.lower()]
    analytics = analytic_row.iloc[0] if not analytic_row.empty else None

    gender = str(student.get("Gender", "Male")).strip().lower()
    image_filename = f"{student_name_value.replace(' ', '_')}.jpg"
    image_fs_path = os.path.join(BASE_DIR, UPLOAD_FOLDER, image_filename)
    if os.path.exists(image_fs_path):
        image_url = url_for("static", filename=f"images/students/{image_filename}")
    else:
        image_url = url_for("static", filename="images/default_female.png" if gender == "female" else "images/default_male.png")

    department_value = str(student.get("Department", "")).strip()
    semester_raw = student.get("Semester", student.get("CurrentSemester", 0))
    semester_value = int(pd.to_numeric(pd.Series([semester_raw]), errors="coerce").fillna(0).iloc[0])

    semester_totals = [int(student[col]) for col in SEMESTER_TOTAL_COLS]
    semester_attendance = [int(student[col]) for col in SEMESTER_ATT_COLS]
    semester_labels = [f"Sem{i}" for i in range(1, 7)]

    sem_table = [
        {
            "semester": sem,
            "total": semester_totals[idx],
            "attendance": semester_attendance[idx],
            "attendance_class": (
                "attendance-high"
                if semester_attendance[idx] > 90
                else "attendance-medium"
                if semester_attendance[idx] >= 75
                else "attendance-low"
            ),
        }
        for idx, sem in enumerate(semester_labels)
    ]

    sem1 = semester_totals[0]
    sem6 = semester_totals[-1]
    improvement_pct = round(((sem6 - sem1) / sem1) * 100, 2) if sem1 else 0.0
    improvement_text = f"Improved by {abs(improvement_pct):.0f}%" if improvement_pct >= 0 else f"Decreased by {abs(improvement_pct):.0f}%"

    best_idx = max(range(6), key=lambda i: semester_totals[i])
    weak_idx = min(range(6), key=lambda i: semester_totals[i])
    best_semester = semester_labels[best_idx]
    weakest_semester = semester_labels[weak_idx]

    # Requested status logic.
    if semester_totals[5] > semester_totals[4] > semester_totals[3]:
        status = "Improving"
    elif semester_totals[5] < semester_totals[4] < semester_totals[3]:
        status = "Declining"
    else:
        status = "Stable"

    charts = _create_profile_charts(student["Name"], semester_totals, semester_attendance)
    performance_index = float(analytics["PerformanceIndex"]) if analytics is not None else round((((sem6 / 500) * 0.7) + ((semester_attendance[-1] / 100) * 0.3)) * 10, 1)
    is_at_risk = bool(analytics["AtRisk"]) if analytics is not None else (semester_attendance[-1] < 75 or sem6 < 250)
    department_rank = int(analytics["DepartmentRank"]) if analytics is not None else 0
    department_count = int(analytics["DepartmentCount"]) if analytics is not None else 0
    insight_text = str(analytics["Insight"]) if analytics is not None else "Performance is acceptable with scope for stronger consistency."

    return render_template(
        "student_profile.html",
        username=session.get("username", "Faculty"),
        student=student.to_dict(),
        student_name=student["Name"],
        department=department_value,
        semester=semester_value,
        current_semester=semester_value,
        image_url=image_url,
        sem_table=sem_table,
        improvement_pct=improvement_pct,
        improvement_text=improvement_text,
        best_semester=best_semester,
        weakest_semester=weakest_semester,
        status=status,
        performance_index=performance_index,
        is_at_risk=is_at_risk,
        department_rank=department_rank,
        department_count=department_count,
        insight_text=insight_text,
        performance_chart=charts["performance_chart"],
        attendance_chart=charts["attendance_chart"],
        contribution_chart=charts["contribution_chart"],
    )


@app.route("/export/<path:student_name>", endpoint="export_student")
@login_required
def export_student_pdf(student_name):
    """Generate a professional student academic report PDF and force download."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ModuleNotFoundError:
        flash("PDF export dependency missing. Install requirements and retry.", "error")
        return redirect(url_for("student_profile", student_name=student_name))

    students_df = load_students()

    # Keep matching behavior aligned with student profile route.
    selected = students_df[students_df["Name"] == student_name]
    if selected.empty:
        selected = students_df[students_df["Name"].astype(str).str.lower() == student_name.lower()]

    if selected.empty:
        flash("Student profile not found.", "error")
        return redirect(url_for("dashboard"))

    student = selected.iloc[0].copy()

    semester_totals = [int(student[col]) for col in SEMESTER_TOTAL_COLS]
    semester_attendance = [int(student[col]) for col in SEMESTER_ATT_COLS]
    semester_labels = [f"Sem{i}" for i in range(1, 7)]

    sem1 = semester_totals[0]
    sem6 = semester_totals[-1]
    improvement_pct = round(((sem6 - sem1) / sem1) * 100, 2) if sem1 else 0.0

    best_idx = max(range(6), key=lambda i: semester_totals[i])
    weak_idx = min(range(6), key=lambda i: semester_totals[i])
    best_semester = semester_labels[best_idx]
    weakest_semester = semester_labels[weak_idx]

    if semester_totals[5] > semester_totals[4] > semester_totals[3]:
        status = "Improving"
    elif semester_totals[5] < semester_totals[4] < semester_totals[3]:
        status = "Declining"
    else:
        status = "Stable"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title="Student Academic Report",
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Student Academic Report", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Basic Information", styles["Heading3"]))
    basic_info_data = [
        ["Name", str(student["Name"])],
        ["Department", str(student["Department"])],
        ["Current Semester", str(int(student["CurrentSemester"]))],
    ]
    basic_info_table = Table(basic_info_data, colWidths=[160, 340])
    basic_info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1E1B4B")),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(basic_info_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("2. Semester-wise Marks Table", styles["Heading3"]))
    marks_data = [["Semester", "Total Marks (out of 500)"]]
    marks_data.extend([[semester_labels[i], semester_totals[i]] for i in range(6)])
    marks_table = Table(marks_data, colWidths=[200, 300])
    marks_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338CA")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ]
        )
    )
    story.append(marks_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("3. Attendance Table", styles["Heading3"]))
    attendance_data = [["Semester", "Attendance (%)"]]
    attendance_data.extend([[semester_labels[i], semester_attendance[i]] for i in range(6)])
    attendance_table = Table(attendance_data, colWidths=[200, 300])
    attendance_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0EA5E9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
            ]
        )
    )
    story.append(attendance_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("4. Performance Analysis", styles["Heading3"]))
    analysis_data = [
        ["Improvement Percentage", f"{improvement_pct}%"],
        ["Best Semester", best_semester],
        ["Weakest Semester", weakest_semester],
        ["Status", status],
    ]
    analysis_table = Table(analysis_data, colWidths=[220, 280])
    analysis_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECFEFF")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#0F172A")),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(analysis_table)
    story.append(Spacer(1, 20))

    generated_on = datetime.now().strftime("%d-%m-%Y %H:%M")
    footer_text = f"Generated on: {generated_on}<br/>Bannari Amman Institute of Technology"
    story.append(Paragraph("5. Footer", styles["Heading3"]))
    story.append(Paragraph(footer_text, styles["Normal"]))

    doc.build(story)
    buffer.seek(0)

    # Keep download filename consistent with requested format.
    filename = f"{str(student['Name']).strip().replace(' ', '_')}_Academic_Report.pdf"
    log_activity("Exported PDF for student", username=session.get("username", "Faculty"), details=str(student["Name"]))
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


@app.route("/student_profile/<path:student_name>")
@app.route("/student-profile/<path:student_name>")
@login_required
def student_profile_alias(student_name):
    """Backward-compatible aliases for profile URLs."""
    return redirect(url_for("student_profile", student_name=student_name))


@app.route("/students", endpoint="students_directory")
@login_required
def students_directory():
    """Premium student directory with ranking, filters, search, and pagination."""
    sort_key = request.args.get("sort", "topper").strip().lower()
    search_query = request.args.get("search", "").strip()

    # Parse page safely; fallback to first page on invalid values.
    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1

    students_df = _build_students_directory_df()

    # Summary cards are based on full directory before search filters.
    total_students = int(len(students_df))
    weak_students_count = int(students_df["IsWeak"].sum()) if total_students else 0
    risky_students_count = int(students_df["AtRisk"].sum()) if total_students else 0
    topper_name = students_df.iloc[0]["Name"] if total_students else "N/A"
    average_attendance = round(float(students_df["Sem6_Attendance"].mean()), 2) if total_students else 0.0

    filtered_df = students_df.copy()
    if search_query:
        name_match = filtered_df["Name"].astype(str).str.contains(search_query, case=False, na=False)
        dept_match = filtered_df["Department"].astype(str).str.contains(search_query, case=False, na=False)
        filtered_df = filtered_df[name_match | dept_match]

    sort_map = {
        "topper": (["Sem6_Total", "Name"], [False, True]),
        "weakest": (["Sem6_Total", "Name"], [True, True]),
        "attendance_high": (["Sem6_Attendance", "Name"], [False, True]),
        "attendance_low": (["Sem6_Attendance", "Name"], [True, True]),
        "name_az": (["Name"], [True]),
        "name_za": (["Name"], [False]),
        "department": (["Department", "Sem6_Total", "Name"], [True, False, True]),
    }

    if sort_key not in sort_map:
        sort_key = "topper"

    sort_columns, sort_ascending = sort_map[sort_key]
    filtered_df = filtered_df.sort_values(sort_columns, ascending=sort_ascending, kind="mergesort").reset_index(drop=True)

    # Pagination: 10 cards per page.
    per_page = 10
    total_records = int(len(filtered_df))
    total_pages = max(1, int(math.ceil(total_records / per_page))) if total_records else 1
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_df = filtered_df.iloc[start : start + per_page].copy()

    return render_template(
        "students.html",
        username=session.get("username", "Faculty"),
        students=page_df.to_dict(orient="records"),
        total_students=total_students,
        weak_students_count=weak_students_count,
        risky_students_count=risky_students_count,
        topper_name=topper_name,
        average_attendance=average_attendance,
        sort=sort_key,
        search=search_query,
        current_page=page,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages,
    )


@app.route("/leaderboard")
@login_required
def leaderboard():
    """Leaderboard with department filtering and sorting options."""
    selected_department = request.args.get("department", "All").strip() or "All"
    sort_by = request.args.get("sort_by", "top_marks").strip().lower() or "top_marks"
    analytics_df = _student_analytics_df()

    departments: list[str] = sorted(DEPARTMENTS)
    leaderboard_rows: list[dict[str, str | int]] = []
    topper: dict[str, str | int] | None = None

    if not analytics_df.empty:
        if selected_department not in departments and selected_department != "All":
            selected_department = "All"

        working_df = analytics_df.copy()
        if selected_department != "All":
            working_df = working_df[working_df["Department"] == selected_department]

        # Ranking is always based on top marks in current filtered scope.
        ranking_df = working_df.sort_values(["Sem6_Total", "Name"], ascending=[False, True]).reset_index(drop=True)
        ranking_df["Rank"] = range(1, len(ranking_df) + 1)
        topper = (
            {
                "Name": str(ranking_df.iloc[0]["Name"]),
                "Department": str(ranking_df.iloc[0]["Department"]),
                "Sem6_Total": int(ranking_df.iloc[0]["Sem6_Total"]),
                "Rank": int(ranking_df.iloc[0]["Rank"]),
            }
            if not ranking_df.empty
            else None
        )

        # For selected department, show Top 5 / Lower 5 controls.
        if sort_by == "lowest_marks":
            display_df = working_df.sort_values(["Sem6_Total", "Name"], ascending=[True, True]).head(5).reset_index(drop=True)
        else:
            sort_by = "top_marks"
            display_df = working_df.sort_values(["Sem6_Total", "Name"], ascending=[False, True]).head(5).reset_index(drop=True)

        leaderboard_rows = [
            {
                "Rank": int(ranking_df[ranking_df["Name"] == row["Name"]]["Rank"].iloc[0]) if not ranking_df.empty else 0,
                "Name": str(row["Name"]),
                "Department": str(row["Department"]),
                "Sem6_Total": int(row["Sem6_Total"]),
            }
            for _, row in display_df.iterrows()
        ]

    return render_template(
        "leaderboard.html",
        username=session.get("username", "Faculty"),
        leaderboard=leaderboard_rows,
        departments=departments,
        selected_department=selected_department,
        selected_sort=sort_by,
        topper=topper,
    )


@app.route("/export_department/<path:department_name>")
@login_required
def export_department_report(department_name):
    """Export department summary PDF report."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ModuleNotFoundError:
        flash("PDF export dependency missing. Install requirements and retry.", "error")
        return redirect(url_for("dashboard"))

    dept = department_name.strip()
    if dept not in DEPARTMENTS:
        flash("Department not found.", "error")
        return redirect(url_for("dashboard"))

    analytics_df = _student_analytics_df()
    dept_df = analytics_df[analytics_df["Department"] == dept].copy() if not analytics_df.empty else pd.DataFrame()

    total_students = int(len(dept_df))
    average_marks = round(float(dept_df["Sem6_Total"].mean()), 2) if total_students else 0.0
    topper_name = str(dept_df.sort_values(["Sem6_Total", "Name"], ascending=[False, True]).iloc[0]["Name"]) if total_students else "N/A"
    weak_df = dept_df[dept_df["Sem6_Total"] < 250].copy() if total_students else pd.DataFrame()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Department Academic Report", styles["Title"]),
        Spacer(1, 10),
        Paragraph(f"Department: {dept}", styles["Heading3"]),
        Spacer(1, 8),
    ]

    summary_data = [
        ["Total Students", str(total_students)],
        ["Average Sem6 Marks", str(average_marks)],
        ["Topper", topper_name],
    ]
    summary_table = Table(summary_data, colWidths=[220, 280])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Weak Students (Sem6 Total < 250)", styles["Heading3"]))
    weak_data = [["Name", "Sem6 Total", "Attendance"]]
    if weak_df.empty:
        weak_data.append(["No weak students", "-", "-"])
    else:
        for _, row in weak_df.sort_values(["Sem6_Total", "Name"], ascending=[True, True]).iterrows():
            weak_data.append([str(row["Name"]), str(int(row["Sem6_Total"])), f"{float(row['Sem6_Attendance']):.2f}%"])

    weak_table = Table(weak_data, colWidths=[240, 120, 140])
    weak_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4338CA")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ]
        )
    )
    story.append(weak_table)

    doc.build(story)
    buffer.seek(0)

    safe_name = dept.replace(" ", "_")
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{safe_name}_Department_Report.pdf",
        mimetype="application/pdf",
    )


@app.route("/activity")
@login_required
def activity():
    """Render admin activity log entries."""
    return render_template(
        "activity.html",
        username=session.get("username", "Faculty"),
        logs=read_activity_logs(),
    )


@app.route("/edit-student/<path:student_name>", methods=["POST"])
@login_required
def edit_student(student_name):
    """Minimal student edit endpoint for admin logging and quick updates."""
    students_df = load_students()
    idx = students_df[students_df["Name"].astype(str).str.lower() == student_name.lower()].index
    if len(idx) == 0:
        flash("Student not found.", "error")
        return redirect(url_for("students_directory"))

    department = request.form.get("department", "").strip()
    if department and department in DEPARTMENTS:
        students_df.at[idx[0], "Department"] = department

    current_sem = request.form.get("current_semester", "").strip()
    if current_sem:
        try:
            students_df.at[idx[0], "CurrentSemester"] = int(current_sem)
        except ValueError:
            pass

    save_students(students_df)
    log_activity("Edited student", username=session.get("username", "Faculty"), details=student_name)
    flash("Student updated successfully.", "success")
    return redirect(url_for("student_profile", student_name=student_name))


@app.route("/delete-student/<path:student_name>", methods=["POST"])
@login_required
def delete_student(student_name):
    """Delete student row and append admin audit log."""
    students_df = load_students()
    keep_df = students_df[students_df["Name"].astype(str).str.lower() != student_name.lower()].copy()
    if len(keep_df) == len(students_df):
        flash("Student not found.", "error")
        return redirect(url_for("students_directory"))

    save_students(keep_df)
    log_activity("Deleted student", username=session.get("username", "Faculty"), details=student_name)
    flash("Student deleted successfully.", "success")
    return redirect(url_for("students_directory"))


@app.route("/courses")
@login_required
def courses():
    """View and search courses."""
    query = request.args.get("q", "").strip().lower()
    courses_df = load_courses()

    if query:
        courses_df = courses_df[
            courses_df["CourseCode"].str.lower().str.contains(query)
            | courses_df["CourseName"].str.lower().str.contains(query)
        ]

    return render_template(
        "courses.html",
        username=session.get("username", "Faculty"),
        courses=courses_df.to_dict(orient="records"),
        query=request.args.get("q", "").strip(),
    )


@app.route("/add_course", methods=["POST"])
@login_required
def add_course():
    """Add a new course and sync student schema."""
    code = request.form.get("course_code", "").strip().upper()
    name = request.form.get("course_name", "").strip()

    if not code or not name:
        flash("Course code and course name are required.", "error")
        return redirect(url_for("courses"))

    courses_df = load_courses()
    if code in courses_df["CourseCode"].values:
        flash("Course code already exists.", "error")
        return redirect(url_for("courses"))

    updated_df = pd.concat(
        [courses_df, pd.DataFrame([{"CourseCode": code, "CourseName": name}])],
        ignore_index=True,
    )
    save_courses(updated_df)

    # Add new course column to students dynamically.
    sync_students_with_courses()

    flash("Course added successfully.", "success")
    return redirect(url_for("courses"))


@app.route("/edit_course/<code>", methods=["GET", "POST"])
@login_required
def edit_course(code):
    """Edit existing course code and/or name."""
    original_code = code.strip().upper()
    courses_df = load_courses()

    selected = courses_df[courses_df["CourseCode"] == original_code]
    if selected.empty:
        flash("Course not found.", "error")
        return redirect(url_for("courses"))

    if request.method == "POST":
        new_code = request.form.get("course_code", "").strip().upper()
        new_name = request.form.get("course_name", "").strip()

        if not new_code or not new_name:
            flash("Course code and course name are required.", "error")
            return redirect(url_for("edit_course", code=original_code))

        duplicate_exists = (
            (courses_df["CourseCode"] == new_code) & (courses_df["CourseCode"] != original_code)
        ).any()
        if duplicate_exists:
            flash("Another course already uses this code.", "error")
            return redirect(url_for("edit_course", code=original_code))

        # Rename student marks column if course code changed.
        students_raw = _safe_read_csv(STUDENTS_PATH)
        if students_raw is not None and original_code != new_code and original_code in students_raw.columns:
            if new_code in students_raw.columns:
                students_raw[new_code] = students_raw[new_code].where(
                    students_raw[new_code].notna(),
                    students_raw[original_code],
                )
                students_raw = students_raw.drop(columns=[original_code])
            else:
                students_raw = students_raw.rename(columns={original_code: new_code})
            students_raw.to_csv(STUDENTS_PATH, index=False)

        courses_df.loc[courses_df["CourseCode"] == original_code, "CourseCode"] = new_code
        courses_df.loc[courses_df["CourseCode"] == new_code, "CourseName"] = new_name
        save_courses(courses_df)

        sync_students_with_courses()
        flash("Course updated successfully.", "success")
        return redirect(url_for("courses"))

    course = selected.iloc[0].to_dict()
    return render_template(
        "edit_course.html",
        username=session.get("username", "Faculty"),
        course=course,
    )


@app.route("/delete_course/<code>")
@login_required
def delete_course(code):
    """Delete a course if it is not used in student records."""
    target_code = code.strip().upper()
    courses_df = load_courses()

    if target_code not in courses_df["CourseCode"].values:
        flash("Course not found.", "error")
        return redirect(url_for("courses"))

    students_df = load_students()
    if target_code in students_df.columns:
        has_marks = students_df[target_code].notna() & (students_df[target_code].astype(str).str.strip() != "")
        if has_marks.any():
            flash("Cannot delete this course. It already exists in student records.", "error")
            return redirect(url_for("courses"))

    updated_courses = courses_df[courses_df["CourseCode"] != target_code].copy()
    save_courses(updated_courses)

    if target_code in students_df.columns:
        students_df = students_df.drop(columns=[target_code])
    save_students(students_df)

    flash("Course deleted successfully.", "success")
    return redirect(url_for("courses"))


@app.route("/logout")
def logout():
    """Clear session and redirect to login page."""
    log_activity("Faculty logged out", username=session.get("user") or session.get("username", "Faculty"), details="Session ended")
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.errorhandler(404)
def not_found(e):
    """Render custom 404 page."""
    return render_template("404.html"), 404


if __name__ == "__main__":
    # Prime CSV files and schemas before first request.
    sync_students_with_courses()
    _ensure_activity_log_file()

    # Startup diagnostics: print key routes so we can verify correct app is running.
    print(f"Starting Flask app from: {os.path.abspath(__file__)}")
    print("Available routes:")
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        print(f"  {rule.rule} -> {rule.endpoint}")

    # Bind to all interfaces so both localhost and network URL work.
    # Keep reloader disabled to avoid thread/signal issues on Windows.
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
