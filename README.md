# Digital Assistant for Classroom Management

## Project Description

Digital Assistant for Classroom Management is a faculty-focused academic monitoring system built with Flask. It centralizes student records, attendance, semester-wise performance, department analytics, leaderboard views, AI-assisted risk analysis, activity tracking, and report export workflows in one web application.

The current version is designed for day-to-day classroom administration. Faculty can log in securely, review overall dashboard metrics, manage student records, inspect detailed student profiles with generated charts, identify weak students quickly, and export academic information for reporting.

## Features

- Secure session-based login system for faculty users
- Interactive dashboard with total students, weak students, attendance, and risk alert metrics
- Department-wise navigation cards with quick access to grouped student views
- Student management module with add, edit, delete, bulk delete, filter, sort, and CSV export
- Student profile dashboard with semester performance table, attendance summary, performance index, department rank, and trend indicators
- Weak student identification from attendance and semester performance thresholds
- AI-based student analysis with live API requests from the profile page
- AI analysis log viewer with filtering and JSON API access
- Leaderboard page with overall topper highlight and department filter
- Activity log page for audit-style tracking of faculty actions
- Course management for add, search, edit, and delete operations
- Feedback form with validation and JSON storage
- PDF export for student reports and department reports
- Generated charts for performance trend, attendance trend, and semester contribution
- Dark mode with saved theme preference in local storage
- Responsive layout, mobile-friendly tables, and loading states for long-running actions
- Friendly error handling for invalid input, missing data, and failed AI/API operations

## Technology Stack

### Frontend

- HTML
- CSS
- JavaScript
- Jinja2 templates

### Backend

- Python
- Flask
- Flask-Compress

### Data Processing

- Pandas
- NumPy
- scikit-learn

### Visualization

- Matplotlib

### Reporting and Storage

- ReportLab
- SQLite
- CSV
- JSON

### Deployment

- Render Cloud Platform
- Gunicorn

## Project Structure

```text
classroom_assistant/
|-- app.py
|-- requirements.txt
|-- README.md
|-- activity_log.txt
|-- classroom_app/
|   |-- __init__.py
|   |-- config.py
|   |-- legacy.py
|   |-- blueprints/
|   |   |-- api.py
|   |   |-- auth.py
|   |   `-- pages.py
|   `-- services/
|       |-- ai_logs.py
|       |-- data.py
|       `-- student_management.py
|-- data/
|   `-- feedback.json
|-- database/
|   |-- app.db
|   |-- courses.csv
|   |-- db.py
|   `-- students.csv
|-- static/
|   |-- charts/
|   |-- css/
|   |-- images/
|   `-- js/
|-- templates/
`-- utils/
```

### Folder Notes

- `app.py` starts the Flask application and configures faculty login users.
- `classroom_app/blueprints/` contains page, auth, and API route logic.
- `classroom_app/services/` contains data preparation, AI log handling, and student management services.
- `database/` stores student records, course data, and SQLite AI logs.
- `data/feedback.json` stores submitted user feedback.
- `static/` contains CSS, JavaScript, images, and generated chart assets.
- `templates/` contains all rendered HTML pages.

## Installation

### Local Setup

```bash
git clone <your-repository-url>
cd classroom_assistant
pip install -r requirements.txt
python app.py
```

Open the app in your browser:

```text
http://127.0.0.1:10000
```

## Deployment Instructions

This project is ready for deployment on Render.

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
gunicorn app:app
```

### Recommended Environment Variable

```text
SECRET_KEY=your-secure-random-secret
```

Note: the application uses SQLite, CSV, JSON, and generated local files. On cloud platforms with ephemeral storage, persistent data should be planned separately for production usage.

## Future Enhancements

- Mobile app version for faculty access on the go
- Advanced AI prediction models using richer academic history
- Parent and student access portal with role-based permissions
- Cloud database integration for stronger deployment persistence
- Notification workflows for at-risk students
- Expanded analytics dashboards and downloadable summary reports

## Author

Poornesh S
Artificial Intelligence and Data Science
Bannari Amman Institute of Technology
