import streamlit as st
from datetime import datetime, timedelta, date
from pathlib import Path
import json
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment
from io import BytesIO

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Activity Tracker",
    page_icon="🕒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= PATHS =================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

EXCEL_FILE = DATA_DIR / "activity_log.xlsx"
PROJECTS_FILE = DATA_DIR / "projects.json"
ENGINEERS_FILE = DATA_DIR / "Engineers.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

# ================= DEFAULT DATA =================
DEFAULT_PROJECTS = [
    {"name": "Project-1", "ifs": ""},
    {"name": "Project-2", "ifs": ""},
    {"name": "Project-3", "ifs": ""},
]

DEFAULT_ENGINEERS = [
    "Engineer-1", "Engineer-2", "Engineer-3",
    "Engineer-4", "Engineer-5",
]

# ================= FILE INITIALIZATION =================
def ensure_files():
    if not EXCEL_FILE.exists():
        wb = Workbook()
        ws = wb.active
        ws.title = "Log"
        ws.append(["Date", "Time", "Project", "Engineer", "Hours", "Note"])
        wb.save(EXCEL_FILE)
        wb.close()

    if not PROJECTS_FILE.exists():
        json.dump(DEFAULT_PROJECTS, open(PROJECTS_FILE, "w"), indent=2)

    if not ENGINEERS_FILE.exists():
        json.dump(DEFAULT_ENGINEERS, open(ENGINEERS_FILE, "w"), indent=2)

    if not SETTINGS_FILE.exists():
        json.dump({"popup_min": 5}, open(SETTINGS_FILE, "w"), indent=2)

ensure_files()

# ================= LOAD DATA =================
projects = json.load(open(PROJECTS_FILE))
engineers = json.load(open(ENGINEERS_FILE))
settings = json.load(open(SETTINGS_FILE))

proj_names = [p["name"] for p in projects]
proj_map = {p["name"]: p.get("ifs", "") for p in projects}

# ================= HELPERS =================
def parse_excel_date(val):
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None

def create_weekly_summary_excel(records):
    wb = Workbook()
    ws = wb.active
    ws.title = "Weekly Summary"
    ws.append(["Date", "Time", "Project", "Engineer", "Hours", "Note"])

    for r in records:
        ws.append([
            r["date"].strftime("%Y-%m-%d"),
            r["time"],
            r["project"],
            r["engineer"],
            r["hours"],
            r["note"]
        ])
        ws[f"F{ws.max_row}"].alignment = Alignment(wrap_text=True)

    return wb

def append_weekly_summary(records):
    wb = load_workbook(EXCEL_FILE)
    name = f"Weekly_Summary_{datetime.now():%Y%m%d_%H%M}"
    ws = wb.create_sheet(name)
    ws.append(["Date", "Time", "Project", "Engineer", "Hours", "Note"])

    for r in records:
        ws.append([
            r["date"].strftime("%Y-%m-%d"),
            r["time"],
            r["project"],
            r["engineer"],
            r["hours"],
            r["note"]
        ])
        ws[f"F{ws.max_row}"].alignment = Alignment(wrap_text=True)

    wb.save(EXCEL_FILE)
    wb.close()

# ================= WIZARDS =================
def manage_projects_wizard():
    st.subheader("🛠 Manage Projects (IFS)")
    df = pd.DataFrame(projects)

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Save Projects"):
        clean = (
            edited.dropna(subset=["name"])
            .drop_duplicates(subset=["name"])
            .to_dict("records")
        )
        json.dump(clean, open(PROJECTS_FILE, "w"), indent=2)
        st.success("Projects saved")
        st.rerun()

def manage_engineers_wizard():
    st.subheader("👷 Manage Engineers")
    df = pd.DataFrame(engineers, columns=["Engineer"])

    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Save Engineers"):
        clean = (
            edited["Engineer"]
            .dropna()
            .drop_duplicates()
            .tolist()
        )
        json.dump(clean, open(ENGINEERS_FILE, "w"), indent=2)
        st.success("Engineers saved")
        st.rerun()

# ================= SIDEBAR =================

st.sidebar.title("RA_Toolbox")
st.sidebar.caption("Tools Collection")
st.sidebar.divider()

page = st.sidebar.radio("Tools List:", ["Activity Tracker","Page-2"])

