import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
import re
from typing import Dict  # Python 3.8 compatibility

load_dotenv()

st.set_page_config(page_title="Survey LMS Dashboard", page_icon="📊", layout="wide")


# ══════════════════════════════════════════════════════════════════════════════
#  SCHOOL NAME NORMALISATION ENGINE
#  ─────────────────────────────────────────────────────────────────────────
#  3-layer strategy:
#   1. Hard alias table  (built from every variant in your real SQL dump)
#   2. Zero-width / invisible-char stripping  (handles ZWSP embedded by phones)
#   3. "🏫 School Mapping" UI tab to add new aliases at runtime
# ══════════════════════════════════════════════════════════════════════════════

ALIAS_FILE = "school_aliases_custom.json"

# ─── canonical school names ───────────────────────────────────────────────────
C = {
    "chatumuk": "អនុវិទ្យាល័យចតុមុខ",
    "aranh": "អនុវិទ្យាល័យអរញ្ញរង្សី",
    "preakleab": "វិទ្យាល័យព្រែកលៀប",
    "preakdambang": "អនុវិទ្យាល័យព្រែកដំបង",
    "preahangdong": "វិទ្យាល័យព្រះអង្គឌួង",
    "ksachsa": "វិទ្យាល័យខ្សាច់ស",
    "sokhan_khvav": "វិទ្យាល័យសុខអានខ្វាវ",
    "sokhan_tonlap": "វិទ្យាល័យសុខអានទន្លាប់",
    "sokhan_tramknar": "វិទ្យាល័យសុខអានត្រាំខ្នារ",
    "sokhan_preysandaek": "វិទ្យាល័យសុខអានព្រៃសណ្តែក",
    "sokhan_doungkhpos": "វិទ្យាល័យសុខអានដូងខ្ពស់បូរីជលសារ",
    "hunsaen_sereipheap": "វិទ្យាល័យហ៊ុនសែនសេរីភាព",
    "hunsaen_1mithuna": "វិទ្យាល័យហ៊ុនសែន១មិថុនា",
    "bunrany": "វិទ្យាល័យបុណ្យរ៉ានីហ៊ុនសែនភ្នំជីសូរ",
    "haspveam": "វិទ្យាល័យហស ពាមជីកង",
    "lve": "អនុវិទ្យាល័យល្វេ",
}

