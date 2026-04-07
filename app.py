import streamlit as st
import asyncio
import os
import sys
import subprocess
import pandas as pd
import random
from playwright.async_api import async_playwright

# --- 1. ENGINE BOOTSTRAP (ANTI-ERROR) ---
def install_browser():
    try:
        # Install chromium binary ke environment Streamlit
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except:
        return False

if 'engine_ready' not in st.session_state:
    with st.spinner("🛠️ Menyiapkan Mesin Browser (Mohon Tunggu)..."):
        install_browser()
        st.session_state.engine_ready = True

# --- 2. UI CONFIG & STYLING ---
st.set_page_config(page_title="Gmail V3 Bulk Checker", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    [data-testid="stTable"] { font-size: 13px; font-family: 'Courier New', Courier, monospace; }
    </style>
""", unsafe_allow_html=True)

# Status 1-6 sesuai permintaan
STATUS_KEYS = ["ALL", "Live", "Verif", "Disabled", "Unregistered", "Bad"]

if 'stats' not in st.session_state or not all(k in st.session_state.stats for k in STATUS_KEYS):
    st.session_state.stats = {k: 0 for k in STATUS_KEYS}
if 'results_log' not in st.session_state:
    st.session_state.results_log = []

# --- 3. CORE LOGIC (STEALH DETECTION) ---
async def check_email_v3(semaphore, browser, email):
    async with semaphore:
        # Context dengan sidik jari browser asli
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            locale="en-US" # Paksa Inggris agar deteksi teks akurat
        )
        page = await context.new_page()
        res_status = "Bad"
        
        try:
            # Masuk ke V3 Identifier
            await page.goto('https://accounts.google.com/v3/signin/identifier?flowName=GlifWebSignIn', timeout=60000)
            
            # Input Email dengan delay mengetik manusia
            await page.fill('input[type="email"]', email)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            await page.keyboard.press("Enter")
            
            # Tunggu respon dinamis (Max 10 detik)
            await asyncio.sleep(4.5) 
            
            content = await page.content()
            url = page.url

            # --- LOGIKA PENENTUAN STATUS (AKURAT) ---
            
            # 1. Cek UNREGISTERED (Email tidak ditemukan)
            if "Gagal menemukan" in content or "Couldn't find" in content or "doesn't exist" in content:
                res_status = "Unregistered"
            
            # 2. Cek DISABLED (Akun kena Ban)
            elif "disabled" in content or "dinonaktifkan" in content or "violation" in content or "denied" in url:
                res_status = "Disabled"
            
            # 3. Cek VERIF (Minta OTP / reCAPTCHA / Selection)
            elif "/challenge/selection" in url or "/challenge/recaptcha" in url or "verify it's you" in content.lower():
                res_status = "Verif"
            
            # 4. Cek LIVE (Lolos ke halaman Password)
            elif "/challenge/pwd" in url or await page.query_selector('input[type="password"]'):
                res_status = "Live"
            
            # 5. Cek BAD (Rate limit atau stuck karena Captcha di awal)
            elif "captcha" in content.lower() or "Too many attempts" in content:
                res_status = "Bad"
            
            else:
                # Jika tidak ada error tapi tidak masuk halaman password
                res_status = "Bad"

        except Exception:
            res_status = "Bad"
        finally:
            await context.close()
            return {"Email": email, "Status": res_status}

# --- 4. DASHBOARD UI ---
st.title("🛡️ Gmail Bulk Checker Pro (V3-Turbo)")
st.caption("Status: Multi-threading Active | Anti-Detection: Stealth V2")

# Container Statistik
stats_ui = st.empty()
def refresh_stats():
    with stats_ui.container():
        cols = st.columns(6)
        cols[0].metric("ALL", len(st.session_state.results_log))
        cols[1].metric("LIVE ✅", st.session_state.stats["Live"])
        cols[2].metric("VERIF 🔑", st.session_state.stats["Verif"])
        cols[3].metric("DISABLED 🚫", st.session_state.stats["Disabled"])
        cols[4].metric("UNREG ❓", st.session_state.stats["Unregistered"])
        cols[5].metric("BAD ⚠️", st.session_state.stats["Bad"])

refresh_stats()

# Area Input & Control
email_raw = st.text_area("Masukkan Email (Per baris):", height=150, placeholder="emailanda@gmail.com")
c1, c2 = st.columns([1, 5])
btn_exec = c1.button("🚀 EXECUTE", use_container_width=True)
if c2.button("🧹 RESET"):
    st.session_state.results_log = []
    st.session_state.stats = {k: 0 for k in STATUS_KEYS}
    st.rerun()

# Placeholder Tabel Live Result
table_ui = st.empty()

# --- 5. EXECUTION ENGINE (CONCURRENT) ---
async def start_checker(emails):
    async with async_playwright() as p:
        # Launch browser dengan flag bypass bot
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        
        # Kecepatan 3 email sekaligus (Ideal untuk Streamlit Cloud)
        semaphore = asyncio.Semaphore(3)
        tasks = [check_email_v3(semaphore, browser, email) for email in emails]
        
        for task in asyncio.as_completed(tasks):
            res = await task
            
            # Update data ke memori
            st.session_state.results_log.insert(0, res)
            st.session_state.stats[res["Status"]] = st.session_state.stats.get(res["Status"], 0) + 1
            
            # Render ulang statistik & tabel secara LIVE
            refresh_stats()
            with table_ui.container():
                st.write("### 📋 Live Feed")
                st.dataframe(pd.DataFrame(st.session_state.results_log), use_container_width=True, hide_index=True)

        await browser.close()

if btn_exec and email_raw:
    list_mail = [e.strip() for e in email_raw.split('\n') if e.strip()]
    st.session_state.results_log = []
    st.session_state.stats = {k: 0 for k in STATUS_KEYS}
    
    asyncio.run(start_checker(list_mail))
    
    # Download Button
    final_df = pd.DataFrame(st.session_state.results_log)
    st.download_button("📥 DOWNLOAD RESULT (CSV)", data=final_df.to_csv(index=False), file_name="gmail_check_report.csv", mime="text/csv")
    st.success("✅ Selesai! Semua email telah diperiksa.")
