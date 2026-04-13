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
    
    # --- TX 發射端設定 ---
    st.subheader("📡 TX Configuration (AP Side)")
    tx_chains = st.selectbox("TX Antenna Chains (N_tx)", options=[1, 2, 3, 4, 8], index=1)
    ic_pwr = st.number_input("Single Path IC Power (dBm)", value=22.0)
    tx_board_loss = st.number_input("TX Board Loss (dB)", value=1.5)
    tx_ant_gain = st.number_input("TX Ant Gain (dBi)", value=3.0)
    
    # TX 功率合成增益 (10log10(N_tx))
    tx_combine_gain = 10 * math.log10(tx_chains)
    # 單路板端功率
    conducted_pwr_single = ic_pwr - tx_board_loss
    # 總合成功率
    total_conducted_pwr = conducted_pwr_single + tx_combine_gain
    
    st.info(f"💡 TX Array Gain: +{tx_combine_gain:.1f} dB")
    st.success(f"Total Conducted: {total_conducted_pwr:.1f} dBm")
    
    st.divider()

    # --- RX 接收端設定 ---
    st.subheader("📥 RX Configuration (Client Side)")
    rx_chains = st.selectbox("RX Antenna Chains (N_rx)", options=[1, 2, 3, 4, 8], index=0)
    rx_ant_gain = st.number_input("RX Ant Gain (dBi)", value=2.0)
    rx_board_loss = st.number_input("RX Board Loss (dB)", value=1.0)
    
    # RX MRC (Maximum Ratio Combining) 收益
    # 物理理論上，每增加一倍天線，SNR 增加約 10log10(N_rx)
    rx_mrc_gain = 10 * math.log10(rx_chains)
    st.info(f"💡 RX MRC Gain: +{rx_mrc_gain:.1f} dB")

    st.divider()
    
    # 環境參數
    st.subheader("🌍 Environment")
    dist = st.number_input("Distance (m)", value=10.0, min_value=0.1)
    band = st.selectbox("Frequency Band", ["2.4 GHz", "5 GHz", "6 GHz"])

# --- 3. 核心運算 ---
f_map = {"5 GHz": 5180, "2.4 GHz": 2412, "6 GHz": 6105}
freq = f_map[band]
fspl = 20 * math.log10(dist) + 20 * math.log10(freq * 10**6) - 147.55

data = []
for i in range(14):
    m_label = f"MCS{i}"
    # 預設調變分配邏輯 (可隨 target_mcs 修改)
    qam = "4096-QAM" if i >= 12 else ("1024-QAM" if i >= 10 else "256-QAM")
    if i < 8: qam = "64-QAM"
    if i < 3: qam = "QPSK"
    if i == 0: qam = "BPSK"
    
    evm = qam_to_evm[qam]
    
    # 考慮 EVM Back-off 的單路 TX 功率
    pwr_single = round(conducted_pwr_single - (abs(evm + 5.0) * 0.4), 1)
    
    # 總合 TX 功率 (N_tx)
    pwr_total = round(pwr_single + tx_combine_gain, 1)
    
    # EIRP = 總功率 + 單根天線增益 (假設全向覆蓋)
    eirp = round(pwr_total + tx_ant_gain, 1)
    
    # RSSI = EIRP - PathLoss + (RX Gain - RX Loss) + RX MRC Gain
    # 這裡是關鍵：分開計算了 TX 的發射增益與 RX 的接收增益
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
st.markdown(f"### 📊 Link Summary: `{tx_chains}T{rx_chains}R` MIMO")
st.write(f"這是一個非對稱系統，發射端有 **{tx_chains}** 根天線提供功率補償，接收端有 **{rx_chains}** 根天線提供 MRC 增益。")

col_table, col_charts = st.columns([1.3, 0.7])

with col_table:
    st.subheader("📋 Detailed Link Budget")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("📥 下載數據報表", df.to_csv(index=False).encode('utf-8'), "Asymmetric_MIMO.csv")

with col_charts:
    st.subheader("📈 Signal Trends")
    # 強調 TX 總功率與端對端 RSSI
    st.line_chart(df.set_index("MCS")[["TX_Total_Cond (dBm)", "RX_RSSI (dBm)"]])
    
    with st.expander("📚 計算原理說明"):
        st.write(f"**1. TX Power:** 單路功率 + $10\log_{{10}}({tx_chains})$")
        st.write(f"**2. Path Loss:** 基於 Friis 公式，當前損失約為 {fspl:.1f} dB")
        st.write(f"**3. RX RSSI:** EIRP - FSPL + RX增益 + $10\log_{{10}}({rx_chains})$ (MRC)")
