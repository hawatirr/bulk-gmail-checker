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
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE (FIXED KEYERROR) ---
required_stats = ["ALL", "Live", "Verif (OTP)", "Verif (Captcha)", "Disabled", "Unregistered"]

if 'stats' not in st.session_state or not all(k in st.session_state.stats for k in required_stats):
    st.session_state.stats = {k: 0 for k in required_stats}

if 'results' not in st.session_state:
    st.session_state.results = []

# --- 4. CORE CHECKER LOGIC ---
async def check_v3(semaphore, browser, email):
    async with semaphore:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720},
            locale="en-US"
        )
        page = await context.new_page()
        res_status = "Unknown"
        
        try:
            await page.goto('https://accounts.google.com/v3/signin/identifier?flowName=GlifWebSignIn', timeout=60000)
            await page.fill('input[type="email"]', email)
            await page.keyboard.press("Enter")
            
            # Tunggu respon URL
            try:
                await page.wait_for_url(lambda url: "identifier" not in url, timeout=12000)
            except:
                pass 
            
            current_url = page.url
            content = await page.content()

            if "/challenge/pwd" in current_url or await page.query_selector('input[type="password"]'):
                res_status = "Live"
            elif "/challenge/recaptcha" in current_url or "captcha" in content.lower():
                res_status = "Verif (Captcha)"
            elif "/challenge/selection" in current_url or "/challenge/challenge" in current_url:
                res_status = "Verif (OTP)"
            elif "Gagal menemukan" in content or "Couldn't find" in content:
                res_status = "Unregistered"
            elif "disabled" in current_url or "disabled" in content.lower() or "violation" in content:
                res_status = "Disabled"
            else:
                res_status = "Bad/Rate Limit"

        except Exception:
            res_status = "Timeout"
        finally:
            await context.close()
            return {"Email": email, "Status": res_status}

# --- 5. DASHBOARD UI ---
st.title("🛡️ Gmail Bulk Checker V3 Pro")

stats_ui = st.empty()

def render_stats():
    with stats_ui.container():
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("TOTAL", len(st.session_state.results))
        # Menggunakan kunci yang sudah dipastikan ada
        m2.metric("LIVE ✅", st.session_state.stats.get("Live", 0))
        m3.metric("VERIF OTP 🔑", st.session_state.stats.get("Verif (OTP)", 0))
        m4.metric("CAPTCHA 🤖", st.session_state.stats.get("Verif (Captcha)", 0))
        m5.metric("DISABLED 🚫", st.session_state.stats.get("Disabled", 0))
        m6.metric("UNREG ❓", st.session_state.stats.get("Unregistered", 0))

render_stats()

email_list_raw = st.text_area("Masukkan Daftar Email:", height=150)
col_a, col_b = st.columns([1, 4])
start_btn = col_a.button("🚀 EXECUTE", use_container_width=True)
clear_btn = col_b.button("🧹 CLEAR ALL")

if clear_btn:
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in required_stats}
    st.rerun()

table_ui = st.empty()

async def run_checker(emails):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        semaphore = asyncio.Semaphore(3)
        tasks = [check_v3(semaphore, browser, email) for email in emails]
        
        for task in asyncio.as_completed(tasks):
            result = await task
            st.session_state.results.insert(0, result)
            st.session_state.stats[result["Status"]] = st.session_state.stats.get(result["Status"], 0) + 1
            
            render_stats()
            with table_ui.container():
                st.dataframe(pd.DataFrame(st.session_state.results), use_container_width=True, hide_index=True)
        await browser.close()

if start_btn and email_list_raw:
    emails = [e.strip() for e in email_list_raw.split('\n') if e.strip()]
    st.session_state.results = []
    st.session_state.stats = {k: 0 for k in required_stats}
    asyncio.run(run_checker(emails))
    st.success("✅ Selesai!")
