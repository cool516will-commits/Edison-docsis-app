import streamlit as st
import pandas as pd
import math

# 設定網頁標題與佈局
st.set_page_config(page_title="WiFi Asymmetric MIMO Tool", layout="wide")
st.title("📶 WiFi Link Budget: TX & RX MIMO Decoupled")

# --- 1. 定義 QAM 與 EVM 對照 ---
qam_to_evm = {
    "BPSK": -5.0, "QPSK": -13.0, "16-QAM": -19.0, 
    "64-QAM": -27.0, "256-QAM": -32.0, "1024-QAM": -35.0, "4096-QAM": -38.0
}

# --- 2. 側邊欄：參數設定 ---
with st.sidebar:
    st.header("⚙️ RF Parameters")
    
    # --- TX 發射端設定 (通常是 AP 端) ---
    st.subheader("📡 TX Configuration (AP)")
    tx_chains = st.selectbox("TX Antenna Chains (N_tx)", options=[1, 2, 3, 4, 8], index=1)
    ic_pwr = st.number_input("Single Path IC Power (dBm)", value=22.0, help="單路晶片原始輸出")
    tx_board_loss = st.number_input("TX Board Loss (dB)", value=1.5, help="板級損耗")
    tx_ant_gain = st.number_input("TX Ant Gain (dBi)", value=3.0)
    
    # TX 功率合成增益 10*log10(N_tx)
    tx_combine_gain = 10 * math.log10(tx_chains)
    # 單路板端傳導功率
    conducted_pwr_single = ic_pwr - tx_board_loss
    
    st.info(f"💡 TX Combine Gain: +{tx_combine_gain:.1f} dB")
    
    st.divider()

    # --- RX 接收端設定 (通常是 Client 端) ---
    st.subheader("📥 RX Configuration (Client)")
    rx_chains = st.selectbox("RX Antenna Chains (N_rx)", options=[1, 2, 3, 4, 8], index=0)
    rx_ant_gain = st.number_input("RX Ant Gain (dBi)", value=2.0)
    rx_board_loss = st.number_input("RX Board Loss (dB)", value=1.0)
    
    # RX MRC (Maximum Ratio Combining) 收益 10*log10(N_rx)
    rx_mrc_gain = 10 * math.log10(rx_chains)
    st.info(f"💡 RX MRC Gain: +{rx_mrc_gain:.1f} dB")

    st.divider()
    
    # 環境參數
    st.subheader("🌍 Environment")
    dist = st.number_input("Distance (m)", value=10.0, min_value=0.1)
    band = st.selectbox("Frequency Band", ["2.4 GHz", "5 GHz", "6 GHz"])
    
    st.divider()
    target_mcs_idx = st.selectbox("修改 MCS 調變", options=range(14))
    target_qam = st.selectbox(f"MCS{target_mcs_idx} 調變設定", options=list(qam_to_evm.keys()), index=6)

# --- 3. 核心運算 ---
f_map = {"5 GHz": 5180, "2.4 GHz": 2412, "6 GHz": 6105}
freq = f_map[band]
# FSPL 公式
fspl = 20 * math.log10(dist) + 20 * math.log10(freq * 10**6) - 147.55

data = []
for i in range(14):
    m_label = f"MCS{i}"
    qam = target_qam if i == target_mcs_idx else ("4096-QAM" if i >= 12 else ("1024-QAM" if i >= 10 else "256-QAM"))
    if i < 8 and i != target_mcs_idx: qam = "64-QAM"
    if i < 3 and i != target_mcs_idx: qam = "QPSK"
    if i == 0 and i != target_mcs_idx: qam = "BPSK"
    
    evm = qam_to_evm[qam]
    
    # 單路發射功率 (考慮 EVM Back-off)
    pwr_single = round(conducted_pwr_single - (abs(evm + 5.0) * 0.4), 1)
    
    # 總發射功率 (MIMO 合併)
    pwr_total = round(pwr_single + tx_combine_gain, 1)
    
    # EIRP (總功率 + 天線增益)
    eirp = round(pwr_total + tx_ant_gain, 1)
    
    # RSSI = EIRP - PathLoss + (RX Gain - RX Loss) + RX MRC Gain
    # 分開計算 TX 合併與 RX 合併的效果
    rssi = round(eirp - fspl + (rx_ant_gain - rx_board_loss) + rx_mrc_gain, 1)
    
    data.append({
        "MCS": m_label,
        "Modulation": qam,
        "TX_Single_Ch (dBm)": pwr_single,
        "TX_Total_Cond (dBm)": pwr_total,
        "EIRP (dBm)": eirp,
        "RX_RSSI (dBm)": rssi
    })

df = pd.DataFrame(data)

# --- 4. 畫面呈現 ---
st.markdown(f"### 📊 Link Analysis: `{tx_chains}T{rx_chains}R` MIMO")

col_table, col_charts = st.columns([1.2, 0.8])

with col_table:
    st.subheader("📋 Link Budget Table")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("📥 下載完整 CSV", df.to_csv(index=False).encode('utf-8'), "MIMO_Budget_Report.csv")

with col_charts:
    st.subheader("📈 Power & Signal Trend")
    # 同時呈現單路功率、總功率與最終接收 RSSI
    st.line_chart(df.set_index("MCS")[["TX_Single_Ch (dBm)", "TX_Total_Cond (dBm)", "RX_RSSI (dBm)"]])
    
    st.subheader("📉 Summary Metrics")
    st.write(f"**Path Loss (FSPL):** {fspl:.1f} dB")
    st.write(f"**TX 合併收益:** +{tx_combine_gain:.1f} dB")
    st.write(f"**RX MRC 收益:** +{rx_mrc_gain:.1f} dB")
