import math
import streamlit as st

# =========================
# 工程計算核心邏輯
# =========================
def get_ds_speed(ver, ch, qam):
    # D3.0 邏輯
    if ver == "3.0":
        return round(5.36 * math.log2(qam) * 0.82 * ch, 2)
    
    # D3.1 / D4.0 邏輯 (錨點對齊法)
    # 基本計算: 192MHz * bits * 效率
    if ver == "3.1":
        # 對齊 2 Block ≈ 3400 Mbps (3.4G)
        eff = 0.738 
        return round(192 * math.log2(qam) * eff * ch, 2)
    
    if ver == "4.0":
        if ch == 4:
            # 對齊 4 Block ≈ 6400 Mbps (6.4G)
            eff = 0.695
            return round(192 * math.log2(qam) * eff * ch, 2)
        elif ch >= 5:
            # 對齊 5 Block ≈ 8070 Mbps (8.0G)
            # 採用 3高2低 調變分配模擬
            eff_fix = 0.725
            s_high = 192 * math.log2(qam) * eff_fix * 3
            s_low = 192 * math.log2(2048) * eff_fix * (ch - 3)
            return round(s_high + s_low, 2)
        else:
            # 1~3 隻跑基礎效率
            return round(192 * math.log2(qam) * 0.75 * ch, 2)

def get_us_speed(ch, qam):
    # 對齊 2 Block (256QAM) ≈ 1045 Mbps (1.04G)
    # 計算: 96MHz * 8 bits * 0.68 效率 * 2 ch
    eff = 0.68
    return round(96 * math.log2(qam) * eff * ch, 2)

# =========================
# UI 介面
# =========================
st.set_page_config(page_title="DOCSIS 實戰計算機", layout="wide")
st.title("📟 DOCSIS 工程實戰計算機")

with st.sidebar:
    st.header("⚙️ 系統設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"], index=2)
    ds_qam = st.selectbox("下行 (DS) QAM", [4096, 2048, 1024, 256], index=0)
    us_qam = st.selectbox("上行 (US) QAM", [1024, 512, 256, 128, 64], index=2)

col_ds, col_us = st.columns(2)

with col_ds:
    st.subheader("🔵 Downstream (DS)")
    ds_ch = st.number_input("DS Block 數量", value=5 if ver=="4.0" else 2, min_value=1)
    ds_res = get_ds_speed(ver, ds_ch, ds_qam)
    st.metric("下行總吞吐量", f"{ds_res} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    us_ch = st.number_input("US Block 數量", value=2, min_value=1)
    if ver == "3.0":
        us_res = round(5.12 * math.log2(us_qam) * 0.82 * us_ch, 2)
    else:
        us_res = get_us_speed(us_ch, us_qam)
    st.metric("上行總吞吐量", f"{us_res} Mbps")

st.divider()