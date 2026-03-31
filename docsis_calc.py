import math
import streamlit as st

# =========================
# 工程計算核心
# =========================
def get_ds_speed(ver, bw, ch, qam, mode):
    if ver == "3.0":
        # D3.0 下行 6MHz (256QAM 約 38~40 Mbps)
        eff_30 = 0.90 if mode == "理論最大值" else 0.86
        return round(5.36 * math.log2(qam) * eff_30 * ch, 2)
    
    if mode == "理論最大值":
        # 修正理論值：效率設為 0.77，讓 5 隻 Block 落在 8.5G 左右
        # 計算：192 * 12 * 0.77 * 5 = 8870 Mbps
        return round(bw * math.log2(qam) * 0.77 * ch, 2)
    else:
        # 實戰模式：基準 1.7G (效率 0.738)
        base_eff = 0.738
        total_speed = 0
        for i in range(int(ch)):
            # 1-2 隻保持 1.7G；3 隻起衰減，符合 4隻~6.4G / 5隻~8G
            loss_factor = 0.99 if i < 2 else 0.965
            eff = base_eff * (loss_factor ** i)
            total_speed += bw * math.log2(qam) * eff
        return round(total_speed, 2)

def get_us_speed(ver, bw, ch, qam, mode):
    if ver == "3.0":
        eff_30_us = 0.88 if mode == "理論最大值" else 0.82
        return round(5.12 * math.log2(qam) * eff_30_us * ch, 2)
    # US 實務基準：256QAM 2 隻 96MHz ≈ 1044 Mbps
    eff_us = 0.75 if mode == "理論最大值" else 0.68
    return round(bw * math.log2(qam) * eff_us * ch, 2)

# =========================
# UI 介面 (移除所有廢話備註)
# =========================
st.set_page_config(page_title="DOCSIS 計算機", layout="wide")
st.title("📟 DOCSIS 工程實戰計算機")

with st.sidebar:
    st.header("⚙️ 系統設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"], index=2)
    mode = st.radio("計算模式", ["理論最大值", "實戰衰減模型"], index=1)
    st.divider()
    ds_qam = st.selectbox("下行 (DS) QAM", [4096, 2048, 1024, 256], index=0 if ver!="3.0" else 3)
    us_qam = st.selectbox("上行 (US) QAM", [1024, 512, 256, 128, 64], index=2 if ver!="3.0" else 4)

col_ds, col_us = st.columns(2)

with col_ds:
    st.subheader("🔵 Downstream (DS)")
    ds_bw = 6.0 if ver == "3.0" else st.number_input("單一 Block 頻寬 (MHz)", value=192.0, step=8.0)
    ds_ch = st.number_input("DS 數量", value=32 if ver=="3.0" else 5, min_value=1)
    st.metric("下行總吞吐量", f"{get_ds_speed(ver, ds_bw, ds_ch, ds_qam, mode)} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    us_bw = 6.4 if ver == "3.0" else st.number_input("US Block 頻寬 (MHz)", value=96.0, step=8.0)
    us_ch = st.number_input("US 數量", value=4 if ver=="3.0" else 2, min_value=1)
    st.metric("上行總吞吐量", f"{get_us_speed(ver, us_bw, us_ch, us_qam, mode)} Mbps")