import pandas as pd

# MCS table (bits per subcarrier, coding rate)
MCS_TABLE = {
    0:  (1, 1/2),
    1:  (2, 1/2),
    2:  (2, 3/4),
    3:  (4, 1/2),
    4:  (4, 3/4),
    5:  (6, 2/3),
    6:  (6, 3/4),
    7:  (6, 5/6),
    8:  (8, 3/4),
    9:  (8, 5/6),
    10: (10, 3/4),
    11: (10, 5/6),
    12: (12, 3/4),  # 4096-QAM
    13: (12, 5/6),
}

# Subcarriers per bandwidth (approx for HE/EHT)
SUBCARRIERS = {
    20: 234,
    40: 468,
    80: 980,
    160: 1960
}

# GI 對應 symbol duration (us)
GI_TABLE = {
    0.8: 13.6,
    1.6: 14.4,
    3.2: 16.0
}

def calculate_rate(mcs, bw, nss, gi):
    bits, rate = MCS_TABLE[mcs]
    subcarriers = SUBCARRIERS[bw]
    symbol_time = GI_TABLE[gi]

    data_rate = (bits * rate * subcarriers * nss) / symbol_time
    return data_rate  # Mbps

# 建立完整表
results = []

for mcs in range(0, 14):  # MCS 0~13
    for bw in [20, 40, 80, 160]:
        for nss in [1, 2, 4]:
            for gi in [0.8, 1.6]:
                rate = calculate_rate(mcs, bw, nss, gi)

                results.append({
                    "MCS": mcs,
                    "Bandwidth(MHz)": bw,
                    "NSS": nss,
                    "GI(us)": gi,
                    "Data Rate (Mbps)": round(rate, 2)
                })

df = pd.DataFrame(results)

# 存成 Excel
df.to_excel("wifi_mcs_table.xlsx", index=False)

print("✅ 已產出 wifi_mcs_table.xlsx")
