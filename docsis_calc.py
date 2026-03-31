import math
import streamlit as st

# 1. 計算核心邏輯
def calc_speed(ver, direction, bw, qam, ch, overhead_on):
    # 每個符號的位元數 (log2 QAM)
    bits = math.log2(qam)
    
    # 設定效率 (Efficiency / Overhead)
    # 一般 3.0 損耗約 18%，3.1 以上約 10-12%
    eff = 1.0
    if overhead_on:
        eff = 0.82 if ver == "3.0" else 0.88
        
    if ver == "3.0":
        if direction == "DS":
            # 3.0 DS: 固定 6 MHz, 標稱 5.360537 Msps
            return round(5.360537 * bits * eff * ch, 2)
        else:
            # 3.0 US: 固定 6.4 MHz, 標稱 5.12 Msps (符合工程實務)
            return round(5.12 * bits * eff * ch, 2)
    else:
        # 3.1 / 4.0 OFDM: 直接以頻寬 (MHz) 換算
        return round(bw * bits * eff * ch, 2)

# 2. 網頁介面設定
st.set_page_config(page_title="DOCSIS Pro 計算機", layout="wide")

# 標題與小圖示
st.title("📟 DOCSIS 上下行獨立配置計算機")

# 側邊欄：控制全域參數
with st.sidebar:
    st.header("⚙️ 全域設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"])
    use_oh = st.toggle("扣除 Overhead (計算實際淨速)", value=False)
    
    st.divider()
    st.subheader("📡 調變設定 (QAM)")
    qam_list = [16384, 4096, 2048, 1024, 512, 256, 128, 64, 32, 16]
    ds_qam = st.selectbox("下行 (DS) QAM", qam_list, index=1) # 預設 4096
    us_qam = st.selectbox("上行 (US) QAM", qam_list, index=5) # 預設 256
    
    st.divider()
    st.caption(f"目前模式: DOCSIS {ver}")
    st.caption(f"Overhead: {'已扣除' if use_oh else '未扣除 (Raw)'}")

# 主畫面：左右分欄 (在手機上會自動變上下排列)
col_ds, col_us = st.columns(2)

# --- 下行區塊 ---
with col_ds:
    st.subheader("🔵 Downstream (DS)")
    if ver == "3.0":
        ds_bw = 6.0
        st.info("💡 3.0 DS 頻寬固定為 6.0 MHz")
    else:
        ds_bw = st.number_input("DS 單一 Block 頻寬 (MHz)", value=192.0, step=6.0, key="ds_bw")
    
    ds_ch = st.number_input("DS 信道 / Block 數量", value=32 if ver=="3.0" else 2, min_value=1, key="ds_ch")
    
    ds_res = calc_speed(ver, "DS", ds_bw, ds_qam, ds_ch, use_oh)
    st.metric("下行預估總速率", f"{ds_res} Mbps")

# --- 上行區塊 ---
with col_us:
    st.subheader("🔴 Upstream (US)")
    if ver == "3.0":
        us_bw = 6.4
        st.info("💡 3.0 US 頻寬固定為 6.4 MHz (5.12 Msps)")
    else:
        us_bw = st.number_input("US 單一 Block 頻寬 (MHz)", value=96.0, step=6.4, key="us_bw")
    
    us_ch = st.number_input("US 信道 / Block 數量", value=8 if ver=="3.0" else 1, min_value=1, key="us_ch")
    
    # 這裡 bw 參數在 3.0 會被 calc_speed 內的 5.12 覆蓋，但仍傳入維持格式
    us_res = calc_speed(ver, "US", us_bw, us_qam, us_ch, use_oh)
    st.metric("上行預估總速率", f"{us_res} Mbps")

st.divider()
st.caption("註：此計算機僅供技術評估使用，實際速率受線路品質及 MAC 層效率影響。")