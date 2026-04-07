import streamlit as st
import requests
import pandas as pd
import time

# --- 1. CONFIG & MILD DARK THEME ---
st.set_page_config(page_title="Gmail Checker Pro", layout="wide", page_icon="🛡️")

# Token Handling (Gunakan Streamlit Secrets atau isi di sini)
DEFAULT_TOKEN = st.secrets.get("MBAHBABAT_TOKEN", "")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Roboto+Mono&display=swap');

    /* Base Theme */
    .main {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }

    /* Elegant Metric Card */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px !important;
        transition: all 0.3s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: #58a6ff;
        background-color: #1c2128;
    }

    /* Input Area */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 6px !important;
        font-family: 'Roboto Mono', monospace;
    }
    .stTextArea textarea:focus {
        border-color: #58a6ff !important;
    }

    /* Tabs Customization */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: #161b22;
        border-radius: 4px 4px 0 0;
        border: 1px solid #30363d;
        color: #8b949e;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1c2128 !important;
        color: #58a6ff !important;
        border-bottom: 2px solid #58a6ff !important;
    }

    /* Buttons */
    .stButton button {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        transition: 0.2s;
    }
    .stButton button:hover {
        border-color: #8b949e;
        background-color: #30363d;
        color: #fff;
    }
    .stButton button:active {
        background-color: #282e33;
    }

    /* Horizontal Line */
    hr { border: 0; border-top: 1px solid #30363d; margin: 2rem 0; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if 'results' not in st.session_state:
    st.session_state.results = {"live": [], "verify": [], "disabled": [], "unregistered": [], "bad": []}

# --- 3. CORE FUNCTIONS ---
def clean_and_fix(text):
    emails = []
    # Split by newline or comma
    items = text.replace(",", "\n").split("\n")
    for x in items:
        clean = x.strip().lower()
        if clean:
            emails.append(clean if "@" in clean else f"{clean}@gmail.com")
    return list(dict.fromkeys(emails)) # Unique values

def fetch_api(chunk, token):
    url = "https://gmail-validation.mbahbabat.workers.dev/check1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"mail": chunk}, timeout=60)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# --- 4. HEADER & API CONFIG ---
st.markdown("### 🛡️ Gmail Bulk Checker")
st.caption("Secure, Clean, and Professional Validation")

with st.expander("🔑 API Configuration"):
    token = st.text_input("Bearer Token", value=DEFAULT_TOKEN, type="password")

# --- 5. INPUT SECTION (TOP) ---
email_raw = st.text_area("Input Emails", height=200, placeholder="Enter emails or usernames (auto-detect @gmail.com)...")

c1, c2, _ = st.columns([1, 1, 3])
start_btn = c1.button("Execute Check", use_container_width=True)
if c2.button("Clear All", use_container_width=True):
    st.session_state.results = {k: [] for k in st.session_state.results}
    st.rerun()

# --- 6. PROCESSING LOGIC ---
if start_btn:
    if not token:
        st.error("Please provide a valid API Token.")
    elif not email_raw:
        st.warning("Input list is empty.")
    else:
        emails = clean_and_fix(email_raw)
        st.session_state.results = {k: [] for k in st.session_state.results} # Reset
        
        # Simple & Clean Progress UI
        status_info = st.empty()
        progress_bar = st.progress(0)
        
        chunks = [emails[i:i+100] for i in range(0, len(emails), 100)]
        
        for i, chunk in enumerate(chunks):
            status_info.markdown(f"⚙️ Processing: {i*100 + len(chunk)} / {len(emails)}")
            res_data = fetch_api(chunk, token)
            if res_data:
                for item in res_data:
                    st.session_state.results[item['status'].lower()].append(item['email'])
            
            progress_bar.progress((i + 1) / len(chunks))
            time.sleep(0.1) # Smoothness
            
        status_info.success(f"Done! Checked {len(emails)} emails.")

# --- 7. METRICS DASHBOARD ---
st.markdown("---")
m = st.columns(5)
m_labels = ["Live", "Verify", "Disabled", "Unreg", "Bad"]
m_keys = ["live", "verify", "disabled", "unregistered", "bad"]
m_colors = ["#2ecc71", "#f1c40f", "#e74c3c", "#3498db", "#9b59b6"] # Professional Muted Colors

for i in range(5):
    with m[i]:
        st.metric(label=m_labels[i], value=len(st.session_state.results[m_keys[i]]))

# --- 8. RESULT TABS (COPY-PASTE READY) ---
st.markdown("### Result Center")
tabs = st.tabs([f"{l}" for l in m_labels])

for i, tab in enumerate(tabs):
    with tab:
        data = st.session_state.results[m_keys[i]]
        if data:
            st.markdown(f"**Total found:** `{len(data)}` email(s)")
            email_str = "\n".join(data)
            
            # st.code menyediakan tombol copy otomatis yang sangat bersih
            st.code(email_str, language="text")
            
            # Simple Download Button
            st.download_button(
                label=f"Download {m_labels[i]} List",
                data=email_str,
                file_name=f"{m_keys[i]}_results.txt",
                mime="text/plain"
            )
        else:
            st.info("No data available for this category.")

st.markdown("<br><p style='text-align: center; opacity: 0.3; font-size: 0.8rem;'>v6.2 | Midnight Professional</p>", unsafe_allow_html=True)
