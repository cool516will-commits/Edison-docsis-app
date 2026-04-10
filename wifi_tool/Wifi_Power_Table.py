import pandas as pd
import os

# ===== MCS TABLE =====
MCS_TABLE = {
    0:(1,1/2),1:(2,1/2),2:(2,3/4),3:(4,1/2),
    4:(4,3/4),5:(6,2/3),6:(6,3/4),7:(6,5/6),
    8:(8,3/4),9:(8,5/6),10:(10,3/4),11:(10,5/6),
    12:(12,3/4),13:(12,5/6)
}

# ===== 子載波數 =====
SUBCARRIERS = {
    20: 234,
    40: 468,
    80: 980,
    160: 1960
}

# ===== Symbol Time (us) =====
GI_TABLE = {
    0.8: 13.6,
    1.6: 14.4
}

def calculate_rate(mcs, bw, nss, gi):
    if mcs not in MCS_TABLE:
        raise ValueError(f"MCS錯誤: {mcs}")

    bits, coding = MCS_TABLE[mcs]
    sub = SUBCARRIERS[bw]
    symbol_time_us = GI_TABLE[gi]

    # 🔥 正確公式（轉 Mbps）
    rate = (bits * coding * sub * nss) / (symbol_time_us * 1e-6) / 1e6
    return rate

# ===== 主程式 =====
rows = []

for mcs in range(14):
    for bw in [20, 40, 80, 160]:
        for nss in [1, 2, 4]:
            for gi in [0.8, 1.6]:
                try:
                    r = calculate_rate(mcs, bw, nss, gi)
                    rows.append([mcs, bw, nss, gi, round(r, 2)])
                except Exception as e:
                    print("錯誤:", e)

df = pd.DataFrame(rows, columns=["MCS", "BW(MHz)", "NSS", "GI(us)", "Rate(Mbps)"])

# ===== 輸出 =====
output = os.path.join(os.getcwd(), "wifi_mcs_table.xlsx")

try:
    df.to_excel(output, index=False, engine="openpyxl")
    print("✅ 成功輸出:", output)
except Exception as e:
    print("❌ Excel輸出失敗:", e)
