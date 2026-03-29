from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import joblib
import pandas as pd
import uvicorn

app = FastAPI()

DB_PARAMS = {
    "dbname": "student_ai_db",
    "user": "postgres",
    "password": "12345",
    "host": "db",
    "port": "5432"
}

# Загружаем модель
try:
    model = joblib.load('student_model.pkl')
    print("Модель успешно загружена")
except:
    model = None
    print("ВНИМАНИЕ: Модель student_model.pkl не найдена!")

class LoginData(BaseModel):
    login: str
    password: str

class StudentData(BaseModel):
    name: str
    group_name: str
    year_of_study: int

class GradeData(BaseModel):
    student_id: int
    subject_id: int
    grade: int

def get_db():
    return psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)

# ====================== НОВЫЙ ENDPOINT ДЛЯ СПИСКА СТУДЕНТОВ ======================
@app.get("/students")
def get_all_students():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, group_name, year_of_study FROM students ORDER BY name")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in data]

# ====================== ОСТАЛЬНОЙ КОД (login, predict, analytics и т.д.) ======================
@app.post("/login")
def login(data: LoginData):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM teachers WHERE login = %s AND password = %s", (data.login, data.password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    return {"status": "ok"}

@app.get("/student_full/{sid}")
def get_student(sid: int):
    # ... (оставляем твой старый код без изменений)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE id = %s", (sid,))
    bio = cur.fetchone()
    if not bio:
        raise HTTPException(status_code=404, detail="Студент не найден")
    cur.execute("""
        SELECT s.name as subject, g.grade, g.date 
        FROM grades g JOIN subjects s ON g.subject_id = s.id 
        WHERE g.student_id = %s ORDER BY g.date DESC
    """, (sid,))
    grades = cur.fetchall()
    cur.close()
    conn.close()
    return {"bio": bio, "grades": grades}

@app.get("/predict/{sid}")
def predict(sid: int):
    if model is None:
        return {"avg_grade": 0, "att": 0, "risk": "Модель не загружена"}

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT AVG(grade) as avg_grade FROM grades WHERE student_id = %s", (sid,))
    g = float(cur.fetchone()['avg_grade'] or 0)
    cur.execute("SELECT AVG(attendance_percent) as avg_att FROM attendance WHERE student_id = %s", (sid,))
    a = float(cur.fetchone()['avg_att'] or 0)
    cur.close()
    conn.close()

    input_df = pd.DataFrame([[g, a]], columns=['avg_grade', 'avg_attendance'])
    risk_prob = model.predict_proba(input_df)[0][1]

    return {
        "avg_grade": round(g, 2),
        "att": round(a, 1),
        "risk": f"{round(risk_prob * 100)}%"
    }

@app.get("/analytics")
def get_analytics():
    # ... (оставляем твой код аналитики без изменений)
    conn = get_db()
    cur = conn.cursor()
    query = """
    SELECT s.id, s.name, s.group_name, s.year_of_study,
           ROUND(AVG(g.grade)::numeric, 2) as avg_grade,
           ROUND(AVG(a.attendance_percent)::numeric, 1) as avg_attendance,
           CASE WHEN AVG(g.grade) < 3.7 OR AVG(a.attendance_percent) < 70 THEN 1 ELSE 0 END as risk_label
    FROM students s
    LEFT JOIN grades g ON s.id = g.student_id
    LEFT JOIN attendance a ON s.id = a.student_id
    GROUP BY s.id, s.name, s.group_name, s.year_of_study
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]

# Остальные эндпоинты (add_student, add_grade) оставляем как были
@app.post("/add_student")
def add_s(data: StudentData):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO students (name, group_name, year_of_study) VALUES (%s, %s, %s)",
                (data.name, data.group_name, data.year_of_study))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "added"}

@app.post("/add_grade")
def add_g(data: GradeData):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO grades (student_id, subject_id, grade, date) VALUES (%s, %s, %s, CURRENT_DATE)",
                (data.student_id, data.subject_id, data.grade))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "saved"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)