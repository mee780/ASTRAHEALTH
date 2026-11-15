import sqlite3
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "astrahealth.db"

st.set_page_config(
    page_title="ASTRAHEALTH | Mission Control",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------- DATABASE -----------------------------
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS physical (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at TEXT NOT NULL,
            crew_id TEXT NOT NULL,
            heart_rate REAL NOT NULL,
            systolic REAL NOT NULL,
            diastolic REAL NOT NULL,
            spo2 REAL NOT NULL,
            temperature REAL NOT NULL,
            sleep_hours REAL NOT NULL,
            notes TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS mental (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at TEXT NOT NULL,
            crew_id TEXT NOT NULL,
            mood TEXT NOT NULL,
            stress INTEGER NOT NULL,
            sleep_quality TEXT NOT NULL,
            notes TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS radiation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at TEXT NOT NULL,
            crew_id TEXT NOT NULL,
            dose_msv REAL NOT NULL,
            notes TEXT DEFAULT ''
        );
        """)

def read_table(table):
    with db() as con:
        return pd.read_sql_query(f"SELECT * FROM {table} ORDER BY recorded_at ASC", con)

def add_record(table, values):
    allowed = {"physical", "mental", "radiation"}
    if table not in allowed:
        raise ValueError("Invalid table")
    cols = list(values.keys())
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
    with db() as con:
        con.execute(sql, list(values.values()))

init_db()

# ----------------------------- DESIGN -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;600;700;800&display=swap');
:root {--bg:#06111f;--panel:#0d1d30;--panel2:#112943;--cyan:#58ddff;--muted:#91a9bf;--white:#eaf5ff;--green:#48dfa2;--amber:#ffca68;--red:#ff7186;}
.stApp {background:radial-gradient(circle at 80% 0%,rgba(30,104,160,.20),transparent 30%),#06111f;color:var(--white);}
html,body,[class*="css"]{font-family:Inter,sans-serif;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1c30,#071321);border-right:1px solid #17344c;}
.brand{font-family:Orbitron,sans-serif;font-size:1.45rem;font-weight:800;color:var(--cyan);letter-spacing:2px}
.brand-sub,.eyebrow{font-size:.68rem;letter-spacing:2px;color:var(--muted);font-weight:700}
.topbar{padding:18px 22px;border:1px solid #1b405a;border-radius:15px;background:linear-gradient(110deg,rgba(15,43,68,.95),rgba(8,25,43,.8));margin-bottom:12px}
.top-title{font-family:Orbitron,sans-serif;font-size:1.12rem;letter-spacing:1.5px;font-weight:700}
.banner{padding:10px 14px;border:1px solid #8a642a;background:#3a2a12;color:#ffe0a1;border-radius:9px;font-size:.78rem;margin:10px 0 20px}
.panel{background:linear-gradient(145deg,#10243a,#0a1929);border:1px solid #1b405a;border-radius:14px;padding:17px 18px;margin-bottom:14px}
.panel-title{font-family:Orbitron,sans-serif;color:var(--cyan);font-size:.76rem;letter-spacing:1.2px;font-weight:700;margin-bottom:5px}
.muted{color:var(--muted);font-size:.82rem}
div[data-testid="stMetric"]{background:#10243a;border:1px solid #1b405a;padding:13px;border-radius:12px}
.stButton>button,.stDownloadButton>button{border:1px solid #3d9bb9;background:#12344c;color:#eafaff;border-radius:8px;font-weight:700}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:#58ddff;color:#58ddff}
hr{border-color:#1b405a}
footer{visibility:hidden}
</style>
""", unsafe_allow_html=True)

# ----------------------------- HELPERS -----------------------------
def heading(title, subtitle):
    st.markdown(f'<div class="eyebrow">ASTRAHEALTH / MISSION SYSTEMS</div><h2>{title}</h2><p class="muted">{subtitle}</p>', unsafe_allow_html=True)

def chart_style(fig, height=300):
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c5d8e8", margin=dict(l=10,r=10,t=45,b=10),
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(145,169,191,.15)"),
        legend=dict(font_color="#c5d8e8")
    )
    return fig

