import streamlit as st
import asyncio
import os
import sys
import subprocess
import pandas as pd
from playwright.async_api import async_playwright

# --- KONFIGURASI INSTALASI BROWSER ---
def install_playwright():
    """Fungsi untuk menginstal Chromium di server Streamlit Cloud"""
    try:
        # Menjalankan perintah instalasi menggunakan executable python yang aktif
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        # Instalasi dependencies tambahan jika diperlukan
        subprocess.run([sys.executable, "-m", "playwright", "install-deps"], check=True)
        return True
    except Exception as e:
        st.error(f"Gagal menginstal engine browser: {e}")
        return False

# Jalankan instalasi otomatis di awal
if 'browser_ready' not in st.session_state:
    with st.spinner("🚀 Menyiapkan Engine Browser (Hanya dilakukan sekali)..."):
        if install_playwright():
            st.session_state.browser_ready = True
        else:
            st.stop() # Hentikan jika instalasi gagal total

# --- KONFIGURASI DASHBOARD UI ---
st.set_page_config(page_title="Ultra Bulk Gmail Checker", layout="wide")

# Custom CSS untuk tampilan Dashboard
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Google Bulk Email Checker")
st.caption("Validasi status email massal (Live, Verif, Unreg, Disabled) tanpa perlu login.")

# Inisialisasi State Data
if 'results_data' not in st.session_state:
    st.session_state.results_data = []
if 'counts' not in st.session_state:
    st.session_state.counts = {"ALL": 0, "Live": 0, "Verif": 0, "Disabled": 0, "Unregistered": 0}

# --- BAGIAN STATISTIK ---
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("TOTAL", st.session_state.counts["ALL"])
m2.metric("LIVE ✅", st.session_state.counts["Live"])
m3.metric("VERIF 🔑", st.session_state.counts["Verif"])
m4.metric("DISABLED 🚫", st.session_state.counts["Disabled"])
m5.metric("UNREG ❓", st.session_state.counts["Unregistered"])

# --- INPUT AREA ---
email_input = st.text_area("Masukkan Daftar Email (Satu per baris):", height=200, placeholder="contoh@gmail.com\nuser123@gmail.com")

col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
start_exec = col_btn1.button("🚀 MULAI CEK", use_container_width=True)
clear_data = col_btn2.button("🧹 CLEAR", use_container_width=True)

if clear_data:
    st.session_state.results_data = []
    st.session_state.counts = {k: 0 for k in st.session_state.counts}
    st.rerun()

# --- LOGIKA PENGECEKAN (ASYNC) ---
async def check_gmail_status(email):
    async with async_playwright() as p:
        # Jalankan browser tanpa GUI
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        try:
            # Gunakan endpoint recovery Google (Tanpa Password)
            await page.goto('https://accounts.google.com/signin/v2/recoveryidentifier', timeout=60000)
            await page.fill('input[type="email"]', email)
            await page.click('#recoveryIdentifierNext')
            
            # Tunggu respon visual dari Google
            await asyncio.sleep(3) 
            
            content = await page.content()
            
            if "Gagal menemukan" in content or "Couldn't find" in content:
                return "Unregistered"
            elif "dinonaktifkan" in content or "disabled" in content:
                return "Disabled"
            elif "verifikasi" in content or "verification" in content or "otp" in content.lower():
                return "Verif"
            else:
                # Jika tidak ada indikasi error, berarti akun "Live" (ada)
                return "Live"
        except:
            return "Error/Timeout"
        finally:
            await browser.close()

# --- EKSEKUSI ---
if start_exec and email_input:
    list_email = [e.strip() for e in email_input.split('\n') if e.strip()]
    st.session_state.counts["ALL"] = len(list_email)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, mail in enumerate(list_email):
        status_text.text(f"⏳ Sedang mengecek: {mail}...")
        res = asyncio.run(check_gmail_status(mail))
        
        # Update Data & Statistik
        st.session_state.counts[res] = st.session_state.counts.get(res, 0) + 1
        st.session_state.results_data.insert(0, {"Email": mail, "Status": res})
        
        # Update Progress
        progress_bar.progress((i + 1) / len(list_email))
    
    status_text.success("✅ Pengecekan Selesai!")
    st.rerun()

# --- TABEL HASIL & DOWNLOAD ---
if st.session_state.results_data:
    st.divider()
    df = pd.DataFrame(st.session_state.results_data)
    
    col_dl1, col_dl2 = st.columns([4, 1])
    col_dl1.subheader("📋 Laporan Hasil")
    
    # Fitur Download CSV
    csv = df.to_csv(index=False).encode('utf-8')
    col_dl2.download_button(
        label="📥 DOWNLOAD CSV",
        data=csv,
        file_name="hasil_cek_email.csv",
        mime="text/csv",
    )
    
    # Tampilkan Tabel dengan Warna Status
    st.dataframe(df, use_container_width=True)
