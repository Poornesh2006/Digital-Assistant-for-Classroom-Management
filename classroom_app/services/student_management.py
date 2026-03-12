import io
import os
from copy import deepcopy
from uuid import uuid4

import pandas as pd
from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from classroom_app.config import DEPARTMENTS
from classroom_app.services.data import _student_analytics_df, get_course_info, load_students, log_activity, save_students

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
_management_data_cache: dict[tuple[str, str, str], dict[str, object]] = {}


def _invalidate_management_cache() -> None:
    _management_data_cache.clear()


def _default_image_for_gender(gender: str) -> str:
    return "images/default_female.png" if str(gender).strip().lower() == "female" else "images/default_male.png"


def _profile_image_url(profile_image: str, gender: str) -> str:
    filename = str(profile_image).strip()
    if filename:
        return f"images/students/{filename}"
    return _default_image_for_gender(gender)


def _normalize_gender(value: str | None) -> str:
    return "Female" if str(value or "").strip().lower() == "female" else "Male"


def _coerce_int(value: str | None, field_name: str, minimum: int, maximum: int) -> int:
    try:
        parsed = int(float(str(value or "").strip()))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid number.") from exc

    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field_name} must be between {minimum} and {maximum}.")
    return parsed


def _subject_label(course_name: str, course_code: str) -> str:
    return f"{str(course_name).strip().title()} ({course_code})"


def _coerce_subject_marks(form: dict) -> dict[str, int]:
    subject_marks: dict[str, int] = {}
    for course_code, course_name in get_course_info():
        raw_value = str(form.get(course_code, "")).strip()
        if raw_value == "":
            raise ValueError(f"{_subject_label(course_name, course_code)} is required.")
        subject_marks[course_code] = _coerce_int(raw_value, _subject_label(course_name, course_code), 0, 100)
    return subject_marks


def _save_profile_image(image: FileStorage | None, register_number: str) -> str:
    if image is None or not image.filename:
        return ""

    filename = secure_filename(image.filename)
    if "." not in filename:
        raise ValueError("Profile image must have a valid file extension.")

    extension = filename.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Profile image must be PNG, JPG, JPEG, GIF, or WEBP.")

    upload_dir = os.path.join(current_app.static_folder, "images", "students")
    try:
        os.makedirs(upload_dir, exist_ok=True)
    except OSError as exc:
        raise ValueError("Unable to prepare the profile image folder.") from exc

    stored_name = f"{secure_filename(register_number.lower())}_{uuid4().hex[:8]}.{extension}"
    try:
        image.save(os.path.join(upload_dir, stored_name))
    except OSError as exc:
        raise ValueError("Unable to save the selected profile image.") from exc
    return stored_name


def _build_history_series(final_value: int, minimum: int, maximum: int, step: int) -> list[int]:
    history: list[int] = []
    for index in range(5):
        distance = 5 - index
        value = max(minimum, min(maximum, final_value - (distance * step)))
        history.append(int(value))
    history.append(int(final_value))
    return history


