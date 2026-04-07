import streamlit as st
import requests
import pandas as pd
import time

# --- 1. CONFIG & THEME (ULTRA DARK ELEGANT) ---
st.set_page_config(page_title="Gmail Bulk Checker Pro", layout="wide", page_icon="🛡️")

# Masukkan Token Anda di sini agar otomatis terisi saat aplikasi dibuka
DEFAULT_TOKEN = "3e9686be5343361007b21f6639af101dd505687dd79ea1c63ab84a300dc32dba"

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;600&family=Roboto+Mono&display=swap');
    
    /* Global Styles */
    .main { background-color: #0d1117; color: #f0f0f0; }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif; letter-spacing: 2px; }
    
    /* Metric Box */
    div[data-testid="stMetric"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 15px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }

    /* Input Area Styling */
    .stTextArea textarea {
        font-family: 'Roboto Mono', monospace;
        background-color: #0d1117 !important;
        color: #58a6ff !important;
        border: 1px solid #30363d !important;
    }

    /* Button Styling */
    .stButton button {
        border-radius: 8px;
        font-family: 'Orbitron';
        font-weight: bold;
        transition: 0.3s;
    }
    
    /* Result Header Styling */
    .tab-header { font-size: 1.2rem; font-weight: bold; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE (STATE MANAGEMENT) ---
if 'check_results' not in st.session_state:
    st.session_state.check_results = {
        "live": [], "verify": [], "disabled": [], "unregistered": [], "bad": []
    }

# --- 3. HELPER FUNCTIONS ---
def process_emails(text):
    """Auto Detect & Auto Fix Email Format"""
    raw_list = text.replace(",", "\n").split("\n")
    processed = []
    for item in raw_list:
        clean = item.strip().lower()
        if clean:
            if "@" not in clean:
                processed.append(f"{clean}@gmail.com")
            else:
                processed.append(clean)
    return processed

def call_mbahbabat_api(emails, token):
    url = "https://gmail-validation.mbahbabat.workers.dev/check1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json={"mail": emails}, timeout=60)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# --- 4. HEADER SECTION ---
st.markdown("<h1 style='text-align: center; color: #ff4500;'>🛡️ GMAIL BULK CHECKER V5</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e;'>High-Speed Validation Engine Powered by Mbahbabat API</p>", unsafe_allow_html=True)

# --- 5. INPUT & CONTROL SECTION (ATAS) ---
with st.container():
    col_input, col_token = st.columns([3, 1])
    
    with col_token:
        token = st.text_input("🔑 API TOKEN", value=DEFAULT_TOKEN, type="password")
        st.caption("[Ambil Token Disini](https://mbahbabat.github.io/bulk-gmail-checker/id/api-docs/)")
        
    with col_input:
        # Fitur Paste & Input Area
        email_input = st.text_area("📧 LIST EMAIL (Otomatis deteksi @gmail.com)", 
                                   height=180, 
                                   placeholder="Contoh:\nuser1\nuser2@gmail.com\nuser3, user4")

    # Control Buttons
    c1, c2, c3 = st.columns([1, 1, 3])
    btn_start = c1.button("🚀 EXECUTE CHECK", type="primary", use_container_width=True)
    
    if c2.button("🧹 CLEAR INPUT", use_container_width=True):
        st.session_state.check_results = {k: [] for k in st.session_state.check_results}
        st.rerun()

# --- 6. LOGIKA UTAMA (LIVE RESULT) ---
if btn_start:
    if not token or token == "MASUKKAN_TOKEN_ANDA_DISINI":
        st.error("❌ Token API belum diisi!")
    elif not email_input:
        st.warning("⚠️ List email masih kosong!")
    else:
        # 1. Parsing & Fix
        emails_to_check = process_emails(email_input)
        
        # 2. Reset Results
        st.session_state.check_results = {k: [] for k in st.session_state.check_results}
        
        # 3. Progress Bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 4. Chunking (API Limit 100 per req)
        chunks = [emails_to_check[i:i + 100] for i in range(0, len(emails_to_check), 100)]
        
        for i, chunk in enumerate(chunks):
            status_text.text(f"⏳ Mengecek Batch {i+1}/{len(chunks)}...")
            api_data = call_mbahbabat_api(chunk, token)
            
            if api_data:
                for item in api_data:
                    stat = item['status'].lower()
                    mail = item['email']
                    if stat in st.session_state.check_results:
                        st.session_state.check_results[stat].append(mail)
            
            progress_bar.progress((i + 1) / len(chunks))
        
        status_text.success("✅ Pengecekan Selesai!")

# --- 7. DASHBOARD METRICS ---
st.divider()
m = st.columns(5)
m[0].metric("LIVE", len(st.session_state.check_results["live"]))
m[1].metric("VERIFY", len(st.session_state.check_results["verify"]))
m[2].metric("DISABLED", len(st.session_state.check_results["disabled"]))
m[3].metric("UNREG", len(st.session_state.check_results["unregistered"]))
m[4].metric("BAD", len(st.session_state.check_results["bad"]))

# --- 8. RESULT CENTER (TAB & COPY FEATURE) ---
st.markdown("### 📋 RESULT CENTER")
st.caption("Gunakan ikon di pojok kanan kotak teks untuk menyalin (copy) semua email dalam kategori tersebut.")

# Membuat Tabs untuk hasil yang terpisah
tabs = st.tabs(["✅ LIVE", "🔑 VERIFY", "🚫 DISABLED", "❓ UNREG", "⚠️ BAD"])

def render_tab(tab_obj, key, color_hex):
    with tab_obj:
        data = st.session_state.check_results[key]
        if data:
            email_text = "\n".join(data)
            # Tampilan data dalam box kode (ada fitur COPY bawaan Streamlit)
            st.code(email_text, language="text")
            
            # Tombol download file
            st.download_button(f"📥 Download {key.upper()}", email_text, file_name=f"{key}_results.txt")
        else:
            st.info(f"Belum ada data untuk kategori {key.upper()}")

render_tab(tabs[0], "live", "#00FF7F")
render_tab(tabs[1], "verify", "#FFD700")
render_tab(tabs[2], "disabled", "#FF6347")
render_tab(tabs[3], "unregistered", "#00CCFF")
render_tab(tabs[4], "bad", "#E600AC")

# --- FOOTER ---
st.markdown("<br><hr><center>© 2024 Bulk Checker Pro | Elegant & Fast Interface</center>", unsafe_allow_html=True)
