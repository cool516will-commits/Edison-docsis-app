import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Full WiFi Link Budget Tool", layout="wide")
st.title("📶  WiFi Link Budget & Target power (含 RX 參數)")

# --- 1. 定義 QAM 與 EVM 對照 ---
qam_to_evm = {
    "BPSK": -5.0, "QPSK": -13.0, "16-QAM": -19.0, 
    "64-QAM": -27.0, "256-QAM": -32.0, "1024-QAM": -35.0, "4096-QAM": -38.0
}

# --- 2. 側邊欄: TX & RX 參數設定 ---
with st.sidebar:
    st.header("⚙️ RF Parameters")
    
    # TX 部分
    st.subheader("📡 TX (發射端)")
    tx_pwr_base = st.number_input("Base Power (MCS0) (dBm)", value=20.0)
    tx_ant = st.number_input("TX Antenna Gain (dBi)", value=5.0)
    tx_loss = st.number_input("TX Cable Loss (dB)", value=2.0)
    
    st.divider()
    
    # RX 部分 (補齊你提到的部分)
    st.subheader("📥 RX (接收端)")
    rx_ant = st.number_input("RX Antenna Gain (dBi)", value=3.0)
    rx_loss = st.number_input("RX Cable Loss (dB)", value=1.0)
    
    st.divider()
    
    # 環境參數
    st.subheader("🌍 Environment")
    dist = st.number_input("Distance (m)", value=10.0)
    band = st.selectbox("Frequency Band", ["5 GHz", "2.4 GHz", "6 GHz"])
    
    st.divider()
    
    # 動態調整
    st.subheader("🎯 MCS/QAM 動態調整")
    target_mcs_idx = st.selectbox("選擇修改 MCS", options=range(14), format_func=lambda x: f"MCS{x}")
    target_qam = st.selectbox(f"設定 MCS{target_mcs_idx} 調變", options=list(qam_to_evm.keys()), index=6)

# --- 3. 核心運算邏輯 ---
f_map = {"5 GHz": 5180, "2.4 GHz": 2412, "6 GHz": 6105}
freq = f_map[band]
# FSPL 公式
fspl = 20 * math.log10(max(dist, 0.1)) + 20 * math.log10(freq * 10**6) - 147.55

data = []
for i in range(14):
    m_label = f"MCS{i}"
    # 判斷 QAM
    qam = target_qam if i == target_mcs_idx else ("4096-QAM" if i >= 12 else ("1024-QAM" if i >= 10 else "256-QAM"))
    if i < 8 and i != target_mcs_idx: qam = "64-QAM"
    if i < 3 and i != target_mcs_idx: qam = "QPSK"
    if i == 0 and i != target_mcs_idx: qam = "BPSK"
    
    evm = qam_to_evm[qam]
    # 模擬 Power Back-off
    pwr = round(tx_pwr_base - (abs(evm + 5.0) * 0.38), 1)
    
    # --- 關鍵 Link Budget 公式 ---
    # RSSI = TX_Pwr + TX_Ant - TX_Loss - FSPL + RX_Ant - RX_Loss
    eirp = pwr + tx_ant - tx_loss
    rssi = round(eirp - fspl + rx_ant - rx_loss, 1) 
    
    data.append({
        "MCS_Level": m_label,
        "Modulation": qam,
        "EVM_Spec": evm,
        "Target_Power": pwr,
        "EIRP": round(eirp, 1),
        "RSSI": rssi
    })

df = pd.DataFrame(data)

# --- 4. 介面呈現 ---
col_table, col_chart = st.columns([1.2, 0.8])

with col_table:
    st.subheader("📋 完整 Link Budget 表格")
    st.write(f"當前路徑損耗 (FSPL): **{round(fspl, 1)} dB**")
    st.data_editor(df, use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 趨勢曲線圖")
    st.line_chart(df.set_index("MCS_Level")[["Target_Power", "RSSI"]])

# --- 5. 下載功能 ---
st.divider()
csv_data = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 下載完整測試報表 (CSV)",
    data=csv_data,
    file_name=f"WiFi_Full_Report_{band}_{dist}m.csv",
    mime="text/csv",
)
