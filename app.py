import streamlit as st
import asyncio
import os
import sys
import subprocess
import pandas as pd
import random
from playwright.async_api import async_playwright

# --- 1. ENGINE SETUP ---
def install_browser():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except: return False

if 'engine_ready' not in st.session_state:
    with st.spinner("🛠️ Menyiapkan Mesin Browser Sendiri..."):
        install_browser()
        st.session_state.engine_ready = True

# --- 2. UI & STATE ---
st.set_page_config(page_title="Private Gmail Checker", layout="wide")
status_keys = ["ALL", "Live", "Verif", "Disabled", "Unregistered", "Bad"]

if 'stats' not in st.session_state or not all(k in st.session_state.stats for k in status_keys):
    st.session_state.stats = {k: 0 for k in status_keys}
if 'results' not in st.session_state:
    st.session_state.results = []

# --- 3. LOGIKA DETEKSI AKURAT (V3 PATTERN) ---
async def check_gmail_engine(semaphore, browser, email):
    async with semaphore:
        # Gunakan sidik jari browser asli
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            locale="en-US"
        )
        page = await context.new_page()
        res_status = "Bad"
        
        try:
            # Akses Login Google
            await page.goto('https://accounts.google.com/v3/signin/identifier?flowName=GlifWebSignIn', timeout=60000)
            await page.fill('input[type="email"]', email)
            await page.keyboard.press("Enter")
            
            # RACE CONDITION: Tunggu salah satu elemen penentu muncul
            # Password field (Live), Error message (Unreg), atau Challenge (Verif)
            try:
                await page.wait_for_selector('input[type="password"], #identifierError, [aria-live="assertive"], div:has-text("Verify it\'s you"), div:has-text("disabled")', timeout=15000)
            except:
                pass 
            
            content = await page.content()
            url = page.url

            # --- PENENTUAN STATUS BERDASARKAN ELEMEN & URL ---
            
            # 1. UNREGISTERED (Email tidak ada)
            if "Couldn't find" in content or "Gagal menemukan" in content or await page.query_selector('#identifierError'):
                res_status = "Unregistered"
            
            # 2. DISABLED (Akun kena ban)
            elif "disabled" in content or "dinonaktifkan" in content or "denied" in url:
                res_status = "Disabled"
            
            # 3. VERIF (Minta OTP / Captcha / Confirm)
            # Sesuai pola link test: /challenge/recaptcha atau /challenge/selection
            elif "/challenge/recaptcha" in url or "/challenge/selection" in url or "/challenge/challenge" in url or "Verify it's you" in content:
                res_status = "Verif"
            
            # 4. LIVE (Berhasil lolos ke input password)
            # Sesuai pola link test: /challenge/pwd
            elif "/challenge/pwd" in url or await page.query_selector('input[type="password"]'):
                res_status = "Live"
            
            # 5. BAD (Rate limit atau Captcha di awal)
            elif "Too many attempts" in content or "captcha" in content.lower():
                res_status = "Bad"
            else:
                res_status = "Bad"

        except:
            res_status = "Bad"
        finally:
            await context.close()
            return {"Email": email, "Status": res_status}

# --- 4. DASHBOARD UI ---
st.title("🛡️ Private Bulk Gmail Checker")

# Metrik Atas
stats_container = st.empty()
def update_stats():
    with stats_container.container():
        m = st.columns(6)
        m[0].metric("ALL", len(st.session_state.results))
        m[1].metric("LIVE ✅", st.session_state.stats["Live"])
        m[2].metric("VERIF 🔑", st.session_state.stats["Verif"])
        m[3].metric("DISABLED 🚫", st.session_state.stats["Disabled"])
        m[4].metric("UNREG ❓", st.session_state.stats["Unregistered"])
        m[5].metric("BAD ⚠️", st.session_state.stats["Bad"])

update_stats()

# Input
email_raw = st.text_area("Masukkan Email (per baris):", height=150)
c1, c2 = st.columns([1, 4])
btn_exec = c1.button("🚀 EXECUTE", use_container_width=True)
if c2.button("🧹 RESET"):
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in status_keys}
    st.rerun()

table_placeholder = st.empty()

# --- 5. EXECUTION ---
async def start_checker(emails):
    async with async_playwright() as p:
        # Launch browser dengan mode sembunyi (Stealth)
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        
        # Kecepatan 2 email sekaligus (Agar IP server tidak cepat diblokir)
        semaphore = asyncio.Semaphore(2)
        tasks = [check_gmail_engine(semaphore, browser, email) for email in emails]
        
        for task in asyncio.as_completed(tasks):
            res = await task
            # Simpan hasil secara real-time
            st.session_state.results.insert(0, res)
            st.session_state.stats[res["Status"]] = st.session_state.stats.get(res["Status"], 0) + 1
            
            # Update UI secara Live
            update_stats()
            with table_placeholder.container():
                st.dataframe(pd.DataFrame(st.session_state.results), use_container_width=True, hide_index=True)
        
        await browser.close()

if btn_exec and email_raw:
    list_mail = [e.strip() for e in email_raw.split('\n') if e.strip()]
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in status_keys}
    asyncio.run(start_checker(list_mail))
    st.success("✅ Pengecekan Selesai!")
