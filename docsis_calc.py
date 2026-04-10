import math
import streamlit as st

# =========================
# 工程計算核心邏輯
# =========================
def get_ds_speed(ver, bw, ch, qam, scs, mode):
    if ver == "3.0":
        # D3.0 下行固定邏輯 (6MHz 基準，扣除 Overhead 後每 Channel 約 38-42 Mbps)
        eff_30 = 0.95 if mode == "理論最大值" else 0.86
        return round(5.36 * math.log2(qam) * eff_30 * ch, 2)
    
    # 根據 Subcarrier Spacing (SCS) 微調效率補償
    scs_factor = 1.0 if scs == 50 else 0.985
    
    if mode == "理論最大值":
        # 對齊 DOCSIS 3.1 PHY 標竿效率
        return round(bw * math.log2(qam) * 0.742 * scs_factor * ch, 2)
    else:
        # 實戰模式：考慮多載波聚合後的疊加損耗 (i 為載波索引)
        base_eff = 0.738 * scs_factor
        total_speed = 0
        for i in range(int(ch)):
            # 模擬 CMTS/Modem 在處理多個 OFDM Block 時的資源競爭與熱雜訊
            loss_factor = 0.99 if i < 2 else 0.965
            eff = base_eff * (loss_factor ** i)
            total_speed += bw * math.log2(qam) * eff
        return round(total_speed, 2)

def get_us_speed(ver, bw, ch, qam, mode):
    if ver == "3.0":
        eff_30_us = 0.88 if mode == "理論最大值" else 0.82
        return round(5.12 * math.log2(qam) * eff_30_us * ch, 2)
    
    if mode == "理論最大值":
        return round(bw * math.log2(qam) * 0.753 * ch, 2)
    else:
        # 實務模式：考慮 OFDMA 的保護時段 (Guard Interval) 與 MAC Overhead
        return round(bw * math.log2(qam) * 0.68 * ch, 2)

# =========================
# UI 介面優化
# =========================
st.set_page_config(page_title="DOCSIS 專業實戰計算機", layout="wide")
st.title("📟 DOCSIS 工程實務計算機")
st.caption("版本 2.0 | 已修正物理層計算邏輯與 SCS 補償")

with st.sidebar:
    st.header("⚙️ 系統參數設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"], index=1)
    mode = st.radio("計算模型", ["理論最大值", "實戰衰減模型"], index=1)
    
    st.divider()
    
    # 動態變更 QAM 選項與 SCS
    if ver == "3.0":
        ds_qams = [256, 64]
        us_qams = [64, 32, 16]
        scs = 50 # D3.0 不適用 SCS，給預設值
    else:
        ds_qams = [4096, 2048, 1024, 512, 256]
        us_qams = [4096, 2048, 1024, 512, 256, 128, 64]
        scs = st.selectbox("Subcarrier Spacing (kHz)", [50, 25], index=0)

    ds_qam = st.selectbox("下行 (DS) QAM 調變", ds_qams, index=0)
    us_qam = st.selectbox("上行 (US) QAM 調變", us_qams, index=0 if ver!="3.0" else 0)

col_ds, col_us = st.columns(2)

with col_ds:
    st.subheader("🔵 Downstream (DS)")
    if ver == "3.0":
        st.info("D3.0 固定頻寬: 6.0 MHz (Annex B)")
        ds_bw = 6.0
    else:
        ds_bw = st.number_input("OFDM Block 頻寬 (MHz)", value=192.0, step=8.0)
    
    ds_ch = st.number_input("DS 載波數量", value=32 if ver=="3.0" else 2, min_value=1)
    ds_res = get_ds_speed(ver, ds_bw, ds_ch, ds_qam, scs, mode)
    
    # 自動換算單位
    if ds_res >= 1000:
        st.metric("下行總吞吐量", f"{round(ds_res/1000, 2)} Gbps")
    else:
        st.metric("下行總吞吐量", f"{ds_res} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    if ver == "3.0":
        st.info("D3.0 固定頻寬: 6.4 MHz")
        us_bw = 6.4
    else:
        us_bw = st.number_input("OFDMA Block 頻寬 (MHz)", value=96.0, step=8.0)
    
    us_ch = st.number_input("US 載波數量", value=4 if ver=="3.0" else 1, min_value=1)
    us_res = get_us_speed(ver, us_bw, us_ch, us_qam, mode)
    
    if us_res >= 1000:
        st.metric("上行總吞吐量", f"{round(us_res/1000, 2)} Gbps")
    else:
        st.metric("上行總吞吐量", f"{us_res} Mbps")
