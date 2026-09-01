#!/usr/bin/env python3
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

    # データ読み込み
    user_data = read_user_file(user_file)   # shape=(N,4)
    kernel_data = read_kernel_file(kernel_file)

    max_rtt = np.max(user_data[:,3])
    print(f"Max RTT: {max_rtt} us")

    if len(user_data) != len(kernel_data):
        print("Error: user と kernel のサンプル数が一致しません")
        sys.exit(1)

    # 系列とラベルをまとめる
    datasets = [
        (user_data[:,0], "SOEM send", "red"),
        (user_data[:,1], "SOEM ppoll loop", "orange"),
        (user_data[:,2], "SOEM recv", "green"),
        (user_data[:,3], "SOEM send to recv", "blue"),
        (kernel_data,   "Kernel send to recv", "violet"),
    ]

    # colors = ["skyblue", "orange", "lightgreen", "violet", "salmon"]

    max_freq = max([np.histogram(sample, bins=50)[0].max() for sample, _, _ in datasets])

    for sample, label, color in datasets:
        # ヒストグラム描画 (10us 刻み)
        fig, ax = plt.subplots(figsize=(10, 6))
        min_val, max_val = np.min(sample), np.max(sample)
        bins = np.arange(min_val, max_val + BIN_WIDTH_US, BIN_WIDTH_US)  

        ax.hist(sample, bins=bins, color=color, alpha=1, label=label)

        # 軸とラベル
        ax.set_xlabel("処理時間 (us)")
        ax.set_ylabel("頻度 (log scale)")
        ax.set_title(f"ラウンドトリップ中の {label} の処理時間ヒストグラム ({BIN_WIDTH_US}us 間隔, 通信回数: {len(sample)})")
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
        ax.set_yscale('log')
        ax.set_xlim(0, ((max_rtt // 1000) + 1) * 1000)
        ax.set_ylim(0.5, max_freq * 1.05)
        ax.grid(True)
        ax.legend()

        plt.tight_layout()
        out_file = f"{label.replace(' ', '_')}_{common}hist.png"
        plt.savefig(out_file)
        plt.close(fig)  # メモリ節約
        print(f"Saved: {out_file}")

if __name__ == "__main__":
    main()
