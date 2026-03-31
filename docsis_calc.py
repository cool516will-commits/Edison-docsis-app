import math
import streamlit as st

# =========================
# 工程計算核心
# =========================
def get_ds_speed(ver, bw, ch, qam, mode):
    if ver == "3.0":
        return round(5.36 * math.log2(qam) * 0.82 * ch, 2)
    
    # 基準點：192MHz @ 4096QAM = 1.7G (1700 / (192 * 12) ≈ 0.738)
    base_eff = 0.738
    
    if mode == "實戰衰減模型" and ver == "4.0":
        total_speed = 0
        for i in range(int(ch)):
            # 1-2 隻保持 1.7G/隻；3 隻起衰減加大以符合 4隻~6.4G / 5隻~8G
            loss_factor = 0.99 if i < 2 else 0.965
            eff = base_eff * (loss_factor ** i)
            total_speed += bw * math.log2(qam) * eff
        return round(total_speed, 2)
    
    return round(bw * math.log2(qam) * base_eff * ch, 2)

def get_us_speed(bw, ch, qam):
    # 基準點：256QAM 2隻 96MHz = 1044.48 Mbps
    return round(bw * math.log2(qam) * 0.68 * ch, 2)

# =========================
# UI 介面
# =========================
st.set_page_config(page_title="DOCSIS 計算機", layout="wide")
st.title("📟 DOCSIS 工程實戰計算機")

with st.sidebar:
    st.header("⚙️ 系統設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"], index=2)
    mode = st.radio("計算模式", ["理論最大值", "實戰衰減模型"], index=1)
    st.divider()
    ds_qam = st.selectbox("下行 (DS) QAM", [4096, 2048, 1024, 256], index=0)
    us_qam = st.selectbox("上行 (US) QAM", [1024, 512, 256, 128, 64], index=2)

col_ds, col_us = st.columns(2)

with col_ds:
    st.subheader("🔵 Downstream (DS)")
    ds_bw = st.number_input("單一 Block 頻寬 (MHz)", value=192.0, step=8.0)
    ds_ch = st.number_input("DS Block 數量", value=5 if ver=="4.0" else 2, min_value=1)
    ds_res = get_ds_speed(ver, ds_bw, ds_ch, ds_qam, mode)
    st.metric("下行總吞吐量", f"{ds_res} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    us_bw = st.number_input("US Block 頻寬 (MHz)", value=96.0, step=8.0)
    us_ch = st.number_input("US Block 數量", value=2, min_value=1)
    if ver == "3.0":
        us_res = round(5.12 * math.log2(us_qam) * 0.82 * us_ch, 2)
    else:
        us_res = get_us_speed(us_bw, us_ch, us_qam)
    st.metric("上行總吞吐量", f"{us_res} Mbps")