#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import os
import japanize_matplotlib

# ---------------------------------------------------------
# 設定値（ここを書き換えるだけで n の対象を変更できる）
# ---------------------------------------------------------
N_LIST = [0, 4, 8, 16, 24]   # ← rtt_syscall_c{n}.log の {n} をここで管理
LOG_PREFIX = "../log/rtt_syscall_nsleep_c"
FIG_PREFIX = "rtt_syscall_nsleep"
LOG_SUFFIX = ".log"

# ---------------------------------------------------------
# ログ読み込み
# ---------------------------------------------------------
def load_log(filepath):
    values = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                values.append(float(line))
            except ValueError:
                continue
    return np.array(values)


# ---------------------------------------------------------
# メイン処理
# ---------------------------------------------------------
def main():

    p99_values = {}            # n → 99 パーセンタイル値
    above_p99_avg = {}         # n → 99 パーセンタイル以上の平均
    above_p99_data = {}        # n → 抽出データ（ヒストグラム用）

    for n in N_LIST:
        filename = f"{LOG_PREFIX}{n}{LOG_SUFFIX}"
        if not os.path.exists(filename):
            print(f"[WARN] {filename} が存在しません")
            continue

        data = load_log(filename)

        # 99 パーセンタイル
        p99 = np.percentile(data, 99)
        p99_values[n] = p99

        # 99 パーセンタイル以上のデータ抽出
        filtered = data[data >= p99]
        above_p99_data[n] = filtered

        # 平均値
        above_p99_avg[n] = filtered.mean() if len(filtered) > 0 else 0

        print(f"n={n}: 99P={p99:.3f} us, 99P 以上平均={above_p99_avg[n]:.3f} us, 件数={len(filtered)}")

    # ------------------------------------------------------------------
    # グラフ 1: 横軸 n、縦軸 99 パーセンタイル値
    # ------------------------------------------------------------------
    plt.figure(figsize=(6, 4))
    x = list(p99_values.keys())
    y = [p99_values[n] for n in x]
    plt.plot(x, y, marker='o')
    plt.xlabel("競合プロセス数")
    plt.ylabel("99 パーセンタイル値 (us)")
    plt.title("競合プロセス数ごとの 99 パーセンタイル値")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{FIG_PREFIX}_p99_values.png")
    plt.close()

    # ------------------------------------------------------------------
    # グラフ 2: 横軸 n、縦軸 99 パーセンタイル以上の平均値
    # ------------------------------------------------------------------
    plt.figure(figsize=(6, 4))
    x = list(above_p99_avg.keys())
    y = [above_p99_avg[n] for n in x]
    plt.plot(x, y, marker='o')
    plt.xlabel("n")
    plt.ylabel("99 パーセンタイル以上の平均値 [us]")
    plt.title("99 パーセンタイル以上データの平均")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{FIG_PREFIX}_p99_above_avg.png")
    plt.close()

    # ------------------------------------------------------------------
    # グラフ 3: 各 n で 99 パーセンタイル以上のデータのヒストグラム
    # ------------------------------------------------------------------
    for n, arr in above_p99_data.items():
        if len(arr) == 0:
            continue

        plt.figure(figsize=(6, 4))
        plt.hist(arr, bins=20)
        plt.xlabel("処理時間 [us]")
        plt.ylabel("頻度")
        plt.title(f"n={n} の 99P 以上データのヒストグラム")
        plt.grid(True)
        plt.tight_layout()

        outname = f"{FIG_PREFIX}_hist_p99_over_n{n}.png"
        plt.savefig(outname)
        plt.close()

    print("完了: p99_values.png, p99_above_avg.png, hist_p99_over_n*.png を出力しました")


# ---------------------------------------------------------
# 実行
# ---------------------------------------------------------
if __name__ == "__main__":
    main()
