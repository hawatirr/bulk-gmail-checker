import streamlit as st
import asyncio
import os
import sys
import subprocess
import pandas as pd
import random
from playwright.async_api import async_playwright

# --- 1. ENGINE BOOTSTRAP ---
@st.cache_resource(show_spinner=False)
def install_playwright():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except:
        return False

# --- 2. CONFIG & INITIALIZATION ---
st.set_page_config(page_title="Gmail V3 Private Checker", layout="wide")

if 'setup_done' not in st.session_state:
    with st.spinner("🛠️ Menyiapkan Engine Browser..."):
        install_playwright()
        st.session_state.setup_done = True

# Definisikan Kunci Status
STATUS_KEYS = ["ALL", "Live", "Verif", "Disabled", "Unregistered", "Bad"]

if 'stats' not in st.session_state:
    st.session_state.stats = {k: 0 for k in STATUS_KEYS}
if 'results' not in st.session_state:
    st.session_state.results = []

# --- 3. CORE ACCURATE LOGIC ---
async def check_gmail_v3(semaphore, browser, email):
    async with semaphore:
        # Context dengan Sidik Jari Browser
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            locale="en-US"
        )
        page = await context.new_page()
        res_status = "Bad"
        
        try:
            # Akses Google V3
            await page.goto('https://accounts.google.com/v3/signin/identifier?flowName=GlifWebSignIn', timeout=60000)
            
            # Isi Email & Enter
            await page.fill('input[type="email"]', email)
            await asyncio.sleep(random.uniform(0.5, 1.0))
            await page.keyboard.press("Enter")
            
            # KUNCI AKURASI: Tunggu URL berubah dari 'identifier'
            try:
                # Tunggu max 12 detik sampai halaman berganti
                await page.wait_for_url(lambda url: "identifier" not in url, timeout=12000)
            except:
                pass 
            
            current_url = page.url
            content = await page.content()

            # --- DETEKSI BERDASARKAN POLA URL V3 & ELEMEN ---
            
            # 1. LIVE: Berhasil masuk ke tantangan Password (/challenge/pwd)
            if "/challenge/pwd" in current_url or await page.query_selector('input[type="password"]'):
                res_status = "Live"
            
            # 2. UNREGISTERED: Tetap di identifier atau muncul pesan error merah
            elif "Gagal menemukan" in content or "Couldn't find" in content or await page.query_selector('#identifierError'):
                res_status = "Unregistered"
            
            # 3. DISABLED: URL mengandung denied/disabled atau pesan khusus
            elif "disabled" in current_url or "disabled" in content.lower() or "dinonaktifkan" in content:
                res_status = "Disabled"
            
            # 4. VERIF: Pola recaptcha, selection, atau OTP (Berdasarkan link test kamu)
            elif "/challenge/recaptcha" in current_url or "/challenge/selection" in current_url or "/challenge/challenge" in current_url:
                res_status = "Verif"
            
            # 5. BAD/LIMIT: Terkena Captcha di awal atau "Too many attempts"
            elif "captcha" in content.lower() or "Too many attempts" in content:
                res_status = "Bad"
            
            else:
                res_status = "Bad"

        except Exception:
            res_status = "Bad"
        finally:
            await context.close()
            return {"Email": email, "Status": res_status}

# --- 4. DASHBOARD UI ---
st.title("🛡️ Gmail Bulk Checker V3 (Private Mode)")
st.info("Mesin mandiri tanpa API Key pihak ketiga.")

# Dashboard Metrik
stats_ui = st.empty()
def render_stats():
    with stats_ui.container():
        cols = st.columns(6)
        cols[0].metric("ALL", len(st.session_state.results))
        cols[1].metric("LIVE ✅", st.session_state.stats["Live"])
        cols[2].metric("VERIF 🔑", st.session_state.stats["Verif"])
        cols[3].metric("DISABLED 🚫", st.session_state.stats["Disabled"])
        cols[4].metric("UNREG ❓", st.session_state.stats["Unregistered"])
        cols[5].metric("BAD ⚠️", st.session_state.stats["Bad"])

render_stats()

# Input & Control
email_input = st.text_area("Masukkan Email (per baris):", height=150)
c1, c2 = st.columns([1, 4])
btn_run = c1.button("🚀 EXECUTE", use_container_width=True)
if c2.button("🧹 RESET"):
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in STATUS_KEYS}
    st.rerun()

table_ui = st.empty()

# --- 5. EXECUTION ---
async def start_process(emails):
    async with async_playwright() as p:
        # Launch browser dengan Anti-Bot flags
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox'
        ])
        
        # Kecepatan 1 (SANGAT PENTING untuk Streamlit Cloud agar RAM tidak crash)
        semaphore = asyncio.Semaphore(1) 
        tasks = [check_gmail_v3(semaphore, browser, email) for email in emails]
        
        # Live Update
        for task in asyncio.as_completed(tasks):
            res = await task
            # Update data
            st.session_state.results.insert(0, res)
            st.session_state.stats[res["Status"]] = st.session_state.stats.get(res["Status"], 0) + 1
            
            # Update Dashboard & Tabel secara Real-time
            render_stats()
            with table_ui.container():
                st.dataframe(pd.DataFrame(st.session_state.results), use_container_width=True, hide_index=True)
        
        await browser.close()

if btn_run and email_input:
    email_list = [e.strip() for e in email_input.split('\n') if e.strip()]
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in STATUS_KEYS}
    
    asyncio.run(start_process(email_list))
    
    # Download Button
    df_final = pd.DataFrame(st.session_state.results)
    st.download_button("📥 DOWNLOAD CSV", data=df_final.to_csv(index=False), file_name="check_result.csv", mime="text/csv")
    st.success("✅ Pengecekan Selesai!")
