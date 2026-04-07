import streamlit as st
import requests
import pandas as pd
import time
from streamlit_lottie import st_lottie

# --- 1. CONFIG & ADVANCED CYBER STYLING ---
st.set_page_config(page_title="Gmail Checker Cyber", layout="wide", page_icon="⚡")

# Token Handling: Prioritaskan dari Secrets, jika tidak ada baru input manual
# Cara setting: Di Streamlit Cloud Dashboard -> Settings -> Secrets -> tulis: MBAHBABAT_TOKEN = "isi_token"
if "MBAHBABAT_TOKEN" in st.secrets:
    DEFAULT_TOKEN = st.secrets["MBAHBABAT_TOKEN"]
else:
    DEFAULT_TOKEN = ""

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');

    /* Global Glow Effect */
    .main { 
        background: radial-gradient(circle at top, #1a1a2e 0%, #0f0f1b 100%);
        color: #e0e0e0;
        font-family: 'Rajdhani', sans-serif;
    }

    /* Animated Card Status */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px !important;
        transition: 0.4s;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetric"]:hover {
        border-color: #00f2ff;
        transform: translateY(-5px);
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.2);
    }

    /* Cyber Input Area */
    .stTextArea textarea {
        background: #0d0d1a !important;
        color: #00f2ff !important;
        border: 2px solid #1a1a2e !important;
        border-radius: 10px !important;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }

    /* Pulse Animation for Scanning */
    @keyframes pulse-border {
        0% { box-shadow: 0 0 0 0 rgba(0, 242, 255, 0.4); }
        70% { box-shadow: 0 0 0 15px rgba(0, 242, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 242, 255, 0); }
    }
    .scanning-active { animation: pulse-border 2s infinite; border-radius: 10px; }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0f0f1b; }
    ::-webkit-scrollbar-thumb { background: #1a1a2e; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #00f2ff; }

    /* Hide API Key Input by Default */
    .token-expander { background: rgba(0,0,0,0.2); border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ASSETS (LOTTIE ANIMATION) ---
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

lottie_scan = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_m6cu96ze.json") # Radar Scan
lottie_done = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_lk8dzp9f.json") # Success Check

# --- 3. SESSION STATE ---
if 'db' not in st.session_state:
    st.session_state.db = {"live": [], "verify": [], "disabled": [], "unregistered": [], "bad": []}
if 'is_running' not in st.session_state:
    st.session_state.is_running = False

# --- 4. LOGIC ENGINE ---
def auto_fix(text):
    emails = []
    for x in text.replace(",", "\n").split("\n"):
        clean = x.strip().lower()
        if clean:
            emails.append(clean if "@" in clean else f"{clean}@gmail.com")
    return emails

def call_api(emails, token):
    url = "https://gmail-validation.mbahbabat.workers.dev/check1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"mail": emails}, timeout=60)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 5. TOP NAV & API KEY ---
t1, t2 = st.columns([3, 1])
with t1:
    st.markdown("<h1 style='color: #00f2ff; margin-bottom: 0;'>⚡ GMAIL CHECKER PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b949e; margin-top: -10px;'>Ultimate Validation Cyber System</p>", unsafe_allow_html=True)

with t2:
    with st.expander("🛠️ API Config"):
        api_token = st.text_input("Bearer Token", value=DEFAULT_TOKEN, type="password")
        if api_token: st.success("Key Injected!")

# --- 6. INPUT SECTION (ELEGAN & CLEAN) ---
st.divider()
input_area = st.container()
with input_area:
    email_raw = st.text_area("🚀 DROP EMAILS HERE", height=150, placeholder="Paste emails here (Automatic fix @gmail.com active)")
    
    col_btn1, col_btn2, _ = st.columns([1, 1, 2])
    start = col_btn1.button("🔥 INITIALIZE SCAN", type="primary", use_container_width=True)
    if col_btn2.button("🧹 PURGE DATA", use_container_width=True):
        st.session_state.db = {k: [] for k in st.session_state.db}
        st.rerun()

# --- 7. PROCESSING (WITH ANIMATION) ---
if start:
    if not api_token:
        st.error("❗ SYSTEM ERROR: API Token Missing")
    elif not email_raw:
        st.warning("❗ SYSTEM ERROR: Data Payload Empty")
    else:
        emails = auto_fix(email_raw)
        st.session_state.db = {k: [] for k in st.session_state.db}
        st.session_state.is_running = True
        
        # UI Animasi Loading
        with st.container():
            c_anim, c_text = st.columns([1, 4])
            with c_anim: st_lottie(lottie_scan, height=100, key="scanning")
            with c_text: 
                msg = st.empty()
                prog = st.progress(0)

        chunks = [emails[i:i+100] for i in range(0, len(emails), 100)]
        for i, chunk in enumerate(chunks):
            msg.markdown(f"📡 **Scanning Phase {i+1}/{len(chunks)}...**")
            results = call_api(chunk, api_token)
            if results:
                for item in results:
                    st.session_state.db[item['status'].lower()].append(item['email'])
            prog.progress((i+1)/len(chunks))
        
        st.session_state.is_running = False
        msg.success("⚡ **SCAN COMPLETE: Target Identified!**")
        st.balloons()

# --- 8. DASHBOARD RESULTS ---
st.divider()
m = st.columns(5)
colors = ["#00f2ff", "#ffcc00", "#ff4d4d", "#008cff", "#e600ac"]
labels = ["LIVE", "VERIFY", "DISABLED", "UNREG", "BAD"]
keys = ["live", "verify", "disabled", "unregistered", "bad"]

for i in range(5):
    m[i].markdown(f"""
        <div style='text-align: center;'>
            <p style='color: {colors[i]}; font-size: 0.9rem; margin-bottom: -5px;'>{labels[i]}</p>
            <h2 style='color: white;'>{len(st.session_state.db[keys[i]])}</h2>
        </div>
    """, unsafe_allow_html=True)

# --- 9. RESULT CENTER (WITH COPY FEATURE) ---
st.markdown("### 🧬 RECOVERY CENTER")
tabs = st.tabs([f"✅ {labels[0]}", f"🔑 {labels[1]}", f"🚫 {labels[2]}", f"❓ {labels[3]}", f"⚠️ {labels[4]}"])

for i, tab in enumerate(tabs):
    with tab:
        data = st.session_state.db[keys[i]]
        if data:
            email_str = "\n".join(data)
            st.markdown(f"<p style='color: {colors[i]};'>Total: {len(data)} items</p>", unsafe_allow_html=True)
            
            # Box hasil dengan fitur auto-copy bawaan streamlit
            st.code(email_str, language="text")
            
            # Action buttons
            b1, b2, _ = st.columns([1, 1, 3])
            b1.download_button(f"📥 Download {labels[i]}", email_str, file_name=f"{keys[i]}.txt")
        else:
            st.info("No data in this sector.")

# Footer
st.markdown("<br><p style='text-align: center; opacity: 0.3;'>⚡ CYBER-CHECKER ENGINE v6.0 | ENCRYPTED CONNECTION</p>", unsafe_allow_html=True)
