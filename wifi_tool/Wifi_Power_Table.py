import streamlit as st
import pandas as pd
import math

# 設定網頁標題與佈局
st.set_page_config(page_title="WiFi AP Link Budget Tool", layout="wide")
st.title("📶 WiFi Link Budget & Target power")

# --- 1. 定義 QAM 與 EVM 對照 ---
qam_to_evm = {
    "BPSK": -5.0, "QPSK": -13.0, "16-QAM": -19.0, 
    "64-QAM": -27.0, "256-QAM": -32.0, "1024-QAM": -35.0, "4096-QAM": -38.0
}

# --- 2. 側邊欄：參數設定 ---
with st.sidebar:
    st.header("⚙️ RF Parameters")
    
    # TX (發射端) - 已移除 TX Ext. Cable Loss
    st.subheader("📡 TX (發射端)")
    ic_pwr = st.number_input("IC/PA Output Power (dBm)", value=25.0, help="晶片輸出的原始功率")
    
    # 將 Trace/Filter/Jumper 全部整合為板級總損耗
    total_board_loss = st.number_input("Total Board Loss (dB)", value=1.5, help="包含 Trace, Filter 以及極短跳線的總損耗")
    
    # 計算板端接頭功率 (這就是你實際能量到的點)
    conducted_pwr = ic_pwr - total_board_loss
    st.success(f"📍 板端 I-PEX 預期輸出: {conducted_pwr:.1f} dBm")
    
    tx_ant = st.number_input("TX Antenna Gain (dBi)", value=3.0)
    
    st.divider()
    
    # RX (接收端)
    st.subheader("📥 RX (接收端)")
    rx_ant = st.number_input("RX Antenna Gain (dBi)", value=2.0)
    rx_loss = st.number_input("RX System Loss (dB)", value=1.0, help="接收端板損與線損總和")
    
    st.divider()
    
    # 環境參數
    st.subheader("🌍 Environment")
    dist = st.number_input("Distance (m)", value=10.0)
    band = st.selectbox("Frequency Band", ["2.4 GHz", "5 GHz", "6 GHz"])
    
    st.divider()
    target_mcs_idx = st.selectbox("選擇要修改的 MCS", options=range(14), format_func=lambda x: f"MCS{x}")
    target_qam = st.selectbox(f"設定 MCS{target_mcs_idx} 調變", options=list(qam_to_evm.keys()), index=6)

# --- 3. 核心運算 ---
f_map = {"5 GHz": 5180, "2.4 GHz": 2412, "6 GHz": 6105}
freq = f_map[band]
fspl = 20 * math.log10(max(dist, 0.1)) + 20 * math.log10(freq * 10**6) - 147.55

data = []
for i in range(14):
    m_label = f"MCS{i}"
    qam = target_qam if i == target_mcs_idx else ("4096-QAM" if i >= 12 else ("1024-QAM" if i >= 10 else "256-QAM"))
    if i < 8 and i != target_mcs_idx: qam = "64-QAM"
    if i < 3 and i != target_mcs_idx: qam = "QPSK"
    if i == 0 and i != target_mcs_idx: qam = "BPSK"
    
    evm = qam_to_evm[qam]
    
    # Conducted Power (板端功率)
    pwr = round(conducted_pwr - (abs(evm + 5.0) * 0.4), 1)
    
    # EIRP = 板端功率 + 天線增益 (因為外部線損已忽略或併入板損)
    eirp = round(pwr + tx_ant, 1)
    
    # RSSI
    rssi = round(eirp - fspl + rx_ant - rx_loss, 1) 
    
    data.append({
        "MCS_Level": m_label,
        "Modulation": qam,
        "EVM_Spec": evm,
        "Conducted_Power_dBm": pwr,
        "EIRP_dBm": eirp,
        "RSSI_dBm": rssi
    })

df = pd.DataFrame(data)

# --- 4. 畫面呈現 ---
col_table, col_charts = st.columns([1.2, 0.8])

with col_table:
    st.subheader("📋 Link Budget Table")
    st.data_editor(df, use_container_width=True, hide_index=True)
    st.download_button("📥 下載完整 CSV", df.to_csv(index=False).encode('utf-8'), "AP_RF_Report.csv")

with col_charts:
    st.subheader("📈 Power & RSSI Trend")
    st.line_chart(df.set_index("MCS_Level")[["Conducted_Power_dBm", "RSSI_dBm"]])
    st.subheader("📉 EVM Spec Requirement")
    st.area_chart(df.set_index("MCS_Level")["EVM_Spec"], color="#ff4b4b")
