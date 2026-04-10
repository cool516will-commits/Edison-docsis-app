import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Dynamic QAM RF Tool", layout="wide")
st.title("📶 WiFi Link Budget (Dynamic QAM & EVM Logic)")

# --- 1. 定義 QAM 與 EVM 的物理連動規則 ---
# 標準連動字典：讓程式知道選哪個 QAM 就該套用哪個 Spec
qam_to_evm = {
    "BPSK": -5.0,
    "QPSK": -13.0,
    "16-QAM": -19.0,
    "64-QAM": -27.0,
    "256-QAM": -32.0,
    "1024-QAM": -35.0,
    "4096-QAM": -38.0
}

# --- 2. 側邊欄：QAM 規格自定義 ---
with st.sidebar:
    st.header("🎯 QAM Customization")
    st.write("調整各階 MCS 的調變方式：")
    
    # 建立一個動態字典來儲存使用者的選擇
    user_mcs_config = {}
    for i in range(14):
        # 預設值參考 HLD_test.xlsm 的標準配置
        default_qam = "4096-QAM" if i >= 12 else ("1024-QAM" if i >= 10 else "256-QAM")
        if i < 8: default_qam = "64-QAM"
        if i < 3: default_qam = "QPSK"
        if i == 0: default_qam = "BPSK"
        
        user_mcs_config[i] = st.selectbox(
            f"MCS {i} Modulation", 
            options=list(qam_to_evm.keys()),
            index=list(qam_to_evm.keys()).index(default_qam),
            key=f"mcs_{i}"
        )

# --- 3. RF 參數與 Link Budget 計算 ---
with st.sidebar:
    st.divider()
    st.header("📡 RF Path Params")
    tx_pwr_m0 = st.number_input("Target Power MCS0 (dBm)", value=20.0)
    dist = st.number_input("Distance (m)", value=10.0)
    # 簡化計算 Path Loss (5GHz 範例)
    fspl = 20 * math.log10(max(dist, 0.1)) + 20 * math.log10(5180 * 10**6) - 147.55

# --- 4. 數據整合與連動運算 ---
data = []
for i in range(14):
    selected_qam = user_mcs_config[i]
    evm_val = qam_to_evm[selected_qam]
    
    # 自動連動：若調變越複雜，自動加大 Power Back-off (模擬硬體極限)
    # 這裡用邏輯模擬：BPSK 降 0dB, 4096-QAM 降 10dB
    qam_penalty = abs(evm_val) / 4.0 
    pwr = round(tx_pwr_m0 - qam_penalty, 1)
    
    # Link Budget
    rssi = pwr + 5.0 - 2.0 - fspl + 3.0 - 1.0 # 帶入天線增益與損耗
    
    data.append({
        "MCS": i,
        "Modulation": selected_qam,
        "Auto EVM Spec": evm_val,
        "Target Power (dBm)": pwr,
        "RSSI (dBm)": round(rssi, 1)
    })

df = pd.DataFrame(data)

# --- 5. 畫面顯示 ---
st.subheader("📊 動態連動結果表")
st.write(f"當前路徑損耗 Path Loss: **{round(fspl, 1)} dB**")
st.data_editor(df, use_container_width=True, hide_index=True)

st.info("💡 **連動說明**：你在左側改變 MCS 的 Modulation，表格中的 **EVM Spec** 與 **Target
