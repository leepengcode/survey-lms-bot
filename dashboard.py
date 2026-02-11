import streamlit as st
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Survey LMS Admin Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS ---
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { 
        background-color: black; 
        padding: 20px; 
        border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        padding: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #007bff; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- DATABASE LOGIC ---
@st.cache_resource
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            database=os.getenv("MYSQL_DATABASE"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
        )
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return None


@st.cache_data(ttl=60)
def fetch_survey_data():
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    # Query using school_name as per your SQL schema
    query = """
        SELECT 
            id, full_name, school_name, class_name, telegram_username, 
            question_1, question_2, question_3, question_4, question_5,
            question_6, question_7, question_8, question_9, question_10,
            created_at
        FROM survey_responses
        ORDER BY created_at DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# --- DASHBOARD UI ---
def main():
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.title("📊 Survey LMS Executive Dashboard")
        st.markdown(
            f"**Status:** 🟢 Connected | **Last Sync:** {datetime.now().strftime('%H:%M:%S')}"
        )

    st.sidebar.image(
        "https://cdn-icons-png.flaticon.com/512/3449/3449692.png", width=100
    )
    st.sidebar.title("Navigation & Filters")

    df = fetch_survey_data()

    if df.empty:
        st.info("Waiting for data submissions...")
        return

    # --- SIDEBAR FILTERS (Fixed Column Names) ---
    with st.sidebar:
        st.markdown("---")
        # Changed "school" -> "school_name"
        school_list = ["All Schools"] + sorted(
            df["school_name"].dropna().unique().tolist()
        )
        sel_school = st.selectbox("🏫 Select School", school_list)

        if sel_school != "All Schools":
            # Filter class list based on selected school_name
            class_list = ["All Classes"] + sorted(
                df[df["school_name"] == sel_school]["class_name"]
                .dropna()
                .unique()
                .tolist()
            )
        else:
            class_list = ["All Classes"] + sorted(
                df["class_name"].dropna().unique().tolist()
            )
        sel_class = st.selectbox("📚 Select Class", class_list)

        st.markdown("---")
        date_range = st.date_input(
            "📅 Date Range", [datetime.now() - timedelta(days=30), datetime.now()]
        )

    # --- FILTER LOGIC (Fixed Column Names) ---
    # Ensure date range is handled even if only one date is picked
    if len(date_range) == 2:
        mask = (df["created_at"].dt.date >= date_range[0]) & (
            df["created_at"].dt.date <= date_range[1]
        )
    else:
        mask = df["created_at"].dt.date == date_range[0]

    if sel_school != "All Schools":
        mask &= df["school_name"] == sel_school
    if sel_class != "All Classes":
        mask &= df["class_name"] == sel_class

    f_df = df[mask]

    # --- TOP KPI METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Submissions", len(f_df))
    m2.metric("Active Schools", f_df["school_name"].nunique())
    m3.metric("Engagement Rate", "100%")
    m4.metric(
        "Last Entry",
        f_df["created_at"].max().strftime("%m/%d %H:%M") if not f_df.empty else "N/A",
    )

    st.markdown("---")

    # --- ANALYTICS TABS ---
    tab_overview, tab_questions, tab_feedback = st.tabs(
        ["🏛️ Overview", "❓ Question Analysis", "💬 Text Feedback"]
    )

    with tab_overview:
        c1, c2 = st.columns(2)
        with c1:
            school_counts = f_df["school_name"].value_counts().reset_index()
            school_counts.columns = [
                "school_name",
                "count",
            ]  # Rename columns for plotly
            fig_school = px.pie(
                school_counts,
                names="school_name",
                values="count",
                hole=0.4,
                title="Participation by School",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            st.plotly_chart(fig_school, use_container_width=True)

        with c2:
            f_df["date"] = f_df["created_at"].dt.date
            timeline = f_df.groupby("date").size().reset_index(name="count")
            fig_time = px.area(
                timeline,
                x="date",
                y="count",
                title="Daily Submission Trend",
                line_shape="spline",
                color_discrete_sequence=["#007bff"],
            )
            st.plotly_chart(fig_time, use_container_width=True)

    with tab_questions:
        q_to_analyze = st.selectbox(
            "Select Question to Visualize", [f"question_{i}" for i in range(1, 10)]
        )
        q_data = f_df[q_to_analyze].value_counts().reset_index()
        q_data.columns = [q_to_analyze, "count"]
        fig_q = px.bar(
            q_data,
            x=q_to_analyze,
            y="count",
            color=q_to_analyze,
            title=f"Results for {q_to_analyze}",
        )
        st.plotly_chart(fig_q, use_container_width=True)

    with tab_feedback:
        st.subheader("💭 Open Feedback (Question 10)")
        # Fixed column name in filtering
        feedback_df = f_df[f_df["question_10"].str.len() > 0][
            ["full_name", "school_name", "question_10", "created_at"]
        ]
        if not feedback_df.empty:
            for _, row in feedback_df.iterrows():
                with st.expander(f"From: {row['full_name']} ({row['school_name']})"):
                    st.write(f"**Feedback:** {row['question_10']}")
                    st.caption(f"Submitted on: {row['created_at']}")
        else:
            st.write("No specific feedback provided yet.")

    # --- RAW DATA & EXPORT ---
    st.markdown("---")
    st.header("📋 Raw Data Explorer")

    search = st.text_input("🔍 Quick Search (Name or School)", "")
    if search:
        # Fixed "school" -> "school_name" in search filter
        f_df = f_df[
            f_df["full_name"].str.contains(search, case=False, na=False)
            | f_df["school_name"].str.contains(search, case=False, na=False)
        ]

    st.dataframe(f_df, use_container_width=True)

    st.download_button(
        label="📥 Download Full Report (CSV)",
        data=f_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"LMS_Report_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
