import duckdb
import pandas as pd
from datetime import datetime

class MolapCube:
    def __init__(self):
        self.con = duckdb.connect(database=':memory:')
        self.last_refresh = None

    def refresh(self, db_params):
        """Загружает данные из PostgreSQL и строит аналитический куб"""
        try:
            self.con.execute(f"""
                ATTACH 'postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}' 
                AS pg (TYPE postgres);
            """)

            # Создаём OLAP-куб (агрегированные данные)
            self.con.execute("""
                CREATE OR REPLACE TABLE student_molap AS 
                SELECT 
                    s.id,
                    s.name,
                    s.group_name,
                    s.year_of_study,
                    ROUND(AVG(g.grade), 2) as avg_grade,
                    ROUND(AVG(a.attendance_percent), 1) as avg_attendance,
                    COUNT(DISTINCT g.subject_id) as subjects_count,
                    MAX(g.date) as last_assessment,
                    CASE 
                        WHEN AVG(g.grade) < 3.7 OR AVG(a.attendance_percent) < 70 THEN 1 
                        ELSE 0 
                    END as high_risk
                FROM pg.students s
                LEFT JOIN pg.grades g ON s.id = g.student_id
                LEFT JOIN pg.attendance a ON s.id = a.student_id
                GROUP BY s.id, s.name, s.group_name, s.year_of_study
            """)

            self.last_refresh = datetime.now()
            print(f"✅ MOLAP Cube успешно обновлён в {self.last_refresh}")
            return True
        except Exception as e:
            print(f"❌ Ошибка при обновлении MOLAP: {e}")
            return False

    def get_data(self, filters=None):
        query = "SELECT * FROM student_molap"
        if filters:
            # Можно добавить фильтры позже
            pass
        return self.con.execute(query).df()

    def get_summary(self):
        return self.con.execute("""
            SELECT 
                COUNT(*) as total_students,
                ROUND(AVG(avg_grade), 2) as overall_avg_grade,
                ROUND(AVG(avg_attendance), 1) as overall_avg_att,
                SUM(high_risk) as high_risk_count,
                ROUND(SUM(high_risk)::float / COUNT(*) * 100, 1) as high_risk_percent
            FROM student_molap
        """).df()

molap_cube = MolapCube()