def download_csv(df, name, label):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"),
                       file_name=name, mime="text/csv", use_container_width=True)

def latest_row(df):
    return None if df.empty else df.iloc[-1]

def demo_flags(row):
    flags=[]
    # Illustrative app rules only; these are not clinical thresholds.
    if row["heart_rate"] < 50 or row["heart_rate"] > 120:
        flags.append(("REVIEW", "Heart-rate value is outside this prototype's illustrative review band. Verify the entry."))
    if row["spo2"] < 94:
        flags.append(("REVIEW", "SpO₂ value is below this prototype's illustrative review level. Verify the entry."))
    if row["sleep_hours"] < 5:
        flags.append(("NOTE", "Recorded sleep duration is low compared with the prototype's illustrative setting."))
    if not flags:
        flags.append(("INFO", "No flag was triggered by the simple demonstration rules. This does not establish medical fitness."))
    return flags

def safe_num(value):
    return float(value) if pd.notna(value) else 0.0

# ----------------------------- SIDEBAR -----------------------------
pages = ["Dashboard","Physical Health","Mental Health","Radiation Monitoring","AI Health Analysis","Health Reports"]
with st.sidebar:
    st.markdown('<div class="brand">✦ ASTRAHEALTH</div><div class="brand-sub">CREW WELLNESS • MISSION SYSTEMS</div><hr>',unsafe_allow_html=True)
    page = st.radio("MISSION NAVIGATION", pages, label_visibility="visible")
    st.markdown("---")
    st.markdown('<div class="eyebrow">DEMO CREW PROFILE</div>',unsafe_allow_html=True)
    st.markdown("### 🧑‍🚀 AST-001")
    st.caption("Deep Space-01 • Fictional demonstration identity")
    crew_id = st.text_input("Crew identifier", value="AST-001", max_chars=30)
    st.caption("Records are stored in the app's SQLite database.")
    st.markdown("---")
    st.caption("Prototype only • No spacecraft connection")

physical = read_table("physical")
mental = read_table("mental")
radiation = read_table("radiation")
physical = physical[physical["crew_id"] == crew_id] if not physical.empty else physical
mental = mental[mental["crew_id"] == crew_id] if not mental.empty else mental
radiation = radiation[radiation["crew_id"] == crew_id] if not radiation.empty else radiation

st.markdown(f"""
<div class="topbar">
 <div class="top-title">MISSION CONTROL <span style="color:#58ddff">/</span> CREW HEALTH</div>
 <div class="muted">DEEP SPACE-01 &nbsp; • &nbsp; CREW {crew_id} &nbsp; • &nbsp; {datetime.now().strftime("%d %b %Y | %H:%M")}</div>
</div>
<div class="banner">⚠ DEMONSTRATION ENVIRONMENT — MANUALLY ENTERED VALUES ONLY. NOT LIVE ASTRONAUT DATA OR A MEDICAL DEVICE.</div>
""", unsafe_allow_html=True)

