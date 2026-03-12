# Final Technical Report

## Project Title
Digital Assistant for Classroom Management

## Submitted By
- Student Name: Poornesh S
- Roll Number: 7376232AD209
- Department: Artificial Intelligence and Data Science
- College: Bannari Amman Institute of Technology, Sathyamangalam
- Guide Name: Ms Saveetha R

## 1. Introduction
The Digital Assistant for Classroom Management is a Flask-based web application built to help faculty manage student academic data, monitor performance, review department-level trends, and use AI-assisted risk analysis from a single dashboard. The system was developed as a practical academic administration tool with emphasis on usability, responsiveness, and robust error handling.

## 2. Problem Statement
Faculty teams often manage student data across multiple spreadsheets and disconnected tools. That approach makes it difficult to track attendance, semester performance, risk levels, and department-level insights efficiently. The project addresses this issue by centralizing student management, analytics, reporting, and AI-supported interpretation in one web application.

## 3. Objectives
- Build a web-based classroom management assistant for faculty.
- Provide structured student profile and academic record management.
- Generate reports and charts for student and department review.
- Offer AI-assisted performance and risk analysis.
- Improve usability through professional UI refinement and clear feedback states.
- Handle invalid input and service failures gracefully without crashing.

## 4. Technology Stack
- Backend: Python, Flask
- Frontend: HTML, CSS, JavaScript, Jinja2 templates
- Data Storage: CSV files, SQLite, JSON
- Reporting: ReportLab PDF generation
- Charts: Matplotlib
- Data Processing / AI Logic: pandas, scikit-learn
- Deployment Target: Render

## 5. System Architecture
The application uses a modular Flask structure:

- `app.py` is the entry point and exposes the Flask application object.
- `classroom_app/__init__.py` creates the app, registers blueprints, initializes the database, and configures global error handling.
- `classroom_app/blueprints/auth.py` handles login, logout, and route protection.
- `classroom_app/blueprints/pages.py` handles user-facing pages such as dashboard, students, feedback, AI logs, and form workflows.
- `classroom_app/blueprints/api.py` exposes API endpoints for AI analysis and AI log retrieval.
- `classroom_app/services/` contains data, chart, logging, and student-management logic.
- `templates/` contains the UI pages.
- `static/` contains CSS, JavaScript, generated charts, and images.

## 6. Major Modules

### 6.1 Authentication Module
Faculty login is handled using session-based authentication. Protected pages require successful login before access is granted.

### 6.2 Student Management Module
The system supports adding, editing, deleting, filtering, sorting, and exporting student records. Validation is applied to reduce incorrect or incomplete submissions.

### 6.3 Student Profile and Analytics Module
Each student profile presents semester-wise academic details, attendance, generated charts, and AI-supported insights.

### 6.4 Department and Leaderboard Module
Department pages summarize student information at a higher level and support report export. A leaderboard view highlights comparative performance.

### 6.5 AI Analysis Module
The AI module processes student data and returns performance-oriented analysis. The API layer includes timeout protection and safe error responses to prevent crashes during long-running or failed requests.

### 6.6 Feedback and Activity Logging Module
The system stores feedback entries and records major user actions such as login, AI analysis, export operations, and student updates.

## 7. Data and File Storage
The project uses multiple storage formats:

- `database/students.csv` for student records
- `database/courses.csv` and `database/semesters.csv` for academic reference data
- `database/app.db` for SQLite-based AI log storage
- `data/feedback.json` for feedback entries
- `activity_log.txt` for activity history
- `static/charts/` for generated chart outputs
- `static/images/students/` for uploaded student images

## 8. UI and UX Refinement
Phase 3 focused on improving the presentation and usability of the application:

- Shared buttons, forms, and input styles were refined for consistent appearance.
- Layout spacing and component behavior were improved for a more professional UI.
- Loading states were added for long-running actions such as AI processing, filtering, export tasks, and profile loading.
- Clear success and error messages were added to improve usability.

## 9. Robustness and Stress Handling
The system was updated to fail safely instead of crashing:

- Invalid form input is validated before processing.
- File upload issues are handled with user-facing error messages.
- AI processing is wrapped with timeout protection.
- API failures return clear JSON error responses.
- Unhandled server errors are caught by a global Flask error handler and rendered through a user-friendly error page.

This directly supports the evaluation criterion requiring graceful handling of invalid input and API timeouts.

## 10. Deployment
The application is prepared for production deployment on Render.

Recommended Render configuration:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT app:app`
- Environment variable: `SECRET_KEY=<secure-random-value>`

Because the app uses SQLite and local files, the deployment must account for persistent storage limitations on cloud platforms with ephemeral filesystems.

## 11. Testing and Verification
The project was verified through functional testing of major workflows:

- Login and logout
- Student add, edit, delete, and filtering
- Feedback submission
- AI analysis request and timeout handling
- AI log viewing
- CSV/PDF export flows
- Error page rendering for invalid routes

Stress checks included invalid inputs, missing records, and service failure scenarios to confirm that the system shows clear feedback instead of exposing raw exceptions.

## 11.1 Website Screenshots
This report can include screenshots of the deployed website or local application pages such as:

- Login page
- Dashboard page
- Student management page
- Student profile page
- AI logs page

Screenshot files placed in `docs/screenshots/` are included automatically in the generated PDF.

## 12. Outcomes
The completed system delivers:

- A centralized classroom management workflow
- Better visibility into academic performance
- AI-supported student risk interpretation
- Export-ready reporting
- Cleaner UI and stronger user feedback
- Safer behavior under invalid input and failure conditions

## 13. Limitations
- The app currently relies on local-file storage and SQLite.
- Role-based access is limited.
- Production persistence needs extra setup on some hosting platforms.
- AI logic can be improved further with more advanced models or real external services.

## 14. Future Enhancements
- Add role-based access control
- Move data storage to a managed production database
- Add email or notification support
- Improve AI recommendations with richer academic history
- Add more analytics dashboards and downloadable reports

## 15. Conclusion
The Digital Assistant for Classroom Management successfully meets the project goals by combining data management, reporting, AI-assisted analysis, and usability improvements in one faculty-focused application. The final version is more polished, more resilient, and better prepared for live deployment and academic demonstration.
