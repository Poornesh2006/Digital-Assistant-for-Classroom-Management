import json
import os
import random
import re
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError
from sklearn.linear_model import LogisticRegression

from classroom_app.config import (
    ACTIVITY_LOG_PATH,
    COURSES_PATH,
    DATA_DIR,
    DEFAULT_COURSES,
    DEPARTMENTS,
    FEEDBACK_PATH,
    SEMESTER_ATT_COLS,
    SEMESTER_TOTAL_COLS,
    STUDENTS_PATH,
)

_CACHE_EMPTY = object()
_courses_cache: dict[str, Any] = {"signature": _CACHE_EMPTY, "data": None}
_students_cache: dict[str, Any] = {"signature": _CACHE_EMPTY, "data": None}
_analytics_cache: dict[str, Any] = {"signature": _CACHE_EMPTY, "data": None}
_processed_students_cache: dict[str, Any] = {"signature": _CACHE_EMPTY, "data": None}
_activity_logs_cache: dict[str, Any] = {"signature": _CACHE_EMPTY, "data": None}


def _file_signature(path: str) -> tuple[bool, int, int]:
    if not os.path.exists(path):
        return (False, 0, 0)
    stat = os.stat(path)
    return (True, int(stat.st_mtime_ns), int(stat.st_size))


def _invalidate_students_cache() -> None:
    _students_cache["signature"] = _CACHE_EMPTY
    _students_cache["data"] = None
    _analytics_cache["signature"] = _CACHE_EMPTY
    _analytics_cache["data"] = None
    _processed_students_cache["signature"] = _CACHE_EMPTY
    _processed_students_cache["data"] = None


def _invalidate_courses_cache() -> None:
    _courses_cache["signature"] = _CACHE_EMPTY
    _courses_cache["data"] = None
    _invalidate_students_cache()


def _invalidate_activity_logs_cache() -> None:
    _activity_logs_cache["signature"] = _CACHE_EMPTY
    _activity_logs_cache["data"] = None


def _ensure_data_dir() -> None:
    """Create data directory if missing."""
    os.makedirs(DATA_DIR, exist_ok=True)


def ensure_feedback_file() -> None:
    """Create feedback storage file if missing."""
    os.makedirs(os.path.dirname(FEEDBACK_PATH), exist_ok=True)
    if not os.path.exists(FEEDBACK_PATH):
        with open(FEEDBACK_PATH, "w", encoding="utf-8") as feedback_file:
            json.dump([], feedback_file, indent=2)


def append_feedback_entry(entry: dict[str, str]) -> None:
    """Append a feedback item to feedback JSON storage."""
    ensure_feedback_file()
    try:
        with open(FEEDBACK_PATH, "r", encoding="utf-8") as feedback_file:
            existing = json.load(feedback_file)
    except (json.JSONDecodeError, FileNotFoundError):
        existing = []

    if not isinstance(existing, list):
        existing = []

    existing.append(entry)
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as feedback_file:
        json.dump(existing, feedback_file, indent=2)


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
    signature = _file_signature(COURSES_PATH)
    if _courses_cache["signature"] == signature and _courses_cache["data"] is not None:
        return _courses_cache["data"].copy(deep=True)

    ensure_courses_file()
    df = _safe_read_csv(COURSES_PATH, dtype=str)
    if df is None or df.empty:
        ensure_courses_file()
        df = _safe_read_csv(COURSES_PATH, dtype=str)
        if df is None or df.empty:
            df = pd.DataFrame(DEFAULT_COURSES, columns=["CourseCode", "CourseName"])
    df = df.fillna("")
    df["CourseCode"] = df["CourseCode"].str.strip().str.upper()
    df["CourseName"] = df["CourseName"].str.strip()
    df = df[df["CourseCode"] != ""]
    df = df.drop_duplicates(subset=["CourseCode"], keep="first")
    result = df[["CourseCode", "CourseName"]].reset_index(drop=True)
    _courses_cache["signature"] = _file_signature(COURSES_PATH)
    _courses_cache["data"] = result.copy(deep=True)
    return result.copy(deep=True)


def save_courses(df: pd.DataFrame) -> None:
    """Persist course catalog to CSV."""
    _ensure_data_dir()
    df = df[["CourseCode", "CourseName"]].copy()
    df.to_csv(COURSES_PATH, index=False)
    _invalidate_courses_cache()


def get_course_info() -> list[tuple[str, str]]:
    """Return course list as (code, name) tuples."""
    courses_df = load_courses()
    return list(courses_df.itertuples(index=False, name=None))


def get_course_codes() -> list[str]:
    """Return list of active course codes."""
    return [code for code, _ in get_course_info()]


