from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import joblib
import pandas as pd
import uvicorn
from molap import molap_cube   # ← Новая строка

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
except:
    model = None

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

# ====================== MOLAP ======================
@app.on_event("startup")
async def startup_event():
    print("Запуск MOLAP Cube...")
    molap_cube.refresh(DB_PARAMS)

@app.get("/molap")
def get_molap_data():
    try:
        df = molap_cube.get_data()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================== Остальные эндпоинты ======================
@app.get("/students")
def get_all_students():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, group_name, year_of_study FROM students ORDER BY name")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in data]

# ... (весь твой предыдущий код login, predict, analytics, add_student, add_grade оставляем)

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

# (Остальные функции predict, student_full, add_student, add_grade — оставь как были)

# ====================== MOLAP REFRESH ======================
@app.get("/molap/refresh")
def refresh_molap():
    try:
        success = molap_cube.refresh(DB_PARAMS)
        if success:
            return {"status": "success", "message": "MOLAP куб успешно обновлён"}
        else:
            return {"status": "error", "message": "Не удалось обновить куб"}
    except Exception as e:
        print(f"Ошибка обновления MOLAP: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка обновления MOLAP: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)