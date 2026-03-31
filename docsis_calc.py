import math
import streamlit as st

# =========================
# 實戰工程計算核心
# =========================
def get_ds_speed(ver, ch, qam):
    if ver == "3.0":
        return round(5.36 * math.log2(qam) * 0.82 * ch, 2)
    
    # 根據你的實測：4096 QAM 1隻約 1.7G~1.8G
    # 設定基礎效率為 0.77 (192 * 12 * 0.77 = 1774 Mbps)
    base_eff = 0.77 
    
    if ver == "4.0":
        # 4.0 聚合損耗模型：每多一隻 Block 損耗約 1.5% (反映高頻 MER 下降)
        total_speed = 0
        for i in range(int(ch)):
            eff = base_eff * (0.985 ** i) 
            total_speed += 192 * math.log2(qam) * eff
        return round(total_speed, 2)
    
    # D3.1 兩隻約 3.4G (1.7G * 2)
    return round(192 * math.log2(qam) * base_eff * ch, 2)

def get_us_speed(ch, qam):
    # 對齊實測：256 QAM 2隻約 1045 Mbps (單隻約 522 Mbps)
    # 96 * 8 * 0.68 = 522 Mbps
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
    
    # 顯示平均值供參考
    st.caption(f"平均每隻 Block: {round(ds_res/ds_ch, 1)} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    us_ch = st.number_input("US Block 數量", value=2, min_value=1)
    if ver == "3.0":
        us_res = round(5.12 * math.log2(us_qam) * 0.82 * us_ch, 2)
    else:
        us_res = get_us_speed(us_ch, us_qam)
    st.metric("上行總吞吐量", f"{us_res} Mbps")

st.divider()