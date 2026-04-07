import streamlit as st
import asyncio
import os  # <--- Ini yang tadi menyebabkan NameError jika terlewat
import subprocess
from playwright.async_api import async_playwright

# 1. Fungsi untuk Install Browser di Server (Hanya jalan sekali)
def install_playwright():
    try:
        # Menjalankan perintah terminal dari dalam Python
        subprocess.run(["playwright", "install", "chromium"], check=True)
        return True
    except Exception as e:
        st.error(f"Error installing browser: {e}")
        return False

# Jalankan instalasi saat pertama kali buka website
if 'browser_installed' not in st.session_state:
    with st.spinner("📦 Menyiapkan mesin browser (ini hanya sekali)..."):
        if install_playwright():
            st.session_state.browser_installed = True

# 2. Konfigurasi UI Dashboard
st.set_page_config(page_title="Bulk Gmail Checker", layout="wide")

st.title("🛡️ Google Bulk Email Checker")
st.write("Cek status email massal (Live, Verif, Unreg, Disabled) tanpa login.")

# Inisialisasi data di memori
if 'results_list' not in st.session_state:
    st.session_state.results_list = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"ALL": 0, "Live": 0, "Verif": 0, "Disabled": 0, "Unregistered": 0}

# --- Tampilan Statistik ---
cols = st.columns(5)
cols[0].metric("ALL", st.session_state.stats["ALL"])
cols[1].metric("LIVE", st.session_state.stats["Live"])
cols[2].metric("VERIF", st.session_state.stats["Verif"])
cols[3].metric("DISABLED", st.session_state.stats["Disabled"])
cols[4].metric("UNREG", st.session_state.stats["Unregistered"])

# Input List Email
email_input = st.text_area("Masukkan Email (per baris):", height=150, placeholder="email@gmail.com")
col1, col2 = st.columns([1, 5])
btn_run = col1.button("🚀 MULAI")
btn_clear = col2.button("🧹 BERSIHKAN")

if btn_clear:
    st.session_state.results_list = []
    st.session_state.stats = {k: 0 for k in st.session_state.stats}
    st.rerun()

# 3. Logika Utama Pengecekan
async def check_email(email):
    async with async_playwright() as p:
        # Launch browser dengan mode headless (tanpa tampilan)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            # Gunakan Recovery Endpoint
            await page.goto('https://accounts.google.com/signin/v2/recoveryidentifier', timeout=60000)
            await page.fill('input[type="email"]', email)
            await page.click('#recoveryIdentifierNext')
            await asyncio.sleep(3) # Jeda agar tidak dianggap robot
            
            content = await page.content()
            if "Gagal menemukan" in content or "Couldn't find" in content:
                return "Unregistered"
            elif "dinonaktifkan" in content or "disabled" in content:
                return "Disabled"
            elif "verifikasi" in content or "verification" in content or "otp" in content.lower():
                return "Verif"
            else:
                return "Live"
        except Exception:
            return "Error"
        finally:
            await browser.close()

# 4. Eksekusi saat Tombol Mulai diklik
if btn_run and email_input:
    emails = [e.strip() for e in email_input.split('\n') if e.strip()]
    st.session_state.stats["ALL"] = len(emails)
    
    status_bar = st.progress(0)
    
    for i, mail in enumerate(emails):
        status = asyncio.run(check_email(mail))
        
        # Update statistik & hasil
        st.session_state.stats[status] = st.session_state.stats.get(status, 0) + 1
        st.session_state.results_list.insert(0, {"Email": mail, "Status": status})
        
        # Update UI secara visual
        status_bar.progress((i + 1) / len(emails))
        
    st.rerun()

# Tampilkan Tabel Hasil
if st.session_state.results_list:
    st.write("---")
    st.write("### 📋 Detail Hasil")
    st.table(st.session_state.results_list)
