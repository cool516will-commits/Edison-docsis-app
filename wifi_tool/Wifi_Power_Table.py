import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="RF Power Table", layout="wide")

st.title("📡 RF Power Table Calculator (WiFi / DOCSIS)")

# =========================
# 🔧 Input Section
# =========================
st.sidebar.header("🔧 Input Parameters")

tx_power = st.sidebar.number_input("TX Power (dBm)", value=20.0)
tx_gain = st.sidebar.number_input("TX Antenna Gain (dBi)", value=5.0)
tx_loss = st.sidebar.number_input("TX Cable/Connector Loss (dB)", value=2.0)

rx_gain = st.sidebar.number_input("RX Antenna Gain (dBi)", value=3.0)
rx_loss = st.sidebar.number_input("RX Cable Loss (dB)", value=1.0)

frequency = st.sidebar.number_input("Frequency (MHz)", value=5000.0)
bandwidth = st.sidebar.number_input("Bandwidth (Hz)", value=20e6)

noise_figure = st.sidebar.number_input("Noise Figure (dB)", value=7.0)

wall_loss = st.sidebar.number_input("Wall Loss (dB)", value=5.0)
shadowing = st.sidebar.number_input("Shadowing (dB)", value=5.0)
fading_margin = st.sidebar.number_input("Fading Margin (dB)", value=10.0)

distance_list = st.sidebar.text_input("Distances (m, comma separated)", "5,10,20,30")

modulation = st.sidebar.selectbox(
    "Modulation",
    ["QAM256", "QAM1024", "QAM4096"]
)

# Required SNR table
snr_required_table = {
    "QAM256": 30,
    "QAM1024": 35,
    "QAM4096": 42
}

required_snr = snr_required_table[modulation]

# =========================
# 📐 Functions
# =========================
def fspl(d, f):
    return 20 * math.log10(d) + 20 * math.log10(f) + 32.44

def noise_floor(bw, nf):
    return -174 + 10 * math.log10(bw) + nf

# =========================
# 🔢 Calculation
# =========================
distances = [float(x.strip()) for x in distance_list.split(",")]

rows = []

eirp = tx_power + tx_gain - tx_loss
nfloor = noise_floor(bandwidth, noise_figure)

for d in distances:
    path_loss = fspl(d, frequency) + wall_loss + shadowing + fading_margin
    prx = eirp - path_loss + rx_gain - rx_loss
    snr = prx - nfloor
    margin = snr - required_snr

    result = "✅ PASS" if snr >= required_snr else "❌ FAIL"

    rows.append({
        "Distance (m)": d,
        "EIRP (dBm)": round(eirp, 2),
        "Path Loss (dB)": round(path_loss, 2),
        "Received Power (dBm)": round(prx, 2),
        "Noise Floor (dBm)": round(nfloor, 2),
        "SNR (dB)": round(snr, 2),
        "Required SNR (dB)": required_snr,
        "Margin (dB)": round(margin, 2),
        "Result": result
    })

df = pd.DataFrame(rows)

# =========================
# 📊 Output
# =========================
st.subheader("📊 Power Table Result")
st.dataframe(df, use_container_width=True)

# =========================
# 📈 Simple Insight
# =========================
st.subheader("📌 Summary")

best = df[df["Result"] == "✅ PASS"]

if not best.empty:
    max_dist = best["Distance (m)"].max()
    st.success(f"✅ Max PASS distance: {max_dist} m")
else:
    st.error("❌ No valid link under current conditions")
