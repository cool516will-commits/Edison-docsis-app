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
    st.header("⚙️ RF Parameters")
    
    # MIMO 設定
    st.subheader("👥 Antenna System")
    # 讓使用者選擇天線數量 (常見 1x1, 2x2, 3x3, 4x4, 8x8)
    ant_count = st.selectbox("Number of TX/RX Chains (MIMO)", options=[1, 2, 3, 4, 8], index=1)
    mimo_gain = 10 * math.log10(ant_count)
    st.info(f"MIMO Power Boost: +{mimo_gain:.1f} dB")

    st.divider()
    
    # TX (發射端)
    st.subheader("📡 TX (發射端)")
    ic_pwr = st.number_input("Single Chain IC Power (dBm)", value=22.0, help="單路晶片輸出的功率")
    total_board_loss = st.number_input("Total Board Loss (dB)", value=1.5, help="包含 Trace, Filter 等")
    
    # 單路板端輸出
    conducted_pwr_single = ic_pwr - total_board_loss
    # 總板端輸出 (MIMO 合併)
    conducted_pwr_total = conducted_pwr_single + mimo_gain
    
    st.success(f"📍 單路 I-PEX 預期: {conducted_pwr_single:.1f} dBm")
    st.warning(f"🚀 總合輸出功率: {conducted_pwr_total:.1f} dBm")
    
    tx_ant = st.number_input("TX Antenna Gain (dBi)", value=3.0)
    
    st.divider()
    
    # RX (接收端)
    st.subheader("📥 RX (接收端)")
    rx_ant = st.number_input("RX Antenna Gain (dBi)", value=2.0)
    rx_loss = st.number_input("RX System Loss (dB)", value=1.0)
    
    st.divider()
    
    # 環境參數
    st.subheader("🌍 Environment")
    dist = st.number_input("Distance (m)", value=10.0, min_value=0.1)
    band = st.selectbox("Frequency Band", ["2.4 GHz", "5 GHz", "6 GHz"])
    
    st.divider()
    target_mcs_idx = st.selectbox("選擇要修改的 MCS", options=range(14), format_func=lambda x: f"MCS{x}")
    target_qam = st.selectbox(f"設定 MCS{target_mcs_idx} 調變", options=list(qam_to_evm.keys()), index=6)

# --- 3. 核心運算 ---
f_map = {"5 GHz": 5180, "2.4 GHz": 2412, "6 GHz": 6105}
freq = f_map[band]
fspl = 20 * math.log10(dist) + 20 * math.log10(freq * 10**6) - 147.55

data = []
for i in range(14):
    m_label = f"MCS{i}"
    qam = target_qam if i == target_mcs_idx else ("4096-QAM" if i >= 12 else ("1024-QAM" if i >= 10 else "256-QAM"))
    if i < 8 and i != target_mcs_idx: qam = "64-QAM"
    if i < 3 and i != target_mcs_idx: qam = "QPSK"
    if i == 0 and i != target_mcs_idx: qam = "BPSK"
    
    evm = qam_to_evm[qam]
    
    # 1. 計算單路功率 (考慮 EVM Back-off)
    pwr_single = round(conducted_pwr_single - (abs(evm + 5.0) * 0.4), 1)
    
    # 2. 計算總合傳導功率 (Total Conducted Power)
    pwr_total = round(pwr_single + mimo_gain, 1)
    
    # 3. EIRP (總功率 + 天線增益)
    # 注意：若有 Beamforming，天線增益計算會更複雜，此處採一般 MIMO 合併
    eirp = round(pwr_total + tx_ant, 1)
    
    # 4. RSSI (考慮接收端 MIMO 合併增益 MRC)
    # 接收端多天線通常會有額外的 Combine Gain
    rssi = round(eirp - fspl + rx_ant - rx_loss + mimo_gain, 1) 
    
    data.append({
        "MCS_Level": m_label,
        "Modulation": qam,
        "Single_Ch_Power_dBm": pwr_single,
        "Total_Conducted_dBm": pwr_total,
        "EIRP_dBm": eirp,
        "RSSI_dBm": rssi
    })

df = pd.DataFrame(data)

# --- 4. 畫面呈現 ---
col_table, col_charts = st.columns([1.2, 0.8])

with col_table:
    st.subheader(f"📋 Link Budget Table ({ant_count}x{ant_count} MIMO)")
    st.data_editor(df, use_container_width=True, hide_index=True)
    st.download_button("📥 下載完整 CSV", df.to_csv(index=False).encode('utf-8'), "MIMO_RF_Report.csv")

with col_charts:
    st.subheader("📈 Power Analysis")
    # 顯示單路與總合功率對比
    st.line_chart(df.set_index("MCS_Level")[["Single_Ch_Power_dBm", "Total_Conducted_dBm", "RSSI_dBm"]])
    
    st.subheader("📊 Summary")
    st.write(f"**天線增益貢獻:** {mimo_gain:.2f} dB")
    st.write(f"**路徑損耗 (FSPL):** {fspl:.2f} dB")