def _decorate_students(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy().reset_index(drop=True)
    if working.empty:
        return working

    working["StudentId"] = working.index + 1
    working["Gender"] = working["Gender"].fillna("Male").astype(str).apply(_normalize_gender)
    working["ProfileImage"] = working["ProfileImage"].fillna("").astype(str).str.strip()
    working["RegisterNumber"] = working["RegisterNumber"].fillna("").astype(str).str.strip().str.upper()
    working["ImagePath"] = working.apply(lambda row: _profile_image_url(row.get("ProfileImage", ""), row.get("Gender", "Male")), axis=1)
    working["Marks"] = pd.to_numeric(working["Sem6_Total"], errors="coerce").fillna(0).astype(int)
    working["AttendanceDisplay"] = pd.to_numeric(working["Sem6_Attendance"], errors="coerce").fillna(
        pd.to_numeric(working["Attendance"], errors="coerce").fillna(0)
    ).astype(int)
    return working


def _student_record_from_row(row: pd.Series | dict[str, object], course_info: list[tuple[str, str]] | None = None) -> dict[str, object]:
    data = row.to_dict() if isinstance(row, pd.Series) else dict(row)
    active_courses = course_info if course_info is not None else get_course_info()
    register_number = str(data.get("RegisterNumber", "")).strip().upper()
    course_marks = {
        course_code: int(pd.to_numeric(pd.Series([data.get(course_code, 0)]), errors="coerce").fillna(0).iloc[0])
        for course_code, _ in active_courses
    }
    attendance_value = int(pd.to_numeric(pd.Series([data.get("AttendanceDisplay", data.get("Attendance", 0))]), errors="coerce").fillna(0).iloc[0])
    semester_value = int(pd.to_numeric(pd.Series([data.get("CurrentSemester", 0)]), errors="coerce").fillna(0).iloc[0])
    total_marks = int(pd.to_numeric(pd.Series([data.get("Marks", data.get("Sem6_Total", 0))]), errors="coerce").fillna(0).iloc[0])

    return {
        "student_id": int(pd.to_numeric(pd.Series([data.get("StudentId", 0)]), errors="coerce").fillna(0).iloc[0]),
        "name": str(data.get("Name", "")).strip(),
        "register_number": register_number,
        "department": str(data.get("Department", "")).strip(),
        "semester": semester_value,
        "attendance": attendance_value,
        "marks": course_marks,
        "total_marks": total_marks,
        "profile_image": str(data.get("ProfileImage", "")).strip(),
        "image_path": str(data.get("ImagePath", _default_image_for_gender(str(data.get("Gender", "Male"))))).strip(),
        "gender": _normalize_gender(str(data.get("Gender", "Male"))),
        "at_risk": bool(data.get("AtRisk", False)),
        "performance_index": float(pd.to_numeric(pd.Series([data.get("PerformanceIndex", 0)]), errors="coerce").fillna(0).iloc[0]),
        # Legacy aliases for templates/routes still reading title-case keys.
        "StudentId": int(pd.to_numeric(pd.Series([data.get("StudentId", 0)]), errors="coerce").fillna(0).iloc[0]),
        "Name": str(data.get("Name", "")).strip(),
        "RegisterNumber": register_number,
        "Department": str(data.get("Department", "")).strip(),
        "CurrentSemester": semester_value,
        "AttendanceDisplay": attendance_value,
        "Attendance": attendance_value,
        "Marks": total_marks,
        "ProfileImage": str(data.get("ProfileImage", "")).strip(),
        "ImagePath": str(data.get("ImagePath", _default_image_for_gender(str(data.get("Gender", "Male"))))).strip(),
        "Gender": _normalize_gender(str(data.get("Gender", "Male"))),
        "AtRisk": bool(data.get("AtRisk", False)),
        "PerformanceIndex": float(pd.to_numeric(pd.Series([data.get("PerformanceIndex", 0)]), errors="coerce").fillna(0).iloc[0]),
    }


def find_student_by_register_number(register_number: str) -> dict[str, object]:
    students_df = _decorate_students(_student_analytics_df())
    target = str(register_number).strip().upper()
    selected = students_df[students_df["RegisterNumber"].astype(str).str.strip().str.upper() == target]
    if selected.empty:
        raise ValueError("Student not found.")
    return _student_record_from_row(selected.iloc[0], course_info=get_course_info())


def get_student_management_data(search: str = "", department: str = "All", sort: str = "name_asc") -> dict[str, object]:
    cache_key = (str(search).strip(), str(department).strip() or "All", str(sort).strip() or "name_asc")
    cached = _management_data_cache.get(cache_key)
    if cached is not None:
        return deepcopy(cached)

    students_df = _decorate_students(_student_analytics_df())
    filtered_df = students_df.copy()

    search_value = str(search).strip()
    selected_department = str(department).strip() or "All"

    if search_value and not filtered_df.empty:
        filtered_df = filtered_df[
            filtered_df["Name"].astype(str).str.contains(search_value, case=False, na=False)
            | filtered_df["RegisterNumber"].astype(str).str.contains(search_value, case=False, na=False)
        ]

    if selected_department != "All" and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df["Department"].astype(str) == selected_department]

    sort_map: dict[str, tuple[list[str], list[bool]]] = {
        "name_asc": (["Name"], [True]),
        "marks_desc": (["Marks", "Name"], [False, True]),
        "attendance_desc": (["AttendanceDisplay", "Name"], [False, True]),
        "weak_first": (["AtRisk", "Marks", "Name"], [False, True, True]),
    }
    sort_fields, ascending = sort_map.get(sort, sort_map["name_asc"])
    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values(sort_fields, ascending=ascending, kind="mergesort").reset_index(drop=True)

    summary = {
        "total_students": int(len(filtered_df.index)),
        "weak_students": int(filtered_df["AtRisk"].sum()) if not filtered_df.empty else 0,
        "top_students": int((filtered_df["Marks"] >= 400).sum()) if not filtered_df.empty else 0,
        "department_count": int(filtered_df["Department"].nunique()) if not filtered_df.empty else 0,
    }

    departments = ["All"] + sorted(students_df["Department"].dropna().astype(str).unique().tolist()) if not students_df.empty else ["All"] + DEPARTMENTS
    course_info = get_course_info()
    students = [_student_record_from_row(row, course_info=course_info) for _, row in filtered_df.iterrows()]

    result = {
        "students": students,
        "summary": summary,
        "departments": departments,
        "search": search_value,
        "selected_department": selected_department,
        "sort": sort,
    }
    _management_data_cache[cache_key] = deepcopy(result)
    return result


