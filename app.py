import streamlit as st
import requests
import pandas as pd

# --- 1. CONFIG & SOFT DARK THEME ---
st.set_page_config(page_title="Gmail Checker Pro", layout="wide", page_icon="🛡️")

# Token Handling dari Secrets
DEFAULT_TOKEN = st.secrets.get("MBAHBABAT_TOKEN", "")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Roboto+Mono&display=swap');

    /* Background Soft Dark (Tidak kontras tajam) */
    .main { 
        background-color: #0d1117; 
        color: #c9d1d9; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* Card/Metric - Soft Grey */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 15px !important;
    }
    
    /* Text Area - Dark & Clean */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-family: 'Roboto Mono', monospace;
    }

    /* Tab Styling - Muted Colors */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 6px 6px 0 0;
        border: 1px solid #30363d;
        color: #8b949e;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1c2128 !important;
        color: #58a6ff !important;
        border-bottom: 2px solid #58a6ff !important;
    }

    /* Button - Professional Grey */
    .stButton button {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        transition: 0.2s;
    }
    .stButton button:hover {
        background-color: #30363d;
        border-color: #8b949e;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE (BULLTEPROOF INITIALIZATION) ---
if 'results' not in st.session_state:
    st.session_state.results = {"all": [], "live": [], "verify": [], "disabled": [], "unregistered": [], "bad": []}

# Fungsi untuk Reset Input tanpa Error
def clear_text_input():
    st.session_state["email_input_key"] = ""
    st.session_state.results = {k: [] for k in st.session_state.results}

# --- 3. HELPER FUNCTIONS ---
def auto_fix_emails(text):
    emails = []
    items = text.replace(",", "\n").split("\n")
    for x in items:
        clean = x.strip().lower()
        if clean:
            emails.append(clean if "@" in clean else f"{clean}@gmail.com")
    return list(dict.fromkeys(emails))

def call_api_checker(chunk, token):
    url = "https://gmail-validation.mbahbabat.workers.dev/check1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"mail": chunk}, timeout=60)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- 4. HEADER ---
st.markdown("### 🛡️ Gmail Checker Professional")
st.caption("Soft Midnight Design • High Accuracy • Independent API")

with st.expander("🛠️ API Configuration"):
    token_val = st.text_input("Bearer Token", value=DEFAULT_TOKEN, type="password")

# --- 5. INPUT AREA ---
# Menggunakan key "email_input_key" agar bisa direset via fungsi callback
email_raw = st.text_area("Input Mails", height=200, key="email_input_key", 
                         placeholder="Paste usernames or emails here...")

col1, col2, col3, _ = st.columns([1.5, 1.5, 1.5, 4])

# Tombol Execute
start_btn = col1.button("🚀 EXECUTE", use_container_width=True)

# Tombol Clear (Memanggil fungsi callback agar tidak error)
col2.button("🧹 CLEAR", on_click=clear_text_input, use_container_width=True)

# Info Paste (Browser tidak mengizinkan akses clipboard otomatis demi keamanan)
col3.info("💡 `Ctrl + V` to Paste")

# --- 6. LOGIKA PENGECEKAN ---
if start_btn:
    if not token_val:
        st.error("Token API dibutuhkan.")
    elif not email_raw:
        st.warning("Daftar email kosong.")
    else:
        emails_list = auto_fix_emails(email_raw)
        # Reset hasil lama
        st.session_state.results = {k: [] for k in st.session_state.results}
        
        status_msg = st.empty()
        progress_bar = st.progress(0)
        
        chunks = [emails_list[i:i+100] for i in range(0, len(emails_list), 100)]
        
        for i, chunk in enumerate(chunks):
            status_msg.markdown(f"⚙️ Processing Batch {i+1}/{len(chunks)}...")
            data = call_api_checker(chunk, token_val)
            
            if data:
                for item in data:
                    email = item['email']
                    status = item['status'].lower()
                    
                    # Tambahkan ke kategori ALL
                    st.session_state.results["all"].append(f"{email} | {status.upper()}")
                    
                    # Tambahkan ke kategori spesifik
                    if status in st.session_state.results:
                        st.session_state.results[status].append(email)
                    else:
                        st.session_state.results["bad"].append(email)
            
            progress_bar.progress((i + 1) / len(chunks))
            
        status_msg.success(f"Pengecekan selesai. {len(emails_list)} email diproses.")

# --- 7. DASHBOARD & RESULT ---
st.divider()
m = st.columns(5)
m_keys = ["live", "verify", "disabled", "unregistered", "bad"]
m_labels = ["LIVE", "VERIFY", "DISABLED", "UNREG", "BAD"]

for i in range(5):
    m[i].metric(label=m_labels[i], value=len(st.session_state.results[m_keys[i]]))

st.markdown("#### 📋 Result Center")
# Tambahkan Tab ALL di paling depan
tab_list = ["📊 ALL RESULT"] + [f"{l}" for l in m_labels]
tabs = st.tabs(tab_list)

# Render Tab ALL
with tabs[0]:
    all_data = st.session_state.results["all"]
    if all_data:
        st.markdown(f"**Total Data Checked:** `{len(all_data)}`")
        st.code("\n".join(all_data), language="text")
        st.download_button("📥 Download All", "\n".join(all_data), file_name="all_results.txt")
    else:
        st.info("No data.")

# Render Tab Spesifik (1-5)
for i in range(1, 6):
    key = m_keys[i-1]
    label = m_labels[i-1]
    with tabs[i]:
        data = st.session_state.results[key]
        if data:
            st.markdown(f"**Status {label}:** `{len(data)}` email(s)")
            st.code("\n".join(data), language="text")
            st.download_button(f"📥 Download {label}", "\n".join(data), file_name=f"{key}.txt")
        else:
            st.info(f"No {label} emails found.")

st.markdown("<br><p style='text-align: center; opacity: 0.3; font-size: 0.7rem;'>Midnight Edition v6.3 | Stable API Integration</p>", unsafe_allow_html=True)
