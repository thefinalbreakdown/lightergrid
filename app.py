# app.py
import streamlit as st
import asyncio
import time
from lighter import Lighter  # ← Official & correct import

st.set_page_config(page_title="Lighter Grid Bot • QZ45EM7CPQYA", layout="wide", page_icon="⚡")

# === YOUR REFERRAL BANNER (permanently baked in) ===
st.markdown("""
<div style="background:linear-gradient(90deg,#8b5cf6,#ec4899);padding:25px;border-radius:15px;text-align:center;margin-bottom:30px;">
<h1 style="margin:0;color:white;">⚡ Lighter.xyz Futures Grid Bot</h1>
<h3 style="margin:5px;color:white;">Zero fees • Bybit-style grid • 100% non-custodial</h3>
<a href="https://app.lighter.xyz/?referral=QZ45EM7CPQYA" target="_blank">
<button style="background:white;color:black;padding:14px 36px;border:none;border-radius:50px;font-size:20px;font-weight:bold;cursor:pointer;">
🎁 Get Bonus with Referral: QZ45EM7CPQYA
</button>
</a>
</div>
""", unsafe_allow_html=True)

st.title("🚀 Public Lighter Grid Bot")

# === Secure API Key Input ===
st.sidebar.header("🔑 Lighter API Credentials")
st.sidebar.markdown("**Create API key here → [app.lighter.xyz/settings/api](https://app.lighter.xyz/settings/api)**")

api_key = st.sidebar.text_input("API Key ID", type="password")
api_secret = st.sidebar.text_input("API Secret", type="password")

if not api_key or not api_secret:
    st.warning("⚠️ Enter your Lighter API Key + Secret to continue")
    st.stop()

# Initialize client
client = Lighter(api_key_id=api_key, api_secret=api_secret)

# === Grid Settings ===
st.sidebar.header("⚙️ Grid Settings")
symbol = st.sidebar.selectbox("Market", ["BTC-USD", "ETH-USD", "SOL-USD", "ARB-USD", "OP-USD"])
mode = st.sidebar.selectbox("Mode", ["Neutral", "Long", "Short"])
grid_type = st.sidebar.selectbox("Grid Type", ["Arithmetic (fixed $)", "Geometric (fixed %)"])
lower = st.sidebar.number_input("Lower Price", value=60000.0, step=50.0)
upper = st.sidebar.number_input("Upper Price", value=72000.0, step=50.0)
grids = st.sidebar.slider("Grid Levels", 10, 200, 50)
amount_usd = st.sidebar.number_input("USDT per Grid Level", value=25.0, min_value=5.0)
leverage = st.sidebar.slider("Leverage", 1, 125, 20)

# Start / Stop buttons
col1, col2 = st.columns(2)
start = col1.button("🚀 Start Grid Bot", type="primary", use_container_width=True)
stop = col2.button("🛑 Stop Bot", use_container_width=True)

# Session state
if "running" not in st.session_state:
    st.session_state.running = False
if "pnl" not in st.session_state:
    st.session_state.pnl = 0.0
if "last_update" not in st.session_state:
    st.session_state.last_update = 0

# Grid bot task
async def grid_bot_task():
    await client.connect()
    ticker = symbol

    while st.session_state.running:
        try:
            info = await client.get_info()
            mark_price = float(info["markets"][ticker]["markPrice"])
            account = await client.get_account()
            equity = float(account["equity"])

            # Calculate grid
            if grid_type.startswith("Arithmetic"):
                step = (upper - lower) / (grids - 1)
                prices = [round(lower + i * step, 4) for i in range(grids)]
            else:
                ratio = (upper / lower) ** (1 / (grids - 1))
                prices = [round(lower * (ratio ** i), 4) for i in range(grids)]

            # Cancel far orders
            orders = await client.get_open_orders(ticker)
            for order in orders:
                if abs(order["price"] - mark_price) / mark_price > 0.25:
                    await client.cancel_order(order["orderId"])

            # Place grid orders
            for p in prices:
                size = round((amount_usd / p) * leverage, 6)

                if mode in ["Neutral", "Long"] and p <= mark_price * 1.01:
                    await client.create_order(ticker, "Buy", size, price=p, reduce_only=False)
                if mode in ["Neutral", "Short"] and p >= mark_price * 0.99:
                    await client.create_order(ticker, "Sell", size, price=p, reduce_only=False)

            st.session_state.pnl = equity - 10000  # adjust base capital if needed
            st.session_state.last_update = time.time()
            await asyncio.sleep(6)

        except Exception as e:
            st.error(f"Bot error: {e}")
            await asyncio.sleep(10)

    await client.close()

# Start bot
if start and not st.session_state.running:
    st.session_state.running = True
    asyncio.create_task(grid_bot_task())
    st.success("✅ Grid bot started!")

# Stop bot
if stop and st.session_state.running:
    st.session_state.running = False
    st.warning("🛑 Grid bot stopped")

# Live dashboard
if st.session_state.running:
    st.metric("Status", "🟢 RUNNING")
    st.metric("Unrealized PnL", f"${st.session_state.pnl:+.2f}")
    st.info(f"Grid: {mode} • {grids} levels • ${amount_usd} per level • {leverage}x")
else:
    st.metric("Status", "🔴 Stopped")

st.caption("Your referral QZ45EM7CPQYA is baked in forever • Share this bot freely! ⚡")
