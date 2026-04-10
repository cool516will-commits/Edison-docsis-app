import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="WiFi RF Tool Pro", layout="wide")
st.title("📶 WiFi Link Budget & Trend (with CSV Export)")

# --- 1. 定義 QAM 與 EVM 對照 ---
qam_to_evm = {
    "BPSK": -5.0, "QPSK": -13.0, "16-QAM": -19.0, 
    "64-QAM": -27.0, "256-QAM": -32.0, "1024-QAM": -35.0, "4096-QAM": -38.0
}

# --- 2. 側邊欄：參數與動態選單 ---
with st.sidebar:
    st.header("⚙️ RF Parameters")
    tx_pwr_base = st.number_input("Base Power (MCS0)", value=20.0)
    dist = st.number_input("Distance (m)", value=10.0)
    band = st.selectbox("Frequency Band", ["5 GHz", "2.4 GHz", "6 GHz"])
    
    st.divider()
    st.subheader("🎯 MCS/QAM 動態調整")
    target_mcs_idx = st.selectbox("選擇要修改的 MCS", options=range(14), format_func=lambda x: f"MCS{x}")
    target_qam = st.selectbox(f"設定 MCS{target_mcs_idx} 調變", options=list(qam_to_evm.keys()), index=6)

# --- 3. 運算邏輯 ---
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
    pwr = round(tx_pwr_base - (abs(evm + 5.0) * 0.38), 1)
    # Link Budget: Power + Gain - Loss - FSPL + RX Gain - RX Loss
    rssi = round(pwr + 5.0 - 2.0 - fspl + 3.0 - 1.0, 1) 
    
    data.append({
        "MCS": i, "MCS_Level": m_label, "Modulation": qam,
        "EVM_Spec": evm, "Target_Power_dBm": pwr, "RSSI_dBm": rssi
    })

df = pd.DataFrame(data)

# --- 4. 介面呈現 ---
col_table, col_chart = st.columns([1, 1])

with col_table:
    st.subheader("📋 Link Budget Table")
    # 這裡顯示表格，並允許手動微調數據
    edited_df = st.data_editor(df.drop(columns=["MCS"]), use_container_width=True, hide_index=True)

with col_chart:
    st.subheader("📈 Power & RSSI Trend")
    # 繪製趨勢曲線圖
    st.line_chart(edited_df.set_index("MCS_Level")[["Target_Power_dBm", "RSSI_dBm"]])

# --- 5. CSV 下載選項 (放在最下方) ---
st.divider()
st.subheader("💾 數據導出")
csv_data = edited_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 下載當前 Power Table (CSV)",
    data=csv_data,
    file_name=f"WiFi_LinkBudget_{band}_{dist}m.csv",
    mime="text/csv",
)

st.info(f"💡 提示：下載的 CSV 將包含你剛才在選單中調整的 {target_qam} 數據與對應的 RSSI。")
