#!/usr/bin/env python3
import sys
import os
import numpy as np
import matplotlib.pyplot as plt

BASE_MAX_RTT = 4000  # Threshold for highlighting RTT values
BIN_US_WIDTH = 100  # ヒストグラムのビン幅

def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_histogram_over99.py <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]
    num_competition_process = sys.argv[2]
    title_label = sys.argv[4]

    # --- 出力ファイル名（ディレクトリ除去 → 拡張子除去 → _p99.png） ---
    filename_only = os.path.basename(logfile)         # logs/data.log → data.log
    base = os.path.splitext(filename_only)[0]         # data.log → data
    out_png = base + "_p99.png"                       # data_p99.png

    # --- データ読み込み ---
    values = []
    with open(logfile, "r") as f:
        for line in f:
            # line = line.strip().replace(",", "")  # カンマ付き数値を対応
            if line:
                try:
                    values.append(float(line))
                except ValueError:
                    pass

    if not values:
        print("No valid data found in the file.")
        sys.exit(1)

    values = np.array(values)

    # --- 99 パーセンタイル値 ---
    p99 = np.percentile(values, 99)

    # p99 超のみ抽出
    over_99 = values[values > p99]

    if len(over_99) == 0:
        print("No values exceed the 99th percentile.")
        sys.exit(1)

    max_rtt = max(values)

    if sys.argv[3] != None:
       xlim = int(sys.argv[3])
    else:
      if max_rtt > BASE_MAX_RTT:
        xlim = max_rtt // 1000 * 1000 + 1000
      else:
        xlim = BASE_MAX_RTT

    # --- ヒストグラム作成 (頻度ベース) ---
    plt.figure(figsize=(10, 6))

    bins = np.arange(0, max_rtt + BIN_US_WIDTH, BIN_US_WIDTH)

    plt.hist(over_99, bins=bins, color="blue")  # ← density=False（デフォルト）で頻度

    plt.xlabel("Processing Time")
    plt.ylabel("Frequency (log scale)")
    plt.yscale("log")  # y 軸対数スケール
    plt.xlim(0, xlim)
    plt.ylim(0.15, 10000)  

    # plt.title("Histogram of Processing Times (Values Over 99th Percentile)")
    plt.title(f'{title_label} での RTT の分布\n'
              f'(ビン幅: {BIN_US_WIDTH}us, 通信回数: {len(values)}, 競合プロセス数: {num_competition_process}', fontsize=15)
    plt.grid(True)
    plt.tight_layout()

    # 保存
    plt.savefig(out_png)
    print(f"Saved histogram to: {out_png}")

    plt.close()


if __name__ == "__main__":
    main()
