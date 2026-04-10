import streamlit as st
import pandas as pd

# 1. 頁面基本配置 (這必須在程式碼最上方)
st.set_page_config(
    page_title="Wi-Fi Power Design Tool",
    page_icon="📶",
    layout="wide"
)

# 2. 標題與簡介
st.title("📶 Wi-Fi Power Table 自動化設計工具")
st.markdown("---")

# 3. 側邊欄參數設定
with st.sidebar:
    st.header("⚙️ 全域參數設定")
    band = st.selectbox("頻段 (Band)", ["2.4 GHz", "5 GHz", "6 GHz", "Wi-Fi 7 (6 GHz)"])
    bw = st.select_slider("頻寬 (Bandwidth MHz)", options=[20, 40, 80, 160, 320], value=80)
    base_pwr = st.number_input("MCS0 基準功率 (Target Power dBm)", value=21.0, step=0.5)
    st.info("調整參數後，右側數據與圖表會自動更新。")

# 4. 數據生成邏輯
# 根據 MCS 等級模擬 Power Drop 趨勢
mcs_list = [f"MCS{i}" for i in range(13)]
# 簡單模擬：高階調變 (MCS 10+) 會有更明顯的 Power Drop
powers = []
for i in range(len(mcs_list)):
    if i <= 7:
        p = base_pwr - (i * 0.5)
    else:
        p = base_pwr - (i * 0.8) # 高階 MCS Drop 較多
    powers.append(round(p, 1))

df = pd.DataFrame({
    "MCS Level": mcs_list,
    "Target Power (dBm)": powers
})

# 5. 主要顯示區域
col_table, col_chart = st.columns([1, 1], gap="large")

with col_table:
    st.subheader("📊 數據編輯器")
    st.write("直接在表格中修改數值，右側圖表會同步跳動：")
    # 使用 data_editor 允許使用者手動微調數據
    edited_df = st.data_editor(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Target Power (dBm)": st.column_config.NumberColumn(step=0.1, format="%.1f")
        }
    )

with col_chart:
    st.subheader("📈 Power Curve 趨勢圖")
    # 畫出折線圖
    chart_data = edited_df.set_index("MCS Level")
    st.line_chart(chart_data, y="Target Power (dBm)", height=400)

# 6. 底部統計與下載
st.divider()
avg_pwr = round(edited_df["Target Power (dBm)"].mean(), 2)

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.metric(label="平均發射功率", value=f"{avg_pwr} dBm")

with footer_col2:
    # 準備下載檔案
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 匯出當前數據 (CSV)",
        data=csv,
        file_name=f"WiFi_{band}_{bw}MHz_Power_Table.csv",
        mime='text/csv'
    )

with footer_col3:
    if st.button("♻️ 恢復預設值"):
        st.rerun()

# 頁尾資訊
st.caption(f"當前配置：{band} / {bw}MHz")
