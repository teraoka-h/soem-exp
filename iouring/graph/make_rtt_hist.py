import sys
import matplotlib.pyplot as plt
import os
import japanize_matplotlib
import numpy as np

BASE_MAX_RTT = 4000  # Threshold for highlighting RTT values
BIN_US_WIDTH = 15  # Width of histogram bins in microseconds
OVER_THRESHOD_US = 500

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <RTT data file>")
        sys.exit(1)

    filepath = sys.argv[1]
    num_competition_process = sys.argv[2]
    title_label = sys.argv[4]
    rtt_list = []

    # if "soem" in filepath:
    #     with open(filepath, 'r') as f:
    #         pt_list = [line.strip().split(',') for line in f]
    #         rtt_list = [float(pt_list[0])]
    # else:
    #     with open(filepath, 'r') as f:
    #         rtt_list = [float(line.strip()) for line in f if line.strip()]

    with open(filepath, 'r') as f:
        rtt_list = [float(line.strip()) for line in f]

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

    p99 = np.percentile(rtt_list, 99)

    # 平均線
    plt.axvline(mean_rtt, color='green', linestyle='dashed', linewidth=2,
                label=f'平均 RTT: {mean_rtt:.2f} us')
    plt.axvline(p99, color='red', linestyle='dotted', linewidth=2, 
                label=f'p99: {p99:.2f} us')
    plt.plot([], [], ' ', label=f'最大 RTT: {max_rtt:.2f} us')
    plt.plot([], [], ' ', label=f'標準偏差: {std:.2f}')

    print(f"[INFO] RTT > {OVER_THRESHOD_US} us")
    rtt_over = [rtt for rtt in rtt_list if rtt > OVER_THRESHOD_US]
    print(f"RTT > {OVER_THRESHOD_US} us count: {len(rtt_over)} / ({len(rtt_list)})")

    # y 軸対数で freq=1 を必ず表示させる
    plt.yscale('log')
    plt.ylim(0.15, max(n) * 1.2 if len(n) > 0 else 10)
    # plt.ylim(0.15, 10000)

    if sys.argv[3] != None:
       xlim = int(sys.argv[3])
    else:
      if max_rtt > BASE_MAX_RTT:
        xlim = max_rtt // 1000 * 1000 + 1000
      else:
        xlim = BASE_MAX_RTT
    print(f"[INFO] xlim set to {xlim} us")

    plt.xlim(0, xlim)
    plt.title(f'{title_label} での RTT の分布\n'
              f'(ビン幅: {BIN_US_WIDTH}us, 通信回数: {len(rtt_list)}, 競合プロセス数: {num_competition_process}, 500 us 超過回数: {len(rtt_over)})', fontsize=15)
    plt.xlabel('処理時間 (us)', fontsize=18)
    plt.ylabel('頻度 (log scale)', fontsize=18)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(save_filename)
    print(f"Saved histogram plot as {save_filename}")
    # print([rtt for rtt in rtt_list if rtt > 4000.0])
    print(f"[INFO] RTT > {OVER_THRESHOD_US} us")
    rtt_over = [rtt for rtt in rtt_list if rtt > OVER_THRESHOD_US]
    # for rtt in rtt_over:
    #     print(f"{rtt:.2f} us")
    # print(f"RTT > {OVER_THRESHOD_US} us count: {len(rtt_over)} / ({len(rtt_list)})")
    # print("min:", min(rtt_list))
    # print("median:", np.percentile(rtt_list, 50))
    # print("90%:", np.percentile(rtt_list, 90))
    # print("95%:", np.percentile(rtt_list, 95))
    # print("99%:", np.percentile(rtt_list, 99))
    # print("99.9%:", np.percentile(rtt_list, 99.9))
    # print("mean:", np.mean(rtt_list))
    # print("max:", max(rtt_list))


if __name__ == "__main__":
    main()
