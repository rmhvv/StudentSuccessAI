import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API = "http://backend:8000"

st.set_page_config(page_title="EduAI Analytics", layout="wide")

if 'auth' not in st.session_state:
    st.session_state.auth = False

st.sidebar.title(" Главное меню")
menu = st.sidebar.selectbox("Раздел", 
    ["🏠 Главная", "👤 Студент", "👨‍🏫 Преподаватель", "📊 Аналитика (MOLAP)"])

# ====================== ГЛАВНАЯ ======================
if menu == "🏠 Главная":
    st.title("🎓 EduAI Analytics")
    st.markdown("### Система мониторинга и прогнозирования успеваемости студентов")

# ====================== СТУДЕНТ ======================
elif menu == "👤 Студент":
    st.header("👤 Личный кабинет студента")

    search_type = st.radio("Способ поиска", ["По ФИО", "По ID"])

    if search_type == "По ФИО":
        name_search = st.text_input("Введите ФИО студента (или часть имени)")
        if st.button("🔍 Найти студента"):
            try:
                res = requests.get(f"{API}/students")
                if res.status_code == 200:
                    students = pd.DataFrame(res.json())
                    filtered = students[students['name'].str.contains(name_search, case=False, na=False)]

                    if len(filtered) == 0:
                        st.error("Студент не найден")
                    elif len(filtered) == 1:
                        st.session_state.selected_sid = int(filtered.iloc[0]['id'])
                        st.rerun()
                    else:
                        st.write("Найдено несколько студентов:")
                        st.dataframe(filtered[['id', 'name', 'group_name', 'year_of_study']])
                        chosen = st.selectbox("Выберите студента из списка", filtered['name'].tolist())
                        sid = int(filtered[filtered['name'] == chosen].iloc[0]['id'])
                        st.session_state.selected_sid = sid
                        st.rerun()
            except Exception as e:
                st.error(f"Ошибка сервера: {e}")
    else:
        sid = st.number_input("Введите ID студента", min_value=1, step=1)
        if st.button("Посмотреть результаты"):
            st.session_state.selected_sid = sid
            st.rerun()

    # Показ информации о студенте
    if 'selected_sid' in st.session_state:
        sid = st.session_state.selected_sid
        try:
            res_info = requests.get(f"{API}/student_full/{sid}")
            res_pred = requests.get(f"{API}/predict/{sid}")

            if res_info.status_code == 200 and res_pred.status_code == 200:
                data = res_info.json()
                pred = res_pred.json()

                st.subheader(f"✅ {data['bio']['name']} — {data['bio']['group_name']} ({data['bio']['year_of_study']} курс)")

                col1, col2, col3 = st.columns(3)
                col1.metric("Средний балл", pred.get('avg_grade', 0))
                col2.metric("Посещаемость", f"{pred.get('att', 0)}%")
                col3.metric("Риск неуспеваемости", pred.get('risk', '—'))

                st.write("### История оценок")
                if data.get('grades'):
                    df_grades = pd.DataFrame(data['grades'])
                    st.dataframe(df_grades, use_container_width=True)
                else:
                    st.info("Оценок пока нет")
            else:
                st.error("Не удалось загрузить данные студента")
        except Exception as e:
            st.error(f"Ошибка: {e}")