# ----------------------------- DASHBOARD -----------------------------
if page == "Dashboard":
    heading("Crew Health Overview","A consolidated view of the latest records entered for the selected demo crew.")
    p = latest_row(physical); m = latest_row(mental); r = latest_row(radiation)
    cols = st.columns(4)
    cols[0].metric("Heart rate", f"{safe_num(p['heart_rate']):.0f} BPM" if p is not None else "—")
    cols[1].metric("SpO₂", f"{safe_num(p['spo2']):.1f}%" if p is not None else "—")
    cols[2].metric("Sleep", f"{safe_num(p['sleep_hours']):.1f} h" if p is not None else "—")
    cols[3].metric("Cumulative demo dose", f"{radiation['dose_msv'].sum():.2f} mSv" if not radiation.empty else "—")
    a,b = st.columns([1.2,1])
    with a:
        st.markdown('<div class="panel"><div class="panel-title">RECENT PHYSICAL RECORDS</div>',unsafe_allow_html=True)
        if not physical.empty:
            st.dataframe(physical.tail(6).iloc[::-1],use_container_width=True,hide_index=True)
            fig=px.line(physical,x="recorded_at",y=["heart_rate","spo2"],markers=True,title="Recorded trend")
            st.plotly_chart(chart_style(fig),use_container_width=True)
        else: st.info("No physical-health records yet. Add one in Physical Health.")
        st.markdown("</div>",unsafe_allow_html=True)
    with b:
        st.markdown('<div class="panel"><div class="panel-title">WELLNESS SNAPSHOT</div>',unsafe_allow_html=True)
        if m is not None:
            st.write(f"**Mood:** {m['mood']}")
            st.write(f"**Stress self-rating:** {m['stress']}/10")
            st.write(f"**Sleep quality:** {m['sleep_quality']}")
            st.caption(f"Recorded {m['recorded_at']}")
        else: st.info("No wellness check-in recorded yet.")
        st.markdown('<div class="panel-title">RADIATION LOG</div>',unsafe_allow_html=True)
        if not radiation.empty:
            st.metric("Sum of manually entered dose values",f"{radiation['dose_msv'].sum():.3f} mSv")
            st.dataframe(radiation.tail(5).iloc[::-1],use_container_width=True,hide_index=True)
        else: st.info("No radiation entries yet.")
        st.markdown("</div>",unsafe_allow_html=True)
    if p is not None:
        st.markdown("#### Prototype review indicators")
        for label,msg in demo_flags(p):
            st.warning(f"**{label}:** {msg}") if label=="REVIEW" else st.info(f"**{label}:** {msg}")
    st.caption("Dashboard summaries reflect saved manual entries. Blank values mean no record is available.")

# ----------------------------- PHYSICAL -----------------------------
elif page == "Physical Health":
    heading("Physical Health","Record manually supplied demonstration measurements. No sensors are connected.")
    left,right=st.columns([1,1.1])
    with left:
        st.markdown('<div class="panel"><div class="panel-title">＋ NEW MEASUREMENT</div>',unsafe_allow_html=True)
        with st.form("physical_entry",clear_on_submit=True):
            recorded_date=st.date_input("Measurement date",value=date.today())
            hr=st.number_input("Heart rate (BPM)",min_value=1,max_value=250,value=76)
            c1,c2=st.columns(2)
            sys=c1.number_input("Systolic BP (mmHg)",min_value=40,max_value=300,value=118)
            dia=c2.number_input("Diastolic BP (mmHg)",min_value=20,max_value=200,value=78)
            spo2=st.number_input("SpO₂ (%)",min_value=1.0,max_value=100.0,value=98.0,step=0.5)
            temp=st.number_input("Temperature (°C)",min_value=25.0,max_value=45.0,value=36.7,step=0.1)
            sleep=st.number_input("Sleep duration (hours)",min_value=0.0,max_value=24.0,value=7.5,step=0.5)
            notes=st.text_area("Notes (optional)",max_chars=500)
            submitted=st.form_submit_button("SAVE MEASUREMENT",use_container_width=True)
        if submitted:
            add_record("physical",{"recorded_at":datetime.combine(recorded_date,datetime.now().time()).isoformat(timespec="seconds"),"crew_id":crew_id,"heart_rate":hr,"systolic":sys,"diastolic":dia,"spo2":spo2,"temperature":temp,"sleep_hours":sleep,"notes":notes})
            st.success("Measurement saved to the local database.")
            st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">MEASUREMENT HISTORY</div>',unsafe_allow_html=True)
        if not physical.empty:
            st.dataframe(physical.sort_values("recorded_at",ascending=False),use_container_width=True,hide_index=True)
            download_csv(physical,"astrahealth_physical_health.csv","DOWNLOAD PHYSICAL HEALTH CSV")
        else: st.info("No saved measurements for this crew identifier.")
        st.markdown("</div>",unsafe_allow_html=True)

