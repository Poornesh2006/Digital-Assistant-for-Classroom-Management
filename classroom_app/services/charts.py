from utils.graph_generator import generate_student_charts


def _create_profile_charts(student_name: str, semester_totals: list[int], semester_attendance: list[int]) -> dict[str, str]:
    """Generate student profile charts and return static-relative file paths."""
    return generate_student_charts(student_name, semester_totals, semester_attendance)