# ====================== ПРЕПОДАВАТЕЛЬ ======================
elif menu == "👨‍🏫 Преподаватель":
    if not st.session_state.auth:
        st.header("🔑 Вход для преподавателя")
        log = st.text_input("Логин", value="admin")
        pas = st.text_input("Пароль", value="12345", type="password")
        if st.button("Войти"):
            try:
                res = requests.post(f"{API}/login", json={"login": log, "password": pas})
                if res.status_code == 200:
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Неверный логин или пароль")
            except:
                st.error("Сервер не отвечает")
    else:
        st.success("✅ Вы вошли как преподаватель")
        if st.sidebar.button("Выйти"):
            st.session_state.auth = False
            st.rerun()

        tab1, tab2, tab3 = st.tabs(["➕ Добавить студента", "📝 Выставить оценку", "📋 Все студенты"])

        with tab1:
            name = st.text_input("ФИО нового студента")
            group = st.text_input("Группа (например: ИВТ-21)")
            year = st.slider("Курс", 1, 5, 2)
            if st.button("Добавить студента"):
                r = requests.post(f"{API}/add_student", 
                                json={"name": name, "group_name": group, "year_of_study": year})
                if r.status_code == 200:
                    st.success("Студент успешно добавлен!")

        with tab2:
            st.subheader("Выставить оценку")
            try:
                res = requests.get(f"{API}/students")
                if res.status_code == 200:
                    students = res.json()
                    options = {f"{s['name']} ({s['group_name']})": s['id'] for s in students}
                    
                    selected = st.selectbox("Выберите студента", options=list(options.keys()))
                    student_id = options[selected]

                    subject = st.selectbox("Предмет", [1,2,3,4,5], 
                                         format_func=lambda x: f"Предмет №{x}")
                    grade_val = st.slider("Оценка", 2, 5, 4)

                    if st.button("Сохранить оценку"):
                        r = requests.post(f"{API}/add_grade", 
                                        json={"student_id": student_id, "subject_id": subject, "grade": grade_val})
                        if r.status_code == 200:
                            st.success("✅ Оценка успешно сохранена!")
            except Exception as e:
                st.error(f"Не удалось загрузить список студентов: {e}")

        with tab3:
            st.subheader("Список всех студентов")
            try:
                res = requests.get(f"{API}/students")
                if res.status_code == 200:
                    df = pd.DataFrame(res.json())
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("Не удалось загрузить список")
            except Exception as e:
                st.error(f"Ошибка: {e}")

# ====================== МОЛАП АНАЛИТИКА ======================
elif menu == "📊 Аналитика (MOLAP)":
    if not st.session_state.auth:
        st.warning("Войдите как преподаватель для доступа к аналитике")
    else:
        st.header("📊 MOLAP Аналитика — Многомерный анализ")

        try:
            response = requests.get(f"{API}/analytics")
            if response.status_code == 200:
                df = pd.DataFrame(response.json())

                # Фильтры
                col1, col2, col3 = st.columns(3)
                with col1:
                    groups = st.multiselect("Группа", df['group_name'].unique().tolist(), 
                                          default=df['group_name'].unique().tolist())
                with col2:
                    courses = st.multiselect("Курс", sorted(df['year_of_study'].unique().tolist()), 
                                           default=sorted(df['year_of_study'].unique().tolist()))
                with col3:
                    risk_filter = st.radio("Риск неуспеваемости", ["Все", "Высокий риск", "Низкий риск"])

                filtered_df = df[(df['group_name'].isin(groups)) & (df['year_of_study'].isin(courses))]
                if risk_filter == "Высокий риск":
                    filtered_df = filtered_df[filtered_df['risk_label'] == 1]
                elif risk_filter == "Низкий риск":
                    filtered_df = filtered_df[filtered_df['risk_label'] == 0]

                # Метрики
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Студентов", len(filtered_df))
                c2.metric("Средний балл", round(filtered_df['avg_grade'].mean(), 2) if len(filtered_df)>0 else 0)
                c3.metric("Средняя посещаемость", f"{round(filtered_df['avg_attendance'].mean(), 1)}%" if len(filtered_df)>0 else "0%")
                high_risk = len(filtered_df[filtered_df['risk_label'] == 1])
                c4.metric("Высокий риск", f"{high_risk} ({round(high_risk/len(filtered_df)*100) if len(filtered_df)>0 else 0}%)")

                # Графики
                tab_g1, tab_g2, tab_g3 = st.tabs(["По группам", "По курсам", "Риск + Таблица"])

                with tab_g1:
                    fig1 = px.bar(filtered_df.groupby('group_name')['avg_grade'].mean().reset_index(),
                                  x='group_name', y='avg_grade', color='group_name')
                    st.plotly_chart(fig1, use_container_width=True)

                with tab_g2:
                    fig2 = px.box(filtered_df, x='year_of_study', y='avg_grade', color='group_name')
                    st.plotly_chart(fig2, use_container_width=True)

                with tab_g3:
                    fig3 = px.pie(filtered_df, names='risk_label', title="Распределение риска",
                                  color_discrete_map={0: 'green', 1: 'red'})
                    st.plotly_chart(fig3, use_container_width=True)

                    st.subheader("Детальная таблица")
                    st.dataframe(filtered_df.sort_values('avg_grade', ascending=False), use_container_width=True)

            else:
                st.error("Не удалось загрузить данные аналитики")
        except Exception as e:
            st.error(f"Ошибка загрузки аналитики: {e}")
