import streamlit as st
import pandas as pd
import math

# 1. 頁面配置
st.set_page_config(page_title="WiFi RF Power Tool", layout="wide")
st.title("📶 WiFi RF Power Table & Link Budget")

# --- 側邊欄：補全 Link Budget 關鍵因素 ---
with st.sidebar:
    st.header("⚙️ RF Parameters")
    tx_pwr = st.number_input("TX Power (dBm) - MCS0", value=20.0, step=0.5)
    tx_ant_gain = st.number_input("TX Antenna Gain (dBi)", value=5.0, step=0.1)
    tx_cable_loss = st.number_input("TX Cable Loss (dB)", value=2.0, step=0.1)
    
    st.divider()
    rx_ant_gain = st.number_input("RX Antenna Gain (dBi)", value=3.0, step=0.1)
    rx_cable_loss = st.number_input("RX Cable Loss (dB)", value=1.0, step=0.1)
    
    st.divider()
    band_choice = st.selectbox("Band", ["2.4 GHz", "5 GHz", "6 GHz"])
    freq = 2412 if "2.4" in band_choice else 5180 if "5" in band_choice else 6105
    dist = st.number_input("Distance (m)", value=10.0, step=1.0) # 距離是 Link Budget 的核心

# --- Link Budget 核心計算公式 ---
# 1. EIRP
eirp = tx_pwr + tx_ant_gain - tx_cable_loss
# 2. Free Space Path Loss (FSPL) 公式: 20log10(d) + 20log10(f) - 147.55
fspl = 20 * math.log10(max(dist, 0.1)) + 20 * math.log10(freq * 10**6) - 147.55
# 3. Received Power (RSSI)
rssi = eirp - fspl + rx_ant_gain - rx_cable_loss

# --- 生成 MCS Power Table 數據 ---
mcs_levels = [f"MCS{i}" for i in range(13)]
powers = [round(tx_pwr - (i * 0.6), 1) for i in range(len(mcs_levels))]

df = pd.DataFrame({
    "MCS Level": mcs_levels,
    "Target Power (dBm)": powers,
    "EIRP (dBm)": [round(p + tx_ant_gain - tx_cable_loss, 1) for p in powers],
    "RSSI @ Dest (dBm)": [round(p + tx_ant_gain - tx_cable_loss - fspl + rx_ant_gain - rx_cable_loss, 1) for p in powers]
})

# --- 主要介面 ---
col_table, col_chart = st.columns([1, 1], gap="large")

with col_table:
    st.subheader(f"📊 Link Budget Result ({dist}m)")
    # 顯示關鍵指標
    c1, c2 = st.columns(2)
    c1.metric("Path Loss (FSPL)", f"{round(fspl, 1)} dB")
    c2.metric("Received Power (RSSI)", f"{round(rssi, 1)} dBm")

    # 編輯表格
    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Target Power (dBm)": st.column_config.NumberColumn(step=0.1),
            "EIRP (dBm)": st.column_config.NumberColumn(disabled=True),
            "RSSI @ Dest (dBm)": st.column_config.NumberColumn(disabled=True)
        }
    )

with col_chart:
    st.subheader("📈 Power & RSSI Trend")
    # 同時畫出發射功率與接收電位的趨勢
    chart_data = edited_df.set_index("MCS Level")[["Target Power (dBm)", "RSSI @ Dest (dBm)"]]
    st.line_chart(chart_data)

# --- 下載區 ---
st.divider()
csv = edited_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 下載完整 Link Budget 報表 (CSV)", data=csv, file_name=f"Link_Budget_{dist}m.csv")
st.success
