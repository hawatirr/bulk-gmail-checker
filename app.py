import streamlit as st
import asyncio
from playwright.async_api import async_playwright

st.set_page_config(page_title="Bulk Gmail Checker", layout="wide")

# Custom CSS agar mirip dashboard profesional
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #d1d5db; }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ Google Bulk Email Checker (No Login)")

# State untuk menyimpan hasil
if 'results_list' not in st.session_state:
    st.session_state.results_list = []
if 'stats' not in st.session_state:
    st.session_state.stats = {"ALL": 0, "Live": 0, "Verif": 0, "Disabled": 0, "Unregistered": 0}

# UI Input
email_input = st.text_area("Masukkan List Email (Satu per baris):", height=150)
col_btn1, col_btn2 = st.columns([1, 5])
start_btn = col_btn1.button("🚀 EXECUTE")
clear_btn = col_btn2.button("🧹 CLEAR")

if clear_btn:
    st.session_state.results_list = []
    st.session_state.stats = {"ALL": 0, "Live": 0, "Verif": 0, "Disabled": 0, "Unregistered": 0}
    st.rerun()

# Dashboard Statistik
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("ALL", st.session_state.stats["ALL"])
c2.metric("LIVE", st.session_state.stats["Live"], delta_color="normal")
c3.metric("VERIF", st.session_state.stats["Verif"])
c4.metric("DISABLED", st.session_state.stats["Disabled"])
c5.metric("UNREG", st.session_state.stats["Unregistered"])

async def check_email(email):
    async with async_playwright() as p:
        # Menjalankan browser tanpa tampilan (headless)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            # Gunakan halaman Recovery untuk intip status tanpa password
            await page.goto('https://accounts.google.com/signin/v2/recoveryidentifier', timeout=30000)
            await page.fill('input[type="email"]', email)
            await page.click('#recoveryIdentifierNext')
            await asyncio.sleep(3) # Jeda agar tidak dianggap bot
            
            content = await page.content()
            if "Couldn't find" in content or "Gagal menemukan" in content:
                return "Unregistered"
            elif "disabled" in content or "dinonaktifkan" in content:
                return "Disabled"
            elif "verification" in content or "verifikasi" in content:
                return "Verif"
            else:
                return "Live"
        except:
            return "Error"
        finally:
            await browser.close()

if start_btn and email_input:
    emails = [e.strip() for e in email_input.split('\n') if e.strip()]
    st.session_state.stats["ALL"] = len(emails)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, mail in enumerate(emails):
        status = asyncio.run(check_email(mail))
        
        # Update Stats & List
        st.session_state.stats[status] = st.session_state.stats.get(status, 0) + 1
        st.session_state.results_list.insert(0, {"email": mail, "status": status})
        
        # Update UI secara real-time
        progress_bar.progress((i + 1) / len(emails))
        status_text.text(f"Checking: {mail}...")
        
    st.rerun()

# Tabel Hasil
if st.session_state.results_list:
    st.write("### Result Details")
    st.table(st.session_state.results_list)
