import psycopg2
from faker import Faker
import random
from datetime import datetime, timedelta

DB_PARAMS = {
    "dbname": "student_ai_db",
    "user": "postgres",
    "password": "12345",
    "host": "db",
    "port": "5432"
}


def init_all():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Удаляем старые таблицы, чтобы создать чистую структуру
        cur.execute("DROP TABLE IF EXISTS grades, attendance, students, subjects, teachers CASCADE;")

        cur.execute("""
            CREATE TABLE students (id SERIAL PRIMARY KEY, name VARCHAR(100), group_name VARCHAR(20), year_of_study INTEGER);
            CREATE TABLE subjects (id SERIAL PRIMARY KEY, name VARCHAR(100));
            CREATE TABLE teachers (id SERIAL PRIMARY KEY, login VARCHAR(50) UNIQUE, password TEXT);
            CREATE TABLE grades (id SERIAL PRIMARY KEY, student_id INTEGER REFERENCES students(id), subject_id INTEGER REFERENCES subjects(id), grade INTEGER, date DATE);
            CREATE TABLE attendance (id SERIAL PRIMARY KEY, student_id INTEGER REFERENCES students(id), subject_id INTEGER REFERENCES subjects(id), attendance_percent INTEGER);
        """)

        # Данные
        cur.execute("INSERT INTO teachers (login, password) VALUES ('admin', '12345')")
        subjects = ['Высшая математика', 'Программирование', 'Базы данных', 'ИИ', 'Физика']
        for s in subjects: cur.execute("INSERT INTO subjects (name) VALUES (%s)", (s,))

        fake = Faker('ru_RU')
        for i in range(1, 51):  # Создадим 50 студентов
            cur.execute("INSERT INTO students (name, group_name, year_of_study) VALUES (%s, %s, %s) RETURNING id",
                        (fake.name(), random.choice(['ИВТ-21', 'ПИ-22']), random.randint(1, 4)))
            s_id = cur.fetchone()[0]
            for sub_id in range(1, 6):
                att = random.randint(40, 100)
                cur.execute("INSERT INTO attendance (student_id, subject_id, attendance_percent) VALUES (%s, %s, %s)",
                            (s_id, sub_id, att))
                for _ in range(5):
                    cur.execute("INSERT INTO grades (student_id, subject_id, grade, date) VALUES (%s, %s, %s, %s)",
                                (s_id, sub_id, random.randint(2, 5), datetime.now().date()))

        conn.commit()
        print(" База данных полностью готова!")
    except Exception as e:
        print(f" Ошибка: {e}")
    finally:
        conn.close()


if __name__ == "__main__": init_all()