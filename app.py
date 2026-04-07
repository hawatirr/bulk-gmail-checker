import streamlit as st
import requests
import pandas as pd

# --- 1. CONFIG & SOFT DARK THEME (GitHub Dark Style) ---
st.set_page_config(page_title="Gmail Checker Pro", layout="wide", page_icon="🛡️")

# Token Handling dari Secrets
DEFAULT_TOKEN = st.secrets.get("MBAHBABAT_TOKEN", "")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Roboto+Mono&display=swap');

    /* Background Soft Midnight (Nyaman di mata) */
    .main { 
        background-color: #0d1117; 
        color: #c9d1d9; 
        font-family: 'Inter', sans-serif; 
    }
    
    /* Card/Metric - Muted Navy */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 15px !important;
    }
    
    /* Text Area */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        font-family: 'Roboto Mono', monospace;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #161b22;
        border-radius: 6px 6px 0 0;
        border: 1px solid #30363d;
        color: #8b949e;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1c2128 !important;
        color: #58a6ff !important;
        border-bottom: 2px solid #58a6ff !important;
    }

    /* Professional Button */
    .stButton button {
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 6px;
        font-weight: 600;
        transition: 0.2s;
    }
    .stButton button:hover {
        background-color: #30363d;
        border-color: #8b949e;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
# Inisialisasi storage jika belum ada
if 'results' not in st.session_state:
    st.session_state.results = {"all": [], "live": [], "verify": [], "disabled": [], "unregistered": [], "bad": []}

# Fungsi Reset yang Aman (Tanpa Error StreamlitAPI)
def reset_all():
    # Menghapus isi text area lewat key
    st.session_state["email_input_widget"] = ""
    # Menghapus data hasil
    st.session_state.results = {"all": [], "live": [], "verify": [], "disabled": [], "unregistered": [], "bad": []}

# --- 3. HELPER FUNCTIONS ---
def fix_emails(text):
    emails = []
    items = text.replace(",", "\n").split("\n")
    for x in items:
        clean = x.strip().lower()
        if clean:
            emails.append(clean if "@" in clean else f"{clean}@gmail.com")
    return list(dict.fromkeys(emails))

def request_api(chunk, token):
    url = "https://gmail-validation.mbahbabat.workers.dev/check1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"mail": chunk}, timeout=60)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 401:
            return "ERR_TOKEN"
        return None
    except:
        return None

# --- 4. HEADER ---
st.markdown("### 🛡️ Gmail Bulk Checker Professional")
st.caption("Soft Midnight Interface • API Version 1.0")

with st.expander("🛠️ API CONFIGURATION"):
    token_val = st.text_input("Bearer Token", value=DEFAULT_TOKEN, type="password")

# --- 5. INPUT SECTION (TOP) ---
email_raw = st.text_area("Input Emails", height=200, key="email_input_widget", 
                         placeholder="Paste usernames or emails here...")

col1, col2, col3, _ = st.columns([1.5, 1.5, 1.5, 4])

# Tombol Execute
start_btn = col1.button("🚀 EXECUTE CHECK", use_container_width=True)

# Tombol Clear (Panggil fungsi reset_all)
col2.button("🧹 CLEAR INPUT", on_click=reset_all, use_container_width=True)

# Petunjuk Paste
col3.info("💡 `Ctrl + V` to Paste")

# --- 6. CORE LOGIC ---
if start_btn:
    if not token_val:
        st.error("❌ Token API tidak ditemukan. Silakan isi di menu Config.")
    elif not email_raw:
        st.warning("⚠️ Masukkan email yang ingin dicek.")
    else:
        emails_to_check = fix_emails(email_raw)
        # Reset hasil lama agar tidak menumpuk
        st.session_state.results = {"all": [], "live": [], "verify": [], "disabled": [], "unregistered": [], "bad": []}
        
        status_box = st.empty()
        progress_bar = st.progress(0)
        
        chunks = [emails_to_check[i:i+100] for i in range(0, len(emails_to_check), 100)]
        
        total_received = 0
        for i, chunk in enumerate(chunks):
            status_box.markdown(f"⚙️ Processing Batch {i+1}/{len(chunks)}...")
            data = request_api(chunk, token_val)
            
            if data == "ERR_TOKEN":
                st.error("❌ Token Expired atau Salah! Ambil token baru dari situs Mbahbabat.")
                break
            elif data:
                for item in data:
                    email = item.get('email', 'Unknown')
                    status = item.get('status', 'bad').lower()
                    
                    # Simpan ke Kategori ALL
                    st.session_state.results["all"].append(f"{email} | {status.upper()}")
                    
                    # Simpan ke Kategori Spesifik
                    if status in st.session_state.results:
                        st.session_state.results[status].append(email)
                    else:
                        st.session_state.results["bad"].append(email)
                    total_received += 1
            
            progress_bar.progress((i + 1) / len(chunks))
            
        if total_received > 0:
            status_box.success(f"✅ Pengecekan selesai. {total_received} email diproses.")
        else:
            status_box.error("❌ API tidak mengembalikan data. Pastikan token Anda benar.")

# --- 7. DASHBOARD & RESULTS ---
st.divider()
m = st.columns(5)
m_keys = ["live", "verify", "disabled", "unregistered", "bad"]
m_labels = ["LIVE", "VERIFY", "DISABLED", "UNREG", "BAD"]

for i in range(5):
    m[i].metric(label=m_labels[i], value=len(st.session_state.results[m_keys[i]]))

st.markdown("#### 📋 RESULT CENTER")
# Gabungkan Tab ALL dengan Tab kategori
tabs = st.tabs(["📊 ALL RESULTS"] + [f"{l}" for l in m_labels])

# Render Tab ALL
with tabs[0]:
    all_data = st.session_state.results["all"]
    if all_data:
        st.code("\n".join(all_data), language="text")
        st.download_button("📥 Download Summary", "\n".join(all_data), file_name="all_summary.txt")
    else:
        st.info("No data checked yet.")

# Render Tab Spesifik (Live, Verify, dll)
for i in range(1, 6):
    key = m_keys[i-1]
    with tabs[i]:
        list_data = st.session_state.results[key]
        if list_data:
            st.code("\n".join(list_data), language="text")
            st.download_button(f"📥 Download {key.upper()}", "\n".join(list_data), file_name=f"{key}.txt")
        else:
            st.info(f"List {key.upper()} is empty.")

st.markdown("<br><p style='text-align: center; opacity: 0.3; font-size: 0.7rem;'>Midnight Edition v6.4 | Independent Checker</p>", unsafe_allow_html=True)
