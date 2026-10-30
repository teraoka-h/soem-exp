#!/usr/bin/env python3

import sys
import re
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib_fontja


def read_elapsed_log(path):
    """elapsed.log から実行時間を読み込む"""
    pattern = re.compile(r"^elapsed:\s*([0-9]+(?:\.[0-9]+)?)$")

    values = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            match = pattern.match(line)

            if match is None:
                continue

            values.append(float(match.group(1)))

    if not values:
        raise ValueError(f"実行時間のデータがありません: {path}")

    return values


def read_granted_log(path):
    """tsx_grant.log から granted の値を読み込む"""
    pattern = re.compile(r"granted=(\d+)")

    values = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            match = pattern.search(line)

            if match is None:
                continue

            values.append(int(match.group(1)))

    if not values:
        raise ValueError(f"granted のデータがありません: {path}")

    return values


def main():
    if len(sys.argv) != 5:
        print(
            f"Usage: {sys.argv[0]} "
            "<default_dir> <dynamic_dir> <tsx_dir> <output_file>"
        )
        sys.exit(1)

    default_dir = Path(sys.argv[1])
    dynamic_dir = Path(sys.argv[2])
    tsx_dir = Path(sys.argv[3])
    output_file = Path(sys.argv[4])

    # --------------------------------------------------
    # デフォルト
    # --------------------------------------------------
    default_log = default_dir / "elapsed.log"
    default_values = read_elapsed_log(default_log)

    # --------------------------------------------------
    # 動的ポリシ変更
    # --------------------------------------------------
    dynamic_log = dynamic_dir / "elapsed.log"
    dynamic_values = read_elapsed_log(dynamic_log)

    # --------------------------------------------------
    # Time Slice Extension
    # tsx_{n}us というディレクトリを探す
    # --------------------------------------------------
    tsx_data = []

    pattern = re.compile(r"^tsx_(\d+)us$")

    for path in tsx_dir.iterdir():
        if not path.is_dir():
            continue

        match = pattern.match(path.name)

        if match is None:
            continue

        n = int(match.group(1))

        elapsed_log = path / "elapsed.log"
        grant_log = path / "tsx_grant.log"

        if not elapsed_log.is_file():
            raise FileNotFoundError(
                f"elapsed.log がありません: {elapsed_log}"
            )

        if not grant_log.is_file():
            raise FileNotFoundError(
                f"tsx_grant.log がありません: {grant_log}"
            )

        elapsed_values = read_elapsed_log(elapsed_log)
        granted_values = read_granted_log(grant_log)

        tsx_data.append(
            (n, elapsed_values, granted_values)
        )

    # n の小さい順に並べる
    tsx_data.sort(key=lambda x: x[0])

    if not tsx_data:
        raise ValueError(
            f"{tsx_dir} に tsx_{{n}}us 形式のディレクトリがありません"
        )

    # --------------------------------------------------
    # 各手法の実行時間の平均値を計算
    # --------------------------------------------------
    means = []
    labels = []
    granted_means = []

    # デフォルト
    default_mean = sum(default_values) / len(default_values)

    means.append(default_mean)
    labels.append("デフォルト")

    # 動的ポリシ変更
    dynamic_mean = sum(dynamic_values) / len(dynamic_values)

    means.append(dynamic_mean)
    labels.append("動的ポリシ変更")

    # Time Slice Extension
    for n, elapsed_values, granted_values in tsx_data:
        elapsed_mean = sum(elapsed_values) / len(elapsed_values)
        granted_mean = sum(granted_values) / len(granted_values)

        means.append(elapsed_mean)
        labels.append(f"TSX\n{n} us")
        granted_means.append(granted_mean)

    # --------------------------------------------------
    # グラフ作成
    # --------------------------------------------------
    fig, ax1 = plt.subplots(figsize=(10, 6))

    x = list(range(len(labels)))

    # 実行時間の棒グラフ
    bars = ax1.bar(
        x,
        means
    )

    ax1.set_xlabel("適用手法")
    ax1.set_ylabel("実行時間 (s)")
    ax1.set_title(
        "SOEM プログラムにおける I/O サイクル完了までの実経過時間と "
        "time slice extension の実行時間延長回数"
    )

    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)

    ax1.grid(
        axis="y",
        linestyle=":",
        alpha=0.5
    )

    # 各棒の上に実行時間を表示
    for bar, mean in zip(bars, means):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{mean:.3f}",
            ha="center",
            va="bottom"
        )

    # --------------------------------------------------
    # granted を右側の Y 軸に点で表示
    # --------------------------------------------------
    ax2 = ax1.twinx()

    # デフォルト・動的ポリシ変更には granted はないので、
    # TSX の位置は x=2 から始まる
    tsx_x = list(range(2, len(labels)))

    ax2.scatter(
        tsx_x,
        granted_means,
        marker="o",
        s=50,
        color="tab:red",
        label="TSX granted"
    )

    ax2.set_ylim(8000, 9000)

    ax2.set_ylabel("time slice extension の実行時間延長回数")

    # --------------------------------------------------
    # レイアウト・保存
    # --------------------------------------------------
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()

    print(f"グラフを出力しました: {output_file}")


if __name__ == "__main__":
    main()