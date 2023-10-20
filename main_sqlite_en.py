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
    layout="wide",
    initial_sidebar_state="collapsed"
)


@st.cache_data(ttl=300, show_spinner="Loading data") 
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

def last_hour_users(df):
    df["created_at"] = pd.to_datetime(df["created_at"])
    max_date = df["created_at"].max()
    last_hour_users = df[df["created_at"] == max_date]
    return last_hour_users

def users_by_hours(df):
    hourly_counts = df.groupby(["hour", "node"])["username"].nunique().fillna(0).reset_index()
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



#Start drawing the page

#Form for login and password

with open('config.yaml') as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    authenticator.logout('Logout', 'main')
    st.write(f'🖐️ Logout *{name}*')
 #Drawing the main page after successful login
    colored_header(
        label="Currently online",
        description="",
        color_name="violet-70",
    )

    total_data_df_now = nodes_df = df_now_connected_with_nodes.groupby('node')['username'].nunique().reset_index(name='unique_users')
    total_data_df_now['percentage'] = ((total_data_df_now['unique_users'] / total_data_df_now['unique_users'].sum()) * 100).round(1)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label='Total', value=df_now_connected_with_nodes['username'].nunique()) 
        st.dataframe(total_data_df_now, use_container_width=True)
    with col2:
        chart = alt.Chart(total_data_df_now).mark_arc(innerRadius=50, outerRadius=100).encode(
            theta='unique_users',
            color='node',
            tooltip=['node', 'unique_users', 'percentage']
        ).properties(title='By nodes')
        st.altair_chart(chart, use_container_width=True)
    with st.expander("More details on users"):
        st.dataframe(df_now_connected_with_nodes, use_container_width=True)

    colored_header(
        label="",
        description="",
        color_name="violet-70",
    )

    st.header("Today by hours") 
    col1, col2 = st.columns(2)
    with col1:
        bars = alt.Chart(df_users_by_hours).mark_bar().encode(
            x=alt.X('hour:N', axis=alt.Axis(title='Hour')),
            y=alt.Y('sum(Connections):Q', stack='zero', axis=alt.Axis(title='Connections')),
            color=alt.Color('node:N', legend=alt.Legend(title='Nodes'), title='Node') 
        )

        text = alt.Chart(df_users_by_hours).mark_text(dx=0, dy=-10, align='center', color='white').encode(
            x=alt.X('hour:N', axis=alt.Axis(title='Hour')),
            y=alt.Y('sum(Connections):Q', stack='zero', axis=alt.Axis(title='Connections')),
            text=alt.Text('sum(Connections):Q')
        )

        mean_line = alt.Chart(df_users_by_hours).transform_aggregate(
            mean_connections='mean(Connections)'
        ).mark_rule(color='lightblue', strokeDash=[10, 5], opacity=0.5).encode(
            y='mean(mean_connections):Q'
        )

        st.altair_chart(bars+text+mean_line, use_container_width=True)

    with col2:
        #-----------------------traffic
        bars = alt.Chart(traffic_by_hours_today).mark_bar().encode(
            x=alt.X('hour:N', axis=alt.Axis(title='Hour')),
            y=alt.Y('sum(traffic):Q', stack='zero', axis=alt.Axis(title='GB')),
            color=alt.Color('node:N', legend=alt.Legend(title='Nodes'), title='Node') 
        )

        text = alt.Chart(traffic_by_hours_today).mark_text(dx=0, dy=-10, align='center', color='white').encode(
            x=alt.X('hour:N', axis=alt.Axis(title='Hour')),
            y=alt.Y('sum(traffic):Q', stack='zero', axis=alt.Axis(title='GB')),
            text=alt.Text('sum(traffic):Q')
        )


        mean_line = alt.Chart(traffic_by_hours_today).transform_aggregate(
            mean_traffic='mean(traffic)'
        ).mark_rule(color='lightblue', strokeDash=[10, 5], opacity=0.5).encode(
            y='mean(mean_traffic):Q'
        )

        st.altair_chart(bars+text+mean_line, use_container_width=True)


    # Renaming columns
    user_traffic_data = stat_by_users_today.rename(columns={"username": "Username", "total_traffic_gb": "Traffic (GB)", "connections": "Connections"})
    stat_by_users_last_hour = stat_by_users_last_hour.rename(columns={"username": "Username", "total_traffic_gb": "Traffic (GB)"})

    # Getting top 5 users by connections and traffic
    top5_connections = user_traffic_data.nlargest(5, 'Connections')[['Username', 'Connections']].reset_index(drop=True)
    top5_traffic = user_traffic_data.nlargest(5, 'Traffic (GB)')[['Username', 'Traffic (GB)']].reset_index(drop=True)
    # Getting top 5 users by traffic for last hour
    top5_last_hour_traffic = stat_by_users_last_hour.nlargest(5, 'Traffic (GB)')[['Username', 'Traffic (GB)']].reset_index(drop=True)

    st.subheader("Top 5 Users")

    col1, col2, col3 = st.columns(3)


    with col1:
        st.write("By connections per day")
        st.dataframe(top5_connections, use_container_width=True)


    with col2:
        st.write("By traffic per day")
        st.dataframe(top5_traffic, use_container_width=True)

    with col3:
        st.write("By traffic for last hour")
        st.dataframe(top5_last_hour_traffic, use_container_width=True)

    st.header("Statistics by nodes")

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
        ).properties(title='For all time')
        st.altair_chart(chart, use_container_width=True)

    with col2:
        chart = alt.Chart(today_data).mark_arc(innerRadius=50, outerRadius=100).encode(
            theta='used_traffic_gb',
            color='node',
            tooltip=['node', 'used_traffic_gb', 'percentage']
        ).properties(title='For today')
        st.altair_chart(chart, use_container_width=True)

    with col3:
        chart = alt.Chart(last_hour_data).mark_arc(innerRadius=50, outerRadius=100).encode(
            theta='used_traffic_gb',
            color='node',
            tooltip=['node', 'used_traffic_gb', 'percentage']
        ).properties(title='For last hour')
        st.altair_chart(chart, use_container_width=True)


    st.header("General statistics") 
    # Renaming columns
    df_all_dates = df_all_dates.rename(columns={
        "username": "Username",
        "cnt_connections": "Number of connections",
        "lifetime_days": "Lifetime (days)",
        "used_traffic": "Traffic (GB)"
    })


    # Generating tops and bottoms
    top_traffic = df_all_dates.nlargest(10, 'Traffic (GB)')[['Username', 'Traffic (GB)']]
    top_connections = df_all_dates.nlargest(10, 'Number of connections')[['Username', 'Number of connections']]
    top_lifetime = df_all_dates.nlargest(10, 'Lifetime (days)')[['Username', 'Lifetime (days)']]
    anti_top_traffic = df_all_dates.nsmallest(10, 'Traffic (GB)')[['Username', 'Traffic (GB)']]
    anti_top_connections = df_all_dates.nsmallest(10, 'Number of connections')[['Username', 'Number of connections']]
    anti_top_lifetime = df_all_dates.nsmallest(10, 'Lifetime (days)')[['Username', 'Lifetime (days)']]


    # Function for creating bar chart
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


    # Bar charts for top 10 users
    col3, col4, col5 = st.columns([1, 1, 1])

    with col3:
        st.write("Top 10 by traffic")
        st.altair_chart(create_bar_chart(top_traffic, 'Username', 'Traffic (GB)'), use_container_width=True)

    with col4:
        st.write("Top 10 by connections")
        st.altair_chart(create_bar_chart(top_connections, 'Username', 'Number of connections'), use_container_width=True)

    with col5:
        st.write("Top 10 by lifetime")
        st.altair_chart(create_bar_chart(top_lifetime, 'Username', 'Lifetime (days)'), use_container_width=True)
    # Columns for tops and bottoms
    col1, col2 = st.columns(2)

    # Top 5 users
    with col1:
        st.subheader("Top 10 Users")
        st.write("By traffic")
        st.dataframe(top_traffic, use_container_width=True)
        st.write("By connections")
        st.dataframe(top_connections, use_container_width=True)
        st.write("By lifetime")
        st.dataframe(top_lifetime, use_container_width=True)

    # Bottom 5 users  
    with col2:
        st.subheader("Bottom 10 Users")
        st.write("By traffic")
        st.dataframe(anti_top_traffic, use_container_width=True)
        st.write("By connections")
        st.dataframe(anti_top_connections, use_container_width=True)
        st.write("By lifetime")
        st.dataframe(anti_top_lifetime, use_container_width=True)




    with st.expander("Source data", expanded=False):
        st.dataframe(df, use_container_width=True)
        st.dataframe(df_last_hour_users, use_container_width=True)
        st.dataframe(df_users_by_hours, use_container_width=True)
        st.dataframe(stat_by_users_today, use_container_width=True)
        st.dataframe(traffic_by_users_last_hour, use_container_width=True)
        st.dataframe(df_all_dates, use_container_width=True)

# If incorrect login or password
elif authentication_status == False:
    st.error('Incorrect username/password')
    print("Error login or pass")
elif authentication_status == None:
    st.warning('Please enter your username and password')
