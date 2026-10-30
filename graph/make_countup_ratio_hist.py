#!/usr/bin/env python3

import sys
import re
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib_fontja


def read_countup_log(path):
    """countup.log から整数値を読み込む"""
    with open(path, "r") as f:
        values = [int(line.strip()) for line in f if line.strip()]

    if not values:
        raise ValueError(f"ログファイルが空です: {path}")

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
    default_log = default_dir / "countup.log"
    default_values = read_countup_log(default_log)

    # --------------------------------------------------
    # 動的ポリシ変更
    # --------------------------------------------------
    dynamic_log = dynamic_dir / "countup.log"
    dynamic_values = read_countup_log(dynamic_log)

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
        log_path = path / "countup.log"

        if not log_path.is_file():
            raise FileNotFoundError(
                f"countup.log がありません: {log_path}"
            )

        values = read_countup_log(log_path)
        tsx_data.append((n, values))

    # n の小さい順に並べる
    tsx_data.sort(key=lambda x: x[0])

    if not tsx_data:
        raise ValueError(
            f"{tsx_dir} に tsx_{{n}}us 形式のディレクトリがありません"
        )

    # --------------------------------------------------
    # 各測定値について比を計算
    #
    #   動的ポリシ変更 / デフォルト
    #   TSX / デフォルト
    #
    # --------------------------------------------------
    ratios = []
    labels = []

    # 動的ポリシ変更
    ratios.append(
        [dynamic / default
         for default, dynamic in zip(default_values, dynamic_values)]
    )
    labels.append("動的ポリシ変更")

    # Time Slice Extension
    for n, values in tsx_data:
        ratios.append(
            [tsx / default
             for default, tsx in zip(default_values, values)]
        )
        labels.append(f"TSX\n{n} us")

    # --------------------------------------------------
    # グラフ作成
    # --------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))

    # 各手法について比の平均値を棒グラフとして表示
    means = [sum(ratio) / len(ratio) for ratio in ratios]

    bars = ax.bar(
        labels,
        means
    )

    # 各棒の上に比の値を表示
    for bar, mean in zip(bars, means):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() - 0.05,
            f"{mean:.3f}",
            ha="center",
            va="bottom"
        )

    ax.axhline(
        y=1.0,
        linestyle="--",
        linewidth=1
    )

    ax.set_xlabel("適用手法")
    ax.set_ylabel("カウントアップ比 (適用手法 / デフォルト)")
    ax.set_title("競合プロセスにおけるカウントアップ数のデフォルト実装との比")

    ax.grid(
        axis="y",
        linestyle=":",
        alpha=0.5
    )

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()

    print(f"グラフを出力しました: {output_file}")


if __name__ == "__main__":
    main()