# Digital Assistant for Classroom Management

A beginner-friendly Streamlit mini project for managing student classroom data, identifying weak students, visualizing attendance/subject analytics, and predicting Pass/Fail using Logistic Regression.

## Project Structure

```text
classroom_assistant/
  app.py
  students.csv
  requirements.txt
  README.md
```

## Features

- Upload student CSV with columns:
  - `Name`, `Maths`, `Science`, `English`, `Attendance`
- Display student data in a clean table
- Auto-calculate:
  - `Total` marks
  - `Average` marks
  - `Grade` (`A >= 75`, `B >= 50`, `C < 50`)
- Identify weak students (`Average < 50`)
- Add new student records using a form
- Dynamic data update using Streamlit session state
- Visual analytics:
  - Attendance bar chart
  - Subject-wise average marks chart
- Simple AI feature:
  - Logistic Regression based on `Average` and `Attendance`
  - Predicts `Pass` or `Fail`

## CSV Format

Use this exact header format:

```csv
Name,Maths,Science,English,Attendance
```

A sample dataset is included in `students.csv`.

## How to Run

1. Open terminal in project folder:

```bash
cd classroom_assistant
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run Streamlit app:

```bash
streamlit run app.py
```

4. Open the local URL shown in terminal (usually `http://localhost:8501`).

## Notes for Mini Project Viva

- The ML model is intentionally simple and practical.
- Training label is derived from classroom logic:
  - `Pass` if `Average >= 50` and `Attendance >= 75`
  - Otherwise `Fail`
- This makes the project easy to explain and extend.

## Future Improvements

- Save added student records permanently to CSV/database
- Add download button for updated data
- Add more ML features (e.g., risk score, clustering)
<<<<<<< HEAD
- Add authentication for teacher/admin usage

=======
- Add authentication for teacher/admin usage

>>>>>>> 5d2bf76286a1dc814412feffe862aa50a594a22e