# ─── alias table: every raw variant → canonical ───────────────────────────────
# ALL variants found in your live SQL dump are included.
SCHOOL_ALIASES_BUILTIN: Dict[str, str] = {
    # ══ អនុវិទ្យាល័យចតុមុខ ══════════════════════════════════════════════════
    "ឣនុវិទ្យាល័យចតុមុខ": C["chatumuk"],  # ឣ vs អ
    "អនុវិទ្យាល័យចតុមុខ": C["chatumuk"],
    "អនុវិទ្យាល័យ ចតុមុខ": C["chatumuk"],
    "អនុ. ចតុមុខ": C["chatumuk"],
    "អនុ.ចតុមុខ": C["chatumuk"],
    "អនុ ចតុមុខ": C["chatumuk"],
    "អនុចតុមុខ": C["chatumuk"],
    "អនុវ.ចតុមុខ": C["chatumuk"],
    "អនុវិ.ចតុមុខ": C["chatumuk"],
    "អនុវិទ្យាលយ័ចតុមុខ": C["chatumuk"],  # លយ័ typo
    "អនុវិឡាល័យចតុមុខ": C["chatumuk"],  # វិឡ typo
    "សាលា អនុវិទ្យាល័យ ចតុមុខ": C["chatumuk"],
    "សាលាអនុវិទ្យាល័យ ចតុមុខ": C["chatumuk"],
    "អនុវិទ្យាល័យ​ចតុមុខ": C["chatumuk"],  # ZWSP after ល័យ
    "អនុវិទ្យាល័យ​ចតុមុខ​": C["chatumuk"],  # trailing ZWSP too
    # ══ អនុវិទ្យាល័យអរញ្ញរង្សី ══════════════════════════════════════════════
    "អនុវិទ្យាល័យអរញ្ញរង្សី": C["aranh"],
    "អនុវិទ្យាល័យ អរញ្ញរង្សី": C["aranh"],
    "អនុវិទ្យាល៏យអរញ្ញរង្សី": C["aranh"],  # ល៏ typo
    "សាលាអនុវិទ្យាល័យអរញ្ញរង្សី": C["aranh"],
    "សាលាអនុវិទ្យាល័យអរញ្ញរង្ស៊ី": C["aranh"],  # ស៊ី variant
    "ARS": C["aranh"],  # abbreviation in DB
    # ══ វិទ្យាល័យព្រះអង្គឌួង ════════════════════════════════════════════════
    "វិទ្យាល័យព្រះអង្គឌួង": C["preahangdong"],
    "វិ.ព្រះអង្គឌួង": C["preahangdong"],
    "វិទ្យាល័យ ព្រះអង្គឌួង": C["preahangdong"],
    "វិទ្យាល័យព្រះ អង្គ ឌួង": C["preahangdong"],
    "វិទ្យាល័យព្រះ អង្គឌួង": C["preahangdong"],
    "វិទ្យាល័យព្រះអង្គឌូង": C["preahangdong"],  # ឌូ typo
    "វិទ្យាល័យព្រះអង្គឌួង(NGS)": C["preahangdong"],
    "វិទ្យាល័យព្រះអង្គឌួងកម្មវិធីជំនាន់ថ្មី": C["preahangdong"],
    "សាលារៀនជំនាន់ថ្មីព្រះអង្គឌួង": C["preahangdong"],
    "សាលាវិទ្យាល័យព្រះអង្គឌួង": C["preahangdong"],
    # ══ វិទ្យាល័យព្រែកលៀប ════════════════════════════════════════════════════
    "វិទ្យាល័យព្រែកលៀប": C["preakleab"],
    "វិទ្យាល័យ ព្រែកលៀប": C["preakleab"],
    "កម្មវិធីសាលារៀនជំនាន់ថ្មី វិទ្យាល័យ ព្រែកលៀប": C["preakleab"],
    "វិទ្យាល័យ​ជំនាន់ថ្មី​ព្រែកលៀប​": C["preakleab"],  # ZWSP chars
    # ══ អនុវិទ្យាល័យព្រែកដំបង ════════════════════════════════════════════════
    "អនុវិទ្យាល័យព្រែកដំបង": C["preakdambang"],
    "អនុវិទ្យាល័យ ព្រែកដំបង": C["preakdambang"],
    "សាលាអនុវិទ្យាល័យព្រែកដំបង": C["preakdambang"],
    "សាលាអនុវិទ្យាល័យ ព្រែកដំបង": C["preakdambang"],
    "អនុ.ព្រែកដំបង": C["preakdambang"],
    "អនុព្រែកដំបង": C["preakdambang"],
    "អនុព្រែកថំបង": C["preakdambang"],  # ថំ typo
    "អនុទ្យាល័យព្រែកដំបង": C["preakdambang"],  # missing វិ
    "អនុវិទ្យាលយ័ ព្រែកដំបង": C["preakdambang"],  # លយ័ typo
    "ឣនុវិទ្យាល័យព្រេកដំបង": C["preakdambang"],  # ព្រេ typo + ឣ
    # ══ វិទ្យាល័យខ្សាច់ស ═════════════════════════════════════════════════════
    "វិទ្យាល័យខ្សាច់ស": C["ksachsa"],
    "វិ.ខ្សាច់ស": C["ksachsa"],
    "វិទ្យាល័យ ខ្សាច់ស": C["ksachsa"],
    "វិទ្យាល័យ​ខ្សាច់ស": C["ksachsa"],  # ZWSP
    "វិទ្យាល័យ​ខ្សាច់​ស​": C["ksachsa"],  # multiple ZWSP
    "វិទ្យាល័យខ្សាច់ស​": C["ksachsa"],  # trailing ZWSP
    "សាលាវិទ្យាល័យខ្សាច់ស": C["ksachsa"],
    # ══ វិទ្យាល័យសុខអានខ្វាវ ════════════════════════════════════════════════
    "វិទ្យាល័យសុខអានខ្វាវ": C["sokhan_khvav"],
    "វិទ្យាល័យ សុខ អាន ខ្វាវ": C["sokhan_khvav"],
    "វិទ្យាល័យ សុខអាន ខ្វាវ": C["sokhan_khvav"],
    "វិទ្យាល័យ សុខអានខ្វាវ": C["sokhan_khvav"],
    "វិទ្យាល័យសុខអាន ខ្វាវ": C["sokhan_khvav"],
    "វិទ្យាល័យសុខ អានខ្វាវ": C["sokhan_khvav"],
    "វិទ្យាល័យ​សុខអានខ្វាវ": C["sokhan_khvav"],  # ZWSP
    "វិទ្យាល័យសុខអានខ្វា": C["sokhan_khvav"],  # missing វ
    # ══ វិទ្យាល័យសុខអានទន្លាប់ ══════════════════════════════════════════════
    "វិទ្យាល័យសុខអានទន្លាប់": C["sokhan_tonlap"],
    "វិទ្យាល័យ សុខ អាន ទន្លាប់": C["sokhan_tonlap"],
    "វិទ្យាល័យ សុខអានទន្លាប់": C["sokhan_tonlap"],
    "វិទ្យាល័យ សុខអាន ទន្លាប់": C["sokhan_tonlap"],
    # ══ វិទ្យាល័យសុខអានត្រាំខ្នារ ═══════════════════════════════════════════
    "វិទ្យាល័យសុខអានត្រាំខ្នារ": C["sokhan_tramknar"],
    "វិទ្យាល័យ សុខអានត្រាំខ្នារ": C["sokhan_tramknar"],
    "វិទ្យាល័យសុខ អានត្រាំខ្នារ": C["sokhan_tramknar"],
    "វិទ្យាលយ័សុខអានត្រាំខ្នារ": C["sokhan_tramknar"],  # លយ័ typo
    # ══ វិទ្យាល័យហ៊ុនសែនសេរីភាព ════════════════════════════════════════════
    "វិទ្យាល័យហ៊ុនសែនសេរីភាព": C["hunsaen_sereipheap"],
    "វិទ្យាល័យ ហ៊ុន សែន សេរីភាព": C["hunsaen_sereipheap"],
    "វិទ្យាល័យ ហ៊ុនសែនសេរីភាព": C["hunsaen_sereipheap"],
    "វិទ្យាល័យហ៊ុន សែនសេរីភាព": C["hunsaen_sereipheap"],
    "វិទ្យាលយ័ហ៊ុនសែនសេរីភាព": C["hunsaen_sereipheap"],  # លយ័ typo
    "វិទ្យាល័យ​ហ៊ុន​សែន​សេរីភាព​": C["hunsaen_sereipheap"],  # ZWSP
    "សាលាវិទ្យាល័យ​ ហ៊ុនសែន​ សេរីភាព​": C["hunsaen_sereipheap"],
    # ══ Single-entry schools ══════════════════════════════════════════════════
    "វិទ្យាល័យហ៊ុនសែន១មិថុនា": C["hunsaen_1mithuna"],
    "វិទ្យាល័យប៑ុនរ៉ានីហ៑ុនសែនភ្នំជីសូរ": C["bunrany"],
    "វិទ្យាល័យ​ ហស​ ពាមជីកង": C["haspveam"],
    "វិទ្យាល័យ សុខ អានព្រៃសណ្តែក": C["sokhan_preysandaek"],
    "វិទ្យាល័យ សុខ អាន ដូងខ្ពស់បូរីជលសារ": C["sokhan_doungkhpos"],
    "អនុវិទ្យាល័យល្វេ": C["lve"],
}


