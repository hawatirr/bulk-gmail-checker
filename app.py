import streamlit as st
import requests
import pandas as pd
import time

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Gmail Checker API Pro", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .status-live { color: #28a745; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'results' not in st.session_state:
    st.session_state.results = []
if 'stats_counter' not in st.session_state:
    st.session_state.stats_counter = {"ALL": 0, "live": 0, "verify": 0, "disabled": 0, "unregistered": 0, "bad": 0}

# --- HEADER ---
st.title("🛡️ Bulk Gmail Checker API v1")
st.caption("Powered by Mbahbabat API Engine | High Accuracy & Speed")

# --- SIDEBAR (INPUT API KEY) ---
with st.sidebar:
    st.header("🔑 Authentication")
    api_key = st.text_input("Enter your Bearer Token:", type="password", help="Dapatkan token dari menu 'AKUN SAYA' di situs mbahbabat")
    st.info("Kunci API dibatasi 500.000 req/hari.")
    
    if st.button("Check API Quota"):
        if api_key:
            res = requests.get(f"https://gmail-validation.mbahbabat.workers.dev/stats?key={api_key}")
            if res.status_code == 200:
                st.json(res.json())
            else:
                st.error("Invalid API Key")

# --- DASHBOARD METRICS ---
m = st.columns(6)
m[0].metric("TOTAL", len(st.session_state.results))
m[1].metric("LIVE ✅", st.session_state.stats_counter["live"])
m[2].metric("VERIFY 🔑", st.session_state.stats_counter["verify"])
m[3].metric("DISABLED 🚫", st.session_state.stats_counter["disabled"])
m[4].metric("UNREG ❓", st.session_state.stats_counter["unregistered"])
m[5].metric("BAD ⚠️", st.session_state.stats_counter["bad"])

# --- INPUT AREA ---
email_input = st.text_area("Masukkan Daftar Email (Satu per baris):", height=150, placeholder="email1@gmail.com\nemail2@gmail.com")
col_a, col_b = st.columns([1, 4])
btn_run = col_a.button("🚀 EXECUTE", use_container_width=True)
if col_b.button("🧹 RESET"):
    st.session_state.results = []
    st.session_state.stats_counter = {k: 0 for k in st.session_state.stats_counter}
    st.rerun()

table_placeholder = st.empty()

# --- LOGIKA PENGECEKAN API ---
def check_via_api(email_list, token):
    url = "https://gmail-validation.mbahbabat.workers.dev/check1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"mail": email_list}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("❌ API Key Salah atau Expired!")
            return None
        else:
            st.error(f"❌ Server Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return None

# --- EXECUTION ---
if btn_run:
    if not api_key:
        st.warning("⚠️ Masukkan API Key dulu di sidebar!")
    elif not email_input:
        st.warning("⚠️ Masukkan daftar email!")
    else:
        emails = [e.strip() for e in email_input.split('\n') if e.strip()]
        
        # Sesuai dokumentasi, /check1 maksimal 100 email per request
        # Kita bagi menjadi chunks agar tidak overload
        chunk_size = 100
        email_chunks = [emails[i:i + chunk_size] for i in range(0, len(emails), chunk_size)]
        
        progress_bar = st.progress(0)
        
        for idx, chunk in enumerate(email_chunks):
            results = check_via_api(chunk, api_key)
            
            if results:
                for item in results:
                    status = item['status'].lower()
                    # Update data ke memori
                    st.session_state.results.insert(0, {
                        "Email": item['email'],
                        "Status": status.upper(),
                        "Details": item.get('details', '-')
                    })
                    # Update counter
                    if status in st.session_state.stats_counter:
                        st.session_state.stats_counter[status] += 1
                    else:
                        st.session_state.stats_counter["bad"] += 1
                
                # Update UI Live
                progress = (idx + 1) / len(email_chunks)
                progress_bar.progress(progress)
                
                # Render Tabel
                with table_placeholder.container():
                    st.dataframe(pd.DataFrame(st.session_state.results), use_container_width=True, hide_index=True)
            
            # Jeda sedikit agar tidak kena rate limit
            time.sleep(0.5)
            
        st.success("✅ Semua email selesai diperiksa!")
        st.rerun()

# --- DOWNLOAD RESULT ---
if st.session_state.results:
    df_final = pd.DataFrame(st.session_state.results)
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD RESULT (CSV)", data=csv, file_name="gmail_check_api.csv", mime="text/csv")
