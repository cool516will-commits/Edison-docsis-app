import math
import streamlit as st

# 1. 計算邏輯
def calc_speed(ver, bw, qam, ch, overhead_on):
    bits = math.log2(qam)
    # 設定效率 (Overhead)
    eff = 1.0
    if overhead_on:
        eff = 0.82 if ver == "3.0" else 0.88
        
    if ver == "3.0":
        # 3.0 使用標稱符號率
        return round(5.360537 * bits * eff * ch, 2)
    else:
        # 3.1 / 4.0 OFDM 使用頻寬計算
        return round(bw * bits * eff * ch, 2)

# 2. 介面設定
st.set_page_config(page_title="DOCSIS 獨立配置", layout="wide")
st.title("📟 DOCSIS 上下行獨立配置計算機")

# 側邊欄：控制版本與 QAM
with st.sidebar:
    st.header("⚙️ 全域設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"])
    use_oh = st.toggle("扣除 Overhead", value=False)
    
    st.divider()
    qam_list = [16384, 4096, 2048, 1024, 512, 256, 128, 64, 32, 16]
    ds_qam = st.selectbox("DS 下行 QAM", qam_list, index=1)
    us_qam = st.selectbox("US 上行 QAM", qam_list, index=5)

# 主畫面：左右分欄設定「頻寬」與「信道數」
col_ds, col_us = st.columns(2)

with col_ds:
    st.subheader("🔵 Downstream (DS)")
    if ver == "3.0":
        ds_bw = 6.0
        st.write("3.0 頻寬固定 6MHz")
    else:
        ds_bw = st.number_input("DS 單一 Block 頻寬 (MHz)", value=192.0, key="ds_bw")
    
    ds_ch = st.number_input("DS 信道/Block 數量", value=32 if ver=="3.0" else 2, min_value=1, key="ds_ch")
    
    ds_res = calc_speed(ver, ds_bw, ds_qam, ds_ch, use_oh)
    st.metric("下行預估速率", f"{ds_res} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    if ver == "3.0":
        us_bw = 6.0
        st.write("3.0 頻寬固定 6MHz")
        # 3.0 US 符號率稍有不同
        us_speed = round(5.12 * math.log2(us_qam) * (0.82 if use_oh else 1.0) * st.number_input("US 信道數量", value=8, key="us_ch_30"), 2)
    else:
        us_bw = st.number_input("US 單一 Block 頻寬 (MHz)", value=96.0, key="us_bw")
        us_ch = st.number_input("US 信道/Block 數量", value=1, min_value=1, key="us_ch")
        us_speed = calc_speed(ver, us_bw, us_qam, us_ch, use_oh)
    
    st.metric("上行預估速率", f"{us_speed} Mbps")