def get_student_by_id(student_id: int) -> dict[str, object]:
    students_df = _decorate_students(_student_analytics_df())
    selected = students_df[students_df["StudentId"] == student_id]
    if selected.empty:
        raise ValueError("Student not found.")
    return _student_record_from_row(selected.iloc[0], course_info=get_course_info())


def _validate_student_payload(form: dict, current_student_id: int | None = None) -> dict[str, object]:
    name = str(form.get("name", "")).strip()
    register_number = str(form.get("register_number", "")).strip().upper()
    department = str(form.get("department", "")).strip()
    gender = _normalize_gender(form.get("gender"))

    if not name:
        raise ValueError("Student name is required.")
    if not register_number:
        raise ValueError("Register number is required.")
    if department not in DEPARTMENTS:
        raise ValueError("Please select a valid department.")

    semester = _coerce_int(form.get("semester"), "Semester", 1, 8)
    attendance = _coerce_int(form.get("attendance"), "Attendance", 0, 100)
    subject_marks = _coerce_subject_marks(form)
    total_marks = sum(subject_marks.values())

    students_df = _decorate_students(load_students())
    duplicate = students_df[students_df["RegisterNumber"].astype(str).str.upper() == register_number]
    if current_student_id is not None:
        duplicate = duplicate[duplicate["StudentId"] != current_student_id]
    if not duplicate.empty:
        raise ValueError("Register number already exists.")

    return {
        "name": name,
        "register_number": register_number,
        "department": department,
        "semester": semester,
        "attendance": attendance,
        "marks": subject_marks,
        "total_marks": total_marks,
        "gender": gender,
    }


def _apply_student_changes(row: dict[str, object], payload: dict[str, object], profile_image: str | None = None) -> dict[str, object]:
    row["Name"] = payload["name"]
    row["RegisterNumber"] = payload["register_number"]
    row["Department"] = payload["department"]
    row["CurrentSemester"] = payload["semester"]
    row["Attendance"] = payload["attendance"]
    row["Sem6_Total"] = payload["total_marks"]
    row["Sem6_Attendance"] = payload["attendance"]
    row["Gender"] = payload["gender"]
    for course_code, mark in payload["marks"].items():
        row[course_code] = mark
    if profile_image is not None:
        row["ProfileImage"] = profile_image
    return row


