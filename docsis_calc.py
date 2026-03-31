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
st.set_page_config(page_title="DOCSIS 8G 精準實戰版", layout="wide")
st.title("📟 DOCSIS 工程吞吐計算機 ")

# =========================
# Sidebar 設定
# =========================
with st.sidebar:
    st.header("⚙️ 系統設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"], index=2)
    
    st.divider()
    mode = st.radio("計算模式", ["理論最大值", "實戰衰減模型"], index=1)
    
    st.divider()
    qam_list = [4096, 2048, 1024, 512, 256, 128, 64]
    ds_base_qam = st.selectbox("下行 (DS) 基礎 QAM", qam_list, index=0)
    us_qam = st.selectbox("上行 (US) QAM", qam_list, index=4) # 預設 256
    
    # 重新對齊效率：4.0 實戰效率約 83% 左右最能反應 8G 出頭的狀況
    total_eff = 0.83 

    st.info(f"實務綜合效率設定: {round(total_eff*100, 1)}%")

# =========================
# 主畫面
# =========================
col_ds, col_us = st.columns(2)

# --- Downstream (DS) ---
with col_ds:
    st.subheader("🔵 Downstream (DS)")
    
    if ver == "3.0":
        ds_ch = st.number_input("DS Channel 數量", value=32)
        ds_res = round(5.360537 * math.log2(ds_base_qam) * 0.82 * ds_ch, 2)
    else:
        ds_bw = st.number_input("DS 單一 Block 頻寬 (MHz)", value=192.0)
        ds_ch = st.number_input("DS Block 數量", value=5)
        
        # 核心修正：確保 5 隻 Block 時一定會跑衰減分配
        if mode == "實戰衰減模型" and ds_ch >= 5:
            # 配置：3 隻跑 4096, 2 隻跑 2048
            # (192 * 12 * 0.83 * 3) + (192 * 11 * 0.83 * 2) = 5737 + 3502 = 9239? 
            # 再下修效率至 0.73 以符合 8G 初點
            eff_fix = 0.725 
            s_high = calc_speed_core(ds_bw, ds_base_qam, eff_fix, 3)
            s_low = calc_speed_core(ds_bw, 2048, eff_fix, 2)
            ds_res = round(s_high + s_low, 2)
            st.success
        else:
            # 理論模式
            ds_res = round(calc_speed_core(ds_bw, ds_base_qam, total_eff, ds_ch), 2)

    st.metric("下行總吞吐量", f"{ds_res} Mbps")

# --- Upstream (US) ---
with col_us:
    st.subheader("🔴 Upstream (US)")
    if ver == "3.0":
        us_ch = st.number_input("US Channel 數量 (SC-QAM)", value=8)
        us_res = round(5.12 * math.log2(us_qam) * 0.82 * us_ch, 2)
    else:
        us_bw = st.number_input("US 單一 Block 頻寬 (MHz)", value=96.0)
        us_ch = st.number_input("US Block 數量 (OFDMA)", value=2)
        us_res = round(calc_speed_core(us_bw, us_qam, total_eff, us_ch), 2)
    
    st.metric("上行總吞吐量", f"{us_res} Mbps")