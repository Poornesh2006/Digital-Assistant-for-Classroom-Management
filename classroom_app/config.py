import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "database")
FEEDBACK_DIR = os.path.join(BASE_DIR, "data")
FEEDBACK_PATH = os.path.join(FEEDBACK_DIR, "feedback.json")

DATABASE_PATH = "database/students.csv"
STUDENTS_PATH = os.path.join(BASE_DIR, DATABASE_PATH)
COURSES_PATH = os.path.join(DATA_DIR, "courses.csv")
SEMESTERS_PATH = os.path.join(DATA_DIR, "semesters.csv")

UPLOAD_FOLDER = "static/images/students"
CHARTS_FOLDER = "static/charts"
EXPORT_FOLDER = "exports/pdf"
ACTIVITY_LOG_PATH = os.path.join(BASE_DIR, "activity_log.txt")

SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")

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