def add_student(form: dict, image: FileStorage | None, username: str = "Faculty") -> None:
    payload = _validate_student_payload(form)
    profile_image = _save_profile_image(image, payload["register_number"])
    students_df = load_students().copy()
    course_codes = [course_code for course_code, _ in get_course_info()]

    final_marks = int(payload["total_marks"])
    final_attendance = int(payload["attendance"])
    semester_totals = _build_history_series(final_marks, 280, 500, 12)
    semester_attendance = _build_history_series(final_attendance, 60, 98, 3)

    new_row = {
        "Name": payload["name"],
        "RegisterNumber": payload["register_number"],
        "Gender": payload["gender"],
        "ProfileImage": profile_image,
        "Department": payload["department"],
        "CurrentSemester": payload["semester"],
        "Attendance": final_attendance,
    }

    for index in range(6):
        new_row[f"Sem{index + 1}_Total"] = semester_totals[index]
        new_row[f"Sem{index + 1}_Attendance"] = semester_attendance[index]

    for code in course_codes:
        new_row[code] = int(payload["marks"].get(code, 0))

    students_df = pd.concat([students_df, pd.DataFrame([new_row])], ignore_index=True)
    save_students(students_df)
    _invalidate_management_cache()
    log_activity("Student added", username=username, details=f"{payload['name']} ({payload['register_number']})")


def edit_student(student_id: int, form: dict, image: FileStorage | None, username: str = "Faculty") -> None:
    payload = _validate_student_payload(form, current_student_id=student_id)
    students_df = load_students().copy().reset_index(drop=True)
    if student_id < 1 or student_id > len(students_df.index):
        raise ValueError("Student not found.")

    row = students_df.iloc[student_id - 1].to_dict()
    profile_image = row.get("ProfileImage", "")
    if image is not None and image.filename:
        profile_image = _save_profile_image(image, payload["register_number"])

    updated = _apply_student_changes(row, payload, profile_image)
    for column, value in updated.items():
        students_df.at[student_id - 1, column] = value

    save_students(students_df)
    _invalidate_management_cache()
    log_activity("Student updated", username=username, details=f"{payload['name']} ({payload['register_number']})")


def delete_student(student_id: int, username: str = "Faculty") -> None:
    students_df = load_students().copy().reset_index(drop=True)
    if student_id < 1 or student_id > len(students_df.index):
        raise ValueError("Student not found.")

    student_name = str(students_df.iloc[student_id - 1].get("Name", "Student"))
    register_number = str(students_df.iloc[student_id - 1].get("RegisterNumber", ""))
    students_df = students_df.drop(index=student_id - 1).reset_index(drop=True)
    save_students(students_df)
    _invalidate_management_cache()
    log_activity("Student deleted", username=username, details=f"{student_name} ({register_number})")


def bulk_delete_students(student_ids: list[int], username: str = "Faculty") -> int:
    cleaned_ids = sorted({student_id for student_id in student_ids if student_id > 0})
    if not cleaned_ids:
        return 0

    students_df = load_students().copy().reset_index(drop=True)
    valid_indexes = [student_id - 1 for student_id in cleaned_ids if student_id <= len(students_df.index)]
    if not valid_indexes:
        return 0

    deleted_rows = students_df.iloc[valid_indexes]
    students_df = students_df.drop(index=valid_indexes).reset_index(drop=True)
    save_students(students_df)
    _invalidate_management_cache()
    log_activity(
        "Bulk student delete",
        username=username,
        details=", ".join(deleted_rows["RegisterNumber"].astype(str).tolist()),
    )
    return len(valid_indexes)


def export_students_csv(search: str = "", department: str = "All", sort: str = "name_asc") -> tuple[str, str]:
    context = get_student_management_data(search=search, department=department, sort=sort)
    export_df = pd.DataFrame(context["students"])
    columns = [
        "register_number",
        "name",
        "department",
        "semester",
        "attendance",
        "total_marks",
        "at_risk",
        "performance_index",
    ]
    if export_df.empty:
        export_df = pd.DataFrame(columns=columns)
    else:
        export_df = export_df[columns].rename(
            columns={
                "register_number": "RegisterNumber",
                "name": "Name",
                "department": "Department",
                "semester": "Semester",
                "attendance": "Attendance",
                "total_marks": "Marks",
                "at_risk": "WeakStudent",
                "performance_index": "PerformanceIndex",
            }
        )

    buffer = io.StringIO()
    export_df.to_csv(buffer, index=False)
    return buffer.getvalue(), "student_management_export.csv"
