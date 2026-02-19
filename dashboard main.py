import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import plotly.express as px
from datetime import datetime, timedelta
import time

load_dotenv()

st.set_page_config(page_title="Survey LMS Dashboard", page_icon="📊", layout="wide")


# Create database connection string
def get_connection_string():
    """Create SQLAlchemy connection string"""
    return f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}?charset=utf8mb4"


@st.cache_data(ttl=60)
def fetch_data():
    """Fetch all survey responses with error handling and retry"""
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            engine = create_engine(
                get_connection_string(),
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": 10},
            )

            query = "SELECT * FROM survey_responses ORDER BY created_at DESC"
            df = pd.read_sql(query, engine)
            engine.dispose()
            return df

        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(
                    f"Retrying connection... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
            else:
                st.error(f"❌ Failed to connect: {e}")
                st.info("Check if MySQL is running: `docker ps`")
                return pd.DataFrame()


def main():
    st.title("📊 Survey LMS Dashboard")
    st.markdown("---")

    # Top controls
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

    # Connection status indicator
    with col2:
        try:
            from sqlalchemy import text

            engine = create_engine(
                get_connection_string(), connect_args={"connect_timeout": 10}
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            st.success("Connected")
            engine.dispose()
        except Exception as e:
            st.error(f"❌ DB Offline: {e}")
            st.stop()

    try:
        df = fetch_data()

        if df.empty:
            st.warning("No survey responses yet.")
            return

        # SIDEBAR FILTERS
        st.sidebar.header("🔍 Filters")

        # School filter
        schools = ["All"] + sorted(df["school_name"].unique().tolist())
        selected_school = st.sidebar.selectbox("School Name", schools)

        # Class filter
        classes = ["All"] + sorted(df["class_name"].unique().tolist())
        selected_class = st.sidebar.selectbox("Class", classes)

        # Computer usage filter
        computer_options = ["All", "ក. ធ្លាប់", "ខ. មិនធ្លាប់"]
        selected_computer = st.sidebar.selectbox(
            "Computer Experience", computer_options
        )

        # Date range
        st.sidebar.subheader("Date Range")
        date_option = st.sidebar.radio(
            "Select period:",
            ["All time", "Last 7 days", "Last 30 days", "Custom range"],
        )

        # APPLY FILTERS
        filtered_df = df.copy()

        if selected_school != "All":
            filtered_df = filtered_df[filtered_df["school_name"] == selected_school]

        if selected_class != "All":
            filtered_df = filtered_df[filtered_df["class_name"] == selected_class]

        if selected_computer != "All":
            filtered_df = filtered_df[
                filtered_df["computer_usage"] == selected_computer
            ]

        if date_option == "Last 7 days":
            cutoff_date = datetime.now() - timedelta(days=7)
            filtered_df = filtered_df[filtered_df["created_at"] >= cutoff_date]
        elif date_option == "Last 30 days":
            cutoff_date = datetime.now() - timedelta(days=30)
            filtered_df = filtered_df[filtered_df["created_at"] >= cutoff_date]
        elif date_option == "Custom range":
            col1, col2 = st.sidebar.columns(2)
            start_date = col1.date_input("From")
            end_date = col2.date_input("To")
            filtered_df = filtered_df[
                (filtered_df["created_at"].dt.date >= start_date)
                & (filtered_df["created_at"].dt.date <= end_date)
            ]

        # KEY METRICS
        st.header("📈 Key Metrics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Responses", len(filtered_df))

        with col2:
            no_computer = len(filtered_df[filtered_df["computer_usage"] == "ខ. មិនធ្លាប់"])
            st.metric("No Computer Experience", no_computer)

        with col3:
            st.metric("Schools", filtered_df["school_name"].nunique())

        with col4:
            if not filtered_df.empty:
                latest = filtered_df["created_at"].max()
                hours_ago = int((datetime.now() - latest).total_seconds() / 3600)
                st.metric("Latest Response", f"{hours_ago}h ago")

        st.markdown("---")

        # TABS
        tab1, tab2, tab3, tab4 = st.tabs(
            ["📊 Overview", "❓ Questions", "📅 Timeline", "🔍 Custom Queries"]
        )

        with tab1:
            col1, col2 = st.columns(2)

            with col1:
                # By School
                school_counts = filtered_df["school_name"].value_counts().reset_index()
                school_counts.columns = ["School", "Responses"]

                fig1 = px.bar(
                    school_counts,
                    x="School",
                    y="Responses",
                    title="Responses by School",
                    color="Responses",
                    color_continuous_scale="Blues",
                )
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                # Computer Usage
                computer_counts = (
                    filtered_df["computer_usage"].value_counts().reset_index()
                )
                computer_counts.columns = ["Experience", "Count"]

                fig2 = px.pie(
                    computer_counts,
                    names="Experience",
                    values="Count",
                    title="Computer Usage Distribution",
                )
                st.plotly_chart(fig2, use_container_width=True)

        with tab2:
            # Filter only those who answered questions
            answered_df = filtered_df[filtered_df["question_1"] != "N/A"]

            if len(answered_df) == 0:
                st.info("No responses with completed questions in current filter.")
            else:
                col1, col2 = st.columns(2)

                with col1:
                    q1_counts = answered_df["question_1"].value_counts().reset_index()
                    q1_counts.columns = ["Answer", "Count"]

                    fig = px.bar(
                        q1_counts, x="Answer", y="Count", title="Q1: Study Hours"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    q2_counts = answered_df["question_2"].value_counts().reset_index()
                    q2_counts.columns = ["Answer", "Count"]

                    fig = px.pie(
                        q2_counts,
                        names="Answer",
                        values="Count",
                        title="Q2: Learning Method",
                    )
                    st.plotly_chart(fig, use_container_width=True)

        with tab3:
            timeline_df = filtered_df.copy()
            timeline_df["date"] = timeline_df["created_at"].dt.date
            daily_counts = timeline_df.groupby("date").size().reset_index()
            daily_counts.columns = ["Date", "Responses"]

            fig = px.line(
                daily_counts,
                x="Date",
                y="Responses",
                title="Daily Responses",
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.subheader("Teachers Without Computer Experience")

            no_comp_df = filtered_df[filtered_df["computer_usage"] == "ខ. មិនធ្លាប់"]
            st.metric("Count", len(no_comp_df))

            if len(no_comp_df) > 0:
                st.dataframe(
                    no_comp_df[
                        ["full_name", "school_name", "class_name", "created_at"]
                    ],
                    use_container_width=True,
                )

            st.markdown("---")
            st.subheader("School vs Computer Usage Cross-Tab")

            cross_tab = pd.crosstab(
                filtered_df["school_name"], filtered_df["computer_usage"]
            )
            st.dataframe(cross_tab, use_container_width=True)

        # DATA TABLE
        st.markdown("---")
        st.header("📋 All Responses")

        search_term = st.text_input("🔎 Search by name, school, or class")

        if search_term:
            display_df = filtered_df[
                filtered_df["full_name"]
                .astype(str)
                .str.contains(search_term, case=False, na=False)
                | filtered_df["school_name"]
                .astype(str)
                .str.contains(search_term, case=False, na=False)
                | filtered_df["class_name"]
                .astype(str)
                .str.contains(search_term, case=False, na=False)
            ]
        else:
            display_df = filtered_df

        st.dataframe(display_df, use_container_width=True, height=400)

        # EXPORT
        st.markdown("---")
        col1, col2 = st.columns([1, 3])

        with col1:
            csv_data = display_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"survey_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
