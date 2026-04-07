import streamlit as st
import requests
import pandas as pd
import time
from streamlit_lottie import st_lottie

# --- 1. CONFIG & CYBER STYLING ---
st.set_page_config(page_title="Gmail Bulk Checker Pro", layout="wide", page_icon="⚡")

# Handle Secrets/Token
if "MBAHBABAT_TOKEN" in st.secrets:
    DEFAULT_TOKEN = st.secrets["MBAHBABAT_TOKEN"]
else:
    DEFAULT_TOKEN = ""

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap');

    .main { 
        background: #0b0e14; 
        color: #e0e0e0;
        font-family: 'Rajdhani', sans-serif;
    }

    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(0, 242, 255, 0.2);
        border-radius: 15px;
        padding: 15px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    
    /* Elegant Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] { 
        background-color: rgba(0, 242, 255, 0.1) !important;
        color: #00f2ff !important;
        border-bottom: 2px solid #00f2ff !important;
    }

    /* TextArea Styling */
    .stTextArea textarea {
        background: #0d1117 !important;
        color: #00f2ff !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
    }

    /* Cyber Button */
    .stButton button {
        background: linear-gradient(90deg, #00f2ff, #008cff);
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Orbitron';
        font-weight: bold;
        padding: 10px;
        transition: 0.3s;
    }
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.5);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. ASSETS & LOGIC ---
def load_lottie(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200: return None
        return r.json()
    except: return None

# Radar Animation for scanning
lottie_radar = load_lottie("https://assets10.lottiefiles.com/packages/lf20_m6cu96ze.json")

if 'db' not in st.session_state:
    st.session_state.db = {"live": [], "verify": [], "disabled": [], "unregistered": [], "bad": []}

def auto_fix_list(text):
    emails = []
    items = text.replace(",", "\n").split("\n")
    for x in items:
        clean = x.strip().lower()
        if clean:
            emails.append(clean if "@" in clean else f"{clean}@gmail.com")
    return list(dict.fromkeys(emails)) # Remove duplicates

def call_api(emails, token):
    url = "https://gmail-validation.mbahbabat.workers.dev/check1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"mail": emails}, timeout=60)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 3. LAYOUT: TOP SECTION ---
t1, t2 = st.columns([3, 1])
with t1:
    st.markdown("<h1 style='color: #00f2ff; margin-bottom: 0;'>⚡ CYBER CHECKER PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8b949e; margin-top: -10px;'>Advanced Multi-Account Gmail Validation</p>", unsafe_allow_html=True)

with t2:
    # Expander untuk sembunyikan Token
    with st.expander("🛠️ API CONFIG"):
        token_input = st.text_input("Bearer Token", value=DEFAULT_TOKEN, type="password")

# --- 4. INPUT SECTION ---
st.divider()
email_raw = st.text_area("📧 INPUT EMAILS", height=180, placeholder="Paste emails here... (user1, user2@gmail.com, etc)")

c1, c2, c3 = st.columns([1.5, 1.5, 4])
start_btn = c1.button("🚀 EXECUTE SCAN", use_container_width=True)
if c2.button("🧹 PURGE DATA", use_container_width=True):
    st.session_state.db = {k: [] for k in st.session_state.db}
    st.rerun()

# --- 5. EXECUTION ENGINE ---
if start_btn:
    if not token_input:
        st.error("❗ Access Denied: Missing API Token")
    elif not email_raw:
        st.warning("❗ Warning: No Data to Scan")
    else:
        emails = auto_fix_list(email_raw)
        st.session_state.db = {k: [] for k in st.session_state.db} # Reset
        
        # Display Scanning Animation
        with st.container():
            col_ani, col_txt = st.columns([1, 4])
            with col_ani:
                if lottie_radar:
                    st_lottie(lottie_radar, height=120, key="scanning")
                else:
                    st.write("🌀")
            with col_txt:
                msg = st.empty()
                prog = st.progress(0)

        # Batch Processing
        chunks = [emails[i:i+100] for i in range(0, len(emails), 100)]
        for i, chunk in enumerate(chunks):
            msg.markdown(f"📡 **Scanning Phase {i+1}/{len(chunks)}...**")
            results = call_api(chunk, token_input)
            if results:
                for item in results:
                    st.session_state.db[item['status'].lower()].append(item['email'])
            prog.progress((i+1)/len(chunks))
        
        msg.success(f"⚡ **SCAN COMPLETE: {len(emails)} Targets Processed!**")
        st.balloons()

# --- 6. STATS DASHBOARD ---
st.divider()
m = st.columns(5)
m_colors = ["#00f2ff", "#ffcc00", "#ff4d4d", "#008cff", "#e600ac"]
m_labels = ["LIVE", "VERIFY", "DISABLED", "UNREG", "BAD"]
m_keys = ["live", "verify", "disabled", "unregistered", "bad"]

for i in range(5):
    with m[i]:
        st.markdown(f"""
            <div style='text-align: center;'>
                <p style='color: {m_colors[i]}; font-size: 0.8rem; margin-bottom: -5px;'>{m_labels[i]}</p>
                <h2 style='color: white;'>{len(st.session_state.db[m_keys[i]])}</h2>
            </div>
        """, unsafe_allow_html=True)

# --- 7. RESULT CENTER (GROUPED & COPYABLE) ---
st.markdown("### 🧬 EXTRACTION CENTER")
tabs = st.tabs([f"✅ {l}" for l in m_labels])

for i, tab in enumerate(tabs):
    with tab:
        data = st.session_state.db[m_keys[i]]
        if data:
            st.markdown(f"<p style='color: {m_colors[i]};'>Total: {len(data)} items</p>", unsafe_allow_html=True)
            email_string = "\n".join(data)
            
            # Box hasil dengan tombol Copy bawaan
            st.code(email_string, language="text")
            
            # Action buttons
            b1, b2 = st.columns([1, 4])
            b1.download_button(f"📥 Download {m_labels[i]}", email_string, file_name=f"{m_keys[i]}.txt")
        else:
            st.info("Sector empty.")

st.markdown("<br><p style='text-align: center; opacity: 0.2;'>⚡ V6.1 CYBER-ENGINE | ENCRYPTED | NO-LOGS</p>", unsafe_allow_html=True)
