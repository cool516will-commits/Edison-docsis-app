import streamlit as st
import pandas as pd
import math

# 1. 頁面配置 (設定標題與寬度)
st.set_page_config(page_title="WiFi RF Power Tool", layout="wide")

st.title("📶 WiFi RF Power Table & Link Budget")

# --- 側邊欄：所有 RF 影響因素都在這裡 ---
with st.sidebar:
    st.header("⚙️ RF Parameters")
    # 發射端設定
    tx_pwr = st.number_input("Target Power MCS0 (dBm)", value=20.0, step=0.5)
    tx_ant_gain = st.number_input("TX Antenna Gain (dBi)", value=5.0, step=0.1)
    tx_cable_loss = st.number_input("TX Cable Loss (dB)", value=2.0, step=0.1)
    
    st.divider()
    # 接收端設定
    rx_ant_gain = st.number_input("RX Antenna Gain (dBi)", value=3.0, step=0.1)
    rx_cable_loss = st.number_input("RX Cable Loss (dB)", value=1.0, step=0.1)
    
    st.divider()
    # 環境設定
    band_choice = st.selectbox("Band", ["2.4 GHz", "5 GHz", "6 GHz"])
    # 根據頻段選定頻率 (用於 FSPL 公式)
    freq_map = {"2.4 GHz": 2412, "5 GHz": 5180, "6 GHz": 6105}
    freq = freq_map[band_choice]
    dist = st.number_input("Testing Distance (m)", value=10.0, step=1.0)

# --- Link Budget 核心計算邏輯 ---
# 1. 計算 Path Loss (FSPL) 公式: 20log10(d) + 20log10(f) - 147.55
# max(dist, 0.1) 防止距離為 0 導致數學錯誤
path_loss = 20 * math.log10(max(dist, 0.1)) + 20 * math.log10(freq * 10**6) - 147.55

# --- 生成 MCS Power Table 數據 ---
mcs_levels = [f"MCS{i}" for i in range(13)]
# 預設 Power Drop 邏輯
powers = [round(tx_pwr - (i * 0.6), 1) for i in range(len(mcs_levels))]

# 建立 DataFrame 並加入 Link Budget 計算結果
data_list = []
for i, mcs in enumerate(mcs_levels):
    current_pwr = powers[i]
    eirp = current_pwr + tx_ant_gain - tx_cable_loss
    rssi = eirp - path_loss + rx_ant_gain - rx_cable_loss
    data_list.append({
        "MCS Level": mcs,
        "Target Power (dBm)": current_pwr,
        "EIRP (dBm)": round(eirp, 1),
        "RSSI @ Receiver (dBm)": round(rssi, 1)
    })

df = pd.DataFrame(data_list)

# --- 主要顯示區域 ---
col_table, col_chart = st.columns([1.2, 0.8], gap="large")

with col_table:
    st.subheader(f"📊 Link Budget Result (Distance: {dist}m)")
    # 顯示核心數據
    st.write(f"**FSPL (Path Loss):** {round(path_loss, 1)} dB")
    
    # 讓表格可直接編輯 Target Power，其餘欄位連動
    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Target Power (dBm)": st.column_config.NumberColumn("Target Power", step=0.1),
            "EIRP (dBm)": st.column_config.NumberColumn(disabled=True),
            "RSSI @ Receiver (dBm)": st.column_config.NumberColumn(disabled=True)
        }
    )

with col_chart:
    st.subheader("📈 Power Curve Trend")
    # 將數據 Index 設為 MCS Level 確保 X 軸排序正確
    chart_df = edited_df.set_index("MCS Level")
    # 同時畫出發射與接收電壓趨勢
    st.line_chart(chart_df[["Target Power (dBm)", "RSSI @ Receiver (dBm)"]])

# --- 底部下載與匯出 ---
st.divider()
c1, c2 = st.columns(2)

with c1:
    avg_rssi = round(edited_df["RSSI @ Receiver (dBm)"].mean(), 1)
    st.metric("平均接收電位 (Average RSSI)", f"{avg_rssi} dBm")

with c2:
    # 產生 CSV 並提供下載按鈕
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 匯出完整報表 (CSV)",
        data=csv,
        file_name=f"WiFi_LinkBudget_{band_choice}_{dist}m.csv",
        mime='text/csv'
    )

# 使用最簡單的 markdown 替代 st.success，避免觸發函數說明文件的 Bug
st.markdown("---")
st.markdown("💡 **Tip:** 您可以直接在表格中點擊修改 **Target Power**，圖表和 RSSI 會即時更新。")
