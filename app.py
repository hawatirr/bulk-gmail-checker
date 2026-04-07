import streamlit as st
import asyncio
import os
import sys
import subprocess
import pandas as pd
import random
from playwright.async_api import async_playwright

# --- 1. SETUP ENGINE ---
def setup_browser():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except:
        return False

if 'engine_ready' not in st.session_state:
    with st.spinner("🛠️ Memanaskan Mesin..."):
        setup_browser()
        st.session_state.engine_ready = True

# --- 2. CONFIG ---
st.set_page_config(page_title="Gmail Bulk Turbo", layout="wide")
st.markdown("""
    <style>
    .reportview-container .main { background-color: #f0f2f6; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
    </style>
""", unsafe_allow_html=True)

if 'results' not in st.session_state:
    st.session_state.results = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"ALL": 0, "Live": 0, "Verif": 0, "Disabled": 0, "Unregistered": 0}

# --- 3. LOGIKA CHECKER (AKURAT & PARALEL) ---
async def check_single_email(semaphore, browser, email):
    async with semaphore: # Batasi jumlah pengecekan simultan
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            locale="en-US" # Paksa bahasa Inggris agar deteksi kata kunci akurat
        )
        page = await context.new_page()
        status = "Error"
        
        try:
            # Bypass deteksi bot dengan navigasi natural
            await page.goto('https://accounts.google.com/signin/v2/recoveryidentifier', timeout=60000)
            await page.fill('input[type="email"]', email)
            await page.keyboard.press("Enter")
            
            # Tunggu transisi halaman atau munculnya pesan error
            await asyncio.sleep(3.5) 
            
            content = await page.content()
            url = page.url

            # LOGIKA FILTER LEBIH DETAIL (BERDASARKAN ELEMEN & URL)
            if "Couldn't find" in content or "Gagal menemukan" in content:
                status = "Unregistered"
            elif "denied" in url or "disabled" in url or "Account disabled" in content:
                status = "Disabled"
            elif "challenge" in url or "confirm" in url or "verification" in content.lower():
                status = "Verif"
            elif "v2/recoverypassword" in url or "Enter your password" in content or "Enter the last password" in content:
                # Jika dia lanjut ke halaman password, berarti akun SEHAT/LIVE
                status = "Live"
            else:
                # Jika Google minta Captcha karena terlalu cepat
                status = "Rate Limited/Bad"

        except Exception:
            status = "Timeout"
        finally:
            await context.close()
            return {"Email": email, "Status": status}

# --- 4. DASHBOARD UI ---
st.title("🛡️ Gmail Bulk Turbo Checker")

# Baris Statistik (Real-time update)
stats_container = st.container()
with stats_container:
    m1, m2, m3, m4, m5 = st.columns(5)
    st_all = m1.metric("ALL", st.session_state.stats["ALL"])
    st_live = m2.metric("LIVE", st.session_state.stats["Live"])
    st_verif = m3.metric("VERIF", st.session_state.stats["Verif"])
    st_dis = m4.metric("DISABLED", st.session_state.stats["Disabled"])
    st_unreg = m5.metric("UNREG", st.session_state.stats["Unregistered"])

# Input
email_input = st.text_area("Masukkan Email (per baris):", height=150)
btn_start = st.button("🚀 JALANKAN SEKARANG", use_container_width=True)

# Placeholder untuk Tabel Live Result
table_placeholder = st.empty()

# --- 5. EKSEKUSI PARALEL ---
async def run_bulk_check(emails):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        semaphore = asyncio.Semaphore(5) # Maksimal 5 email dicek sekaligus agar aman
        
        tasks = []
        for email in emails:
            tasks.append(check_single_email(semaphore, browser, email))
            
        # Kita ambil hasilnya satu per satu saat selesai (as_completed)
        for task in asyncio.as_completed(tasks):
            result = await task
            
            # Update Session State
            st.session_state.results.insert(0, result)
            st.session_state.stats[result["Status"]] = st.session_state.stats.get(result["Status"], 0) + 1
            
            # UPDATE UI SECARA LIVE
            with stats_container:
                st_all.metric("ALL", len(st.session_state.results))
                st_live.metric("LIVE", st.session_state.stats.get("Live", 0))
                st_verif.metric("VERIF", st.session_state.stats.get("Verif", 0))
                st_dis.metric("DISABLED", st.session_state.stats.get("Disabled", 0))
                st_unreg.metric("UNREG", st.session_state.stats.get("Unregistered", 0))
            
            # Render Tabel Terbaru
            df = pd.DataFrame(st.session_state.results)
            table_placeholder.table(df.head(15)) # Tampilkan 15 hasil terbaru saja agar tidak berat

        await browser.close()

if btn_start and email_input:
    email_list = [e.strip() for e in email_input.split('\n') if e.strip()]
    # Reset stats
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in st.session_state.stats}
    
    # Jalankan Async
    asyncio.run(run_bulk_check(email_list))
    st.success("✅ Semua email selesai diperiksa!")
