# Digital Assistant for Classroom Management

A Flask-based classroom management system for faculty teams to monitor student performance, manage academic records, generate reports, and review AI-assisted student risk insights.

## Project Overview

This project helps faculty manage classroom operations from one dashboard without changing the existing visual theme. It combines student management, course management, department analytics, PDF export, AI risk analysis, and activity tracking in a single web application.

## Features

- Faculty login with protected dashboard routes
- Student management with add, edit, delete, bulk delete, and CSV export
- Student profile dashboard with semester-wise marks, attendance, charts, and AI insights
- Department-level academic view with PDF report export
- Course management for active subjects
- AI analysis API with timeout protection and error-safe responses
- Loading spinner for profile opening, AI analysis, filtering, and export actions
- Activity logging for student operations, exports, logins, and AI analysis
- Graceful validation for invalid inputs and file upload issues

## Phase 3 Improvements

- Refined shared buttons, inputs, and forms for consistent spacing and hover behavior
- Added visual action icons without changing the design theme
- Added frontend loading states for long-running operations
- Added safer route-level exception handling for student and export workflows
- Added API timeout handling for AI analysis requests
- Improved logging coverage for key classroom management actions

## Tech Stack

- Backend: Python, Flask
- Frontend: HTML, Jinja2, CSS, JavaScript
- Data Storage: CSV files, SQLite
- Charts/Reports: Matplotlib-generated charts, ReportLab PDF export
- Data Processing: Pandas, scikit-learn

## Project Structure

```text
classroom_assistant/
├── app.py
├── requirements.txt
├── README.md
├── classroom_app/
│   ├── __init__.py
│   ├── config.py
│   ├── legacy.py
│   ├── blueprints/
│   │   ├── api.py
│   │   ├── auth.py
│   │   └── pages.py
│   └── services/
│       ├── ai_logs.py
│       ├── charts.py
│       ├── data.py
│       └── student_management.py
├── database/
│   ├── app.db
│   ├── courses.csv
│   ├── db.py
│   ├── semesters.csv
│   └── students.csv
├── static/
│   ├── css/
│   ├── images/
│   └── js/
├── templates/
└── utils/
```

## Installation

1. Clone or download the project.
2. Open a terminal in the project root.
3. Create and activate a virtual environment.
4. Install dependencies.

```bash
pip install -r requirements.txt
```

## How to Run Locally

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Default Login

Use one of the configured faculty accounts, or the default admin credentials if enabled in the app:

```text
Username: admin
Password: admin
```

## Key Workflows

### Student Management

- Open `Student Management`
- Filter by name, department, or sort order
- Add a new student or update an existing record
- Export the filtered list as CSV

### AI Analysis

- Open a student profile
- Click `Run AI Analysis`
- Review updated risk level and performance score
- Check stored entries in `AI Logs`

### Reports

- Export individual student PDF reports from the student profile page
- Export department PDF reports from the department page

## Screenshots

Add screenshots to this section before final submission.

- Login page
- Dashboard page
- Student management page
- Student profile page
- AI logs page

Example markdown:

```md
![Dashboard](docs/screenshots/dashboard.png)
```

## Deployment Link

Add your live deployment URL here before evaluation.

```text
https://your-deployment-link-here
```

## Logs and Generated Files

- Activity log file: `activity_log.txt`
- AI analysis log table: `database/app.db`
- Generated charts: `static/charts/`
- Uploaded student images: `static/images/students/`

## Validation Notes

The application now includes:

- Invalid input handling for student forms and AI requests
- File upload validation for profile images
- Timeout-safe AI API responses
- Loading feedback for long-running user actions
- Expanded activity logging for audit visibility

## Future Enhancements

- Role-based access for faculty and admin users
- Email notifications for at-risk students
- Searchable academic history reports by semester
- Deployment with environment-based configuration

