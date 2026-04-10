import streamlit as st
import pandas as pd
import math

# 1. 頁面配置
st.set_page_config(page_title="WiFi RF Power Tool", layout="wide")
st.title("📶 WiFi RF Power Table & Link Budget")

# --- 側邊欄：RF 參數輸入 ---
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
    # 根據頻段選定中心頻率計算 FSPL
    freq = 2412 if "2.4" in band_choice else 5180 if "5" in band_choice else 6105
    dist = st.number_input("Distance (m)", value=10.0, step=1.0)

# --- Link Budget 核心計算 ---
# 1. EIRP
eirp_val = tx_pwr + tx_ant_gain - tx_cable_loss
# 2. Path Loss (FSPL)
fspl = 20 * math.log10(max(dist, 0.1)) + 20 * math.log10(freq * 10**6) - 147.55
# 3. RSSI
rssi_val = eirp_val - fspl + rx_ant_gain - rx_cable_loss

# --- 生成 MCS 數據表 ---
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
    
    # 這裡只放數據指標，不放會報錯的函數說明
    st.write(f"**Path Loss:** {round(fspl, 1)} dB")
    st.write(f"**Max RSSI:** {round(rssi_val, 1)} dBm")

    # 可編輯表格
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
    st.subheader("📈 Power & RSSI Curve")
    chart_data = edited_df.set_index("MCS Level")[["Target Power (dBm)", "RSSI @ Dest (dBm)"]]
    st.line_chart(chart_data)

# --- 底部功能區 (徹底移除紅圈部分的雜訊) ---
st.divider()
c1, c2 = st.columns([1, 1])

with c1:
    avg_pwr = round(edited_df["Target Power (dBm)"].mean(), 2)
    st.metric("平均發射功率", f"{avg_pwr} dBm")

with c2:
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 下載 Link Budget CSV", data=csv, file_name="WiFi_Link_Budget.csv")

# 這裡只用最簡單的文字，絕對不會噴說明文件
st.info("💡 數據計算完成。您可以直接在左側表格手動微調 Target Power。")