# ──────────────────────────────────────────────────────────────────────────────
#  Normalisation helpers
# ──────────────────────────────────────────────────────────────────────────────
_INVISIBLE = re.compile(
    r"[\u200b\u200c\u200d\u00ad\ufeff\u2060\u180e\u2028\u2029]",
    re.UNICODE,
)


def strip_invisible(text: str) -> str:
    """Remove zero-width and other invisible Unicode characters."""
    return _INVISIBLE.sub("", text)


def normalize_key(text: str) -> str:
    """
    Lookup key: strip invisible chars, collapse ALL whitespace to nothing,
    lower-case. This collapses space variants and ZWSP in one step.
    """
    if not isinstance(text, str):
        return str(text)
    return re.sub(r"\s+", "", strip_invisible(text)).lower()


def load_custom_aliases() -> dict:
    if os.path.exists(ALIAS_FILE):
        try:
            with open(ALIAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_custom_aliases(aliases: dict):
    with open(ALIAS_FILE, "w", encoding="utf-8") as f:
        json.dump(aliases, f, ensure_ascii=False, indent=2)


def get_all_aliases() -> dict:
    merged = dict(SCHOOL_ALIASES_BUILTIN)
    merged.update(load_custom_aliases())
    return merged


def build_fast_lookup(alias_map: dict) -> dict:
    return {normalize_key(k): v for k, v in alias_map.items()}


def resolve_school(raw: str, fast_lookup: dict, alias_map: dict) -> str:
    if not isinstance(raw, str):
        return str(raw)
    # 1. exact match (fastest)
    if raw in alias_map:
        return alias_map[raw]
    # 2. space / ZWSP stripped match
    key = normalize_key(raw)
    if key in fast_lookup:
        return fast_lookup[key]
    # 3. fallback: at least strip invisible chars & tidy whitespace
    return re.sub(r"\s+", " ", strip_invisible(raw).strip())


def apply_normalization(df: pd.DataFrame) -> pd.DataFrame:
    alias_map = get_all_aliases()
    fast_lookup = build_fast_lookup(alias_map)
    df = df.copy()
    df["school_raw"] = df["school_name"]  # keep original for audit
    df["school_name"] = df["school_name"].apply(
        lambda x: resolve_school(x, fast_lookup, alias_map)
    )
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════════════════════════════════════


def get_connection_string():
    return (
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
        f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}"
        f"/{os.getenv('MYSQL_DATABASE')}?charset=utf8mb4"
    )


