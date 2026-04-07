import streamlit as st
import asyncio
import os
import sys
import subprocess
import pandas as pd
import random
from playwright.async_api import async_playwright

# --- 1. BOOTSTRAP ENGINE (Anti-Error Version) ---
def setup_browser():
    """Menginstal chromium tanpa menggunakan sudo/install-deps"""
    try:
        # Mencoba install chromium saja (user-level)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except:
        return False

if 'engine_ready' not in st.session_state:
    with st.spinner("🛠️ Menginisialisasi Mesin Antarmuka..."):
        setup_browser()
        st.session_state.engine_ready = True

# --- 2. CONFIG & STYLING ---
st.set_page_config(page_title="Gmail Bulk Pro", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: bold; }
    .stProgress .st-bo { background-color: #4CAF50; }
    .status-live { color: #28a745; font-weight: bold; }
    .status-verif { color: #ffc107; font-weight: bold; }
    .status-disabled { color: #dc3545; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if 'results' not in st.session_state:
    st.session_state.results = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"ALL": 0, "Live": 0, "Verif": 0, "Disabled": 0, "Unregistered": 0, "Bad": 0}

# --- 4. HEADER & DASHBOARD ---
st.title("🛡️ Gmail Bulk Pro Checker")
st.info("Status: Engine Ready ✅ | Anti-Detection: Active 🛡️")

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("TOTAL", st.session_state.stats["ALL"])
m2.metric("LIVE", st.session_state.stats["Live"], delta="Stable", delta_color="normal")
m3.metric("VERIF", st.session_state.stats["Verif"], delta="OTP Required", delta_color="off")
m4.metric("DISABLED", st.session_state.stats["Disabled"], delta="Banned", delta_color="inverse")
m5.metric("UNREG", st.session_state.stats["Unregistered"], delta="Not Found", delta_color="off")
m6.metric("BAD", st.session_state.stats["Bad"], delta="Login Fail", delta_color="inverse")

# --- 5. LOGIKA CHECKER (ADVANCED) ---
async def deep_check_email(email):
    async with async_playwright() as p:
        # Gunakan User-Agent acak agar tidak terbaca bot
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        ]
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=random.choice(user_agents))
        page = await context.new_page()
        
        try:
            # Pergi ke halaman recovery (Metode paling aman tanpa password)
            await page.goto('https://accounts.google.com/signin/v2/recoveryidentifier', wait_until="networkidle")
            
            # Simulasi mengetik seperti manusia
            await page.type('input[type="email"]', email, delay=random.randint(50, 150))
            await page.keyboard.press("Enter")
            
            # Tunggu respon dinamis
            await asyncio.sleep(random.uniform(2.5, 4.0)) 
            
            content = await page.content()
            current_url = page.url

            # LOGIKA PENENTU STATUS (Berdasarkan elemen UI Google)
            if "Couldn't find" in content or "Gagal menemukan" in content:
                return "Unregistered"
            elif "disabled" in content or "dinonaktifkan" in content or "melanggar" in content:
                return "Disabled"
            elif "verification" in content or "verifikasi" in content or "challenge" in current_url:
                return "Verif"
            elif "re-enter" in content or "password" in content.lower():
                # Jika dia minta password, artinya email itu LIVE dan AKTIF
                return "Live"
            else:
                # Jika tertahan di halaman aneh atau minta captcha terus menerus
                return "Bad"
                
        except Exception:
            return "Error/Timeout"
        finally:
            await browser.close()

# --- 6. INPUT & CONTROL ---
email_input = st.text_area("Masukkan Email (Satu baris satu email):", height=200)

c1, c2 = st.columns([1, 5])
btn_start = c1.button("🚀 EXECUTE", use_container_width=True)
btn_clear = c2.button("🧹 CLEAR DATA", use_container_width=False)

if btn_clear:
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in st.session_state.stats}
    st.rerun()

if btn_start and email_input:
    emails = [e.strip() for e in email_input.split('\n') if e.strip()]
    st.session_state.stats["ALL"] = len(emails)
    
    prog_bar = st.progress(0)
    log_status = st.empty()
    
    for i, mail in enumerate(emails):
        log_status.text(f"🔍 Checking: {mail} ({i+1}/{len(emails)})")
        
        status = asyncio.run(deep_check_email(mail))
        
        # Update Stats & List
        st.session_state.stats[status] = st.session_state.stats.get(status, 0) + 1
        st.session_state.results.insert(0, {"Timestamp": pd.Timestamp.now().strftime("%H:%M:%S"), "Email": mail, "Status": status})
        
        # UI Update
        prog_bar.progress((i + 1) / len(emails))
        
    log_status.success("🎉 Semua email telah selesai diperiksa!")
    st.rerun()

# --- 7. HASIL & EKSPOR ---
if st.session_state.results:
    st.divider()
    df = pd.DataFrame(st.session_state.results)
    
    col_h1, col_h2 = st.columns([4, 1])
    col_h1.subheader("📋 Detail Log Pemeriksaan")
    
    # Tombol Download
    csv = df.to_csv(index=False).encode('utf-8')
    col_h2.download_button("📥 DOWNLOAD CSV", data=csv, file_name="gmail_report.csv", mime="text/csv")
    
    # Tabel interaktif
    st.dataframe(
        df,
        column_config={
            "Status": st.column_config.TextColumn("Status", help="Live, Verif, Disabled, atau Unreg"),
            "Email": st.column_config.TextColumn("Alamat Email")
        },
        use_container_width=True,
        hide_index=True
    )
