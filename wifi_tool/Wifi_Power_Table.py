import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="WiFi RF Tool - QAM Edition", layout="wide")
st.title("📶 WiFi Link Budget (MCS 0-13 + QAM Modulation)")

# --- 側邊欄參數 ---
with st.sidebar:
    st.header("⚙️ RF Parameters")
    tx_pwr_m0 = st.number_input("Target Power MCS0 (dBm)", value=20.0, step=0.5)
    tx_ant = st.number_input("TX Antenna Gain (dBi)", value=5.0)
    tx_loss = st.number_input("TX Cable Loss (dB)", value=2.0)
    st.divider()
    rx_ant = st.number_input("RX Antenna Gain (dBi)", value=3.0)
    rx_loss = st.number_input("RX Cable Loss (dB)", value=1.0)
    st.divider()
    dist = st.number_input("Distance (m)", value=10.0, step=1.0)
    band = st.selectbox("Frequency Band", ["5 GHz", "2.4 GHz", "6 GHz"])

# --- Link Budget 計算 ---
f_map = {"5 GHz": 5180, "2.4 GHz": 2412, "6 GHz": 6105}
freq = f_map[band]
fspl = 20 * math.log10(max(dist, 0.1)) + 20 * math.log10(freq * 10**6) - 147.55

# --- MCS 對應 QAM 與 EVM SPEC 表 ---
# 這是根據你的 HLD 檔案與 802.11ax 規範整理
mcs_specs = {
    0:  {"mod": "BPSK",     "evm": -5.0},
    1:  {"mod": "QPSK",     "evm": -10.0},
    2:  {"mod": "QPSK",     "evm": -13.0},
    3:  {"mod": "16-QAM",   "evm": -16.0},
    4:  {"mod": "16-QAM",   "evm": -19.0},
    5:  {"mod": "64-QAM",   "evm": -22.0},
    6:  {"mod": "64-QAM",   "evm": -25.0},
    7:  {"mod": "64-QAM",   "evm": -27.0},
    8:  {"mod": "256-QAM",  "evm": -30.0},
    9:  {"mod": "256-QAM",  "evm": -32.0},
    10: {"mod": "1024-QAM", "evm": -35.0},
    11: {"mod": "1024-QAM", "evm": -35.0},
    12: {"mod": "4096-QAM", "evm": -38.0},
    13: {"mod": "4096-QAM", "evm": -38.0}
}

# --- 生成數據 ---
data = []
for i in range(14):
    spec = mcs_specs[i]
    # 功率隨 MCS 提高而下降的邏輯
    pwr_drop = i * 0.7 if i < 10 else (9 * 0.7) + (i - 9) * 0.9
    pwr = round(tx_pwr_m0 - pwr_drop, 1)
    
    eirp = pwr + tx_ant - tx_loss
    rssi = eirp - fspl + rx_ant - rx_loss
    
    data.append({
        "MCS": i,
        "Modulation (QAM)": spec["mod"],
        "EVM SPEC (dB)": spec["evm"],
        "Target Power (dBm)": pwr,
        "RSSI (dBm)": round(rssi, 1)
    })

df = pd.DataFrame(data)

# --- 顯示介面 ---
col_table, col_chart = st.columns([1.3, 0.7], gap="medium")

with col_table:
    st.subheader(f"📊 Full Link Budget Table")
    st.write(f"**Path Loss:** {round(fspl, 1)} dB")
    # 將 QAM 欄位放在顯眼位置
    st.data_editor(df, use_container_width=True, hide_index=True, height=520)

with col_chart:
    st.subheader("📈 QAM Level vs Power")
    # 顯示隨 QAM 階數提高，功率下降的趨勢
    chart_df = df.copy()
    st.line_chart(chart_df.set_index("Modulation (QAM)")["Target Power (dBm)"])

st.info("✅ **已補上 QAM 運算**：現在表格會顯示每個 MCS 對應的調變方式（如 1024-QAM），讓你一眼看出為什麼 EVM 要求會變嚴格。")
