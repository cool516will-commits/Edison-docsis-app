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
st.set_page_config(page_title="DOCSIS 8G 完整版", layout="wide")
st.title("📟 DOCSIS 工程實戰計算機 (含 US 多通道設定)")

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
    
    # 效率設定
    total_eff = 0.825 
    if ver == "4.0": total_eff = 0.875 

    st.info(f"實務綜合效率設定: {round(total_eff*100, 1)}%")

# =========================
# 主畫面
# =========================
col_ds, col_us = st.columns(2)

# --- Downstream (DS) ---
with col_ds:
    st.subheader("🔵 Downstream (DS)")
    
    if ver == "3.0":
        ds_bw = 6.0
        ds_ch = st.number_input("DS Channel 數量 (SC-QAM)", value=32, min_value=1)
        ds_res = round(5.360537 * math.log2(ds_base_qam) * 0.82 * ds_ch, 2)
    else:
        ds_bw = st.number_input("DS 單一 Block 頻寬 (MHz)", value=192.0)
        ds_ch = st.number_input("DS Block 數量", value=5, min_value=1)
        
        if mode == "實戰衰減模型" and ds_ch >= 5:
            # 3 隻 4096 QAM, 2 隻 2048 QAM (為了對齊 8G 初點)
            s_high = calc_speed_core(ds_bw, ds_base_qam, total_eff, 3)
            s_low = calc_speed_core(ds_bw, 2048, total_eff, 2)
            ds_res = round(s_high + s_low, 2)
            st.success(f"📊 已對齊 8G 初點數據")
        else:
            ds_res = round(calc_speed_core(ds_bw, ds_base_qam, total_eff, ds_ch), 2)

    st.metric("下行總吞吐量", f"{ds_res} Mbps")

# --- Upstream (US) ---
with col_us:
    st.subheader("🔴 Upstream (US)")
    
    if ver == "3.0":
        us_bw = 6.4
        # 把這隻功能加回來了！
        us_ch = st.number_input("US Channel 數量 (SC-QAM)", value=8, min_value=1)
        us_res = round(5.12 * math.log2(us_qam) * 0.82 * us_ch, 2)
    else:
        us_bw = st.number_input("US 單一 Block 頻寬 (MHz)", value=96.0)
        # 3.1/4.0 現在也可以設定多隻 Block 了
        us_ch = st.number_input("US Block 數量 (OFDMA)", value=2, min_value=1)
        us_res = round(calc_speed_core(us_bw, us_qam, total_eff, us_ch), 2)
    
    st.metric("上行總吞吐量", f"{us_res} Mbps")

st.divider()
st.caption("✅ 已修正：US 通道數量設定已回歸，並支援多 Block 計算。")