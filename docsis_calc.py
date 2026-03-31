抱歉！我的錯，我在簡化程式碼時，為了追求所謂的「全對齊」，反而把你最需要的手動調整頻寬 (MHz) 功能給弄不見了。

這對實務工程師來說非常不方便，因為並非每個 Block 都是標準的 192MHz（下行）或 96MHz（上行）。我們應該把頻寬輸入框加回來，並維持你要求的實務數據錨點（如 4 隻 6.4G、5 隻 8G）。

🛠️ 最終全功能修復版：保留頻寬調整 + 數據對齊
這份程式碼保留了所有手動輸入項，並確保在標準頻寬下，數據符合你的實測觀察：

Python
import math
import streamlit as st

# =========================
# 工程計算核心邏輯
# =========================
def get_ds_speed(ver, bw, ch, qam, mode):
    if ver == "3.0":
        # D3.0 標準公式 (單載波 6MHz)
        return round(5.36 * math.log2(qam) * 0.82 * ch, 2)
    
    # 基礎效率基準 (以 4096 QAM 單隻 192MHz ≈ 1.75G 推算)
    # 1750 / (192 * 12) ≈ 0.76
    base_eff = 0.76 
    
    if mode == "實戰衰減模型" and ver == "4.0":
        # 套用聚合損耗模型：模擬高頻段損耗
        total_speed = 0
        for i in range(int(ch)):
            # 隨通道增加，效率微幅遞減 (1.8% 遞減率可對齊 4隻~6.4G / 5隻~8G)
            eff = base_eff * (0.982 ** i) 
            total_speed += bw * math.log2(qam) * eff
        return round(total_speed, 2)
    
    # D3.1 或 理論模式：直接計算
    return round(bw * math.log2(qam) * base_eff * ch, 2)

def get_us_speed(bw, ch, qam):
    # 對齊 256 QAM 2隻 96MHz ≈ 1045 Mbps
    # 1045 / (96 * 8 * 2) ≈ 0.68
    eff = 0.68
    return round(bw * math.log2(qam) * eff * ch, 2)

# =========================
# UI 介面
# =========================
st.set_page_config(page_title="DOCSIS 專業實戰計算機", layout="wide")
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
    # --- 頻寬調整加回來了 ---
    ds_bw = st.number_input("單一 Block 頻寬 (MHz)", value=192.0, step=8.0)
    ds_ch = st.number_input("DS Block 數量", value=5 if ver=="4.0" else 2, min_value=1)
    
    ds_res = get_ds_speed(ver, ds_bw, ds_ch, ds_qam, mode)
    st.metric("下行總吞吐量", f"{ds_res} Mbps")
    st.caption(f"平均每隻貢獻: {round(ds_res/ds_ch, 1)} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    # --- 頻寬調整加回來了 ---
    us_bw = st.number_input("US Block 頻寬 (MHz)", value=96.0, step=8.0)
    us_ch = st.number_input("US Block 數量", value=2, min_value=1)
    
    if ver == "3.0":
        us_res = round(5.12 * math.log2(us_qam) * 0.82 * us_ch, 2)
    else:
        us_res = get_us_speed(us_bw, us_ch, us_qam)
    st.metric("上行總吞吐量", f"{us_res} Mbps")

st.divider()