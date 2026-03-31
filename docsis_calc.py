import math
import streamlit as st

# =========================
# 實戰工程計算核心
# =========================
def get_ds_speed(ver, bw, ch, qam, mode):
    if ver == "3.0":
        return round(5.36 * math.log2(qam) * 0.82 * ch, 2)
    
    # 基礎效率：確保 192MHz @ 4096QAM 單隻約 1.7G+
    base_eff = 0.77 
    
    if mode == "實戰衰減模型" and ver == "4.0":
        total_speed = 0
        for i in range(int(ch)):
            # 損耗邏輯：前 2 隻損耗極小，第 3 隻起損耗係數加大 (累乘遞減)
            # 這樣能實現：2隻~3.4G+, 4隻~6.4G, 5隻~8.0G 的實戰曲線
            if i < 2:
                loss_factor = 0.99  # 前兩隻幾乎不掉速
            else:
                loss_factor = 0.965 # 第三隻起，受高頻 MER 影響損耗加劇
                
            eff = base_eff * (loss_factor ** i)
            total_speed += bw * math.log2(qam) * eff
        return round(total_speed, 2)
    
    # D3.1 或 理論模式 (線性計算)
    return round(bw * math.log2(qam) * base_eff * ch, 2)

def get_us_speed(bw, ch, qam):
    # 對齊實測：256 QAM 2隻 96MHz ≈ 1045 Mbps
    eff = 0.68
    return round(bw * math.log2(qam) * eff * ch, 2)

# =========================
# UI 介面設定
# =========================
st.set_page_config(page_title="DOCSIS 專業實務計算機", layout="wide")
st.title("📟 DOCSIS 工程實務計算機 (全功能版)")

with st.sidebar:
    st.header("⚙️ 系統參數")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"], index=2)
    mode = st.radio("計算模式", ["理論最大值", "實戰衰減模型"], index=1)
    
    st.divider()
    ds_qam = st.selectbox("下行 (DS) 基礎 QAM", [4096, 2048, 1024, 256], index=0)
    us_qam = st.selectbox("上行 (US) 基礎 QAM", [1024, 512, 256, 128, 64], index=2)

col_ds, col_us = st.columns(2)

with col_ds:
    st.subheader("🔵 Downstream (DS)")
    # 頻寬輸入框已找回
    ds_bw = st.number_input("單一 Block 頻寬 (MHz)", value=192.0, step=8.0)
    ds_ch = st.number_input("DS Block 數量", value=5 if ver=="4.0" else 2, min_value=1)
    
    ds_res = get_ds_speed(ver, ds_bw, ds_ch, ds_qam, mode)
    st.metric("下行總吞吐量", f"{ds_res} Mbps")
    st.caption(f"平均每隻 Block 貢獻: {round(ds_res/ds_ch, 1)} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    # 頻寬輸入框已找回
    us_bw = st.number_input("US Block 頻寬 (MHz)", value=96.0, step=8.0)
    us_ch = st.number_input("US Block 數量", value=2, min_value=1)
    
    if ver == "3.0":
        us_res = round(5.12 * math.log2(us_qam) * 0.82 * us_ch, 2)
    else:
        us_res = get_us_speed(us_bw, us_ch, us_qam)
    st.metric("上行總吞吐量", f"{us_res} Mbps")

st.divider()