import streamlit as st
import requests
import pandas as pd
import time

# --- 1. CONFIG & THEME (MIDNIGHT DARK) ---
st.set_page_config(page_title="Gmail Checker Pro", layout="wide", page_icon="🛡️")

# Ambil token dari Secrets jika ada
DEFAULT_TOKEN = st.secrets.get("MBAHBABAT_TOKEN", "")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Roboto+Mono&display=swap');

    .main { background-color: #0d1117; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    
    /* Card Styling */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 15px !important;
    }

    /* Input Area */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-family: 'Roboto Mono', monospace;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 5px 5px 0 0;
        border: 1px solid #30363d;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1c2128 !important;
        color: #58a6ff !important;
        border-bottom: 2px solid #58a6ff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
# Inisialisasi list penampung hasil
if 'results' not in st.session_state:
    st.session_state.results = {"live": [], "verify": [], "disabled": [], "unregistered": [], "bad": []}

# --- 3. FUNCTIONS ---
def auto_fix(text):
    emails = []
    items = text.replace(",", "\n").split("\n")
    for x in items:
        clean = x.strip().lower()
        if clean:
            emails.append(clean if "@" in clean else f"{clean}@gmail.com")
    return list(dict.fromkeys(emails))

def call_api(chunk, token):
    url = "https://gmail-validation.mbahbabat.workers.dev/check1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"mail": chunk}, timeout=60)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 4. UI HEADER ---
st.markdown("### 🛡️ Gmail Bulk Checker")
st.caption("Midnight Professional - Clean & Accurate")

with st.expander("🛠️ API Configuration"):
    token = st.text_input("Bearer Token", value=DEFAULT_TOKEN, type="password")

# --- 5. INPUT AREA (WITH CLEAR FUNCTION) ---
# Gunakan key agar bisa di-reset lewat session_state
if "input_val" not in st.session_state:
    st.session_state.input_val = ""

email_raw = st.text_area("Input Emails", height=200, key="main_input", placeholder="user1\nuser2@gmail.com\nuser3")

c1, c2, c3, _ = st.columns([1, 1, 1, 4])
start_btn = c1.button("🚀 EXECUTE", use_container_width=True)

# Fungsi Clear Input
if c2.button("🧹 CLEAR", use_container_width=True):
    st.session_state.main_input = "" # Reset widget
    st.rerun()

# Info Paste
c3.info("💡 Tip: Use `Ctrl+V` to Paste")

# --- 6. EXECUTION ---
if start_btn:
    if not token:
        st.error("API Token Required.")
    elif not email_raw:
        st.warning("Input is empty.")
    else:
        emails = auto_fix(email_raw)
        # Reset results sebelum mulai baru
        st.session_state.results = {k: [] for k in st.session_state.results}
        
        status_info = st.empty()
        progress_bar = st.progress(0)
        
        chunks = [emails[i:i+100] for i in range(0, len(emails), 100)]
        
        for i, chunk in enumerate(chunks):
            status_info.markdown(f"⚙️ Processing: {i*100 + len(chunk)} / {len(emails)}")
            res_data = call_api(chunk, token)
            
            if res_data:
                for item in res_data:
                    raw_status = item['status'].lower()
                    email_addr = item['email']
                    
                    # FIX KEYERROR: Jika status API tidak ada di dict, masukkan ke 'bad'
                    if raw_status in st.session_state.results:
                        st.session_state.results[raw_status].append(email_addr)
                    else:
                        st.session_state.results["bad"].append(email_addr)
            
            progress_bar.progress((i + 1) / len(chunks))
            
        status_info.success(f"Finished. Total {len(emails)} targets.")

# --- 7. STATS & RESULT CENTER ---
st.divider()
m = st.columns(5)
m_keys = ["live", "verify", "disabled", "unregistered", "bad"]
m_labels = ["LIVE", "VERIFY", "DISABLED", "UNREG", "BAD"]

for i in range(5):
    m[i].metric(label=m_labels[i], value=len(st.session_state.results[m_keys[i]]))

st.markdown("### 📋 Result Center")
tabs = st.tabs([f"{l}" for l in m_labels])

for i, tab in enumerate(tabs):
    with tab:
        data = st.session_state.results[m_keys[i]]
        if data:
            st.markdown(f"**Total Found:** `{len(data)}` email(s)")
            email_str = "\n".join(data)
            
            # st.code otomatis memberikan tombol COPY di pojok kanan atas
            st.code(email_str, language="text")
            
            st.download_button(
                label=f"Download {m_labels[i]}",
                data=email_str,
                file_name=f"{m_keys[i]}_results.txt"
            )
        else:
            st.info("No data available.")

st.markdown("<br><p style='text-align: center; opacity: 0.3; font-size: 0.7rem;'>v6.2.1 | Stable Midnight Edition</p>", unsafe_allow_html=True)
