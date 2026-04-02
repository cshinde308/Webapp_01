import streamlit as st
import streamlit as st
import json
from pathlib import Path
import pandas as pd


def init_styles():
    """Inject global CSS styles"""
    st.markdown("""
    <style>
    body {
        background-color: black;
        color: white;
    }

    .stApp {
        background-color: black;
    }

    input {
        background-color: transparent !important;
        color: white !important;
        border: 1px solid white !important;
    }

    button {
        background-color: #4da6ff !important;
        color: black !important;
        border-radius: 8px !important;
    }

    .canvas-container {
        min-height: 85vh;
        padding: 10px;
    }

    .fab-button {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 70px;
        height: 70px;
        border-radius: 50%;
        font-size: 36px;
        font-weight: bold;
        z-index: 1000;
    }

    .menu-bubble {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        font-size: 20px;
    }
    </style>
    """, unsafe_allow_html=True)


def init_session_state():
    """Initialize required session state variables"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "screen" not in st.session_state:
        st.session_state.screen = "login"

    if "menu_open" not in st.session_state:
        st.session_state.menu_open = False


def login_screen():
    st.markdown("<h2 style='text-align:center;'>Login</h2>", unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                if username == "admin" and password == "admin":
                    st.session_state.logged_in = True
                    st.session_state.screen = "canvas"
                    st.rerun()
                else:
                    st.error("Invalid credentials")


def run_gui():
    """
    Main Streamlit GUI router
    New layout: Login → Tab-based application
    """

    init_styles()
    init_session_state()

    # ---------- LOGIN ----------
    if not st.session_state.logged_in:
        login_screen()
        return

    # ---------- MAIN APP ----------
    st.title("🕒 Activity Tracker")

    tabs = st.tabs([
        "📝 Log Activity",
        "➕ Plus",
        "🗂 Screens",
        "⚙ Settings"
    ])

    # ---- Tab 1: Canvas / Log Activity ----
    with tabs[0]:
        canvas_screen()

    # ---- Tab 2: Plus Screen ----
    with tabs[1]:
        plus_screen()

    # ---- Tab 3: Generic Screens ----
    with tabs[2]:
        screen_name = st.selectbox(
            "Select Screen",
            ["screen_1", "screen_2", "screen_3"],
            key="generic_screen_select"
        )
        generic_screen(screen_name)

    # ---- Tab 4: Settings ----
    with tabs[3]:
        settings_screen()

import streamlit as st
import json
from pathlib import Path
import pandas as pd

def render_manage_projects(projects_json_path: Path):
    """
    Streamlit UI to Manage Projects with IFS codes
    """

    st.subheader("🛠 Manage Projects (IFS)")

    # ---------- Load data ----------
    if projects_json_path.exists():
        with open(projects_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    if not data:
        data = [{"name": "", "ifs": ""}]

    df = pd.DataFrame(data)

    # ---------- Editable table ----------
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn(
                "Project",
                required=True
            ),
            "ifs": st.column_config.TextColumn(
                "IFS"
            )
        },
        key="projects_editor"
    )

    st.markdown("### Actions")

    col1, col2, col3 = st.columns(3)

    # ---------- Add ----------
    with col1:
        if st.button("➕ Add"):
            edited_df.loc[len(edited_df)] = ["", ""]
            st.session_state.projects_editor = edited_df

    # ---------- Delete ----------
    with col2:
        delete_index = st.number_input(
            "Row to delete (index)",
            min_value=0,
            max_value=len(edited_df) - 1,
            step=1
        )
        if st.button("🗑 Delete"):
            edited_df = edited_df.drop(delete_index).reset_index(drop=True)
            st.session_state.projects_editor = edited_df

    # ---------- Save ----------
    with col3:
        if st.button("💾 Save"):
            clean = []
            seen = set()

            for _, row in edited_df.iterrows():
                name = str(row["name"]).strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                clean.append({
                    "name": name,
                    "ifs": str(row["ifs"]).strip()
                })

            with open(projects_json_path, "w", encoding="utf-8") as f:
                json.dump(clean, f, indent=2, ensure_ascii=False)

            st.success("✅ Projects saved successfully")