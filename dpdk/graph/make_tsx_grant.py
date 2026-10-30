#!/usr/bin/env python3

import sys
import re
from pathlib import Path

import matplotlib.pyplot as plt


if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <log_file>")
    sys.exit(1)

input_path = Path(sys.argv[1])

if not input_path.is_file():
    print(f"Error: file not found: {input_path}")
    sys.exit(1)


# --------------------------------------------------
# YYYYMMDD ディレクトリを探す
# --------------------------------------------------

# date_dir = None

# for parent in input_path.parents:
#     if re.fullmatch(r"\d{8}", parent.name):
#         date_dir = parent.name
#         break

# if date_dir is None:
#     print("Error: YYYYMMDD directory was not found.")
#     sys.exit(1)


# --------------------------------------------------
# 出力先
# --------------------------------------------------

output_dir = Path.cwd()
# output_dir.mkdir(parents=True, exist_ok=True)

output_path = "tsx_granted.png"


# --------------------------------------------------
# データ
# --------------------------------------------------

comps = [0, 4, 8, 16, 24]

# data[comp][tsx] = granted
data = {
    comp: {} for comp in comps
}


# --------------------------------------------------
# ログ読み込み
# --------------------------------------------------

pattern = re.compile(
    r"tsx=(\d+)us,\s*comp=(\d+),\s*granted=(\d+),\s*denied=(\d+)"
)

with input_path.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()

        if not line:
            continue

        match = pattern.search(line)

        if match is None:
            print(f"Warning: skipped line: {line}")
            continue

        tsx = int(match.group(1))
        comp = int(match.group(2))
        granted = int(match.group(3))

        if comp not in data:
            print(f"Warning: unknown comp={comp}")
            continue

        data[comp][tsx] = granted


# --------------------------------------------------
# 読み込んだデータを確認
# --------------------------------------------------

for comp in comps:
    print(f"comp={comp}:")
    for tsx in sorted(data[comp]):
        print(f"  tsx={tsx}, granted={data[comp][tsx]}")


# --------------------------------------------------
# グラフ作成
# --------------------------------------------------

plt.figure(figsize=(12, 7))

# 横軸は必ず 5～50
tsx_values = list(range(5, 51))

for comp in comps:

    # データが存在しない tsx は None にする
    granted_values = [
        data[comp].get(tsx, None)
        for tsx in tsx_values
    ]

    plt.plot(
        tsx_values,
        granted_values,
        marker="o",
        label=f"comp={comp}"
    )


# --------------------------------------------------
# 軸・タイトル
# --------------------------------------------------

plt.ylim(-500, 15000)

plt.xlabel("Time Slice Extension (us)")
plt.ylabel("Granted Count")

plt.title("Time Slice Extension vs Granted Count")

# 5～50 を1us刻みで表示
plt.xticks(range(5, 51))

plt.grid(True)
plt.legend()

plt.tight_layout()

plt.savefig(output_path, dpi=300)

plt.close()

print()
print(f"Saved: {output_path}")