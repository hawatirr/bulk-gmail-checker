import streamlit as st
import requests
import pandas as pd
import time

# --- 1. CONFIG & STYLING (ELEGANT & RESPONSIVE) ---
st.set_page_config(page_title="Gmail Bulk Checker Pro", layout="wide", page_icon="🛡️")

# Custom CSS untuk tampilan elegan dan tombol copy
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono&display=swap');
    
    .main { background-color: #0d1117; color: #f0f0f0; }
    .stMetric { background-color: #161b22; padding: 20px; border-radius: 12px; border: 1px solid #30363d; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .result-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 10px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; transition: 0.3s; }
    .result-card:hover { border-color: #ff4500; background: #1c2128; }
    
    /* Status Colors */
    .status-live { color: #00FF7F; font-weight: bold; }
    .status-verify { color: #FFD700; font-weight: bold; }
    .status-disabled { color: #FF6347; font-weight: bold; }
    .status-unreg { color: #00CCFF; font-weight: bold; }
    .status-bad { color: #E600AC; font-weight: bold; }
    
    /* Copy Button Style */
    .copy-btn { background: #ff4500; color: white; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; font-family: 'Orbitron'; }
    .copy-btn:active { transform: scale(0.95); }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if 'results' not in st.session_state:
    st.session_state.results = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"live": 0, "verify": 0, "disabled": 0, "unregistered": 0, "bad": 0}

# --- 3. HELPER FUNCTIONS ---
def auto_fix_email(email_str):
    """Mendeteksi dan memperbaiki email jika tanpa @gmail.com"""
    email = email_str.strip().lower()
    if not email: return None
    if "@" not in email:
        return f"{email}@gmail.com"
    return email

def call_checker_api(emails, token):
    url = "https://gmail-validation.mbahbabat.workers.dev/check1"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"mail": emails}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# --- 4. SIDEBAR & HEADER ---
with st.sidebar:
    st.title("🔑 SETTINGS")
    api_token = st.text_input("API Bearer Token:", type="password", placeholder="Paste your token here...")
    st.markdown("[Dapatkan Token Di Sini](https://mbahbabat.github.io/bulk-gmail-checker/id/execute/)")
    st.divider()
    st.caption("v1.0 - Powered by Mbahbabat API")

st.title("🛡️ BULK GMAIL CHECKER PRO")
st.write("Cek status akun Google massal dengan kecepatan tinggi dan hasil akurat.")

# --- 5. DASHBOARD STATS (LIVE) ---
stat_cols = st.columns(5)
metrics = {
    "live": stat_cols[0].empty(),
    "verify": stat_cols[1].empty(),
    "disabled": stat_cols[2].empty(),
    "unregistered": stat_cols[3].empty(),
    "bad": stat_cols[4].empty()
}

def update_metrics():
    for key in metrics:
        color_label = key.upper()
        metrics[key].metric(label=color_label, value=st.session_state.stats[key])

update_metrics()

# --- 6. INPUT AREA ---
email_input = st.text_area("Masukkan Email (per baris atau pisahkan dengan koma):", height=150, placeholder="user1\nuser2@gmail.com\nuser3")

col_start, col_clear, _ = st.columns([1.5, 1.5, 5])
btn_run = col_start.button("🚀 EXECUTE CHECK", use_container_width=True)
if col_clear.button("🧹 CLEAR ALL", use_container_width=True):
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in st.session_state.stats}
    st.rerun()

# Container untuk Live Result
live_result_container = st.container()

# --- 7. MAIN LOGIC ---
if btn_run:
    if not api_token:
        st.error("❌ Silakan masukkan API Token di sidebar!")
    elif not email_input:
        st.warning("⚠️ Masukkan daftar email terlebih dahulu!")
    else:
        # 1. Parsing & Auto-Fixing
        raw_emails = email_input.replace(",", "\n").split("\n")
        clean_emails = []
        for e in raw_emails:
            fixed = auto_fix_email(e)
            if fixed: clean_emails.append(fixed)
        
        # 2. Chunking (API Limit 100 per request)
        chunk_size = 100
        chunks = [clean_emails[i:i + chunk_size] for i in range(0, len(clean_emails), chunk_size)]
        
        progress_bar = st.progress(0)
        
        for idx, chunk in enumerate(chunks):
            api_results = call_checker_api(chunk, api_token)
            
            if api_results:
                for item in api_results:
                    email = item['email']
                    status = item['status'].lower()
                    
                    # Update Stats
                    if status in st.session_state.stats:
                        st.session_state.stats[status] += 1
                    
                    # Store Result
                    res_entry = {"email": email, "status": status}
                    st.session_state.results.insert(0, res_entry)
                    
                    # LIVE RESULT DISPLAY (Elegant Card with Copy Button)
                    with live_result_container:
                        status_class = f"status-{status}"
                        st.markdown(f"""
                            <div class="result-card">
                                <div>
                                    <span style="font-family: 'Roboto Mono';">{email}</span>
                                    <span class="{status_class}" style="margin-left: 15px;">[{status.upper()}]</span>
                                </div>
                                <button class="copy-btn" onclick="navigator.clipboard.writeText('{email}')">COPY</button>
                            </div>
                        """, unsafe_allow_html=True)
                
                update_metrics()
            
            progress = (idx + 1) / len(chunks)
            progress_bar.progress(progress)
            
        st.success(f"✅ Selesai! {len(clean_emails)} email telah diperiksa.")

# Tombol Download di Akhir
if st.session_state.results:
    st.divider()
    df = pd.DataFrame(st.session_state.results)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD CSV REPORT", data=csv, file_name="gmail_check_results.csv", mime="text/csv")
