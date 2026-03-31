import math
import streamlit as st

# =========================
# 工程計算核心
# =========================
def calc_speed(
    ver,
    direction,
    bw,
    qam,
    ch,
    profile,
    usable_sc,
    pilot_eff,
    control_eff,
    ldpc_eff,
    mac_eff
):
    bits = math.log2(qam)

    # =========================
    # DOCSIS 3.0 (SC-QAM)
    # =========================
    if ver == "3.0":
        if direction == "DS":
            sym_rate = 5.360537
        else:
            sym_rate = 5.12

        mac_eff_30 = 0.82
        return round(sym_rate * bits * mac_eff_30 * ch, 2)

    # =========================
    # DOCSIS 3.1 / 4.0 (OFDM)
    # =========================
    else:
        total_eff = (
            usable_sc *
            pilot_eff *
            control_eff *
            ldpc_eff *
            mac_eff
        )

        # D4.0 slight improvement
        if ver == "4.0":
            total_eff *= 1.05

        return round(bw * bits * total_eff * ch, 2)


# =========================
# 頁面設定
# =========================
st.set_page_config(page_title="DOCSIS 工程計算機", layout="wide")

st.title("📟 DOCSIS 工程級吞吐量計算機")

# =========================
# Sidebar 設定
# =========================
with st.sidebar:
    st.header("⚙️ 系統設定")

    ver = st.selectbox("DOCSIS 版本", ["3.0", "3.1", "4.0"])

    st.divider()

    # QAM
    qam_list = [16384, 8192, 4096, 2048, 1024, 512, 256, 128, 64, 32, 16]
    ds_qam = st.selectbox("下行 (DS) QAM", qam_list, index=2)
    us_qam = st.selectbox("上行 (US) QAM", qam_list, index=6)

    st.divider()

    # 工程模式
    profile = st.selectbox(
        "工程效率模型",
        ["保守", "一般", "理想"],
        index=1
    )

    # 預設值
    if profile == "保守":
        usable_sc = 0.94
        pilot_eff = 0.95
        control_eff = 0.98
        ldpc_eff = 0.87
        mac_eff = 0.85

    elif profile == "理想":
        usable_sc = 0.97
        pilot_eff = 0.97
        control_eff = 0.99
        ldpc_eff = 0.92
        mac_eff = 0.95

    else:  # 一般（建議）
        usable_sc = 0.96
        pilot_eff = 0.96
        control_eff = 0.985
        ldpc_eff = 0.89
        mac_eff = 0.90

    st.divider()

    # 可調參數（進階）
    st.subheader("🔧 進階調整")
    usable_sc = st.slider("Subcarrier 可用率", 0.90, 1.0, usable_sc)
    pilot_eff = st.slider("Pilot 效率", 0.90, 1.0, pilot_eff)
    control_eff = st.slider("控制訊號效率", 0.95, 1.0, control_eff)
    ldpc_eff = st.slider("LDPC Coding", 0.80, 1.0, ldpc_eff)
    mac_eff = st.slider("MAC 效率", 0.80, 1.0, mac_eff)

    st.caption(f"總效率 ≈ {round(usable_sc * pilot_eff * control_eff * ldpc_eff * mac_eff, 3)}")


# =========================
# 主畫面
# =========================
col_ds, col_us = st.columns(2)

# =========================
# Downstream
# =========================
with col_ds:
    st.subheader("🔵 Downstream (DS)")

    if ver == "3.0":
        st.info("SC-QAM（固定 Symbol Rate）")
        ds_bw = 6.0
        ds_ch = st.number_input("DS Channel 數量", value=32, min_value=1)

    else:
        st.info("OFDM（含完整工程效率）")
        ds_bw = st.number_input("DS 單一 Block 頻寬 (MHz)", value=192.0, step=6.0)
        ds_ch = st.number_input("DS Block 數量", value=2, min_value=1)

    ds_res = calc_speed(
        ver, "DS", ds_bw, ds_qam, ds_ch,
        profile,
        usable_sc, pilot_eff, control_eff, ldpc_eff, mac_eff
    )

    st.metric("下行總吞吐量", f"{ds_res} Mbps")


# =========================
# Upstream
# =========================
with col_us:
    st.subheader("🔴 Upstream (US)")

    if ver == "3.0":
        st.info("SC-QAM（固定 Symbol Rate）")
        us_bw = 6.4
        us_ch = st.number_input("US Channel 數量", value=8, min_value=1)

    else:
        st.info("OFDMA（含完整工程效率）")
        us_bw = st.number_input("US 單一 Block 頻寬 (MHz)", value=96.0, step=6.4)
        us_ch = st.number_input("US Block 數量", value=1, min_value=1)

    us_res = calc_speed(
        ver, "US", us_bw, us_qam, us_ch,
        profile,
        usable_sc, pilot_eff, control_eff, ldpc_eff, mac_eff
    )

    st.metric("上行總吞吐量", f"{us_res} Mbps")


# =========================
# Footer
# =========================
st.divider()
st.caption("""
本工具採用工程模型（包含 Subcarrier 利用率、Pilot、控制訊號、LDPC coding 與 MAC scheduling），
計算結果為實際可用吞吐量估算值（非理論 PHY rate）。
""")