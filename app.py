import streamlit as st
import asyncio
import os
import sys
import subprocess
import pandas as pd
import random
from playwright.async_api import async_playwright

# --- 1. SETUP ENGINE (Force Install) ---
def setup_browser():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except: return False

if 'engine_ready' not in st.session_state:
    with st.spinner("🛠️ Optimizing Engine..."):
        setup_browser()
        st.session_state.engine_ready = True

# --- 2. ADVANCED CHECKER LOGIC ---
async def check_gmail_stealth(semaphore, browser, email):
    async with semaphore:
        # Gunakan User-Agent yang lebih modern & bervariasi
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=1,
        )
        page = await context.new_page()
        status = "Bad/Limit"
        
        try:
            # Pola 1: Masuk ke halaman login utama (lebih "aman" dibanding recovery)
            await page.goto('https://accounts.google.com/signin/v2/identifier?flowName=GlifWebSignIn&flowEntry=ServiceLogin', 
                            wait_until="networkidle", timeout=60000)
            
            # Pola 2: Ketik manual dengan delay random (Mimic Human)
            await page.fill('input[type="email"]', email)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.keyboard.press("Enter")
            
            # Tunggu respon (Google butuh waktu untuk validasi)
            await asyncio.sleep(random.uniform(3.0, 5.0))
            
            content = await page.content()
            url = page.url

            # --- POOLA DETEKSI AKURAT ---
            
            # 1. Cek Unregistered (Elemen Error Merah)
            if "Gagal menemukan" in content or "Couldn't find" in content or 'div[aria-live="assertive"]' in content:
                status = "Unregistered"
            
            # 2. Cek Disabled (Pesan spesifik Akun Dinonaktifkan)
            elif "dinonaktifkan" in content or "disabled" in content or "violation" in content:
                status = "Disabled"
            
            # 3. Cek Verif / OTP (Minta konfirmasi HP atau Email Pemulihan)
            elif "challenge" in url or "verify" in url or "verifikasi" in content.lower() or "confirm" in content:
                status = "Verif"
                
            # 4. Cek LIVE (Berhasil lolos ke halaman input Password)
            # Ditandai dengan adanya field password atau profil user muncul
            elif await page.query_selector('input[type="password"]') or "password" in url or "Welcome" in content:
                status = "Live"
            
            # 5. Cek Rate Limited (Jika muncul Captcha atau "Terlalu banyak percobaan")
            elif "Too many attempts" in content or "captcha" in content.lower():
                status = "Rate Limited"
            
            else:
                status = "Bad"

        except Exception as e:
            status = "Timeout/Error"
        finally:
            await context.close()
            return {"Email": email, "Status": status}

# --- 3. UI DASHBOARD ---
st.set_page_config(page_title="Gmail Stealth Checker", layout="wide")
st.title("🛡️ Gmail Stealth Bulk Checker")

if 'results' not in st.session_state:
    st.session_state.results = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"ALL": 0, "Live": 0, "Verif": 0, "Disabled": 0, "Unregistered": 0, "Rate Limited": 0}

# Metrik Real-time
stats_placeholder = st.empty()

def update_stats_ui():
    with stats_placeholder.container():
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("ALL", len(st.session_state.results))
        m2.metric("LIVE", st.session_state.stats.get("Live", 0))
        m3.metric("VERIF", st.session_state.stats.get("Verif", 0))
        m4.metric("DISABLED", st.session_state.stats.get("Disabled", 0))
        m5.metric("UNREG", st.session_state.stats.get("Unregistered", 0))
        m6.metric("LIMIT", st.session_state.stats.get("Rate Limited", 0))

update_stats_ui()

# Control Area
email_input = st.text_area("List Email:", height=150)
btn_exec = st.button("🚀 EXECUTE STEALH CHECK", use_container_width=True)
table_placeholder = st.empty()

async def start_process(emails):
    async with async_playwright() as p:
        # Launcher dengan beberapa argumen anti-bot
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox'
        ])
        
        # Gunakan Semaphore 3 agar tidak terlalu brutal (Google benci ribuan req dari 1 IP)
        semaphore = asyncio.Semaphore(3) 
        tasks = [check_gmail_stealth(semaphore, browser, email) for email in emails]
        
        for task in asyncio.as_completed(tasks):
            res = await task
            st.session_state.results.insert(0, res)
            st.session_state.stats[res["Status"]] = st.session_state.stats.get(res["Status"], 0) + 1
            
            # Live Update UI
            update_stats_ui()
            table_placeholder.table(pd.DataFrame(st.session_state.results).head(10))

    st.success("✅ Done!")

if btn_exec and email_input:
    email_list = [e.strip() for e in email_input.split('\n') if e.strip()]
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in st.session_state.stats}
    asyncio.run(start_process(email_list))