# ----------------------------- MENTAL -----------------------------
elif page == "Mental Health":
    heading("Mental Wellness","A voluntary self-report check-in for mood, perceived stress and sleep quality.")
    left,right=st.columns([1,1])
    with left:
        st.markdown('<div class="panel"><div class="panel-title">◉ CREW WELLNESS CHECK-IN</div>',unsafe_allow_html=True)
        with st.form("mental_form",clear_on_submit=True):
            mood=st.selectbox("How are you feeling?",["Very good","Good","Okay","Low","Very low"])
            stress=st.slider("Perceived stress level",1,10,3)
            st.caption("1 = very low perceived stress • 10 = very high perceived stress")
            quality=st.selectbox("How would you rate your sleep?",["Very good","Good","Fair","Poor","Very poor"])
            notes=st.text_area("Optional note (avoid sensitive personal details)",max_chars=500)
            mental_submit=st.form_submit_button("SAVE WELLNESS CHECK-IN",use_container_width=True)
        if mental_submit:
            add_record("mental",{"recorded_at":datetime.now().isoformat(timespec="seconds"),"crew_id":crew_id,"mood":mood,"stress":stress,"sleep_quality":quality,"notes":notes})
            st.success("Wellness check-in saved.")
            st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">WELLNESS HISTORY</div>',unsafe_allow_html=True)
        if not mental.empty:
            st.dataframe(mental.sort_values("recorded_at",ascending=False),use_container_width=True,hide_index=True)
            download_csv(mental,"astrahealth_wellness.csv","DOWNLOAD WELLNESS CSV")
            fig=px.line(mental.sort_values("recorded_at"),x="recorded_at",y="stress",markers=True,title="Self-reported stress over time")
            st.plotly_chart(chart_style(fig,250),use_container_width=True)
        else: st.info("Your check-ins will appear here after saving.")
        st.markdown("</div>",unsafe_allow_html=True)
    st.info("This is a self-reflection tool, not a mental-health assessment or diagnosis. Seek qualified support when needed.")

# ----------------------------- RADIATION -----------------------------
elif page == "Radiation Monitoring":
    heading("Radiation Monitoring","Log manually entered illustrative dose values. This is not a radiation detector or exposure safety assessment.")
    left,right=st.columns([1,1.1])
    with left:
        st.markdown('<div class="panel"><div class="panel-title">＋ ADD DOSE ENTRY</div>',unsafe_allow_html=True)
        with st.form("radiation_form",clear_on_submit=True):
            d=st.date_input("Entry date",value=date.today(),key="rad_date")
            dose=st.number_input("Additional dose (mSv)",min_value=0.0,max_value=100000.0,value=0.1,step=0.1,format="%.3f")
            note=st.text_area("Source / notes (optional)",max_chars=500)
            rad_submit=st.form_submit_button("SAVE DOSE ENTRY",use_container_width=True)
        if rad_submit:
            add_record("radiation",{"recorded_at":datetime.combine(d,datetime.now().time()).isoformat(timespec="seconds"),"crew_id":crew_id,"dose_msv":dose,"notes":note})
            st.success("Dose entry saved.")
            st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-title">CUMULATIVE LOG TOTAL</div>',unsafe_allow_html=True)
        total=float(radiation["dose_msv"].sum()) if not radiation.empty else 0.0
        st.metric("Sum of entered values",f"{total:.3f} mSv")
        st.caption("This is only the sum of entries provided by the user. It is not a measured cumulative astronaut dose or a safety threshold.")
        if not radiation.empty:
            st.dataframe(radiation.sort_values("recorded_at",ascending=False),use_container_width=True,hide_index=True)
            download_csv(radiation,"astrahealth_radiation_log.csv","DOWNLOAD RADIATION CSV")
        else: st.info("No dose entries recorded.")
        st.markdown("</div>",unsafe_allow_html=True)

