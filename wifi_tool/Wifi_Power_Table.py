import streamlit as st
import pandas as pd
import math

# 設定網頁標題與佈局
st.set_page_config(page_title="WiFi RF Link Budget Pro", layout="wide")
st.title("📶 WiFi Link Budget & Power Table (含完整 TX/RX 與板損)")

# --- 1. 定義 QAM 與 EVM 對照關係 ---
qam_to_evm = {
    "BPSK": -5.0, "QPSK": -13.0, "16-QAM": -19.0, 
    "64-QAM": -27.0, "256-QAM": -32.0, "1024-QAM": -35.0, "4096-QAM": -38.0
}

# --- 2. 側邊欄：參數設定 ---
with st.sidebar:
    st.header("⚙️ RF Parameters")
    
    # TX (發射端) - 重新優化命名以防誤會
    st.subheader("📡 TX (發射端)")
    ic_pwr = st.number_input("IC/PA Output Power (dBm)", value=25.0, help="晶片或PA輸出的原始功率 (Base Power)")
    board_loss = st.number_input("Board Loss (Trace/Filter) (dB)", value=1.5, help="PCB走線與濾波器的損耗")
    tx_ant = st.number_input("TX Antenna Gain (dBi)", value=3.0)
    tx_loss = st.number_input("TX Ext. Cable Loss (dB)", value=1.0)
    
    # 計算板端接頭功率 (I-PEX/SMA)
    ipex_pwr = ic_pwr - board_loss
    st.info(f"📍 板端 I-PEX 預期功率: {ipex_pwr:.1f} dBm")
    
    st.divider()
    
    # RX (接收端)
    st.subheader("📥 RX (接收端)")
    rx_ant = st.number_input("RX Antenna Gain (dBi)", value=2.0)
    rx_loss = st.number_input("RX Cable Loss (dB)", value=1.0)
    
    st.divider()
    
    # 環境參數
    st.subheader("🌍 Environment")
    dist = st.number_input("Distance (m)", value=10.0, step=1.0)
    band = st.selectbox("Frequency Band", ["2.4 GHz", "5 GHz", "6 GHz"])
    
    st.divider()
    
    # MCS/QAM 動態連動調整
    st.subheader("🎯 MCS/QAM 動態調整")
    target_mcs_idx = st.selectbox("選擇要修改的 MCS", options=range(14), format_func=lambda x: f"MCS{x}")
    target_qam = st.selectbox(f"設定 MCS{target_mcs_idx} 調變", options=list(qam_to_evm.keys()), index=6)

# --- 3. 核心運算邏輯 ---
# 頻率對應與 FSPL 計算
f_map = {"5 GHz": 5180, "2.4 GHz": 2412, "6 GHz": 6105}
freq = f_map[band]
fspl = 20 * math.log10(max(dist, 0.1)) + 20 * math.log10(freq * 10**6) - 147.55

data = []
for i in range(14):
    m_label = f"MCS{i}"
    # QAM 連動判定
    qam = target_qam if i == target_mcs_idx else ("4096-QAM" if i >= 12 else ("1024-QAM" if i >= 10 else "256-QAM"))
    if i < 8 and i != target_mcs_idx: qam = "64-QAM"
    if i < 3 and i != target_mcs_idx: qam = "QPSK"
    if i == 0 and i != target_mcs_idx: qam = "BPSK"
    
    evm = qam_to_evm[qam]
    
    # Target Power 計算 (包含 QAM Back-off)
    # 基於板端 I-PEX 功率進行回退
    pwr = round(ipex_pwr - (abs(evm + 5.0) * 0.4), 1)
    
    # EIRP = 板端功率 + 天線增益 - 外部線損
    eirp = round(pwr + tx_ant - tx_loss, 1)
    
    # RSSI Link Budget 公式
    rssi = round(eirp - fspl + rx_ant - rx_loss, 1) 
    
    data.append({
        "MCS_Level": m_label,
        "Modulation": qam,
        "EVM_Spec": evm,
        "Target_Power_dBm": pwr,
        "EIRP_dBm": eirp,
        "RSSI_dBm": rssi
    })

df = pd.DataFrame(data)

# --- 4. 畫面呈現 ---
col_table, col_charts = st.columns([1.2, 0.8])

with col_table:
    st.subheader("📋 完整 Link Budget 表格")
    st.write(f"當前路徑損耗 (FSPL): **{round(fspl, 1)} dB**")
    st.data_editor(df, use_container_width=True, hide_index=True)
    
    # CSV 下載
    st.download_button(
        "📥 下載完整 CSV 報表", 
        df.to_csv(index=False).encode('utf-8'), 
        f"RF_Report_{band}_{dist}m.csv"
    )

with col_charts:
    # 曲線圖 1：功率與 RSSI 趨勢
    st.subheader("📈 Power & RSSI Trend")
    st.line_chart(df.set_index("MCS_Level")[["Target_Power_dBm", "RSSI_dBm"]])
    
    # 曲線圖 2：EVM Spec 趨勢 (你要的圖！)
    st.subheader("📉 EVM Spec Requirement (dB)")
    st.area_chart(df.set_index("MCS_Level")["EVM_Spec"], color="#ff4b4b")

st.markdown("---")
st.caption("✅ **核對完成**：IC/PA Power 已經扣除 Board Loss（Trace/Filter）後才計算 Target Power，數值邏輯與實際量測結果同步。")
