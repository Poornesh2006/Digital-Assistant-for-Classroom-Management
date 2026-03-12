import os
from hashlib import sha1
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_FOLDER = os.path.join("static", "charts")


def _safe_slug(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in str(value).strip())
    return "_".join(part for part in cleaned.split("_") if part) or "student"


def _chart_paths(slug: str) -> dict[str, Path]:
    charts_dir = Path(BASE_DIR) / CHARTS_FOLDER
    return {
        "performance": charts_dir / f"{slug}_performance_trend.png",
        "attendance": charts_dir / f"{slug}_attendance_trend.png",
        "contribution": charts_dir / f"{slug}_semester_pie.png",
        "meta": charts_dir / f"{slug}_charts.meta",
    }


def _chart_signature(semester_totals: list[int], semester_attendance: list[int]) -> str:
    payload = ",".join(map(str, semester_totals + semester_attendance))
    return sha1(payload.encode("utf-8")).hexdigest()


def generate_student_charts(student_name: str, semester_totals: list[int], semester_attendance: list[int]) -> dict[str, str]:
    """Generate chart assets in a stable static/charts directory."""
    charts_dir = os.path.join(BASE_DIR, CHARTS_FOLDER)
    os.makedirs(charts_dir, exist_ok=True)

    slug = _safe_slug(student_name)
    paths = _chart_paths(slug)
    signature = _chart_signature(semester_totals, semester_attendance)
    if (
        paths["meta"].exists()
        and all(paths[key].exists() for key in ("performance", "attendance", "contribution"))
        and paths["meta"].read_text(encoding="utf-8").strip() == signature
    ):
        return {
            "performance_chart": f"charts/{paths['performance'].name}",
            "attendance_chart": f"charts/{paths['attendance'].name}",
            "contribution_chart": f"charts/{paths['contribution'].name}",
        }

    sem_labels = [f"Sem{i}" for i in range(1, 7)]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(sem_labels, semester_totals, marker="o", linewidth=2.4, color="#4f46e5")
    ax.set_title("Performance Trend")
    ax.set_xlabel("Semester")
    ax.set_ylabel("Total Marks (out of 500)")
    ax.set_ylim(250, 520)
    ax.grid(alpha=0.25, linestyle="--")
    plt.tight_layout()
    fig.savefig(paths["performance"], dpi=120, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(sem_labels, semester_attendance, marker="o", linewidth=2.4, color="#10b981")
    ax.set_title("Attendance Analysis")
    ax.set_xlabel("Semester")
    ax.set_ylabel("Attendance (%)")
    ax.set_ylim(55, 100)
    ax.grid(alpha=0.25, linestyle="--")
    plt.tight_layout()
    fig.savefig(paths["attendance"], dpi=120, bbox_inches="tight")
    plt.close(fig)

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
    fig.savefig(paths["contribution"], dpi=120, bbox_inches="tight")
    plt.close(fig)
    paths["meta"].write_text(signature, encoding="utf-8")

    return {
        "performance_chart": f"charts/{paths['performance'].name}",
        "attendance_chart": f"charts/{paths['attendance'].name}",
        "contribution_chart": f"charts/{paths['contribution'].name}",
    }


def chart_file_map(student_name: str) -> dict[str, Path]:
    slug = _safe_slug(student_name)
    paths = _chart_paths(slug)
    return {
        "performance": paths["performance"],
        "attendance": paths["attendance"],
        "contribution": paths["contribution"],
    }