# ----------------------------- ANALYSIS -----------------------------
elif page == "AI Health Analysis":
    heading("Health Pattern Analysis","Explainable rule-based comparisons over saved sample entries. No trained AI model is included.")
    if physical.empty:
        st.info("Save at least one physical-health record to view analysis.")
    else:
        latest=physical.sort_values("recorded_at").iloc[-1]
        st.markdown('<div class="panel"><div class="panel-title">LATEST ENTRY REVIEW</div>',unsafe_allow_html=True)
        for label,msg in demo_flags(latest):
            if label=="REVIEW": st.warning(msg)
            else: st.info(msg)
        st.markdown("</div>",unsafe_allow_html=True)
        if len(physical)>=2:
            ordered=physical.sort_values("recorded_at")
            first=ordered.iloc[0]; last=ordered.iloc[-1]
            a,b,c=st.columns(3)
            a.metric("Heart-rate change",f"{last['heart_rate']-first['heart_rate']:+.0f} BPM")
            b.metric("SpO₂ change",f"{last['spo2']-first['spo2']:+.1f} pp")
            c.metric("Sleep change",f"{last['sleep_hours']-first['sleep_hours']:+.1f} h")
            fig=px.line(ordered,x="recorded_at",y=["heart_rate","spo2","sleep_hours"],markers=True,title="Recorded measurements (different units)")
            st.plotly_chart(chart_style(fig),use_container_width=True)
        else:
            st.info("Add another physical-health record to compare changes over time.")
    st.caption("Rules are illustrative and are not clinically validated. They do not diagnose, predict, or determine fitness for duty.")

# ----------------------------- REPORTS -----------------------------
elif page == "Health Reports":
    heading("Health Reports","Review and export the records stored for the selected demo crew.")
    tabs=st.tabs(["Physical","Mental wellness","Radiation","Combined export"])
    with tabs[0]:
        st.dataframe(physical.sort_values("recorded_at",ascending=False) if not physical.empty else physical,use_container_width=True,hide_index=True)
        if not physical.empty: download_csv(physical,"astrahealth_physical.csv","DOWNLOAD PHYSICAL CSV")
    with tabs[1]:
        st.dataframe(mental.sort_values("recorded_at",ascending=False) if not mental.empty else mental,use_container_width=True,hide_index=True)
        if not mental.empty: download_csv(mental,"astrahealth_mental.csv","DOWNLOAD WELLNESS CSV")
    with tabs[2]:
        st.dataframe(radiation.sort_values("recorded_at",ascending=False) if not radiation.empty else radiation,use_container_width=True,hide_index=True)
        if not radiation.empty: download_csv(radiation,"astrahealth_radiation.csv","DOWNLOAD RADIATION CSV")
    with tabs[3]:
        combined=[]
        for name,frame in [("physical",physical),("mental",mental),("radiation",radiation)]:
            if not frame.empty:
                temp=frame.copy()
                temp.insert(0,"record_type",name)
                combined.append(temp)
        if combined:
            report=pd.concat(combined,ignore_index=True,sort=False)
            st.dataframe(report,use_container_width=True,hide_index=True)
            download_csv(report,"astrahealth_combined_report.csv","DOWNLOAD COMBINED REPORT")
        else: st.info("No records are available to export yet.")
    st.caption("Exports contain only manually entered records for the selected crew identifier.")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#7893aa;font-size:.72rem;letter-spacing:1px">ASTRAHEALTH • CREW HEALTH MONITORING PROTOTYPE<br>NOT A MEDICAL DEVICE • NOT CONNECTED TO SPACECRAFT SENSORS • MANUAL DEMONSTRATION DATA ONLY</div>',unsafe_allow_html=True)
