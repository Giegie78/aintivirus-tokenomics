import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIG ---
st.set_page_config(page_title="Aintivirus Coin Tokenomics Simulator", layout="wide")

# --- CONSTANTS ---
FIXED_SUPPLY = 100_000_000
DAYS_IN_YEAR = 365
MAX_DAYS = 4 * DAYS_IN_YEAR  # Up to 4 years

# --- TITLE ---
st.title("🔥 Aintivirus Coin Tokenomics Simulator")
st.markdown("Explore how **burn mechanisms** affect the token price and supply of Aintivirus Coin over time.")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Simulation Settings")
initial_price = st.sidebar.number_input("Initial Coin Price ($)", min_value=0.01, value=1.0, step=0.01)
price_change_pct = st.sidebar.slider("Yearly Market-Driven Price Change (%)", -50, 200, 20)
days_to_simulate = st.sidebar.slider("Days to Simulate", 30, MAX_DAYS, 365)

# --- BURN RATES & VOLUME SLIDERS ---
st.sidebar.markdown("---")
st.sidebar.header("Service Volumes & Burn Info")

burn_rates = {
    "Mixer": 0.02,
    "Merch-Shop": 0.2,
    "eSIM": 0.02,
    "Gift Card": 0.02,
}

default_volumes = {
    "Mixer": 25_000,
    "Merch-Shop": 5_000,
    "eSIM": 10_000,
    "Gift Card": 20_000,
}

# Placeholder for day 1 price
estimated_price_with_burn_today = initial_price

# User input + estimated burn per service
service_volumes = {}
initial_burn_estimates = {}

for service, burn_rate in burn_rates.items():
    st.sidebar.markdown(f"### {service}")
    volume = st.sidebar.slider(
        f"{service} Volume ($/day)",
        min_value=0,
        max_value=1_000_000,
        value=default_volumes[service],
        step=5_000,
        key=f"{service}_volume"
    )
    service_volumes[service] = volume
    tokens_burned = (volume * burn_rate) / estimated_price_with_burn_today

    col1, col2 = st.sidebar.columns([1, 2])
    col1.caption("Burn Rate")
    col2.caption("Est. Day 1 Burn")

    col1.write(f"{int(burn_rate * 100)}%")
    col2.write(f"{tokens_burned:,.0f} AVT")

# --- SIMULATION LOOP ---
days = np.arange(1, days_to_simulate + 1)
supply = FIXED_SUPPLY
initial_market_price = initial_price
daily_growth_factor = (1 + price_change_pct / 100) ** (1 / 365)

# Prepare storage
price_no_burn = []
price_with_burn = []
remaining_supply = []
cumulative_burned = []
daily_burned_total = []
daily_burn_by_service = {service: [] for service in burn_rates}

cumulative_burn = 0

for day in days:
    price_no_burn_today = initial_market_price * (daily_growth_factor ** day)
    price_with_burn_today = price_no_burn_today * (FIXED_SUPPLY / supply) if supply > 0 else float("inf")

    burned_today_total = 0
    for service, volume in service_volumes.items():
        burn_rate = burn_rates[service]
        burn_amount = (volume * burn_rate) / price_with_burn_today
        burned_today_total += burn_amount
        daily_burn_by_service[service].append(burn_amount)

    supply -= burned_today_total
    supply = max(supply, 1)  # prevent negative supply

    cumulative_burn += burned_today_total

    price_no_burn.append(price_no_burn_today)
    price_with_burn.append(price_with_burn_today)
    remaining_supply.append(supply)
    cumulative_burned.append(cumulative_burn)
    daily_burned_total.append(burned_today_total)

# --- DATAFRAME ---
df = pd.DataFrame({
    "Day": days,
    "Market Price (No Burn)": price_no_burn,
    "Price with Burn": price_with_burn,
    "Remaining Supply": remaining_supply,
    "Daily Burned Tokens": daily_burned_total,
    "Cumulative Burned": cumulative_burned
})

# Add per-service daily burn to the DataFrame
for service, burn_list in daily_burn_by_service.items():
    df[f"Burned - {service}"] = burn_list

# --- VISUALIZATION ---
st.subheader("📈 Price Evolution")
fig1, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(df["Day"], df["Market Price (No Burn)"], label="Price (No Burn)", linestyle="--")
ax1.plot(df["Day"], df["Price with Burn"], label="Price (With Burn)", linewidth=2)
ax1.set_xlabel("Day")
ax1.set_ylabel("Price ($)")
ax1.legend()
st.pyplot(fig1)

st.subheader("🔥 Supply & Cumulative Burn")
fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.plot(df["Day"], df["Remaining Supply"], label="Remaining Supply", color="blue")
ax2.plot(df["Day"], df["Cumulative Burned"], label="Cumulative Burned", color="red")
ax2.set_xlabel("Day")
ax2.set_ylabel("Token Amount")
ax2.legend()
st.pyplot(fig2)

# --- SIDEBAR: AVERAGE DAILY BURN ---
st.sidebar.markdown("---")
st.sidebar.header("📊 Avg. Daily Burn per Service")

for service in burn_rates:
    avg_burn = np.mean(daily_burn_by_service[service])
    st.sidebar.write(f"**{service}**: {avg_burn:,.0f} AVT/day")

# --- DOWNLOAD ---
st.sidebar.markdown("---")
csv = df.to_csv(index=False).encode("utf-8")
st.sidebar.download_button("📥 Download Simulation Data", csv, "aintivirus_simulation.csv", "text/csv")

st.sidebar.markdown("Made with ❤️ by giegie")