def _department_code(department: str) -> str:
    cleaned = re.sub(r"[^A-Z]", "", str(department).upper())
    return cleaned[:4] or "GEN"


def _generate_register_number(position: int, department: str) -> str:
    return f"{_department_code(department)}{2026}{position + 1:03d}"


def _demo_first_names() -> list[str]:
    return [
        "Aarav", "Vivaan", "Aditya", "Arjun", "Krish", "Ishaan", "Reyansh", "Ayaan", "Rohan", "Siddharth",
        "Diya", "Ananya", "Aadhya", "Ira", "Meera", "Saanvi", "Kavya", "Priya", "Nithya", "Anika",
        "Harsh", "Naveen", "Karthik", "Varun", "Rahul", "Surya", "Pranav", "Ritvik", "Abhinav", "Dev",
    ]


def _demo_last_names() -> list[str]:
    return [
        "Kumar", "Sharma", "Iyer", "Nair", "Reddy", "Patel", "Singh", "Gupta", "Mishra", "Yadav",
        "Bhat", "Rao", "Menon", "Das", "Joshi", "Verma", "Chauhan", "Saxena", "Kulkarni", "Pillai",
        "Agarwal", "Jain", "Malhotra", "Srinivasan", "Narayanan", "Rajan", "Bhaskar", "Venkatesh", "Dubey", "Chawla",
    ]


