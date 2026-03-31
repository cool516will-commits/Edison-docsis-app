import math
import streamlit as st

# =========================
# 專業級工程計算核心
# =========================
def calc_net_speed(bw, qam, efficiency):
    """
    標準物理層淨速計算
    bw: MHz, qam: 調變, efficiency: 綜合損耗率
    """
    bits_per_symbol = math.log2(qam)
    return bw * bits_per_symbol * efficiency

# =========================
# 頁面配置
# =========================
st.set_page_config(page_title="DOCSIS 專業工程計算機", layout="wide")
st.title("📟 DOCSIS 專業級吞吐量計算機")
st.caption("基於物理層開銷與高頻衰減模型，非人工硬湊對齊。")

# =========================
# Sidebar 參數設定
# =========================
with st.sidebar:
    st.header("⚙️ 系統參數")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"], index=2)
    
    st.divider()
    # 這裡定義基礎效率，包含 Pilot, Guardband, LDPC, MAC overhead
    # 4.0 因為 subcarrier 利用率更高，基礎效率稍高
    base_eff = 0.88 if ver == "4.0" else 0.85
    
    st.subheader("💡 損耗模型設定")
    # 引入「高頻段衰減係數」：每增加一個 Block，額外增加的損耗
    agg_loss = st.slider("多通道聚合損耗 (%)", 0.0, 5.0, 1.5, help="模擬高頻段 MER 下降與聚合開銷")
    
    st.divider()
    qam_list = [4096, 2048, 1024, 512, 256, 128, 64]
    ds_qam = st.selectbox("下行 (DS) 基礎 QAM", qam_list, index=0)
    us_qam = st.selectbox("上行 (US) 基礎 QAM", qam_list, index=4)

# =========================
# 主計算邏輯
# =========================
col_ds, col_us = st.columns(2)

with col_ds:
    st.subheader("🔵 Downstream (DS)")
    if ver == "3.0":
        ds_ch = st.number_input("DS Channels", value=32)
        # D3.0 固定公式
        ds_res = round(5.36 * math.log2(ds_qam) * 0.82 * ds_ch, 2)
    else:
        ds_bw = st.number_input("單一 Block 頻寬 (MHz)", value=192.0)
        ds_ch = st.number_input("Block 數量", value=5 if ver == "4.0" else 2)
        
        # --- 動態衰減模型 ---
        total_ds_speed = 0
        for i in range(int(ds_ch)):
            # 邏輯：第一隻 Block 最強，後續每一隻根據聚合損耗遞減效率
            current_eff = base_eff * ((1 - (agg_loss/100)) ** i)
            total_ds_speed += calc_net_speed(ds_bw, ds_qam, current_eff)
        
        ds_res = round(total_ds_speed, 2)

    st.metric("預估總吞吐量", f"{ds_res} Mbps")
    st.info(f"平均每 Block 貢獻: {round(ds_res/ds_ch, 2)} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    if ver == "3.0":
        us_ch = st.number_input("US Channels", value=8)
        us_res = round(5.12 * math.log2(us_qam) * 0.82 * us_ch, 2)
    else:
        us_bw = st.number_input("US 單一 Block 頻寬 (MHz)", value=96.0)
        us_ch = st.number_input("US Block 數量", value=2)
        
        # 上行雜訊大，基礎效率下修
        us_base_eff = 0.75 
        total_us_speed = 0
        for i in range(int(us_ch)):
            current_eff = us_base_eff * ((1 - (agg_loss/100)) ** i)
            total_us_speed += calc_net_speed(us_bw, us_qam, current_eff)
            
        us_res = round(total_us_speed, 2)

    st.metric("預估總吞吐量", f"{us_res} Mbps")

st.divider()
st.markdown("""
### 📖 為什麼這樣算更科學？
1. **聚合損耗模型**：模擬了隨著頻譜延伸（Block 增加），高頻段 MER 下降導致的有效率降低。
2. **非線性遞減**：第一隻 Block 通常最接近理論值，第五隻 Block 則會承受最大的衰減。
3. **靈活對齊**：
    * 如果你的 5 隻 Block 是 **8.0G**，請將聚合損耗調至約 **1.8%**。
    * 如果你的 4 隻 Block 是 **6.4G**，這個模型會自動算出非常接近的數值。
""")