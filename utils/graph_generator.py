import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_FOLDER = os.path.join("static", "charts")


def _safe_slug(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in str(value).strip())
    return "_".join(part for part in cleaned.split("_") if part) or "student"


def generate_student_charts(student_name: str, semester_totals: list[int], semester_attendance: list[int]) -> dict[str, str]:
    """Generate chart assets in a stable static/charts directory."""
    charts_dir = os.path.join(BASE_DIR, CHARTS_FOLDER)
    os.makedirs(charts_dir, exist_ok=True)

    slug = _safe_slug(student_name)
    sem_labels = [f"Sem{i}" for i in range(1, 7)]

    perf_file = f"{slug}_performance_trend.png"
    perf_path = os.path.join(charts_dir, perf_file)
    perf_default_path = os.path.join(charts_dir, "performance_trend.png")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(sem_labels, semester_totals, marker="o", linewidth=2.4, color="#4f46e5")
    ax.set_title("Performance Trend")
    ax.set_xlabel("Semester")
    ax.set_ylabel("Total Marks (out of 500)")
    ax.set_ylim(250, 520)
    ax.grid(alpha=0.25, linestyle="--")
    plt.tight_layout()
    fig.savefig(perf_path, dpi=120, bbox_inches="tight")
    fig.savefig(perf_default_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    att_file = f"{slug}_attendance_trend.png"
    att_path = os.path.join(charts_dir, att_file)
    att_default_path = os.path.join(charts_dir, "attendance_trend.png")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(sem_labels, semester_attendance, marker="o", linewidth=2.4, color="#10b981")
    ax.set_title("Attendance Analysis")
    ax.set_xlabel("Semester")
    ax.set_ylabel("Attendance (%)")
    ax.set_ylim(55, 100)
    ax.grid(alpha=0.25, linestyle="--")
    plt.tight_layout()
    fig.savefig(att_path, dpi=120, bbox_inches="tight")
    fig.savefig(att_default_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    pie_file = f"{slug}_semester_pie.png"
    pie_path = os.path.join(charts_dir, pie_file)
    pie_default_path = os.path.join(charts_dir, "semester_pie.png")
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        semester_totals,
        labels=sem_labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=["#4f46e5", "#7c3aed", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"],
        textprops={"fontsize": 10},
    )
    ax.set_title("Semester Contribution")
    ax.axis("equal")
    plt.tight_layout()
    fig.savefig(pie_path, dpi=120, bbox_inches="tight")
    fig.savefig(pie_default_path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    return {
        "performance_chart": "charts/performance_trend.png",
        "attendance_chart": "charts/attendance_trend.png",
        "contribution_chart": "charts/semester_pie.png",
    }


def chart_file_map(student_name: str) -> dict[str, Path]:
    charts_dir = Path(BASE_DIR) / CHARTS_FOLDER
    slug = _safe_slug(student_name)
    return {
        "performance": charts_dir / f"{slug}_performance_trend.png",
        "attendance": charts_dir / f"{slug}_attendance_trend.png",
        "contribution": charts_dir / f"{slug}_semester_pie.png",
    }
