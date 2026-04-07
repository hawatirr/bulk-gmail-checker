import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
import pandas as pd

# --- 1. CONFIG & SOFT DARK THEME ---
st.set_page_config(page_title="Gmail Monitor Pro", layout="wide", page_icon="📡")

# Database File
DB_FILE = "monitor_db.json"
DEFAULT_TOKEN = st.secrets.get("MBAHBABAT_TOKEN", "")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Roboto+Mono&display=swap');
    .main { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    div[data-testid="stMetric"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px !important; }
    .stTextArea textarea { background-color: #0d1117 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; border-radius: 8px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border: 1px solid #30363d; color: #8b949e; border-radius: 5px 5px 0 0; }
    .stTabs [aria-selected="true"] { color: #58a6ff !important; border-bottom: 2px solid #58a6ff !important; }
    .stButton button { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATABASE LOGIC (PERSISTENT STORAGE) ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"last_check": None, "emails": [], "results": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

if 'db' not in st.session_state:
    st.session_state.db = load_db()

# --- 3. HELPER FUNCTIONS ---
def fix_emails(text):
    emails = []
    for x in text.replace(",", "\n").split("\n"):
        clean = x.strip().lower()
        if clean:
            emails.append(clean if "@" in clean else f"{clean}@gmail.com")
    return list(dict.fromkeys(emails))

def call_api(emails, token):
    url = "https://gmail-validation.mbahbabat.workers.dev/check1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"mail": emails}, timeout=60)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 4. MONITORING ENGINE ---
def run_monitor_scan(token, manual=False):
    db = st.session_state.db
    if not db["emails"]:
        return
    
    # Cek Waktu (Auto 12 Jam)
    now = datetime.now()
    if not manual and db["last_check"]:
        last = datetime.fromisoformat(db["last_check"])
        if now < last + timedelta(hours=12):
            return # Belum waktunya scan

    # Jalankan Scan
    emails = db["emails"]
    new_results = {"all": [], "live": [], "verify": [], "disabled": [], "unregistered": [], "bad": []}
    
    chunks = [emails[i:i+100] for i in range(0, len(emails), 100)]
    for chunk in chunks:
        data = call_api(chunk, token)
        if data:
            for item in data:
                email, stat = item['email'], item['status'].lower()
                new_results["all"].append(f"{email} | {stat.upper()}")
                if stat in new_results: new_results[stat].append(email)
                else: new_results["bad"].append(email)
    
    # Update DB
    db["last_check"] = now.isoformat()
    db["results"] = new_results
    st.session_state.db = db
    save_db(db)
    if manual: st.success("Scan Manual Selesai!")

# --- 5. UI HEADER & AUTO TRIGGER ---
st.markdown("### 📡 Gmail Monitoring System")
st.caption("Auto-check setiap 12 jam (Lazy Trigger) • Midnight Soft Theme")

with st.expander("🛠️ CONFIGURATION"):
    token_val = st.text_input("API Token", value=DEFAULT_TOKEN, type="password")

# Trigger Otomatis saat App dibuka
if token_val:
    run_monitor_scan(token_val)

# --- 6. INPUT & MONITORING SETUP ---
st.divider()
col_left, col_right = st.columns([2, 1])

with col_left:
    email_raw = st.text_area("📋 MANAGE MONITORING LIST", height=150, 
                             placeholder="Paste email yang ingin dimonitor secara rutin di sini...")
    
    c1, c2, c3 = st.columns([1, 1, 1])
    if c1.button("💾 SAVE & SYNC", use_container_width=True):
        if email_raw:
            st.session_state.db["emails"] = fix_emails(email_raw)
            save_db(st.session_state.db)
            st.success("List disimpan! Sistem akan mengecek setiap 12 jam.")
        else: st.warning("List kosong.")
        
    if c2.button("🚀 FORCE SCAN NOW", use_container_width=True):
        if token_val: run_monitor_scan(token_val, manual=True)
        else: st.error("Isi Token dulu!")

    if c3.button("🧹 CLEAR LIST", use_container_width=True):
        st.session_state.db = {"last_check": None, "emails": [], "results": {}}
        save_db(st.session_state.db)
        st.rerun()

with col_right:
    st.markdown("#### 🕒 Status")
    last_time = st.session_state.db.get("last_check")
    if last_time:
        st.info(f"**Last Scan:**\n{datetime.fromisoformat(last_time).strftime('%d %b, %H:%M')}")
        next_check = datetime.fromisoformat(last_time) + timedelta(hours=12)
        st.warning(f"**Next Auto Scan:**\n{next_check.strftime('%d %b, %H:%M')}")
    else:
        st.write("Belum pernah discan.")

# --- 7. RESULTS DASHBOARD ---
st.divider()
res = st.session_state.db.get("results", {})
if res:
    m = st.columns(5)
    keys = ["live", "verify", "disabled", "unregistered", "bad"]
    labels = ["LIVE", "VERIFY", "DISABLED", "UNREG", "BAD"]
    
    for i in range(5):
        m[i].metric(labels[i], len(res.get(keys[i], [])))

    st.markdown("#### 📊 RESULT CENTER")
    tabs = st.tabs(["📋 ALL DATA"] + [f"{l}" for l in labels])
    
    with tabs[0]:
        all_data = res.get("all", [])
        if all_data:
            st.code("\n".join(all_data), language="text")
            st.download_button("Download All", "\n".join(all_data), file_name="monitoring_all.txt")
    
    for i in range(1, 6):
        with tabs[i]:
            key = keys[i-1]
            list_data = res.get(key, [])
            if list_data:
                st.code("\n".join(list_data), language="text")
                st.download_button(f"Download {key.upper()}", "\n".join(list_data), file_name=f"{key}.txt")
            else: st.info("Empty.")
else:
    st.info("Belum ada data hasil monitoring. Klik 'Save & Sync' lalu 'Force Scan' untuk memulai.")
