import pandas as pd
import altair as alt
import streamlit as st
import matplotlib.pyplot as plt
import sqlite3
import yaml
import streamlit_authenticator as stauth


db_path = "/var/lib/marzban/db.sqlite3" 

st.set_page_config(
    page_title="MarzbanStat",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


@st.cache_data(ttl=300, show_spinner="Загрузка данных") 
def getdata(query):
    db_path = "/var/lib/marzban/db.sqlite3" 
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    return df


def data_from_marzban(query):
    df = getdata(query)
    df["used_traffic_gb"] = df["used_traffic"] / 1073741824
    df["used_traffic_gb"] = df["used_traffic_gb"].round(2)
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["hour"] = df["created_at"].dt.hour
    return df 

def last_hour_users(df):
    df["created_at"] = pd.to_datetime(df["created_at"])
    max_date = df["created_at"].max()
    last_hour_users = df[df["created_at"] == max_date]
    return last_hour_users

def users_by_hours(df):
    hourly_counts = df.groupby(["hour", "node"])["username"].nunique()
    hourly_counts = hourly_counts.reset_index()
    hourly_counts = hourly_counts.rename(columns={"username": "Connections"})
    return hourly_counts

def traffic_by_hours(df):
    hourly_counts = df.groupby(["hour", "node"])["used_traffic_gb"].sum().reset_index()
    hourly_counts["used_traffic_gb"] = hourly_counts["used_traffic_gb"].round(1)
    hourly_counts = hourly_counts.rename(columns={"used_traffic_gb": "traffic"})
    hourly_counts = hourly_counts.sort_values(['hour', 'node', 'traffic'], ascending=[True, True, False])
    return hourly_counts

def traffic_by_users(df):
    user_traffic_data = df.groupby("username")["used_traffic_gb"].agg(
        total_traffic_gb = 'sum',
        connections = 'count'
    )
    user_traffic_data = user_traffic_data.reset_index()
    user_traffic_data = user_traffic_data.sort_values(by=['total_traffic_gb', 'connections'], ascending=[False, False])
    return user_traffic_data



df = data_from_marzban("""
                        SELECT 
                            datetime(a.created_at, '+3 hours') AS created_at,
                            a.used_traffic AS used_traffic, 
                            COALESCE(n.name, 'Main') AS node, 
                            u.username AS username
                        FROM 
                            node_user_usages a 
                            LEFT JOIN users u ON u.id = a.user_id
                            LEFT JOIN nodes n ON n.id = a.node_id
                        WHERE 
                            a.created_at >= datetime('now', '-1 day', 'start of day', '+21 hours')
                        ORDER BY 
                            a.created_at DESC;
                       """)
df_last_hour_users = last_hour_users(df)
df_users_by_hours = users_by_hours(df)
stat_by_users_today = traffic_by_users(df)
stat_by_users_last_hour = traffic_by_users(df_last_hour_users)
traffic_by_users_last_hour = traffic_by_users(df_last_hour_users)
traffic_by_hours_today = traffic_by_hours(df)
df_all_dates = data_from_marzban("""
                                    SELECT 
                                        users_usage.username AS username,
                                        COUNT(users_usage.created_at) AS cnt_connections,
                                        SUM(users_usage.used_traffic) AS used_traffic,
                                        MIN(users_usage.created_at) AS first_conn,
                                        MAX(users_usage.created_at) AS last_conn,
                                        julianday(MAX(users_usage.created_at)) - julianday(MIN(users_usage.created_at)) AS lifetime_days
                                    FROM (
                                        SELECT 
                                            datetime(a.created_at, '+3 hours') AS created_at,
                                            a.used_traffic AS used_traffic,
                                            COALESCE(n.name, 'Main') AS node,
                                            u.username AS username
                                        FROM 
                                            node_user_usages a 
                                            LEFT JOIN users u ON u.id = a.user_id
                                            LEFT JOIN nodes n ON n.id = a.node_id
                                        ORDER BY 
                                            a.created_at DESC
                                    ) AS users_usage
                                    GROUP BY
                                        users_usage.username
                                    ORDER BY
                                        COUNT(users_usage.created_at) DESC;
                                """)
df_ttl_with_nodes = data_from_marzban("""
                        SELECT 
                            datetime(a.created_at, '+3 hours') AS created_at,
                            a.used_traffic AS used_traffic, 
                            COALESCE(n.name, 'Main') AS node
                        FROM 
                            node_user_usages a 
                            LEFT JOIN users u ON u.id = a.user_id
                            LEFT JOIN nodes n ON n.id = a.node_id
                        ORDER BY 
                            a.created_at DESC;
                        """)




#Начало отрисовки страницы

#Форма для логина и пароля

with open('config.yaml') as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('Войти', 'main')

if authentication_status:
    authenticator.logout('Выход', 'main')
    st.write(f'🖐️ Привет *{name}*')
    
    
#Отрисовка основной страницы после успешного логина
    st.header("Сегодня по часам") 
    col1, col2 = st.columns(2)
    with col1:
        bars = alt.Chart(df_users_by_hours).mark_bar().encode(
            x=alt.X('hour:N', axis=alt.Axis(title='Час')),
            y=alt.Y('sum(Connections):Q', stack='zero', axis=alt.Axis(title='Подключений')),
            color=alt.Color('node:N', legend=alt.Legend(title='Узлы'), title='Узел') 
        )

        text = alt.Chart(df_users_by_hours).mark_text(dx=0, dy=-10, align='center', color='white').encode(
            x=alt.X('hour:N', axis=alt.Axis(title='Час')),
            y=alt.Y('sum(Connections):Q', stack='zero', axis=alt.Axis(title='Подключений')),
            text=alt.Text('sum(Connections):Q')
        )

        mean_line = alt.Chart(df_users_by_hours).transform_aggregate(
            mean_connections='mean(Connections)'
        ).mark_rule(color='lightblue', strokeDash=[10, 5], opacity=0.5).encode(
            y='mean(mean_connections):Q'
        )

        st.altair_chart(bars+text+mean_line, use_container_width=True)

    with col2:
        #-----------------------траффик
        bars = alt.Chart(traffic_by_hours_today).mark_bar().encode(
            x=alt.X('hour:N', axis=alt.Axis(title='Час')),
            y=alt.Y('sum(traffic):Q', stack='zero', axis=alt.Axis(title='GB')),
            color=alt.Color('node:N', legend=alt.Legend(title='Узлы'), title='Узел') 
        )

        text = alt.Chart(traffic_by_hours_today).mark_text(dx=0, dy=-10, align='center', color='white').encode(
            x=alt.X('hour:N', axis=alt.Axis(title='Час')),
            y=alt.Y('sum(traffic):Q', stack='zero', axis=alt.Axis(title='GB')),
            text=alt.Text('sum(traffic):Q')
        )


        mean_line = alt.Chart(traffic_by_hours_today).transform_aggregate(
            mean_traffic='mean(traffic)'
        ).mark_rule(color='lightblue', strokeDash=[10, 5], opacity=0.5).encode(
            y='mean(mean_traffic):Q'
        )

        st.altair_chart(bars+text+mean_line, use_container_width=True)


    # Переименование колонок
    user_traffic_data = stat_by_users_today.rename(columns={"username": "Имя пользователя", "total_traffic_gb": "Трафик (ГБ)", "connections": "Подключения"})
    stat_by_users_last_hour = stat_by_users_last_hour.rename(columns={"username": "Имя пользователя", "total_traffic_gb": "Трафик (ГБ)"})

    # Получение топ 5 пользователей по подключениям и трафику
    top5_connections = user_traffic_data.nlargest(5, 'Подключения')[['Имя пользователя', 'Подключения']].reset_index(drop=True)
    top5_traffic = user_traffic_data.nlargest(5, 'Трафик (ГБ)')[['Имя пользователя', 'Трафик (ГБ)']].reset_index(drop=True)
    # Получение топ 5 пользователей по трафику за последний час
    top5_last_hour_traffic = stat_by_users_last_hour.nlargest(5, 'Трафик (ГБ)')[['Имя пользователя', 'Трафик (ГБ)']].reset_index(drop=True)

    st.subheader("Топ 5 пользователей")

    col1, col2, col3 = st.columns(3)


    with col1:
        st.write("По подключениям за день")
        st.dataframe(top5_connections, use_container_width=True)


    with col2:
        st.write("По траффику за день")
        st.dataframe(top5_traffic, use_container_width=True)

    with col3:
        st.write("По трафику за последний час")
        st.dataframe(top5_last_hour_traffic, use_container_width=True)

    st.header("Статистика по узлам") 

    total_data = df_ttl_with_nodes.groupby("node")['used_traffic_gb'].sum().round(2).reset_index()
    total_data['percentage'] = ((total_data['used_traffic_gb'] / total_data['used_traffic_gb'].sum()) * 100).round(1)
    today_data = df.groupby("node")['used_traffic_gb'].sum().round(2).reset_index()
    today_data['percentage'] = ((today_data['used_traffic_gb'] / today_data['used_traffic_gb'].sum()) * 100).round(1)
    last_hour_data = df_last_hour_users.groupby("node")['used_traffic_gb'].sum().round(2).reset_index()
    last_hour_data['percentage'] = ((last_hour_data['used_traffic_gb'] / last_hour_data['used_traffic_gb'].sum()) * 100).round(1)

    col1, col2, col3 = st.columns(3)
    with col1:
        chart = alt.Chart(total_data).mark_arc(innerRadius=50, outerRadius=100).encode(
            theta='used_traffic_gb',
            color='node',
            tooltip=['node', 'used_traffic_gb', 'percentage']
        ).properties(title='За все время')
        st.altair_chart(chart, use_container_width=True)

    with col2:
        chart = alt.Chart(today_data).mark_arc(innerRadius=50, outerRadius=100).encode(
            theta='used_traffic_gb',
            color='node',
            tooltip=['node', 'used_traffic_gb', 'percentage']
        ).properties(title='За сегодня')
        st.altair_chart(chart, use_container_width=True)

    with col3:
        chart = alt.Chart(last_hour_data).mark_arc(innerRadius=50, outerRadius=100).encode(
            theta='used_traffic_gb',
            color='node',
            tooltip=['node', 'used_traffic_gb', 'percentage']
        ).properties(title='За последний час')
        st.altair_chart(chart, use_container_width=True)


    st.header("Общая статистика") 
    # Переименование колонок
    df_all_dates = df_all_dates.rename(columns={
        "username": "Имя пользователя",
        "cnt_connections": "Количество подключений",
        "lifetime_days": "Время жизни (дни)",
        "used_traffic_gb": "Трафик (ГБ)"
    })


    # Генерация топов и антитопов
    top_traffic = df_all_dates.nlargest(10, 'Трафик (ГБ)')[['Имя пользователя', 'Трафик (ГБ)']]
    top_connections = df_all_dates.nlargest(10, 'Количество подключений')[['Имя пользователя', 'Количество подключений']]
    top_lifetime = df_all_dates.nlargest(10, 'Время жизни (дни)')[['Имя пользователя', 'Время жизни (дни)']]
    anti_top_traffic = df_all_dates.nsmallest(10, 'Трафик (ГБ)')[['Имя пользователя', 'Трафик (ГБ)']]
    anti_top_connections = df_all_dates.nsmallest(10, 'Количество подключений')[['Имя пользователя', 'Количество подключений']]
    anti_top_lifetime = df_all_dates.nsmallest(10, 'Время жизни (дни)')[['Имя пользователя', 'Время жизни (дни)']]


    # Функция для создания гистограммы
    def create_bar_chart(data, x, y):
        max_y = data[y].max()
        max_y += max_y * 0.1  
        chart = alt.Chart(data).mark_bar().encode(
            x=alt.X(x, title=x),
            y=alt.Y(y, title=y, scale=alt.Scale(domain=(0, max_y)))
        )
        text = alt.Chart(data).mark_text(dx=0, dy=-10, align='center', color='white').encode(
            x=alt.X(x, title=x),
            y=alt.Y(y, title=y),
            text=alt.Text(y)
        )
        return chart+text


    # Гистограммы для топ 10 пользователей
    col3, col4, col5 = st.columns([1, 1, 1])

    with col3:
        st.write("Топ 10 по траффику")
        st.altair_chart(create_bar_chart(top_traffic, 'Имя пользователя', 'Трафик (ГБ)'), use_container_width=True)

    with col4:
        st.write("Топ 10 по подключениям")
        st.altair_chart(create_bar_chart(top_connections, 'Имя пользователя', 'Количество подключений'), use_container_width=True)

    with col5:
        st.write("Топ 10 по времени жизни")
        st.altair_chart(create_bar_chart(top_lifetime, 'Имя пользователя', 'Время жизни (дни)'), use_container_width=True)
    # Колонки для топов и антитопов
    col1, col2 = st.columns(2)

    # Топ 5 пользователей
    with col1:
        st.subheader("Топ 10 Пользователей")
        st.write("По траффику")
        st.dataframe(top_traffic, use_container_width=True)
        st.write("По подключениям")
        st.dataframe(top_connections, use_container_width=True)
        st.write("По времени жизни")
        st.dataframe(top_lifetime, use_container_width=True)

    # Антитоп 5 пользователей
    with col2:
        st.subheader("Антитоп 10 Пользователей")
        st.write("По траффику")
        st.dataframe(anti_top_traffic, use_container_width=True)
        st.write("По подключениям")
        st.dataframe(anti_top_connections, use_container_width=True)
        st.write("По времени жизни")
        st.dataframe(anti_top_lifetime, use_container_width=True)




    with st.expander("Исходные данные", expanded=False):
        st.dataframe(df, use_container_width=True)
        st.dataframe(df_last_hour_users, use_container_width=True)
        st.dataframe(df_users_by_hours, use_container_width=True)
        st.dataframe(stat_by_users_today, use_container_width=True)
        st.dataframe(traffic_by_users_last_hour, use_container_width=True)
        st.dataframe(df_all_dates, use_container_width=True)

#Если неверные логин или пароль
elif authentication_status == False:
    st.error('Логин/пароль неверные')
    print("Error login or pass")
elif authentication_status == None:
    st.warning('Введите ваш логин и пароль')
