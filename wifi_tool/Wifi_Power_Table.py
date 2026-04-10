import streamlit as st
import pandas as pd

# 1. 頁面配置
st.set_page_config(page_title="WiFi RF Power Tool", layout="wide")

st.title("📶 WiFi RF Power Table & Link Budget")

# --- 側邊欄：把天線因素全部補回來 ---
with st.sidebar:
    st.header("⚙️ RF Parameters")
    tx_pwr = st.number_input("TX Power (dBm) - MCS0", value=20.0, step=0.5)
    tx_ant_gain = st.number_input("TX Antenna Gain (dBi)", value=5.0, step=0.1)
    tx_cable_loss = st.number_input("TX Cable Loss (dB)", value=2.0, step=0.1)
    
    st.divider()
    rx_ant_gain = st.number_input("RX Antenna Gain (dBi)", value=3.0, step=0.1)
    rx_cable_loss = st.number_input("RX Cable Loss (dB)", value=1.0, step=0.1)
    
    st.divider()
    band = st.selectbox("Band", ["2.4 GHz", "5 GHz", "6 GHz"])
    bw = st.selectbox("BW (MHz)", [20, 40, 80, 160, 320])

# --- 計算 EIRP ---
eirp = tx_pwr + tx_ant_gain - tx_cable_loss

# --- 生成 MCS Power Table 數據 ---
mcs_levels = [f"MCS{i}" for i in range(13)]
# 根據 MCS 等級自動模擬 Power 下降
powers = [round(tx_pwr - (i * 0.6), 1) for i in range(len(mcs_levels))]

df = pd.DataFrame({
    "MCS Level": mcs_levels,
    "Target Power (dBm)": powers,
    "EIRP (dBm)": [round(p + tx_ant_gain - tx_cable_loss, 1) for p in powers]
})

# --- 主要介面 ---
col_table, col_chart = st.columns([1, 1], gap="large")

with col_table:
    st.subheader("📊 Power Table (Editable)")
    # 讓你可以直接改 Target Power
    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Target Power (dBm)": st.column_config.NumberColumn(step=0.1),
            "EIRP (dBm)": st.column_config.NumberColumn(disabled=True)
        }
    )

with col_chart:
    st.subheader("📈 Power Curve")
    # 修正圖表 X 軸排序問題
    chart_data = edited_df.copy()
    chart_data.index = chart_data["MCS Level"]
    st.line_chart(chart_data["Target Power (dBm)"])

# --- 底部功能區 ---
st.divider()
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    avg_pwr = round(edited_df["Target Power (dBm)"].mean(), 2)
    st.metric("平均發射功率", f"{avg_pwr} dBm")

with f_col2:
    # 修正紅圈處的錯誤：直接輸入字串，不要誤觸函數說明
    st.success("✅ 數據計算完成，可直接編輯表格。")

with f_col3:
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 下載此 Power Table (CSV)",
        data=csv,
        file_name=f"WiFi_Power_Report_{band}.csv",
        mime='text/csv'
    )
