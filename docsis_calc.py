import math
import streamlit as st

# =========================
# 工程計算核心邏輯
# =========================
def get_ds_speed(ver, bw, ch, qam, mode):
    if ver == "3.0":
        # D3.0 下行 (6MHz SC-QAM)
        # 理論: 接近物理極限 (約 42.8 Mbps/ch)
        # 實務: 扣除封包開銷與損耗 (約 38.8 Mbps/ch)
        eff_30 = 0.95 if mode == "理論最大值" else 0.86
        return round(5.36 * math.log2(qam) * eff_30 * ch, 2)
    
    if mode == "理論最大值":
        # 純物理計算，不考慮衰減 (192MHz @ 4096QAM 理论約 2.1G)
        return round(bw * math.log2(qam) * 0.94 * ch, 2)
    else:
        # 實務模式：以 192MHz @ 4096QAM = 1.7G 為基準 (效率 0.738)
        base_eff = 0.738
        total_speed = 0
        for i in range(int(ch)):
            # 實務損耗模型：1-2 隻保持 1.7G 基準；3 隻起衰減加大
            # 確保對齊：2隻≈3.4G / 4隻≈6.4G / 5隻≈8.0G
            loss_factor = 0.99 if i < 2 else 0.965
            eff = base_eff * (loss_factor ** i)
            total_speed += bw * math.log2(qam) * eff
        return round(total_speed, 2)

def get_us_speed(ver, bw, ch, qam, mode):
    if ver == "3.0":
        # D3.0 上行 (6.4MHz SC-QAM)
        eff_30_us = 0.92 if mode == "理論最大值" else 0.82
        return round(5.12 * math.log2(qam) * eff_30_us * ch, 2)
    
    # D3.1/4.0 上行基準：256QAM 2 隻 96MHz ≈ 1044 Mbps (效率 0.68)
    eff_us = 0.85 if mode == "理論最大值" else 0.68
    return round(bw * math.log2(qam) * eff_us * ch, 2)

# =========================
# UI 介面
# =========================
st.set_page_config(page_title="DOCSIS 實戰計算機", layout="wide")
st.title("📟 DOCSIS 工程實戰計算機")

with st.sidebar:
    st.header("⚙️ 系統設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"], index=2)
    mode = st.radio("計算模式", ["理論最大值", "實戰衰減模型"], index=1)
    
    st.divider()
    # 根據版本預設 QAM
    ds_qam_idx = 3 if ver == "3.0" else 0
    us_qam_idx = 4 if ver == "3.0" else 2
    
    ds_qam = st.selectbox("下行 (DS) QAM", [4096, 2048, 1024, 256], index=ds_qam_idx)
    us_qam = st.selectbox("上行 (US) QAM", [1024, 512, 256, 128, 64], index=us_qam_idx)

col_ds, col_us = st.columns(2)

with col_ds:
    st.subheader("🔵 Downstream (DS)")
    if ver == "3.0":
        st.info("D3.0 固定使用 6.0 MHz 計算")
        ds_bw_val = 6.0
        default_ch = 32
    else:
        ds_bw_val = st.number_input("單一 Block 頻寬 (MHz)", value=192.0, step=8.0)
        default_ch = 5 if ver == "4.0" else 2
        
    ds_ch = st.number_input("DS 數量", value=default_ch, min_value=1)
    ds_res = get_ds_speed(ver, ds_bw_val, ds_ch, ds_qam, mode)
    st.metric("下行總吞吐量", f"{ds_res} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    if ver == "3.0":
        st.info("D3.0 上行固定使用 6.4 MHz 計算")
        us_bw_val = 6.4
        default_us_ch = 4
    else:
        us_bw_val = st.number_input("US Block 頻寬 (MHz)", value=96.0, step=8.0)
        default_us_ch = 2
        
    us_ch = st.number_input("US 數量", value=default_us_ch, min_value=1)
    us_res = get_us_speed(ver, us_bw_val, us_ch, us_qam, mode)
    st.metric("上行總吞吐量", f"{us_res} Mbps")