@st.cache_data(ttl=60)
def fetch_data():
    max_retries, retry_delay = 3, 2
    for attempt in range(max_retries):
        try:
            engine = create_engine(
                get_connection_string(),
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": 10},
            )
            df = pd.read_sql(
                "SELECT * FROM survey_responses ORDER BY created_at DESC", engine
            )
            engine.dispose()
            df = apply_normalization(df)  # ← normalise immediately after fetch
            return df
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"Retrying… ({attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                st.error(f"❌ Failed to connect: {e}")
                st.info("Check if MySQL is running: `docker ps`")
                return pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════


def main():
    st.title("📊 Survey LMS Dashboard")
    st.markdown("---")

    col1, col2, _ = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        try:
            from sqlalchemy import text

            engine = create_engine(
                get_connection_string(), connect_args={"connect_timeout": 10}
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            st.success("✅ Connected")
            engine.dispose()
        except Exception as e:
            st.error(f"❌ DB Offline: {e}")
            st.stop()

    try:
        df = fetch_data()
        if df.empty:
            st.warning("No survey responses yet.")
            return

        # ── SIDEBAR ───────────────────────────────────────────────────────────
        st.sidebar.header("🔍 Filters")

        # School dropdown uses canonical names → no duplicates
        schools = ["All"] + sorted(df["school_name"].unique().tolist())
        selected_school = st.sidebar.selectbox("School Name", schools)
        classes = ["All"] + sorted(df["class_name"].unique().tolist())
        selected_class = st.sidebar.selectbox("Class", classes)
        computer_options = ["All", "ក. ធ្លាប់", "ខ. មិនធ្លាប់"]
        selected_computer = st.sidebar.selectbox(
            "Computer Experience", computer_options
        )

        st.sidebar.subheader("Date Range")
        date_option = st.sidebar.radio(
            "Select period:",
            ["All time", "Last 7 days", "Last 30 days", "Custom range"],
        )

        # ── APPLY FILTERS ─────────────────────────────────────────────────────
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
            filtered_df = filtered_df[
                filtered_df["created_at"] >= datetime.now() - timedelta(days=7)
            ]
        elif date_option == "Last 30 days":
            filtered_df = filtered_df[
                filtered_df["created_at"] >= datetime.now() - timedelta(days=30)
            ]
        elif date_option == "Custom range":
            c1, c2 = st.sidebar.columns(2)
            start_date = c1.date_input("From")
            end_date = c2.date_input("To")
            filtered_df = filtered_df[
                (filtered_df["created_at"].dt.date >= start_date)
                & (filtered_df["created_at"].dt.date <= end_date)
            ]

        # ── KEY METRICS ───────────────────────────────────────────────────────
        st.header("📈 Key Metrics")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Responses", len(filtered_df))
        with m2:
            no_computer = len(filtered_df[filtered_df["computer_usage"] == "ខ. មិនធ្លាប់"])
            st.metric("No Computer Experience", no_computer)
        with m3:
            st.metric("Schools (unique)", filtered_df["school_name"].nunique())
        with m4:
            if not filtered_df.empty:
                latest = filtered_df["created_at"].max()
                hours_ago = int((datetime.now() - latest).total_seconds() / 3600)
                st.metric("Latest Response", f"{hours_ago}h ago")

        st.markdown("---")

        # ── TABS ──────────────────────────────────────────────────────────────
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "📊 Overview",
                "❓ Questions",
                "📅 Timeline",
                "🔍 Custom Queries",
                "🏫 School Mapping",
            ]
        )

        # TAB 1 ───────────────────────────────────────────────────────────────
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                sc = filtered_df["school_name"].value_counts().reset_index()
                sc.columns = ["School", "Responses"]
                fig = px.bar(
                    sc,
                    x="School",
                    y="Responses",
                    title="Responses by School (duplicates merged)",
                    color="Responses",
                    color_continuous_scale="Blues",
                )
                fig.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                cc = filtered_df["computer_usage"].value_counts().reset_index()
                cc.columns = ["Experience", "Count"]
                st.plotly_chart(
                    px.pie(
                        cc,
                        names="Experience",
                        values="Count",
                        title="Computer Usage Distribution",
                    ),
                    use_container_width=True,
                )

        # TAB 2 ───────────────────────────────────────────────────────────────
        with tab2:
            answered = filtered_df[filtered_df["question_1"] != "N/A"]
            if len(answered) == 0:
                st.info("No completed responses in current filter.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    q1 = answered["question_1"].value_counts().reset_index()
                    q1.columns = ["Answer", "Count"]
                    st.plotly_chart(
                        px.bar(q1, x="Answer", y="Count", title="Q1: Study Hours"),
                        use_container_width=True,
                    )
                with col2:
                    q2 = answered["question_2"].value_counts().reset_index()
                    q2.columns = ["Answer", "Count"]
                    st.plotly_chart(
                        px.pie(
                            q2,
                            names="Answer",
                            values="Count",
                            title="Q2: Learning Method",
                        ),
                        use_container_width=True,
                    )

        # TAB 3 ───────────────────────────────────────────────────────────────
        with tab3:
            tl = filtered_df.copy()
            tl["date"] = tl["created_at"].dt.date
            daily = tl.groupby("date").size().reset_index()
            daily.columns = ["Date", "Responses"]
            st.plotly_chart(
                px.line(
                    daily,
                    x="Date",
                    y="Responses",
                    title="Daily Responses",
                    markers=True,
                ),
                use_container_width=True,
            )

        # TAB 4 ───────────────────────────────────────────────────────────────
        with tab4:
            st.subheader("Teachers Without Computer Experience")
            no_comp = filtered_df[filtered_df["computer_usage"] == "ខ. មិនធ្លាប់"]
            st.metric("Count", len(no_comp))
            if len(no_comp) > 0:
                st.dataframe(
                    no_comp[["full_name", "school_name", "class_name", "created_at"]],
                    use_container_width=True,
                )

            st.markdown("---")
            st.subheader("School vs Computer Usage Cross-Tab")
            st.dataframe(
                pd.crosstab(filtered_df["school_name"], filtered_df["computer_usage"]),
                use_container_width=True,
            )

            st.markdown("---")
            st.subheader("🔀 Name Variants Merged")
            st.caption("Every raw name that was mapped to a canonical name.")
            if "school_raw" in filtered_df.columns:
                vdf = (
                    filtered_df[
                        filtered_df["school_raw"] != filtered_df["school_name"]
                    ][["school_raw", "school_name"]]
                    .drop_duplicates()
                    .rename(
                        columns={
                            "school_raw": "As Written by Teacher",
                            "school_name": "Canonical Name",
                        }
                    )
                    .sort_values("Canonical Name")
                )
                if vdf.empty:
                    st.success("✅ No variants in current filter.")
                else:
                    st.dataframe(vdf, use_container_width=True)

            st.markdown("---")
            st.subheader("⚠️ Unresolved School Names")
            st.caption("Names not in any alias table — go to 🏫 School Mapping to fix.")
            all_canonical = set(get_all_aliases().values())
            unresolved = (
                filtered_df[~filtered_df["school_name"].isin(all_canonical)][
                    "school_name"
                ]
                .value_counts()
                .reset_index()
            )
            unresolved.columns = ["School Name", "Count"]
            if unresolved.empty:
                st.success("✅ All school names resolved.")
            else:
                st.warning(
                    f"{len(unresolved)} unresolved name(s). Add them in 🏫 School Mapping."
                )
                st.dataframe(unresolved, use_container_width=True)

        # TAB 5 ───────────────────────────────────────────────────────────────
        with tab5:
            st.subheader("🏫 School Name Alias Manager")
            st.info(
                "When a teacher writes a school name in a new way, add it here.  \n"
                "Changes take effect after **🔄 Refresh Data**."
            )

            custom_aliases = load_custom_aliases()

            with st.form("add_alias_form", clear_on_submit=True):
                st.markdown("**➕ Add New Alias**")
                c1, c2 = st.columns(2)
                new_raw = c1.text_input(
                    "Alias (as typed by teacher)", placeholder="e.g. វិ.ខ្សាច់ ស"
                )
                new_canonical = c2.text_input(
                    "Canonical (official) name", placeholder="e.g. វិទ្យាល័យខ្សាច់ស"
                )
                if st.form_submit_button("✅ Save Alias"):
                    if new_raw.strip() and new_canonical.strip():
                        custom_aliases[new_raw.strip()] = new_canonical.strip()
                        save_custom_aliases(custom_aliases)
                        st.cache_data.clear()
                        st.success(f"Saved: **{new_raw}** → **{new_canonical}**")
                        st.rerun()
                    else:
                        st.warning("Both fields are required.")

            st.markdown("---")
            st.markdown("**📋 Your Custom Aliases**")
            if custom_aliases:
                ca_df = pd.DataFrame(
                    list(custom_aliases.items()),
                    columns=["Alias (Raw)", "Canonical Name"],
                )
                st.dataframe(ca_df, use_container_width=True)
                del_key = st.selectbox(
                    "Select alias to delete",
                    ["— none —"] + list(custom_aliases.keys()),
                )
                if st.button("🗑️ Delete") and del_key != "— none —":
                    del custom_aliases[del_key]
                    save_custom_aliases(custom_aliases)
                    st.cache_data.clear()
                    st.success(f"Deleted: {del_key}")
                    st.rerun()
            else:
                st.caption("No custom aliases yet.")

            st.markdown("---")
            st.markdown("**📚 Built-in Alias Table (from code)**")
            builtin_df = pd.DataFrame(
                sorted(SCHOOL_ALIASES_BUILTIN.items(), key=lambda x: x[1]),
                columns=["Alias (Raw)", "Canonical Name"],
            )
            st.dataframe(builtin_df, use_container_width=True)

        # ── DATA TABLE ────────────────────────────────────────────────────────
        st.markdown("---")
        st.header("📋 All Responses")

        search = st.text_input("🔎 Search by name, school, or class")
        if search:
            display_df = filtered_df[
                filtered_df["full_name"]
                .astype(str)
                .str.contains(search, case=False, na=False)
                | filtered_df["school_name"]
                .astype(str)
                .str.contains(search, case=False, na=False)
                | filtered_df["school_raw"]
                .astype(str)
                .str.contains(search, case=False, na=False)
                | filtered_df["class_name"]
                .astype(str)
                .str.contains(search, case=False, na=False)
            ]
        else:
            display_df = filtered_df

        st.dataframe(display_df, use_container_width=True, height=400)

        # ── EXPORT ────────────────────────────────────────────────────────────
        st.markdown("---")
        col_dl, _ = st.columns([1, 3])
        with col_dl:
            csv = display_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"survey_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Error: {e}")
        st.exception(e)


if __name__ == "__main__":
    main()
