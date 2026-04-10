import streamlit as st
import pandas as pd
import numpy as np

# 頁面配置
st.set_page_config(page_title="WiFi Power Tool", layout="wide")

st.title("📶 RF Power Table Calculator (WiFi / DOCSIS)")

# --- 側邊欄參數 ---
with st.sidebar:
    st.header("⚙️ Input Parameters")
    band = st.selectbox("Frequency Band", ["2.4 GHz", "5 GHz", "6 GHz"])
    bw = st.selectbox("Bandwidth (MHz)", [20, 40, 80, 160, 320])
    base_pwr = st.number_input("MCS0 Target Power (dBm)", value=20.0, step=0.5)
    
    st.divider()
    st.info("調整上方數值，下方表格與圖表將自動同步。")

# --- 生成 MCS Power Table 數據 ---
# 定義 WiFi 6/7 常用的 MCS Level
mcs_levels = [f"MCS{i}" for i in range(13)]
# 模擬 Power Drop (通常 MCS 越高，為了 EVM，Power 會往下降)
# 這裡設定每升一階 MCS，Power 約下降 0.5~1 dBm (可手動在網頁修改)
powers = [round(base_pwr - (i * 0.7), 1) for i in range(len(mcs_list := mcs_levels))]

df = pd.DataFrame({
    "MCS Level": mcs_levels,
    "Target Power (dBm)": powers,
    "EVM Limit (dB)": [-5, -10, -13, -16, -19, -22, -25, -27, -30, -32, -35, -35, -38] # 參考值
})

# --- 主要顯示區 ---
st.subheader("📊 Power Table Result")

# 讓表格可以手動編輯 (Data Editor)
edited_df = st.data_editor(
    df, 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Target Power (dBm)": st.column_config.NumberColumn(format="%.1f dBm")
    }
)

# --- 繪製曲線圖 ---
st.subheader("📈 Power Curve Trend")
# 使用 Streamlit 內建圖表，最快最穩
st.line_chart(edited_df.set_index("MCS Level")["Target Power (dBm)"])

# --- 統計與下載 CSV ---
st.divider()
col1, col2 = st.columns(2)

with col1:
    avg_pwr = round(edited_df["Target Power (dBm)"].mean(), 2)
    st.metric("Average TX Power", f"{avg_pwr} dBm")

with col2:
    # 產生 CSV 下載內容
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 匯出 Power Table CSV",
        data=csv,
        file_name=f"WiFi_Power_Table_{band}_{bw}MHz.csv",
        mime='text/csv'
    )

st.success("✅ 數據已更新。你可以直接在表格中修改 Power 值，圖表會即時跟著動。")
