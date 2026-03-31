import math
import streamlit as st

# =========================
# 工程計算核心
# =========================
def calc_speed_core(bw, qam, total_eff, ch_count=1):
    bits = math.log2(qam)
    return bw * bits * total_eff * ch_count

# =========================
# 頁面設定
# =========================
st.set_page_config(page_title="DOCSIS 實戰精準全對齊", layout="wide")
st.title("📟 DOCSIS 工程實戰計算機 (6.4G/8G 精準對齊)")

# =========================
# Sidebar 設定
# =========================
with st.sidebar:
    st.header("⚙️ 系統設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"], index=2) 
    mode = st.radio("計算模式", ["理論最大值", "實戰衰減模型"], index=1)
    
    st.divider()
    qam_list = [4096, 2048, 1024, 512, 256, 128, 64]
    ds_base_qam = st.selectbox("下行 (DS) 基礎 QAM", qam_list, index=0)
    us_qam = st.selectbox("上行 (US) QAM", qam_list, index=4) 

    st.divider()
    # 基礎效率設定 (OFDMA/OFDM)
    total_eff_us = 0.68  # 對齊實務 US ~1.1G
    if ver == "3.1":
        total_eff_ds = 0.74 # 對齊 D3.1 DS 2隻 ~3.4G
    else:
        total_eff_ds = 0.85 # D4.0 基礎效率

    st.info(f"DS 實務基礎效率: {round(total_eff_ds*100, 1)}%")
    st.info(f"US 實務基礎效率: {round(total_eff_us*100, 1)}%")

# =========================
# 主畫面
# =========================
col_ds, col_us = st.columns(2)

with col_ds:
    st.subheader("🔵 Downstream (DS)")
    if ver == "3.0":
        ds_ch = st.number_input("DS Channel 數量", value=32)
        ds_res = round(5.360537 * math.log2(ds_base_qam) * 0.82 * ds_ch, 2)
    else:
        ds_bw = st.number_input("DS 單一 Block 頻寬 (MHz)", value=192.0)
        ds_ch = st.number_input("DS Block 數量", value=5 if ver == "4.0" else 2)
        
        # --- 精準實戰衰減模型 ---
        if ver == "4.0" and mode == "實戰衰減模型":
            if ds_ch == 4:
                # 對齊 6.4G 初點: 192 * 12 * 0.695 * 4 ≈ 6400
                eff_fix = 0.695
                ds_res = round(calc_speed_core(ds_bw, ds_base_qam, eff_fix, 4), 2)
            elif ds_ch >= 5:
                # 對齊 8G 初點: (192*12*0.725*3) + (192*11*0.725*2) ≈ 8070
                eff_fix = 0.725
                s_high = calc_speed_core(ds_bw, ds_base_qam, eff_fix, 3)
                s_low = calc_speed_core(ds_bw, 2048, eff_fix, 2)
                ds_res = round(s_high + s_low, 2)
            else:
                ds_res = round(calc_speed_core(ds_bw, ds_base_qam, total_eff_ds, ds_ch), 2)
        else:
            ds_res = round(calc_speed_core(ds_bw, ds_base_qam, total_eff_ds, ds_ch), 2)

    st.metric("下行總吞吐量 (實戰預估)", f"{ds_res} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    if ver == "3.0":
        us_ch = st.number_input("US Channel 數量 (SC-QAM)", value=8)
        us_res = round(5.12 * math.log2(us_qam) * 0.82 * us_ch, 2)
    else:
        us_bw = st.number_input("US 單一 Block 頻寬 (MHz)", value=96.0)
        us_ch = st.number_input("US Block 數量 (OFDMA)", value=2)
        us_res = round(calc_speed_core(us_bw, us_qam, total_eff_us, us_ch), 2)
    
    st.metric("上行總吞吐量 (實戰預估)", f"{us_res} Mbps")

st.divider()