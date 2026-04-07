import streamlit as st
import asyncio
import os
import sys
import subprocess
import pandas as pd
import random
from playwright.async_api import async_playwright

# --- 1. SETUP ENGINE ---
def install_browser():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except: return False

if 'engine_ready' not in st.session_state:
    with st.spinner("🛠️ Menyiapkan Mesin Browser..."):
        install_browser()
        st.session_state.engine_ready = True

# --- 2. UI CONFIG ---
st.set_page_config(page_title="Gmail V3 Bulk Checker", layout="wide")
status_keys = ["ALL", "Live", "Verif", "Disabled", "Unregistered", "Bad"]

if 'stats' not in st.session_state or not all(k in st.session_state.stats for k in status_keys):
    st.session_state.stats = {k: 0 for k in status_keys}
if 'results' not in st.session_state:
    st.session_state.results = []

# --- 3. CORE LOGIC (DEEP DETECTION) ---
async def check_email_deep(semaphore, browser, email):
    async with semaphore:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800},
            locale="en-US"
        )
        page = await context.new_page()
        res_status = "Bad"
        
        try:
            # Akses Login
            await page.goto('https://accounts.google.com/v3/signin/identifier?flowName=GlifWebSignIn', timeout=60000)
            await page.fill('input[type="email"]', email)
            await page.keyboard.press("Enter")
            
            # TUNGGU ELEMEN SPESIFIK MUNCUL (Bukan cuma sleep)
            # Kita tunggu salah satu dari: Field Password, Pesan Error, atau Challenge OTP
            try:
                await page.wait_for_selector('input[type="password"], #identifierError, [aria-live="assertive"], div:has-text("Verify it\'s you"), div:has-text("disabled")', timeout=15000)
            except:
                pass 
            
            content = await page.content()
            url = page.url

            # --- LOGIKA VALIDASI BERDASARKAN ELEMEN ---
            
            # 1. Cek UNREGISTERED (ID Error identifierError muncul)
            if "Gagal menemukan" in content or "Couldn't find" in content or await page.query_selector('#identifierError'):
                res_status = "Unregistered"
            
            # 2. Cek DISABLED (Teks spesifik disabled)
            elif "disabled" in content or "dinonaktifkan" in content or "denied" in url:
                res_status = "Disabled"
            
            # 3. Cek VERIF (Minta OTP / reCAPTCHA / Challenge Selection)
            # Pola URL: /challenge/selection, /challenge/recaptcha, /challenge/challenge
            elif "/challenge/selection" in url or "/challenge/recaptcha" in url or "/challenge/challenge" in url or "Verify it's you" in content:
                res_status = "Verif"
            
            # 4. Cek LIVE (Berhasil Lolos ke halaman Input Password)
            # Pola URL: /challenge/pwd atau adanya field Password
            elif "/challenge/pwd" in url or await page.query_selector('input[type="password"]'):
                res_status = "Live"
            
            else:
                # Jika tidak terdeteksi apapun tapi ada indikasi captcha/limit
                if "Too many attempts" in content or "captcha" in content.lower():
                    res_status = "Bad"
                else:
                    res_status = "Bad"

        except Exception:
            res_status = "Bad"
        finally:
            await context.close()
            return {"Email": email, "Status": res_status}

# --- 4. DASHBOARD UI ---
st.title("🛡️ Gmail Bulk Checker (Fixed Accuracy)")

stats_ui = st.empty()
def refresh_stats():
    with stats_ui.container():
        m = st.columns(6)
        m[0].metric("ALL", len(st.session_state.results))
        m[1].metric("LIVE ✅", st.session_state.stats["Live"])
        m[2].metric("VERIF 🔑", st.session_state.stats["Verif"])
        m[3].metric("DISABLED 🚫", st.session_state.stats["Disabled"])
        m[4].metric("UNREG ❓", st.session_state.stats["Unregistered"])
        m[5].metric("BAD ⚠️", st.session_state.stats["Bad"])

refresh_stats()

email_raw = st.text_area("List Email:", height=150)
c1, c2 = st.columns([1, 4])
btn_exec = c1.button("🚀 EXECUTE", use_container_width=True)
if c2.button("🧹 RESET"):
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in status_keys}
    st.rerun()

table_ui = st.empty()

async def start_checker(emails):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        # Gunakan Semaphore 2 saja agar Google tidak curiga dan salah memberikan respon
        semaphore = asyncio.Semaphore(2)
        tasks = [check_email_deep(semaphore, browser, email) for email in emails]
        
        for task in asyncio.as_completed(tasks):
            res = await task
            st.session_state.results.insert(0, res)
            st.session_state.stats[res["Status"]] = st.session_state.stats.get(res["Status"], 0) + 1
            refresh_stats()
            with table_ui.container():
                st.dataframe(pd.DataFrame(st.session_state.results), use_container_width=True, hide_index=True)
        await browser.close()

if btn_exec and email_raw:
    list_mail = [e.strip() for e in email_raw.split('\n') if e.strip()]
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in status_keys}
    asyncio.run(start_checker(list_mail))
    st.success("✅ Pengecekan Selesai!")