# ================= MAIN PAGE =================
if page == "Activity Tracker":
    tab_log, tab_today, tab_summary, tab_settings = st.tabs(
        ["📝 Log Activity", "📅 Today", "📊 Summary", "⚙ Settings"]
    )

    # ---------- LOG ----------
    with tab_log:
        project = st.selectbox("Project", proj_names)
        engineer = st.selectbox("Engineer", engineers)
        st.info(f"IFS Code: {proj_map.get(project, 'Not Set')}")

        hours = st.number_input("Hours", 0.0, 24.0, step=0.25)
        note = st.text_area("Activity Note")

        if st.button("✅ Submit"):
            wb = load_workbook(EXCEL_FILE)
            ws = wb["Log"]
            now = datetime.now()
            ws.append([
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S"),
                project,
                engineer,
                hours,
                note
            ])
            ws[f"F{ws.max_row}"].alignment = Alignment(wrap_text=True)
            wb.save(EXCEL_FILE)
            wb.close()
            st.success("Activity saved")

    # ---------- TODAY ----------
    with tab_today:
        st.subheader("Today's Activity Details")

        # ---- View Mode Selector ----
        view_mode = st.radio(
            "View activities by",
            ["Date-wise", "Engineer-wise", "Project-wise"],
            horizontal=True
        )

        wb = load_workbook(EXCEL_FILE, read_only=True)
        ws = wb["Log"]

        today = datetime.now().date()
        records = []
        total_hours = 0.0

        # ---- Collect today's records ----
        for r in ws.iter_rows(min_row=2, values_only=True):
            if parse_excel_date(r[0]) == today:
                hours = float(r[4]) if r[4] else 0.0
                total_hours += hours

                records.append({
                    "time": r[1][:5] if r[1] else "--:--",
                    "project": r[2] or "N/A",
                    "engineer": r[3] or "N/A",
                    "hours": hours,
                    "note": r[5] or ""
                })

        wb.close()

        # ---- No data case (DO NOT stop the app) ----
        if not records:
            st.info("No activity logged today.")
        else:
            st.divider()

            # =====================================================
            # DATE‑WISE VIEW
            # =====================================================
            if view_mode == "Date-wise":
                st.subheader("Date‑wise Activity View")

                records.sort(key=lambda x: x["time"])

                for r in records:
                    st.write(
                        f"⏱ {r['time']}  |  "
                        f"📌 {r['project']}  |  "
                        f"👷 {r['engineer']}  |  "
                        f"⏳ {r['hours']:.2f} h"
                    )

                    st.caption(
                        f"📝 {r['note']}" if r["note"] else "📝 No notes provided"
                    )

                    st.divider()

            # =====================================================
            # ENGINEER‑WISE VIEW
            # =====================================================
            elif view_mode == "Engineer-wise":
                st.subheader("Engineer‑wise Activity View")

                grouped = {}
                for r in records:
                    grouped.setdefault(r["engineer"], []).append(r)

                for engineer, items in grouped.items():
                    engineer_total = sum(x["hours"] for x in items)

                    with st.expander(f"{engineer} — Total {engineer_total:.2f} h"):
                        for x in items:
                            st.write(
                                f"⏱ {x['time']}  |  "
                                f"📌 {x['project']}  |  "
                                f"⏳ {x['hours']:.2f} h"
                            )
                            st.caption(
                                f"📝 {x['note']}" if x["note"] else "📝 No notes provided"
                            )
                            st.divider()

            # =====================================================
            # PROJECT‑WISE VIEW
            # =====================================================
            elif view_mode == "Project-wise":
                st.subheader("Project‑wise Activity View")

                grouped = {}
                for r in records:
                    grouped.setdefault(r["project"], []).append(r)

                for project, items in grouped.items():
                    project_total = sum(x["hours"] for x in items)

                    with st.expander(f"{project} — Total {project_total:.2f} h"):
                        for x in items:
                            st.write(
                                f"⏱ {x['time']}  |  "
                                f"👷 {x['engineer']}  |  "
                                f"⏳ {x['hours']:.2f} h"
                            )
                            st.caption(
                                f"📝 {x['note']}" if x["note"] else "📝 No notes provided"
                            )
                            st.divider()

            # ---- Daily Total (SAFE position) ----
            st.success(f"✅ Total Hours Today = {total_hours:.2f}")

    # ---------- WEEK ----------
    with tab_summary:
        # Generate Summary
        st.subheader("Generate Summary")

        # ---- Date Range ----
        col1, col2 = st.columns(2)
        start = col1.date_input("Start Date")
        end = col2.date_input("End Date", start + timedelta(days=6))

        # ---- Summary Type ----
        summary_type = st.radio(
            "Summary Type",
            ["Date-wise", "Engineer-wise", "Project-wise"],
            horizontal=True
        )

        st.divider()

        # ---- Filters ----
        pf, ef = st.columns(2)
        selected_projects = pf.multiselect(
            "Select Project(s)",
            proj_names,
            default=proj_names
        )
        selected_engineers = ef.multiselect(
            "Select Engineer(s)",
            engineers,
            default=engineers
        )

        st.divider()

        # ---- Generate Summary ----
        if st.button("📊 Generate Summary"):
            wb = load_workbook(EXCEL_FILE, read_only=True)
            ws = wb["Log"]
            records = []

            for r in ws.iter_rows(min_row=2, values_only=True):
                d = parse_excel_date(r[0])
                if not d or not (start <= d <= end):
                    continue

                if r[2] not in selected_projects:
                    continue
                if r[3] not in selected_engineers:
                    continue

                records.append({
                    "date": d,
                    "time": r[1][:5] if r[1] else "--:--",
                    "project": r[2],
                    "engineer": r[3],
                    "hours": float(r[4]) if r[4] else 0.0,
                    "note": r[5] or ""
                })

            wb.close()
            st.session_state.weekly = records

        records = st.session_state.get("weekly", [])

        if not records:
            st.info("No data found for selected filters.")
        else:
            st.divider()

            # =====================================================
            # DATE‑WISE VIEW
            # =====================================================
            if summary_type == "Date-wise":
                grouped = {}
                for r in records:
                    grouped.setdefault(r["date"], []).append(r)

                for d, items in sorted(grouped.items()):
                    day_total = sum(x["hours"] for x in items)
                    with st.expander(f"{d} — Total {day_total:.2f} h"):
                        items.sort(key=lambda x: x["time"])
                        for x in items:
                            st.write(
                                f"⏱ {x['time']}  |  "
                                f"📌 {x['project']}  |  "
                                f"👷 {x['engineer']}  |  "
                                f"⏳ {x['hours']:.2f} h"
                            )
                            st.caption(
                                f"📝 {x['note']}" if x["note"] else "📝 No notes provided"
                            )
                            st.divider()

            # =====================================================
            # ENGINEER‑WISE VIEW
            # =====================================================
            elif summary_type == "Engineer-wise":
                grouped = {}
                for r in records:
                    grouped.setdefault(r["engineer"], []).append(r)

                for engineer, items in grouped.items():
                    eng_total = sum(x["hours"] for x in items)
                    with st.expander(f"{engineer} — Total {eng_total:.2f} h"):
                        for x in items:
                            st.write(
                                f"🗓 {x['date']}  |  "
                                f"⏱ {x['time']}  |  "
                                f"📌 {x['project']}  |  "
                                f"⏳ {x['hours']:.2f} h"
                            )
                            st.caption(
                                f"📝 {x['note']}" if x["note"] else "📝 No notes provided"
                            )
                            st.divider()

            # =====================================================
            # PROJECT‑WISE VIEW
            # =====================================================
            elif summary_type == "Project-wise":
                grouped = {}
                for r in records:
                    grouped.setdefault(r["project"], []).append(r)

                for project, items in grouped.items():
                    proj_total = sum(x["hours"] for x in items)
                    with st.expander(f"{project} — Total {proj_total:.2f} h"):
                        for x in items:
                            st.write(
                                f"🗓 {x['date']}  |  "
                                f"⏱ {x['time']}  |  "
                                f"👷 {x['engineer']}  |  "
                                f"⏳ {x['hours']:.2f} h"
                            )
                            st.caption(
                                f"📝 {x['note']}" if x["note"] else "📝 No notes provided"
                            )
                            st.divider()

            # ---- ACTIONS (ONLY ONCE) ----
            st.divider()

            if st.button("⬇ Download Excel", key="download_week_excel"):
                wb = create_weekly_summary_excel(records)
                buffer = BytesIO()
                wb.save(buffer)
                wb.close()
                buffer.seek(0)

                st.download_button(
                    label="📥 Download Weekly Summary",
                    data=buffer,
                    file_name="Weekly_Summary.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_week_excel_btn"
                )

            if st.button("📄 Save Summary to Activity Excel", key="save_week_summary"):
                append_weekly_summary(records)
                st.success("Weekly summary sheet created")

    # ---------- SETTINGS ----------
    with tab_settings:
        # Manage Projects (IFS) and Manage Engineers
        col1, col2 = st.columns(2)
        with col1:
            manage_projects_wizard()
        with col2:
            manage_engineers_wizard()

        # Divider Line
        st.divider()

        # Reminder interval setting
        popup_min = st.number_input(
            "Reminder interval (minutes)", 1, value=settings["popup_min"]
        )
        if st.button("Save Settings"):
            settings["popup_min"] = popup_min
            json.dump(settings, open(SETTINGS_FILE, "w"), indent=2)
            st.success("Settings saved")

if page == "Page-2":
    tab_1, tab_2, tab_3, tab_4 = st.tabs(
        ["📝 Tab-01", "📝 Tab-01", "📝 Tab-01", "📝 Tab-01"]
    )