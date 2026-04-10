import streamlit as st
import pandas as pd

# 1. 頁面配置
st.set_page_config(page_title="WiFi Power Tool", layout="wide")

st.title("📶 WiFi Power Table & Curve Calculator")

# --- 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ Settings")
    band = st.selectbox("Frequency Band", ["2.4 GHz", "5 GHz", "6 GHz"])
    bw = st.selectbox("Bandwidth (MHz)", [20, 40, 80, 160, 320])
    base_pwr = st.number_input("MCS0 Target Power (dBm)", value=21.0, step=0.5)
    st.divider()
    st.info("可以直接在右側表格修改數值。")

# --- 生成數據 ---
# 定義 MCS 0 到 11 (或 12)
mcs_levels = [f"MCS{i}" for i in range(13)]

# 模擬 Power Drop：隨著 MCS 增加，Power 下降
powers = [round(base_pwr - (i * 0.6), 1) for i in range(len(mcs_levels))]

# 建立 DataFrame
df = pd.DataFrame({
    "MCS Level": mcs_levels,
    "Target Power (dBm)": powers
})

# --- 主要介面佈局 ---
col_table, col_chart = st.columns([1, 1], gap="large")

with col_table:
    st.subheader("📊 Power Table (Editable)")
    # 使用 data_editor 讓你可以直接改數字
    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Target Power (dBm)": st.column_config.NumberColumn(step=0.1, format="%.1f")
        }
    )

with col_chart:
    st.subheader("📈 Power Curve")
    # 把 MCS Level 當成 index 這樣圖表 X 軸才會顯示 MCS
    chart_df = edited_df.set_index("MCS Level")
    st.line_chart(chart_df, y="Target Power (dBm)")

# --- 下載區 ---
st.divider()
footer_col1, footer_col2 = st.columns(2)

with footer_col1:
    avg_pwr = round(edited_df["Target Power (dBm)"].mean(), 2)
    st.metric("Average Power", f"{avg_pwr} dBm")

with footer_col2:
    # 產生 CSV
    csv_data = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 下載此 Power Table (CSV)",
        data=csv_data,
        file_name=f"WiFi_{band}_{bw}MHz_PowerTable.csv",
        mime='text/csv'
    )

st.success
