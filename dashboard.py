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

# Determine DB credentials
try:
    # Streamlit Cloud secrets (if running on Streamlit Cloud)
    DB = st.secrets["mysql"]
except Exception:
    # Local development: use .env
    DB = {
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "host": os.getenv("MYSQL_HOST"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "database": os.getenv("MYSQL_DATABASE"),
    }


def get_connection_string():
    """Return SQLAlchemy connection string for MySQL."""
    return (
        f"mysql+pymysql://{DB['user']}:{DB['password']}"
        f"@{DB['host']}:{DB['port']}"
        f"/{DB['database']}?charset=utf8mb4"
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
            answered = filtered_df[filtered_df["question_1"] != "N/A"].copy()
            if len(answered) == 0:
                st.info("No completed responses in current filter.")
            else:
                # ── Valid answer choices only (filter out typos/garbage) ──────
                Q_VALID = {
                    "question_1": [
                        "ក. ចុច Start Menu → Microsoft Word",
                        "ខ. ចុច File -> ជ្រើសរើស New (ថ្មី) -> Blank Document",
                        "គ. ចុច File -> ជ្រើសរើស Save -> ដាក់ឈ្មោះឯកសារ -> Save",
                    ],
                    "question_2": [
                        "ក. ចុច File -> Save -> ដាក់ឈ្មោះឯកសារ -> Save ឬ Ctrl + S",
                        "ខ. ចុច Ctrl + S",
                        "គ. ចុច File → Save As -> ដាក់ឈ្មោះឯកសារ -> Save ឬ Ctrl + S",
                    ],
                    "question_3": [
                        "ក. ចុច File → Print (បោះពុម្ភ)",
                        "ខ. ចុច File → Open (បើក) -> ជ្រើសរើសឈ្មោះ -> Open",
                        "គ. Home → Save",
                    ],
                    "question_4": [
                        "ក. វាយអត្ថបទ",
                        "ខ. គណនា និងវិភាគទិន្នន័យ",
                        "គ. បង្កើតស្លាយ",
                    ],
                    "question_5": [
                        "ក. = Cell + Cell",
                        "ខ. = Cell - Cell",
                        "គ. = Cell + Cell ឬ =Sum(Cell:Cell)",
                    ],
                    "question_6": [
                        "ក. Login user",
                        "ខ. ចូលមើលវីដេអូមេរៀន",
                    ],
                    "question_7": [
                        "ក. មានតែវីដេអូ",
                        "ខ. វីដេអូ សង្ខេបមេរៀន និងរង្វាយតម្លៃ",
                        "គ. វីដេអូ សង្ខេបមេរៀន រង្វាយតម្លៃ និងកិច្ចការផ្ទះ",
                    ],
                    "question_8": [
                        "ក. ចេញពីសៀវភៅពុម្ពរបស់ក្រសួង",
                        "ខ. សៀវភៅពុម្ព EBC",
                        "គ. ចេញពីគ្រូល្បីៗ",
                    ],
                }

                Q_LABELS = {
                    "question_1": "Q1: បង្កើតឯកសារថ្មី",
                    "question_2": "Q2: រក្សាទុកការងារ",
                    "question_3": "Q3: បើកឯកសារ",
                    "question_4": "Q4: Excel ប្រើសម្រាប់អ្វី?",
                    "question_5": "Q5: រូបមន្តបូកលេខ Excel",
                    "question_6": "Q6: ចូលថ្នាល EBC",
                    "question_7": "Q7: ប្រភេទខ្លឹមសារ EBC",
                    "question_8": "Q8: ប្រភព​មេរៀន EBC",
                }

                CORRECT_LABEL = {
                    "question_1": "ខ. ចុច File -> ជ្រើសរើស New (ថ្មី) -> Blank Document",
                    "question_2": "គ. ចុច File → Save As -> ដាក់ឈ្មោះឯកសារ -> Save ឬ Ctrl + S",
                    "question_3": "ខ. ចុច File → Open (បើក) -> ជ្រើសរើសឈ្មោះ -> Open",
                    "question_4": "ខ. គណនា និងវិភាគទិន្នន័យ",
                    "question_5": "គ. = Cell + Cell ឬ =Sum(Cell:Cell)",
                    "question_6": "ក. Login user",
                    "question_7": "គ. វីដេអូ សង្ខេបមេរៀន រង្វាយតម្លៃ និងកិច្ចការផ្ទះ",
                    "question_8": "ក. ចេញពីសៀវភៅពុម្ពរបស់ក្រសួង",
                }

                # Show 2 questions per row
                q_keys = list(Q_VALID.keys())
                for i in range(0, len(q_keys), 2):
                    cols = st.columns(2)
                    for j, q in enumerate(q_keys[i : i + 2]):
                        with cols[j]:
                            valid_answers = Q_VALID[q]
                            # Filter to only valid choices
                            q_data = answered[answered[q].isin(valid_answers)]
                            counts = (
                                q_data[q]
                                .value_counts()
                                .reindex(valid_answers, fill_value=0)
                                .reset_index()
                            )
                            counts.columns = ["Answer", "Count"]
                            total_q = counts["Count"].sum()
                            counts["Percent"] = (
                                (counts["Count"] / total_q * 100).round(1)
                                if total_q > 0
                                else 0
                            )
                            counts["Color"] = counts["Answer"].apply(
                                lambda x: (
                                    "#4CAF50" if x == CORRECT_LABEL[q] else "#90CAF9"
                                )
                            )
                            counts["Label"] = counts["Answer"].str[
                                :40
                            ]  # shorten for axis

                            fig = px.bar(
                                counts,
                                x="Label",
                                y="Count",
                                title=Q_LABELS[q],
                                text=counts["Percent"].astype(str) + "%",
                                color="Answer",
                                color_discrete_map={
                                    row["Answer"]: (
                                        "#4CAF50"
                                        if row["Answer"] == CORRECT_LABEL[q]
                                        else "#90CAF9"
                                    )
                                    for _, row in counts.iterrows()
                                },
                            )
                            fig.update_traces(textposition="outside", showlegend=False)
                            fig.update_layout(
                                xaxis_title="",
                                yaxis_title="Count",
                                showlegend=False,
                                margin=dict(t=50, b=10),
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            st.caption(f"✅ Correct: **{CORRECT_LABEL[q]}**")

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
            # ── 1. School vs Computer Usage ───────────────────────────────────
            st.subheader("🏫 School vs Computer Usage")

            # Build clean cross-tab: only ក. ធ្លាប់ and ខ. មិនធ្លាប់ columns
            comp_yes = "ក. ធ្លាប់"
            comp_no = "ខ. មិនធ្លាប់"

            def school_computer_table(df_in):
                grp = (
                    df_in.groupby("school_name")["computer_usage"]
                    .value_counts()
                    .unstack(fill_value=0)
                )
                for col in [comp_yes, comp_no]:
                    if col not in grp.columns:
                        grp[col] = 0
                grp = grp[[comp_yes, comp_no]].copy()
                grp.index.name = "School Name"
                grp["Total"] = grp[comp_yes] + grp[comp_no]
                grp["% ធ្លាប់"] = (grp[comp_yes] / grp["Total"] * 100).round(1).astype(
                    str
                ) + "%"
                grp["% មិនធ្លាប់"] = (grp[comp_no] / grp["Total"] * 100).round(1).astype(
                    str
                ) + "%"
                grp = grp.reset_index()
                grp.columns = [
                    "School Name",
                    "ក. ធ្លាប់",
                    "ខ. មិនធ្លាប់",
                    "Total",
                    "% ធ្លាប់",
                    "% មិនធ្លាប់",
                ]
                return grp.sort_values("Total", ascending=False).reset_index(drop=True)

            comp_table = school_computer_table(filtered_df)
            st.dataframe(comp_table, use_container_width=True, hide_index=True)

            # Bar chart
            fig_comp = px.bar(
                comp_table,
                x="School Name",
                y=["ក. ធ្លាប់", "ខ. មិនធ្លាប់"],
                title="Computer Experience by School",
                barmode="stack",
                color_discrete_map={"ក. ធ្លាប់": "#2196F3", "ខ. មិនធ្លាប់": "#FF5722"},
            )
            fig_comp.update_layout(xaxis_tickangle=-30, legend_title="Experience")
            st.plotly_chart(fig_comp, use_container_width=True)

            # ── 2. Teachers Without Computer Experience ───────────────────────
            st.markdown("---")
            st.subheader("🙋 Teachers Without Computer Experience")
            no_comp = filtered_df[filtered_df["computer_usage"] == comp_no]
            st.metric("Count", len(no_comp))
            if len(no_comp) > 0:
                st.dataframe(
                    no_comp[["full_name", "school_name", "class_name", "created_at"]],
                    use_container_width=True,
                )

            # ── 3. Quiz Score per Teacher ─────────────────────────────────────
            st.markdown("---")
            st.subheader("📝 Quiz Score per Teacher (Q1–Q8)")
            st.caption(
                "Only teachers who have computer experience and answered questions are scored."
            )

            # Correct answers map
            CORRECT = {
                "question_1": "ខ. ចុច File -> ជ្រើសរើស New (ថ្មី) -> Blank Document",
                "question_2": "គ. ចុច File → Save As -> ដាក់ឈ្មោះឯកសារ -> Save ឬ Ctrl + S",
                "question_3": "ខ. ចុច File → Open (បើក) -> ជ្រើសរើសឈ្មោះ -> Open",
                "question_4": "ខ. គណនា និងវិភាគទិន្នន័យ",
                "question_5": "គ. = Cell + Cell ឬ =Sum(Cell:Cell)",
                "question_6": "ក. Login user",
                "question_7": "គ. វីដេអូ សង្ខេបមេរៀន រង្វាយតម្លៃ និងកិច្ចការផ្ទះ",
                "question_8": "ក. ចេញពីសៀវភៅពុម្ពរបស់ក្រសួង",
            }

            scored_df = filtered_df[filtered_df["question_1"] != "N/A"].copy()

            if scored_df.empty:
                st.info("No answered responses in current filter.")
            else:
                # Score each row
                for q, correct in CORRECT.items():
                    scored_df[f"{q}_correct"] = (
                        scored_df[q].str.strip() == correct.strip()
                    )

                scored_df["score"] = scored_df[[f"{q}_correct" for q in CORRECT]].sum(
                    axis=1
                )
                scored_df["score_pct"] = (
                    scored_df["score"] / len(CORRECT) * 100
                ).round(1)

                # ── Per-teacher score table ───────────────────────────────────
                score_cols = ["full_name", "school_name", "score", "score_pct"] + [
                    f"{q}_correct" for q in CORRECT
                ]
                score_display = scored_df[score_cols].copy()
                score_display.columns = ["ឈ្មោះ", "សាលា", "ពិន្ទុ (/ 8)", "ភាគរយ (%)"] + [
                    f"Q{i + 1}" for i in range(len(CORRECT))
                ]

                # Colour True/False
                def colour_bool(val):
                    if val is True:
                        return "background-color: #c8e6c9; color: #1b5e20"
                    elif val is False:
                        return "background-color: #ffcdd2; color: #b71c1c"
                    return ""

                bool_cols = [f"Q{i + 1}" for i in range(len(CORRECT))]
                st.dataframe(
                    score_display.style.applymap(colour_bool, subset=bool_cols),
                    use_container_width=True,
                    height=400,
                )

                # ── Score summary by school ───────────────────────────────────
                st.markdown("---")
                st.subheader("📊 Average Score by School")
                school_score = (
                    scored_df.groupby("school_name")
                    .agg(
                        Teachers=("score", "count"),
                        Avg_Score=("score", "mean"),
                        Avg_Pct=("score_pct", "mean"),
                    )
                    .round(1)
                    .reset_index()
                    .rename(
                        columns={
                            "school_name": "School Name",
                            "Avg_Score": "Avg Score (/ 8)",
                            "Avg_Pct": "Avg %",
                        }
                    )
                    .sort_values("Avg %", ascending=False)
                )
                st.dataframe(school_score, use_container_width=True, hide_index=True)

                fig_score = px.bar(
                    school_score,
                    x="School Name",
                    y="Avg %",
                    title="Average Quiz Score % by School",
                    color="Avg %",
                    color_continuous_scale="RdYlGn",
                    range_color=[0, 100],
                    text="Avg %",
                )
                fig_score.update_traces(texttemplate="%{text}%", textposition="outside")
                fig_score.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig_score, use_container_width=True)

            # ── 4. Q9 — How much has EBC helped? ─────────────────────────────
            st.markdown("---")
            st.subheader("📊 Q9: EBC ជួយការបង្រៀនប៉ុន្មានភាគរយ?")

            Q9_VALID = [
                "ក. ១០% ទៅ ៣០%",
                "ខ. ៤០% ទៅ ៦០%",
                "គ. ៧០% ទៅ ១០០%",
            ]
            Q9_COLORS = {
                "ក. ១០% ទៅ ៣០%": "#FF7043",
                "ខ. ៤០% ទៅ ៦០%": "#42A5F5",
                "គ. ៧០% ទៅ ១០០%": "#66BB6A",
            }

            # Filter: only rows with valid Q9 answer
            q9_df = filtered_df[filtered_df["question_9"].isin(Q9_VALID)].copy()

            if q9_df.empty:
                st.info("No valid Q9 responses in current filter.")
            else:
                q9_total = len(q9_df)
                q9_counts = (
                    q9_df["question_9"]
                    .value_counts()
                    .reindex(Q9_VALID, fill_value=0)
                    .reset_index()
                )
                q9_counts.columns = ["Answer", "Count"]
                q9_counts["Percent"] = (q9_counts["Count"] / q9_total * 100).round(1)

                # Metrics + pie side by side
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Overall Distribution**")
                    for _, row in q9_counts.iterrows():
                        st.metric(
                            label=row["Answer"],
                            value=f"{row['Count']} teachers",
                            delta=f"{row['Percent']}%",
                        )

                with col_b:
                    fig_q9 = px.pie(
                        q9_counts,
                        names="Answer",
                        values="Count",
                        title="Q9 Distribution",
                        color="Answer",
                        color_discrete_map=Q9_COLORS,
                    )
                    fig_q9.update_traces(textinfo="percent+value")
                    st.plotly_chart(fig_q9, use_container_width=True)

                # Bar chart overall
                fig_q9_bar = px.bar(
                    q9_counts,
                    x="Answer",
                    y="Count",
                    title="Q9 — Overall Count",
                    text=q9_counts["Percent"].astype(str) + "%",
                    color="Answer",
                    color_discrete_map=Q9_COLORS,
                )
                fig_q9_bar.update_traces(textposition="outside", showlegend=False)
                fig_q9_bar.update_layout(xaxis_title="", showlegend=False)
                st.plotly_chart(fig_q9_bar, use_container_width=True)

                # Q9 breakdown by school
                st.markdown("**Q9 Breakdown by School**")
                q9_school = (
                    q9_df.groupby(["school_name", "question_9"])
                    .size()
                    .unstack(fill_value=0)
                    .reset_index()
                )
                q9_school.columns.name = None
                for opt in Q9_VALID:
                    if opt not in q9_school.columns:
                        q9_school[opt] = 0
                q9_school = q9_school[["school_name"] + Q9_VALID].copy()
                q9_school["Total"] = q9_school[Q9_VALID].sum(axis=1)
                for opt in Q9_VALID:
                    q9_school[f"% {opt}"] = (
                        q9_school[opt] / q9_school["Total"] * 100
                    ).round(1).astype(str) + "%"
                q9_school = q9_school.rename(columns={"school_name": "School Name"})
                st.dataframe(q9_school, use_container_width=True, hide_index=True)

                fig_q9s = px.bar(
                    q9_school,
                    x="School Name",
                    y=Q9_VALID,
                    title="Q9 by School",
                    barmode="stack",
                    color_discrete_map=Q9_COLORS,
                )
                fig_q9s.update_layout(xaxis_tickangle=-30, legend_title="Q9 Answer")
                st.plotly_chart(fig_q9s, use_container_width=True)

            # ── 5. Unresolved school names (diagnostic) ───────────────────────
            st.markdown("---")
            with st.expander("🔀 Name Variants Merged / Unresolved (diagnostic)"):
                if "school_raw" in filtered_df.columns:
                    vdf = (
                        filtered_df[
                            filtered_df["school_raw"] != filtered_df["school_name"]
                        ][["school_raw", "school_name"]]
                        .drop_duplicates()
                        .rename(
                            columns={
                                "school_raw": "As Written",
                                "school_name": "Canonical",
                            }
                        )
                        .sort_values("Canonical")
                    )
                    if vdf.empty:
                        st.success("✅ No variants in current filter.")
                    else:
                        st.dataframe(vdf, use_container_width=True)

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
                        f"{len(unresolved)} unresolved — add in 🏫 School Mapping tab."
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