def _generate_demo_student_name(position: int) -> str:
    first_names = _demo_first_names()
    last_names = _demo_last_names()
    first = first_names[position % len(first_names)]
    last = last_names[(position // len(first_names)) % len(last_names)]
    return f"{first} {last}"


def _legacy_demo_student_name(position: int) -> str:
    first_names = _demo_first_names()
    last_names = _demo_last_names()
    first = first_names[position % len(first_names)]
    last = last_names[(position * 3) % len(last_names)]
    return f"{first} {last}"


def _repair_legacy_demo_names(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "Name" not in df.columns:
        return df

    normalized_names = df["Name"].fillna("").astype(str).str.strip()
    matches = sum(name == _legacy_demo_student_name(position) for position, name in enumerate(normalized_names.tolist()))
    if matches < max(60, int(len(df.index) * 0.75)):
        return df

    repaired = df.copy()
    for position, idx in enumerate(repaired.index):
        current_name = str(repaired.at[idx, "Name"]).strip()
        if current_name == _legacy_demo_student_name(position):
            repaired.at[idx, "Name"] = _generate_demo_student_name(position)
    return repaired


def student_columns(course_codes: list[str]) -> list[str]:
    """Return dynamic student CSV columns with department."""
    return ["Name", "RegisterNumber", "Gender", "ProfileImage", "Department", "CurrentSemester"] + SEMESTER_TOTAL_COLS + SEMESTER_ATT_COLS + course_codes + ["Attendance"]


def generate_sample_students_df(course_codes: list[str]) -> pd.DataFrame:
    """Generate sample students with marks, attendance, and semester tracking."""
    rng = random.Random(42)

    records = []
    name_index = 0

    # 10 sample students per department for a predictable demo dataset.
    for dept in DEPARTMENTS:
        for _ in range(10):
            name = _generate_demo_student_name(name_index)
            name_index += 1

            row = {
                "Name": name,
                "RegisterNumber": _generate_register_number(len(records), dept),
                "Gender": "Male" if name_index % 2 else "Female",
                "ProfileImage": "",
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
    cache_signature = (_file_signature(STUDENTS_PATH), _file_signature(COURSES_PATH))
    if _students_cache["signature"] == cache_signature and _students_cache["data"] is not None:
        return _students_cache["data"].copy(deep=True)

    _ensure_data_dir()
    course_codes = get_course_codes()
    required_cols = student_columns(course_codes)

    df = _safe_read_csv(STUDENTS_PATH)
    if df is None or df.empty:
        df = generate_sample_students_df(course_codes)
        df.to_csv(STUDENTS_PATH, index=False)
        _students_cache["signature"] = (_file_signature(STUDENTS_PATH), _file_signature(COURSES_PATH))
        _students_cache["data"] = df.copy(deep=True)
        return df.copy(deep=True)

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
    df["Name"] = df["Name"].astype(str).str.strip()
    df["Department"] = df["Department"].apply(_normalize_department)
    if "Gender" in df.columns:
        df["Gender"] = df["Gender"].fillna("Male").astype(str).str.strip().replace("", "Male")
    if "ProfileImage" in df.columns:
        df["ProfileImage"] = df["ProfileImage"].fillna("").astype(str).str.strip()
    if "RegisterNumber" in df.columns:
        df["RegisterNumber"] = df["RegisterNumber"].fillna("").astype(str).str.strip().str.upper()

    df = _repair_legacy_demo_names(df)

    seen_register_numbers: set[str] = set()
    for position, idx in enumerate(df.index):
        current = str(df.at[idx, "RegisterNumber"]).strip().upper() if "RegisterNumber" in df.columns else ""
        if not current or current in seen_register_numbers:
            current = _generate_register_number(position, str(df.at[idx, "Department"]))
            while current in seen_register_numbers:
                position += 1
                current = _generate_register_number(position, str(df.at[idx, "Department"]))
        df.at[idx, "RegisterNumber"] = current
        seen_register_numbers.add(current)

    df.to_csv(STUDENTS_PATH, index=False)
    _students_cache["signature"] = (_file_signature(STUDENTS_PATH), _file_signature(COURSES_PATH))
    _students_cache["data"] = df.copy(deep=True)
    return df.copy(deep=True)


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
    _invalidate_students_cache()


def _ensure_activity_log_file() -> None:
    """Create activity log file if it does not exist."""
    if not os.path.exists(ACTIVITY_LOG_PATH):
        with open(ACTIVITY_LOG_PATH, "w", encoding="utf-8"):
            pass


def _format_activity_action(action: str) -> str:
    normalized = str(action or "").strip().title()
    return (
        normalized.replace("Ai", "AI")
        .replace("Pdf", "PDF")
        .replace("Csv", "CSV")
        .replace("Api", "API")
    )


def log_activity(action: str, username: str | None = None, details: str | None = None) -> None:
    """
    Append timestamped activity event.
    Supports both simple and detailed logging.
    """
    _ensure_activity_log_file()
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    action_label = _format_activity_action(action)
    detail_text = str(details or "").strip()
    user_text = str(username or "").strip()

    line = f"{timestamp} - {action_label}"
    if detail_text:
        line += f": {detail_text}"
    if user_text:
        line += f" | User: {user_text}"
    line += "\n"

    with open(ACTIVITY_LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(line)
    _invalidate_activity_logs_cache()


def read_activity_logs() -> list[dict[str, str]]:
    """Read activity log file into structured rows."""
    signature = _file_signature(ACTIVITY_LOG_PATH)
    if _activity_logs_cache["signature"] == signature and _activity_logs_cache["data"] is not None:
        return list(_activity_logs_cache["data"])

    _ensure_activity_log_file()

    rows: list[dict[str, str]] = []
    with open(ACTIVITY_LOG_PATH, "r", encoding="utf-8") as log_file:
        for line in log_file:
            entry = line.rstrip("\n").strip()
            if not entry:
                continue

            modern_match = re.match(
                r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2})(?:\:\d{2})?\s+-\s+(?P<action>[^:|]+?)(?:\:\s*(?P<details>.*?))?(?:\s+\|\s+User:\s*(?P<username>.+))?$",
                entry,
            )
            if modern_match:
                rows.append(
                    {
                        "timestamp": modern_match.group("timestamp"),
                        "username": (modern_match.group("username") or "System").strip(),
                        "action": (modern_match.group("action") or "").strip(),
                        "details": (modern_match.group("details") or "").strip(),
                    }
                )
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
    result = list(reversed(rows))
    _activity_logs_cache["signature"] = _file_signature(ACTIVITY_LOG_PATH)
    _activity_logs_cache["data"] = list(result)
    return result


def _student_analytics_df() -> pd.DataFrame:
    """Compute cross-page analytics for risk, API, trend, improvement, and department rank."""
    signature = (_file_signature(STUDENTS_PATH), _file_signature(COURSES_PATH))
    if _analytics_cache["signature"] == signature and _analytics_cache["data"] is not None:
        return _analytics_cache["data"].copy(deep=True)

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
    _analytics_cache["signature"] = signature
    _analytics_cache["data"] = df.copy(deep=True)
    return df.copy(deep=True)


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


def get_processed_students_df() -> pd.DataFrame:
    """Return cached classroom dashboard dataframe with totals, grades, and predictions."""
    signature = (_file_signature(STUDENTS_PATH), _file_signature(COURSES_PATH))
    if _processed_students_cache["signature"] == signature and _processed_students_cache["data"] is not None:
        return _processed_students_cache["data"].copy(deep=True)

    course_codes = get_course_codes()
    students_df = load_students()
    processed_df = add_prediction(prepare_data(students_df, course_codes))
    _processed_students_cache["signature"] = signature
    _processed_students_cache["data"] = processed_df.copy(deep=True)
    return processed_df.copy(deep=True)


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
