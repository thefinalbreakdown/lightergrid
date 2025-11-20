import streamlit as st
import asyncio
from lighter_sdk.lighter import Lighter  # ← Correct & working import

st.set_page_config(page_title="Lighter Grid Bot • QZ45EM7CPQYA", layout="wide", page_icon="⚡")

# === PERMANENT REFERRAL BANNER ===
st.markdown("""
<div style="background:linear-gradient(90deg,#8b5cf6,#ec4899);padding:25px;border-radius:15px;text-align:center;margin-bottom:30px;">
<h1 style="margin:0;color:white;">⚡ Lighter.xyz Grid Bot</h1>
<h3 style="margin:5px;color:white;">Zero fees • Bybit-style grid • Non-custodial</h3>
<a href="https://app.lighter.xyz/?referral=QZ45EM7CPQYA" target="_blank">
<button style="background:white;color:black;padding:14px 36px;border:none;border-radius:50px;font-size:20px;font-weight:bold;">
🎁 Get Bonus – Referral: QZ45EM7CPQYA
</button>
</a>
</div>
""", unsafe_allow_html=True)

st.title("🚀 Lighter Futures Grid Bot (Public)")

# === Safe API Key Input ===
st.sidebar.header("🔑 Lighter API Key")
st.sidebar.markdown("Create → [app.lighter.xyz/settings/api](https://app.lighter.xyz/settings/api)")

api_key = st.sidebar.text_input("API Key ID", type="password")
api_secret = st.sidebar.text_input("API Secret", type="password")

if not (api_key and api_secret):
    st.stop()

client = Lighter(key=api_key, secret=api_secret)

# === Settings ===
st.sidebar.header("⚙️ Grid Settings")
symbol = st.sidebar.selectbox("Market", ["BTC", "ETH", "SOL", "ARB", "OP", "HYPE", "XRP"])
mode = st.sidebar.selectbox("Mode", ["Neutral", "Long", "Short"])
grid_type = st.sidebar.selectbox("Grid Type", ["Arithmetic", "Geometric"])
lower = st.sidebar.number_input("Lower Price", value=60000.0)
upper = st.sidebar.number_input("Upper Price", value=72000.0)
grids = st.sidebar.slider("Grid Levels", 10, 200, 50)
amount_usd = st.sidebar.number_input("USDT per Level", value=25.0)
leverage = st.sidebar.slider("Leverage", 1, 125, 20)

col1, col2 = st.columns(2)
start = col1.button("🚀 Start Bot", type="primary", use_container_width=True)
stop = col2.button("🛑 Stop Bot", use_container_width=True)

if "running" not in st.session_state:
    st.session_state.running = False

# === Grid Calculation ===
def calc_grid(lower, upper, n, gtype):
    if gtype == "Arithmetic":
        step = (upper - lower) / (n - 1)
        return [round(lower + i * step, 4) for i in range(n)]
    else:
        ratio = (upper / lower) ** (1 / (n - 1))
        return [round(lower * (ratio ** i), 4) for i in range(n)]

# === Bot Task ===
async def grid_bot():
    await client.init_client()
    ticker = f"{symbol}-USD" if symbol not in ["BTC", "ETH", "SOL"] else symbol + "-USD"
    prices = calc_grid(lower, upper, grids, grid_type)

    while st.session_state.running:
        try:
            info = await client.info()
            mark = float(info["markets"][ticker]["mark_price"])

            # Cancel far orders
            orders = await client.open_orders(ticker=ticker)
            for o in orders:
                if abs(o["price"] - mark) / mark > 0.2:
                    await client.cancel_order(ticker=ticker, order_id=o["order_id"])

            # Place grid
            for p in prices:
                size = round((amount_usd / p) * leverage, 6)

                if mode in ["Neutral", "Long"] and p < mark * 1.01:
                    await client.limit_order(ticker=ticker, amount=size, price=p, reduce_only=False)
                if mode in ["Neutral", "Short"] and p > mark * 0.99:
                    await client.limit_order(ticker=ticker, amount=-size, price=p, reduce_only=False)

            await asyncio.sleep(5)
        except Exception as e:
            st.error(f"Error: {e}")
            await asyncio.sleep(10)

    await client.cleanup()

# Start / Stop
if start and not st.session_state.running:
    st.session_state.running = True
    asyncio.create_task(grid_bot())
    st.success("Bot started!")

if stop and st.session_state.running:
    st.session_state.running = False
    st.warning("Bot stopped")

# Live status
if st.session_state.running:
    st.metric("Status", "🟢 RUNNING")
else:
    st.metric("Status", "🔴 STOPPED")

st.caption("Your referral QZ45EM7CPQYA is permanent • Share this bot everywhere! ⚡")
