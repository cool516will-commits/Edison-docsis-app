import math
import streamlit as st

# =========================
# 工程計算核心 (實戰版)
# =========================
def calc_speed_core(bw, qam, total_eff, ch_count=1):
    bits = math.log2(qam)
    return bw * bits * total_eff * ch_count

# =========================
# 頁面設定
# =========================
st.set_page_config(page_title="DOCSIS 實戰計算機", layout="wide")

st.title("📟 DOCSIS 工程實戰吞吐量計算機")

# =========================
# Sidebar 設定
# =========================
with st.sidebar:
    st.header("⚙️ 系統設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"])
    
    st.divider()
    
    # 實戰模式切換
    mode = st.radio("計算模式", ["理論最大值", "實戰衰減模型"], index=1)
    
    st.divider()
    
    # QAM 基礎設定
    qam_list = [16384, 4096, 2048, 1024, 512, 256, 128, 64]
    ds_base_qam = st.selectbox("下行 (DS) 基礎 QAM", qam_list, index=1)
    us_qam = st.selectbox("上行 (US) 基礎 QAM", qam_list, index=5)

    st.divider()

    # 預設工程效率 (一般建議值)
    usable_sc = 0.96
    pilot_eff = 0.96
    control_eff = 0.985
    ldpc_eff = 0.89
    mac_eff = 0.90
    
    # 計算總效率
    total_eff = usable_sc * pilot_eff * control_eff * ldpc_eff * mac_eff
    if ver == "4.0": total_eff *= 1.05

    st.subheader("🔧 隱形損耗參數")
    st.caption(f"當前工程總效率: {round(total_eff*100, 1)}%")
    st.info("已自動計入 Pilot, LDPC 與 MAC 開銷")

# =========================
# 主畫面
# =========================
col_ds, col_us = st.columns(2)

# --- Downstream (DS) ---
with col_ds:
    st.subheader("🔵 Downstream (DS)")
    
    if ver == "3.0":
        ds_ch = st.number_input("DS Channel 數量", value=32, min_value=1)
        # 3.0 固定效率模型
        ds_res = round(5.360537 * math.log2(ds_base_qam) * 0.82 * ds_ch, 2)
        st.info("SC-QAM 模式")
    else:
        ds_bw = st.number_input("單一 Block 頻寬 (MHz)", value=192.0, step=6.0)
        ds_ch = st.number_input("Block 數量", value=5, min_value=1)
        
        if mode == "實戰衰減模型" and ds_ch >= 3:
            # 模擬高頻衰減邏輯：
            # 前 2 隻跑基礎 QAM, 中間 2 隻降一階, 最後 1 隻再降一階
            ch_group1 = 2
            ch_group2 = 2 if ds_ch >= 4 else 1
            ch_group3 = ds_ch - ch_group1 - ch_group2
            
            qam_mid = max(ds_base_qam / 4, 256) # 降一階
            qam_low = max(ds_base_qam / 16, 64) # 降兩階
            
            s1 = calc_speed_core(ds_bw, ds_base_qam, total_eff, ch_group1)
            s2 = calc_speed_core(ds_bw, qam_mid, total_eff, ch_group2)
            s3 = calc_speed_core(ds_bw, qam_low, total_eff, max(0, ch_group3))
            
            ds_res = round(s1 + s2 + s3, 2)
            
            with st.expander("查看實戰 QAM 分佈"):
                st.write(f"🟢 低頻段 ({ch_group1} Block): {int(ds_base_qam)} QAM")
                st.write(f"🟡 中頻段 ({ch_group2} Block): {int(qam_mid)} QAM")
                if ch_group3 > 0:
                    st.write(f"🔴 高頻段 ({ch_group3} Block): {int(qam_low)} QAM")
        else:
            ds_res = round(calc_speed_core(ds_bw, ds_base_qam, total_eff, ds_ch), 2)

    st.metric("下行總吞吐量 (實戰預估)", f"{ds_res} Mbps")

# --- Upstream (US) ---
with col_us:
    st.subheader("🔴 Upstream (US)")
    if ver == "3.0":
        us_ch = st.number_input("US Channel 數量", value=8, min_value=1)
        us_res = round(5.12 * math.log2(us_qam) * 0.82 * us_ch, 2)
    else:
        us_bw = st.number_input("US Block 頻寬 (MHz)", value=96.0)
        us_ch = st.number_input("US Block 數量", value=1, min_value=1)
        us_res = round(calc_speed_core(us_bw, us_qam, total_eff, us_ch), 2)
    
    st.metric("上行總吞吐量 (實戰預估)", f"{us_res} Mbps")

st.divider()
st.caption("註：『實戰衰減模型』會根據 Block 數量自動模擬高頻段 QAM 降級，這更接近真實 HFC 線路表現。")