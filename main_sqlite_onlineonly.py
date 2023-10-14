import pandas as pd
import altair as alt
import streamlit as st
import matplotlib.pyplot as plt
import sqlite3
import yaml
import streamlit_authenticator as stauth
from streamlit_extras.colored_header import colored_header


db_path = "/var/lib/marzban/db.sqlite3" 

st.set_page_config(
    page_title="MarzbanStat",
    page_icon="🧊",
    layout="wide"
)


@st.cache_data(ttl=300, show_spinner="Загрузка данных") 
def getdata(query):
    db_path = "/var/lib/marzban/db.sqlite3" 
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    return df


def data_from_marzban(query):
    df = getdata(query)
    if "used_traffic" in df.columns:
        df["used_traffic"] = df["used_traffic"].astype(float).fillna(0)
        df["used_traffic_gb"] = df["used_traffic"] / 1073741824
        df["used_traffic_gb"] = df["used_traffic_gb"].round(2)
    if "created_at" in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at']).fillna(pd.NaT)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["hour"] = df["created_at"].dt.hour
    return df 

df_now_connected_with_nodes = data_from_marzban(r"""
                                       SELECT a.username, 
                                         b.type,
                                         c.node
                                       FROM users as a
                                       LEFT JOIN (
                                         SELECT DISTINCT 
                                           sub_last_user_agent,
                                           CASE 
                                             WHEN sub_last_user_agent IS NULL OR TRIM(sub_last_user_agent) = '' THEN 'Unknown'  
                                             ELSE SUBSTR(sub_last_user_agent, 1, INSTR(sub_last_user_agent, '/')-1)
                                           END AS type
                                         FROM users
                                       ) AS b ON b.sub_last_user_agent = a.sub_last_user_agent
                                       LEFT JOIN (
                                         SELECT
                                           user_id,
                                           IFNULL(n.name, 'Main') AS node,
                                           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY node_id) AS row_num
                                         FROM node_user_usages AS a
                                         LEFT JOIN nodes AS n ON n.id = a.node_id
                                         WHERE DATE(a.created_at) = DATE('now')
                                           AND CAST(STRFTIME('%H', a.created_at) AS INTEGER) = CAST(STRFTIME('%H', 'now') AS INTEGER)
                                       ) AS c ON c.row_num = 1 AND c.user_id = a.id
                                       WHERE DATE(online_at) = DATE('now')
                                         AND TIME(online_at) BETWEEN TIME(DATETIME('now', '-1 minute')) AND TIME(DATETIME('now', '+1 minute'));         
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
    colored_header(
        label="Текущий онлайн",
        description="",
        color_name="violet-70",
    )

    total_data_df_now = nodes_df = df_now_connected_with_nodes.groupby('node')['username'].nunique().reset_index(name='unique_users')
    total_data_df_now['percentage'] = ((total_data_df_now['unique_users'] / total_data_df_now['unique_users'].sum()) * 100).round(1)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label='Всего', value=df_now_connected_with_nodes['username'].nunique()) 
        st.dataframe(total_data_df_now, use_container_width=True)
    with col2:
        chart = alt.Chart(total_data_df_now).mark_arc(innerRadius=50, outerRadius=100).encode(
            theta='unique_users',
            color='node',
            tooltip=['node', 'unique_users', 'percentage']
        ).properties(title='По нодам')
        st.altair_chart(chart, use_container_width=True)
    with st.expander("Подробнее по юзерам"):
        st.dataframe(df_now_connected_with_nodes, use_container_width=True)

    colored_header(
        label="",
        description="",
        color_name="violet-70",
    )

 

#Если неверные логин или пароль
elif authentication_status == False:
    st.error('Логин/пароль неверные')
    print("Error login or pass")
elif authentication_status == None:
    st.warning('Введите ваш логин и пароль')
