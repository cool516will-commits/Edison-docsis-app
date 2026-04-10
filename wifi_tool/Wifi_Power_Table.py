import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="WiFi RF Tool with EVM", layout="wide")
st.title("📶 WiFi RF Power Table & Link Budget (Inc. EVM SPEC)")

# --- 側邊欄：參數設定 ---
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

# --- EVM SPEC 對應表 (根據 WiFi 標準與 HLD 資料) ---
# 注意：EVM 數值越小(越負)代表要求越嚴格
evm_specs = {
    "MCS0": -5.0,  "MCS1": -10.0, "MCS2": -13.0, "MCS3": -16.0,
    "MCS4": -19.0, "MCS5": -22.0, "MCS6": -25.0, "MCS7": -27.0,
    "MCS8": -30.0, "MCS9": -32.0, "MCS10": -35.0, "MCS11": -35.0,
    "MCS12": -38.0, "MCS13": -38.0
}

# --- 生成數據 ---
data = []
for i in range(14):
    m_level = f"MCS{i}"
    # 功率隨 MCS 提高而 Back-off
    pwr_drop = i * 0.7 if i < 10 else (9 * 0.7) + (i - 9) * 0.9
    pwr = round(tx_pwr_m0 - pwr_drop, 1)
    
    eirp = pwr + tx_ant - tx_loss
    rssi = eirp - fspl + rx_ant - rx_loss
    
    data.append({
        "MCS Level": m_level,
        "EVM SPEC (dB)": evm_specs.get(m_level, 0.0), # 這裡就是你要的 SPEC
        "Target Power (dBm)": pwr,
        "EIRP (dBm)": round(eirp, 1),
        "RSSI (dBm)": round(rssi, 1)
    })

df = pd.DataFrame(data)

# --- 顯示介面 ---
col_table, col_chart = st.columns([1.2, 0.8], gap="medium")

with col_table:
    st.subheader(f"📊 Link Budget & EVM Table")
    st.write(f"**Path Loss:** {round(fspl, 1)} dB | **Distance:** {dist}m")
    # 增加 EVM 欄位顯示
    st.data_editor(df, use_container_width=True, hide_index=True, height=520)

with col_chart:
    st.subheader("📈 Power vs RSSI Trend")
    # 雙軸趨勢圖
    st.line_chart(df.set_index("MCS Level")[["Target Power (dBm)", "RSSI (dBm)"]])
    
    st.subheader("📉 EVM Requirement")
    # 顯示 EVM 嚴格度趨勢
    st.area_chart(df.set_index("MCS Level")["EVM SPEC (dB)"])

# --- 下載 ---
st.divider()
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 下載完整報告 (含 EVM SPEC)", data=csv, file_name="WiFi_Full_Budget_EVM.csv")

st.markdown("---")
st.info("✅ **核對完畢**：已加入 EVM SPEC 欄位。這能解釋為什麼在高階 MCS 時，你的 Target Power 必須被迫下降。")
