import streamlit as st
import asyncio
import os
import sys
import subprocess
import pandas as pd
import random
from playwright.async_api import async_playwright

# --- 1. ENGINE BOOTSTRAP ---
def install_browser():
    try:
        # Install hanya chromium binary tanpa sudo deps
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except:
        return False

if 'browser_setup' not in st.session_state:
    with st.spinner("⚙️ Memulai Engine Browser..."):
        install_browser()
        st.session_state.browser_setup = True

# --- 2. UI CONFIG ---
st.set_page_config(page_title="Gmail V3 Checker Pro", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #e0e0e0; }
    [data-testid="stTable"] { font-size: 12px; }
    .status-live { color: #28a745; font-weight: bold; }
    .status-verif { color: #f39c12; font-weight: bold; }
    .status-disabled { color: #e74c3c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Session State Initialization
if 'results' not in st.session_state:
    st.session_state.results = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"ALL": 0, "Live": 0, "Verif (OTP)": 0, "Verif (Captcha)": 0, "Disabled": 0, "Unregistered": 0}

# --- 3. CORE CHECKER LOGIC (V3 Pattern) ---
async def check_v3(semaphore, browser, email):
    async with semaphore:
        # Stealth Context
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            locale="en-US" # Konsisten dalam Bahasa Inggris
        )
        page = await context.new_page()
        res_status = "Unknown/Error"
        
        try:
            # Akses Endpoint V3 Sign-in
            await page.goto('https://accounts.google.com/v3/signin/identifier?flowName=GlifWebSignIn', timeout=60000)
            
            # Input Email dengan Human-like delay
            await page.fill('input[type="email"]', email)
            await asyncio.sleep(random.uniform(0.5, 1.2))
            await page.keyboard.press("Enter")
            
            # Tunggu perubahan URL (Deteksi Pola V3)
            # timeout 10 detik untuk transisi halaman
            try:
                await page.wait_for_url(lambda url: "identifier" not in url, timeout=12000)
            except:
                pass 
            
            current_url = page.url
            content = await page.content()

            # --- LOGIKA VALIDASI BERDASARKAN LINK TEST USER ---
            
            # 1. LIVE: Lanjut ke input password
            if "/challenge/pwd" in current_url or await page.query_selector('input[type="password"]'):
                res_status = "Live"
            
            # 2. VERIF CAPTCHA: Muncul tantangan bot (Link test #2 & #3)
            elif "/challenge/recaptcha" in current_url or "captcha" in content.lower():
                res_status = "Verif (Captcha)"
            
            # 3. VERIF OTP: Minta verifikasi nomor/identitas
            elif "/challenge/selection" in current_url or "/challenge/challenge" in current_url:
                res_status = "Verif (OTP)"
            
            # 4. UNREGISTERED: Tetap di identifier dan ada pesan error
            elif "Gagal menemukan" in content or "Couldn't find" in content:
                res_status = "Unregistered"
            
            # 5. DISABLED: Pesan akun dinonaktifkan
            elif "disabled" in current_url or "disabled" in content.lower() or "violation" in content:
                res_status = "Disabled"
            
            else:
                res_status = "Bad/Rate Limit"

        except Exception:
            res_status = "Timeout"
        finally:
            await context.close()
            return {"Email": email, "Status": res_status}

# --- 4. DASHBOARD UI ---
st.title("🛡️ Gmail Bulk Checker V3 Pro")
st.caption("Mode: Parallel Async | Stealth: Enabled | Version: 3.0 (Turbo)")

# Metrics Placeholder
stats_ui = st.empty()

def render_stats():
    with stats_ui.container():
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("TOTAL", len(st.session_state.results))
        m2.metric("LIVE ✅", st.session_state.stats["Live"])
        m3.metric("VERIF OTP 🔑", st.session_state.stats["Verif (OTP)"])
        m4.metric("CAPTCHA 🤖", st.session_state.stats["Verif (Captcha)"])
        m5.metric("DISABLED 🚫", st.session_state.stats["Disabled"])
        m6.metric("UNREG ❓", st.session_state.stats["Unregistered"])

render_stats()

# Control Panel
email_list_raw = st.text_area("Masukkan Daftar Email:", height=150, placeholder="email1@gmail.com\nemail2@gmail.com")
col_a, col_b = st.columns([1, 4])
start_btn = col_a.button("🚀 EXECUTE", use_container_width=True)
clear_btn = col_b.button("🧹 CLEAR ALL")

if clear_btn:
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in st.session_state.stats}
    st.rerun()

# Table Placeholder for Live Results
table_ui = st.empty()

# --- 5. EXECUTION ENGINE ---
async def run_checker(emails):
    async with async_playwright() as p:
        # Stealth Launch
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        
        # Gunakan Semaphore 3 agar IP tidak cepat panas (Rate Limit)
        semaphore = asyncio.Semaphore(3)
        tasks = [check_v3(semaphore, browser, email) for email in emails]
        
        # Proses satu per satu saat selesai (Live Update)
        for task in asyncio.as_completed(tasks):
            result = await task
            
            # Update Session State
            st.session_state.results.insert(0, result)
            st.session_state.stats[result["Status"]] = st.session_state.stats.get(result["Status"], 0) + 1
            
            # Update UI Real-time
            render_stats()
            with table_ui.container():
                st.write("### 📋 Live Result Log")
                st.dataframe(pd.DataFrame(st.session_state.results), use_container_width=True, hide_index=True)

        await browser.close()

if start_btn and email_list_raw:
    emails = [e.strip() for e in email_list_raw.split('\n') if e.strip()]
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in st.session_state.stats}
    
    # Jalankan proses async
    asyncio.run(run_checker(emails))
    
    # Download Button after finish
    df_final = pd.DataFrame(st.session_state.results)
    st.download_button("📥 DOWNLOAD CSV RESULT", data=df_final.to_csv(index=False), file_name="checker_result.csv", mime="text/csv")
    st.success("✅ Pengecekan Selesai!")
