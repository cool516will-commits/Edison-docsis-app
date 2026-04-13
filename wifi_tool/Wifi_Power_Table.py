import streamlit as st
import pandas as pd
import math

# 設定網頁標題與佈局
st.set_page_config(page_title="WiFi MIMO Link Budget Tool", layout="wide")
st.title("📶 WiFi Link Budget & MIMO Target Power")

# --- 1. 定義 QAM 與 EVM 對照 ---
qam_to_evm = {
    "BPSK": -5.0, "QPSK": -13.0, "16-QAM": -19.0, 
    "64-QAM": -27.0, "256-QAM": -32.0, "1024-QAM": -35.0, "4096-QAM": -38.0
}

# --- 2. 側邊欄：參數設定 ---
with st.sidebar:
    st.header("⚙️ RF & MIMO Settings")
    
    # MIMO 設定
    st.subheader("👥 Antenna Configuration")
    mimo_streams = st.selectbox("Spatial Streams (MIMO)", [1, 2, 3, 4, 8], index=1, help="例如 2x2 MIMO 請選 2")
    array_gain = 10 * math.log10(mimo_streams)
    st.caption(f"ℹ️ MIMO Array Gain: +{array_gain:.1f} dB")

    st.divider()

    # TX (發射端)
    st.subheader("📡 TX (Access Point)")
    ic_pwr = st.number_input("Single Path IC Power (dBm)", value=22.0, help="單一路徑的晶片輸出功率")
    total_board_loss = st.number_input("Board Loss (dB)", value=1.5)
    tx_ant = st.number_input("Single Ant Gain (dBi)", value=3.0)
    
    # 計算單路徑 Conducted Power
    conducted_pwr_per_path = ic_pwr - total_board_loss
    
    st.divider()
    
    # 環境與接收端
    st.subheader("🌍 Environment & RX")
    dist = st.number_input("Distance (m)", value=10.0, min_value=0.1)
    band = st.selectbox("Frequency Band", ["2.4 GHz", "5 GHz", "6 GHz"])
    rx_ant = st.number_input("RX Antenna Gain (dBi)", value=2.0)
    rx_loss = st.number_input("RX System Loss (dB)", value=1.0)

# --- 3. 核心運算 ---
f_map = {"2.4 GHz": 2442, "5 GHz": 5500, "6 GHz": 6500}
freq = f_map[band]
# FSPL 公式: 20log10(d) + 20log10(f_MHz) - 27.55
fspl = 20 * math.log10(dist) + 20 * math.log10(freq) - 27.55

data = []
for i in range(14):
    m_label = f"MCS{i}"
    # 簡單自動分配調變 (可視需求調整)
    if i == 0: qam = "BPSK"
    elif i <= 2: qam = "QPSK"
    elif i <= 4: qam = "16-QAM"
    elif i <= 7: qam = "64-QAM"
    elif i <= 9: qam = "256-QAM"
    elif i <= 11: qam = "1024-QAM"
    else: qam = "4096-QAM"
    
    evm = qam_to_evm[qam]
    
    # 考慮 EVM Back-off 的單路功率
    # 假設越高階調變功率需降載 (Back-off 經驗公式)
    pwr_backoff = abs(evm - qam_to_evm["BPSK"]) * 0.4
    pwr_single = round(conducted_pwr_per_path - pwr_backoff, 1)
    
    # --- 重要：MIMO 功率合成 ---
    # Total Conducted Power = Single Path Power + 10log10(N)
    total_conducted = round(pwr_single + array_gain, 1)
    
    # EIRP = Total Conducted + Antenna Gain (假設同步發射增益)
    eirp = round(total_conducted + tx_ant, 1)
    
    # RSSI = EIRP - PathLoss + RX Gain - RX Loss + RX Combine Gain
    # 這裡假設接收端也有對應的 MIMO Combine 收益
    rssi = round(eirp - fspl + rx_ant - rx_loss + array_gain, 1)
    
    data.append({
        "MCS": m_label,
        "Modulation": qam,
        "Single_Path_dBm": pwr_single,
        "Total_Conducted_dBm": total_conducted,
        "EIRP_dBm": eirp,
        "RSSI_dBm": rssi
    })

df = pd.DataFrame(data)

# --- 4. 畫面呈現 ---
st.info(f"💡 當前配置: {mimo_streams}x{mimo_streams} MIMO | 距離: {dist}m | 頻段: {band}")

col_table, col_charts = st.columns([1.3, 0.7])

with col_table:
    st.subheader("📋 Link Budget Table")
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 提供 CSV 下載
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 下載數據報表", csv, "WiFi_MIMO_Spec.csv", "text/csv")

with col_charts:
    st.subheader("📈 Total Power vs RSSI")
    st.line_chart(df.set_index("MCS")[["Total_Conducted_dBm", "RSSI_dBm"]])
    
    st.subheader("📉 Path Loss Analysis")
    st.metric("Free Space Path Loss", f"{fspl:.1f} dB")
    st.write(f"在 {dist} 公尺下，訊號衰減非常顯著，增加天線數量（MIMO）可有效補償約 {array_gain:.1f} dB 的增益。")
