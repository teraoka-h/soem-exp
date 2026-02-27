#!/usr/bin/env python3
import sys
import os
import matplotlib.pyplot as plt
import japanize_matplotlib
import numpy as np

BIN_WIDTH_US = 10

def read_kernel_file(filename):
    return np.loadtxt(filename)

def read_user_file(filename):
    data = np.loadtxt(filename, delimiter=",")
    # data[:,0]=send, data[:,1]=poll_recv, data[:,2]=recv, data[:,3]=total
    return data

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} user_log kernel_log")
        sys.exit(1)

    user_file, kernel_file = sys.argv[1], sys.argv[2]
    threshold_us = int(sys.argv[3]) if len(sys.argv) > 3 else None


    # 共通部分から出力ファイル名生成
    basename1 = os.path.splitext(os.path.basename(user_file))[0]
    basename2 = os.path.splitext(os.path.basename(kernel_file))[0]
    common = os.path.commonprefix([basename1, basename2])
    out_file = f"over_hist/over{threshold_us}_{common}all_hist.png"

    # データ読み込み
    user_data = read_user_file(user_file)   # shape=(N,4)
    kernel_data = read_kernel_file(kernel_file)

    if len(user_data) != len(kernel_data):
        print("Error: user と kernel のサンプル数が一致しません")
        sys.exit(1)

    # 系列とラベルをまとめる
    datasets = [
        (user_data[:,0], "$\it{T_{s1}}$"),
        (user_data[:,1], "$\it{T_{s2}}$"),
        (user_data[:,2], "$\it{T_{s3}}$"),
        (user_data[:,3], "$\it{T_{s4}}$"),
        (kernel_data,   "$\it{T_{k}}$")
    ]

    max_rtt = np.max(user_data[:,3])
    max_freq = 0
    for sample, _ in datasets:
        hist, _ = np.histogram([v for v in sample if threshold_us is not None and v > threshold_us], bins=50)
        max_freq = max(max_freq, hist.max())

    # 色リスト（系列ごとに違う色を割当て）
    colors = ["red", "orange", "green", "blue", "violet"]

    # サブプロット作成（縦に5つ並べる）
    fig, axes = plt.subplots(len(datasets), 1, figsize=(10, 12), sharex=False)
    fig.suptitle(f"SOEM の送信開始から受信完了までの各処理区間において {threshold_us}us を超える処理時間ヒストグラム\n(ビン幅: {BIN_WIDTH_US}us, 通信回数: {len(user_data)})", fontsize=14)


    for ax, (sample, label), color in zip(axes, datasets, colors):
        min_val, max_val = np.min(sample), np.max(sample)
        bins = np.arange(min_val, max_val + BIN_WIDTH_US, BIN_WIDTH_US) 

        over_data = [v for v in sample if threshold_us is not None and v > threshold_us]

        # ax.hist(over_data, bins=bins, color=color, alpha=0.7, label=label)
        counts, edges = np.histogram(over_data, bins=bins)
        ax.bar(edges[:-1], counts, width=np.diff(edges),
               align="edge", color=color, alpha=1, label=label)
        
        ax.set_xlim(threshold_us, ((max_rtt // 1000) + 1) * 1000)
        ax.set_ylim(0.5, max_freq * 1.05)
        ax.set_ylabel("頻度 (log scale)")
        ax.set_yscale('log')
        ax.grid(True)
        # ax.set_title(f"{label}")
        ax.legend()
        

    axes[-1].set_xlabel("処理時間 (us)")

    plt.tight_layout()
    plt.savefig(out_file)
    print(f"Saved: {out_file}")

if __name__ == "__main__":
    main()
