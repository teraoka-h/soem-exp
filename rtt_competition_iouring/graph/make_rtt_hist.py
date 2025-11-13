import sys
import matplotlib.pyplot as plt
import os
import japanize_matplotlib
import numpy as np

MAX_RTT = 4000  # Threshold for highlighting RTT values
BIN_US_WIDTH = 15  # Width of histogram bins in microseconds
OVER_THRESHOD_US = 500

def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <RTT data file>")
        sys.exit(1)

    filepath = sys.argv[1]
    rtt_list = []

    if "soem" in filepath:
        with open(filepath, 'r') as f:
            pt_list = [line.strip().split(',') for line in f]
            rtt_list = [float(rtt[2]) for rtt in pt_list if len(rtt) > 2]
    else:
        with open(filepath, 'r') as f:
            rtt_list = [float(line.strip()) for line in f if line.strip()]

    if not rtt_list:
        print("No RTT data found.")
        sys.exit(1)

    # 入力ファイルの拡張子取得
    base = os.path.splitext(os.path.basename(filepath))[0]
    save_filename = base + '_rtt_hist.png'

    mean_rtt = sum(rtt_list) / len(rtt_list)
    max_rtt = max(rtt_list)
    min_rtt = min(rtt_list)
    varance = np.var(rtt_list)
    std = np.std(rtt_list)

    print(f"平均 RTT: {mean_rtt:.2f} us\n最大 RTT: {max_rtt:.2f} us\n最小 RTT: {min_rtt:.2f}")
    print(f"分散: {varance:.2f}\n標準偏差: {std:.2f}\n")

    # bins の作成
    bins = np.arange(0, max_rtt + BIN_US_WIDTH * 10, BIN_US_WIDTH)

    plt.figure(figsize=(10, 6))
    n, bins_edges, patches = plt.hist(
        rtt_list, bins=bins, color="blue", range=(0, bins[-1])
    )

    # 平均線
    plt.axvline(mean_rtt, color='green', linestyle='dashed', linewidth=2,
                label=f'平均 RTT: {mean_rtt:.2f} us')
    plt.plot([], [], ' ', label=f'最大 RTT: {max_rtt:.2f} us')
    plt.plot([], [], ' ', label=f'標準偏差: {std:.2f}')

    print(f"[INFO] RTT > {OVER_THRESHOD_US} us")
    rtt_over = [rtt for rtt in rtt_list if rtt > OVER_THRESHOD_US]
    print(f"RTT > {OVER_THRESHOD_US} us count: {len(rtt_over)} / ({len(rtt_list)})")

    # y 軸対数で freq=1 を必ず表示させる
    plt.yscale('log')
    plt.ylim(0.15, max(n) * 1.2 if len(n) > 0 else 10)

    # xlim = max_rtt // 1000 * 1000 + 1000
    xlim = MAX_RTT
    print(f"[INFO] xlim set to {xlim} us")

    plt.xlim(0, xlim)
    plt.title(f'io_uring 実装でのラウンドトリップの処理時間ヒストグラム \n'
              f'(ビン幅: {BIN_US_WIDTH}us, 通信回数: {len(rtt_list)}, 競合プロセス数: 8, over 500 us: {len(rtt_over)})')
    plt.xlabel('処理時間 (us)', fontsize=24)
    plt.ylabel('頻度 (log scale)', fontsize=24)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(save_filename)
    print(f"Saved histogram plot as {save_filename}")
    # print([rtt for rtt in rtt_list if rtt > 4000.0])

if __name__ == "__main__":
    main()
