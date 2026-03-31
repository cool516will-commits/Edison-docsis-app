加進去完全不麻煩，但這正是區分「初階工具」與「專業模擬器」的關鍵。

在 DOCSIS 3.1/4.0 中，Subcarrier Spacing (SCS) 通常有 25 kHz 和 50 kHz 兩種選擇。這會直接影響 FFT Size（8K 或 4K）以及循環前綴（Cyclic Prefix）的開銷。

如果要讓你的程式碼更值錢，我們可以把這個參數加在 Downstream (DS) 的設定中。當使用者調整這個值時，理論值會微幅變動，以符合實務上對不同載波間距的效率要求。

🛠️ 升級版：加入 Subcarrier-BW (SCS) 的完整代碼
這版程式碼將子載波頻寬納入變數，並確保在預設情況下依然精準對齊 Table 40 與你的 1.7G/8.0G 實測目標。

Python
import math
import streamlit as st

# =========================
# 工程計算核心邏輯
# =========================
def get_ds_speed(ver, bw, ch, qam, scs, mode):
    if ver == "3.0":
        # D3.0 下行固定邏輯
        eff_30 = 0.95 if mode == "理論最大值" else 0.86
        return round(5.36 * math.log2(qam) * eff_30 * ch, 2)
    
    # 根據 Subcarrier Spacing (SCS) 微調效率補償
    # 50 kHz 通常比 25 kHz 的有效負載比例稍微高一點點 (因為 Guardband 佔比略異)
    scs_factor = 1.0 if scs == 50 else 0.985
    
    if mode == "理論最大值":
        # 對齊 Table 40 基準效率 0.742
        return round(bw * math.log2(qam) * 0.742 * scs_factor * ch, 2)
    else:
        # 實戰模式：鎖定 1.7G 基準 (效率 0.738)
        base_eff = 0.738 * scs_factor
        total_speed = 0
        for i in range(int(ch)):
            # 1-2 隻 1.7G；3 隻起衰減，符合 4隻~6.4G / 5隻~8.0G
            loss_factor = 0.99 if i < 2 else 0.965
            eff = base_eff * (loss_factor ** i)
            total_speed += bw * math.log2(qam) * eff
        return round(total_speed, 2)

def get_us_speed(ver, bw, ch, qam, mode):
    if ver == "3.0":
        eff_30_us = 0.88 if mode == "理論最大值" else 0.82
        return round(5.12 * math.log2(qam) * eff_30_us * ch, 2)
    
    if mode == "理論最大值":
        # 對齊 Table 41 基準效率 0.753
        return round(bw * math.log2(qam) * 0.753 * ch, 2)
    else:
        # 實務模式：256QAM 2 隻 96MHz = 1044 Mbps
        return round(bw * math.log2(qam) * 0.68 * ch, 2)

# =========================
# UI 介面
# =========================
st.set_page_config(page_title="DOCSIS 專業實戰計算機", layout="wide")
st.title("📟 DOCSIS 工程實務計算機 (含子載波參數)")

with st.sidebar:
    st.header("⚙️ 系統設定")
    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"], index=2)
    mode = st.radio("計算模式", ["理論最大值", "實戰衰減模型"], index=1)
    
    st.divider()
    # 物理層進階參數
    if ver != "3.0":
        scs = st.selectbox("Subcarrier Spacing (kHz)", [50, 25], index=0)
    else:
        scs = 50 # D3.0 不適用
        
    ds_qam = st.selectbox("下行 (DS) QAM", [4096, 2048, 1024, 512, 256], index=0 if ver!="3.0" else 4)
    us_qam = st.selectbox("上行 (US) QAM", [4096, 2048, 1024, 512, 256, 128, 64], index=4 if ver!="3.0" else 6)

col_ds, col_us = st.columns(2)

with col_ds:
    st.subheader("🔵 Downstream (DS)")
    ds_bw = 6.0 if ver == "3.0" else st.number_input("單一 Block 頻寬 (MHz)", value=192.0, step=8.0)
    ds_ch = st.number_input("DS 數量", value=32 if ver=="3.0" else 5, min_value=1)
    ds_res = get_ds_speed(ver, ds_bw, ds_ch, ds_qam, scs, mode)
    st.metric("下行總吞吐量", f"{ds_res} Mbps")

with col_us:
    st.subheader("🔴 Upstream (US)")
    us_bw = 6.4 if ver == "3.0" else st.number_input("US Block 頻寬 (MHz)", value=96.0, step=8.0)
    us_ch = st.number_input("US 數量", value=4 if ver=="3.0" else 2, min_value=1)
    us_res = get_us_speed(ver, us_bw, us_ch, us_qam, mode)
    st.metric("上行總吞吐量", f"{us_res} Mbps")