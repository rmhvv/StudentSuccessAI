import psycopg2
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Настройки БД
DB_PARAMS = {
    "dbname": "student_ai_db",
    "user": "postgres",
    "password": "12345",
    "host": "db",
    "port": "5432"
}


def train():
    try:
        # 1. Загружаем данные из БД
        conn = psycopg2.connect(**DB_PARAMS)

        # Получаем среднюю оценку и посещаемость для каждого студента
        query = """
        SELECT 
            s.id,
            AVG(g.grade) as avg_grade,
            AVG(a.attendance_percent) as avg_attendance
        FROM students s
        JOIN grades g ON s.id = g.student_id
        JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id
        """
        df = pd.read_sql(query, conn)
        conn.close()

        # Считаем, что риск высокий (1), если оценка < 3.7 ИЛИ посещаемость < 70%
        df['risk_label'] = ((df['avg_grade'] < 3.7) | (df['avg_attendance'] < 70)).astype(int)

        # 3. Готовим данные для модели
        X = df[['avg_grade', 'avg_attendance']]  # Признаки
        y = df['risk_label']  # Цель

        # 4. Создаем и обучаем модель
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)

        joblib.dump(model, 'student_model.pkl')

        print(f" Модель обучена на данных {len(df)} студентов!")
        print(" Файл 'student_model.pkl' успешно создан.")

    except Exception as e:
        print(f" Ошибка при обучении: {e}")


if __name__ == "__main__":
    train()