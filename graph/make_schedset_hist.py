#!/usr/bin/env python3

import sys
import os

import matplotlib.pyplot as plt
import matplotlib_fontja
import numpy as np


BASE_MAX_OVERHEAD = 100  # x軸の基本最大値 [us]
BIN_US_WIDTH = 10         # ヒストグラムのビン幅 [us]


def make_histogram(
    overhead_list,
    output_filename,
    title_label,
    input_filename
):
    """処理時間のヒストグラムを作成する"""

    if not overhead_list:
        print(f"No overhead data found: {title_label}")
        return

    mean_overhead = np.mean(overhead_list)
    max_overhead = max(overhead_list)
    min_overhead = min(overhead_list)
    variance = np.var(overhead_list)
    std = np.std(overhead_list)
    p99 = np.percentile(overhead_list, 99)

    print(f"\n===== {title_label} =====")
    print(f"平均: {mean_overhead:.2f} us")
    print(f"最大: {max_overhead:.2f} us")
    print(f"最小: {min_overhead:.2f} us")
    print(f"中央値: {np.median(overhead_list):.2f} us")
    print(f"分散: {variance:.2f}")
    print(f"標準偏差: {std:.2f}")
    print(f"p99: {p99:.2f} us")

    # --------------------------------------------------
    # bins の作成
    # --------------------------------------------------
    bins = np.arange(
        0,
        max_overhead + BIN_US_WIDTH * 10,
        BIN_US_WIDTH
    )

    plt.figure(figsize=(10, 6))

    n, bins_edges, patches = plt.hist(
        overhead_list,
        bins=bins,
        color="blue",
        range=(0, bins[-1])
    )

    # --------------------------------------------------
    # 平均・p99
    # --------------------------------------------------
    plt.axvline(
        mean_overhead,
        color="green",
        linestyle="dashed",
        linewidth=2,
        label=f"平均: {mean_overhead:.2f} us"
    )

    plt.axvline(
        p99,
        color="red",
        linestyle="dotted",
        linewidth=2,
        label=f"p99: {p99:.2f} us"
    )

    # 凡例に最大値・標準偏差を表示
    plt.plot(
        [],
        [],
        " ",
        label=f"最大: {max_overhead:.2f} us"
    )

    # 中央値
    plt.plot(
        [],
        [],
        " ",
        label=f"中央値: {np.median(overhead_list):.2f} us"
    )

    plt.plot(
        [],
        [],
        " ",
        label=f"標準偏差: {std:.2f}"
    )

    # --------------------------------------------------
    # Y軸を対数表示
    # --------------------------------------------------
    plt.yscale("log")
    plt.ylim(
        0.15,
        1000000
    )

    # --------------------------------------------------
    # X軸
    # --------------------------------------------------
    if max_overhead > BASE_MAX_OVERHEAD:
        xlim = int(max_overhead // 100 * 100 + 100)
    else:
        xlim = BASE_MAX_OVERHEAD

    print(f"[INFO] xlim set to {xlim} us")

    plt.xlim(0, 5000)

    # --------------------------------------------------
    # タイトル・軸ラベル
    # --------------------------------------------------
    plt.title(
        f"動的ポリシ変更方式における{title_label}の処理時間分布\n"
        f"(ビン幅: {BIN_US_WIDTH}us, "
        f"サンプル数: {len(overhead_list)})",
        fontsize=15
    )

    plt.xlabel(
        "処理時間 (us)",
        fontsize=18
    )

    plt.ylabel(
        "頻度 (log scale)",
        fontsize=18
    )

    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        output_filename,
        dpi=300
    )

    plt.close()

    print(
        f"Saved histogram plot as {output_filename}"
    )


def main():
    if len(sys.argv) != 2:
        print(
            f"Usage: python {sys.argv[0]} "
            "<overhead data file>"
        )
        sys.exit(1)

    filepath = sys.argv[1]

    # --------------------------------------------------
    # 入力ファイル読み込み
    #
    # 形式:
    #   15.043500,11.453000
    #   6.728000,20.056000
    #   ...
    #
    # 左: 1回目のポリシ変更 (RT)
    # 右: 2回目のポリシ変更 (NORMAL)
    # --------------------------------------------------

    rt_overhead_list = []
    normal_overhead_list = []

    with open(filepath, "r") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            parts = line.split(",")

            if len(parts) != 2:
                print(
                    f"[WARNING] {line_number} 行目をスキップ: "
                    f"{line}"
                )
                continue

            try:
                rt_overhead = float(parts[0].strip())
                normal_overhead = float(parts[1].strip())
            except ValueError:
                print(
                    f"[WARNING] {line_number} 行目をスキップ: "
                    f"{line}"
                )
                continue

            rt_overhead_list.append(rt_overhead)
            normal_overhead_list.append(normal_overhead)

    if not rt_overhead_list:
        print("No overhead data found.")
        sys.exit(1)

    # --------------------------------------------------
    # 出力ファイル名
    # --------------------------------------------------
    base = os.path.splitext(
        os.path.basename(filepath)
    )[0]

    rt_output_filename = (
        base + "_RT.png"
    )

    normal_output_filename = (
        base + "_NORMAL.png"
    )

    # --------------------------------------------------
    # 1回目のポリシ変更
    # --------------------------------------------------
    make_histogram(
        rt_overhead_list,
        rt_output_filename,
        "1回目のポリシ変更 (RT)",
        filepath
    )

    # --------------------------------------------------
    # 2回目のポリシ変更
    # --------------------------------------------------
    make_histogram(
        normal_overhead_list,
        normal_output_filename,
        "2回目のポリシ変更 (NORMAL)",
        filepath
    )


if __name__ == "__main__":
    main()