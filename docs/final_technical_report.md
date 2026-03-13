# Digital Assistant for Classroom Management

## Title Page
- Project Title: Digital Assistant for Classroom Management
- Developer Name: Poornesh S
- Institution: Bannari Amman Institute of Technology, Sathyamangalam
- Department: Artificial Intelligence and Data Science
- Academic Year: 2025 - 2026

## Abstract
Digital Assistant for Classroom Management is a web-based academic monitoring system developed for faculty members. The application consolidates student records, attendance, semester performance, AI-assisted risk analysis, leaderboard ranking, department analytics, activity logging, and export workflows into one responsive platform. The final version focuses on day-to-day usability, clear data presentation, and safer handling of invalid input and service failures.

## Introduction
Traditional classroom monitoring often depends on spreadsheets, disconnected records, and manual review of attendance and marks. This slows down academic decision-making and makes it difficult for faculty to identify weak students early. The current system addresses that problem through a centralized web interface where student performance, department trends, and risk signals can be reviewed in a consistent and structured way.

## Objectives
- Build a secure faculty-facing classroom management web application.
- Maintain student records with validation and structured academic data entry.
- Provide dashboard-level analytics for faster academic monitoring.
- Highlight weak students using attendance and performance indicators.
- Offer detailed student profile pages with semester-wise charts and AI insights.
- Support leaderboard and department-level review workflows.
- Maintain activity logs for important classroom operations.
- Enable report export for student and department analysis.

## System Architecture
The overall application flow follows this structure:

- User
- Web Interface
- Flask Backend
- Data Storage Layer
- Analysis and Reporting Layer
- Dashboard and Profile Views

In practical terms, the system works as:

- User requests are sent through HTML, CSS, and JavaScript based pages.
- Flask blueprints process login, page rendering, and API calls.
- Student and course data are read from CSV files.
- AI log history is stored in SQLite.
- Feedback data is stored in JSON format.
- Service modules prepare analytics, weak student indicators, rankings, and chart data.
- The processed results are rendered in dashboard, student profile, leaderboard, and activity log pages.

## Technology Stack
- Frontend: HTML, CSS, JavaScript, Jinja2
- Backend: Python, Flask, Flask-Compress
- Data Processing: Pandas, NumPy, scikit-learn
- Visualization: Matplotlib
- Reporting: ReportLab
- Storage: CSV, JSON, SQLite
- Deployment Target: Render using Gunicorn

## Implementation Details

### Login System
The application uses a faculty login flow with session-based authentication. Protected pages redirect unauthenticated users to the login page. Logout is confirmed on the client side and the session is cleared safely.

### Dashboard Analytics
The dashboard presents high-level academic visibility with:

- total student count
- weak student count
- average attendance
- risk alerts
- department cards showing total and weak student counts
- a performance table with grades and predictions

The dashboard also includes animated counters, loading states, and responsive layout behavior.

### Student Management
The student management module supports:

- add student
- edit student
- delete student
- bulk delete
- search by name or register number
- department filtering
- sort by marks, attendance, and weak-student priority
- CSV export
- profile image upload

The student form uses validation for semester, attendance, unique register number, and subject marks.

### Student Profile Analysis
Each student profile provides:

- personal and department details
- current semester
- performance index
- department rank
- improvement summary
- semester-wise marks table
- attendance analysis
- performance trend chart
- semester contribution chart
- AI insight area with live analysis button
- student PDF export

Charts are generated dynamically using Matplotlib and stored inside the static charts directory.

### Leaderboard
The leaderboard module ranks students by current semester performance. It includes:

- overall topper card
- department filtering
- top five and lowest five views
- direct links from leaderboard rows to student profiles

### Weak Student Detection
Weak student identification is based on low semester totals, attendance thresholds, and risk conditions derived from processed academic data. These indicators are visible on the dashboard, department views, and student profiles.

### Activity Logs
The activity log page records key faculty actions such as:

- login and logout
- student add, edit, delete, and bulk delete
- feedback submission
- AI analysis activity
- CSV export
- PDF export

This provides an audit-friendly history of important classroom workflows.

### AI Analysis and AI Logs
The student profile page can trigger AI analysis through the API layer. The AI service returns:

- risk level
- performance score
- average marks
- attendance

The AI logs page displays stored AI responses from SQLite and supports filtering by student name, row limit selection, and JSON API access. API processing includes timeout protection and safe JSON error responses.

### Course and Feedback Management
The final implementation also includes:

- course add, search, edit, and delete workflows
- feedback form with name, email, message, and rating validation
- JSON-based feedback storage

### UI Improvements
The final website includes several user interface refinements:

- dark mode with saved preference in local storage
- responsive navigation and layout behavior for smaller screens
- loading overlays for long-running actions
- fade-in and reveal animations
- auto-dismiss alerts
- confirmation prompts for deletion and logout actions

## Database Structure
The application uses a mixed local storage model:

- `database/students.csv` stores student academic records, attendance, semester totals, register numbers, departments, and course marks.
- `database/courses.csv` stores active course codes and names.
- `database/app.db` stores AI analysis logs in the `ai_logs` SQLite table.
- `data/feedback.json` stores submitted feedback entries.
- `activity_log.txt` stores activity history in text form.

This structure works well for the current project scope and local demonstration environment.

## Screenshots
The PDF generator automatically embeds screenshots found in `docs/screenshots/`.

The current documentation includes screenshots for:

- Login page
- Dashboard
- Student Management
- Leaderboard
- AI Logs
- Feedback
- Courses

## Advantages of the System
- Centralized academic monitoring in one interface
- Faster identification of weak and at-risk students
- Better faculty visibility into attendance and performance trends
- Export-ready reports for student and department review
- Audit support through activity logging
- Improved usability through responsive layout, dark mode, and loading feedback

## Future Enhancements
- Mobile application support
- Parent and student access portal
- Managed cloud database integration
- Role-based access control for faculty and administrators
- Advanced predictive models with richer academic history
- Notification and alert workflows for at-risk students

## Conclusion
Digital Assistant for Classroom Management improves classroom administration by combining student record maintenance, academic analytics, AI-assisted insights, activity tracking, and export workflows in a single faculty-oriented web application. The final version is more polished, responsive, and deployment-ready, while still remaining simple enough for academic demonstration and future extension.
