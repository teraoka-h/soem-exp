#!/usr/bin/env python3

import sys
import re
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib_fontja


def read_tsx_io_cnt_log(path):
    """
    tsx_io_cnt.log から
    (サイクル数, RTT) の組を読み込む
    """
    values = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            parts = line.split(",")

            if len(parts) != 2:
                continue

            cycle = int(parts[0].strip())
            rtt = float(parts[1].strip())

            values.append((cycle, rtt))

    if not values:
        raise ValueError(
            f"TSX により延長された RTT のデータがありません: {path}"
        )

    return values


def main():
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} "
            "<tsx_dir> <output_file>"
        )
        sys.exit(1)

    tsx_dir = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

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

        tsx_io_cnt_log = path / "tsx_io_cnt.log"

        if not tsx_io_cnt_log.is_file():
            raise FileNotFoundError(
                f"tsx_io_cnt.log がありません: {tsx_io_cnt_log}"
            )

        # TSX により延長された RTT
        tsx_io_values = read_tsx_io_cnt_log(
            tsx_io_cnt_log
        )

        # 実行時間が延長された回数
        extended_count = len(tsx_io_values)

        tsx_data.append(
            (n, extended_count)
        )

    # n の小さい順に並べる
    tsx_data.sort(key=lambda x: x[0])

    if not tsx_data:
        raise ValueError(
            f"{tsx_dir} に tsx_{{n}}us 形式のディレクトリがありません"
        )

    # --------------------------------------------------
    # データを分離
    # --------------------------------------------------
    labels = [
        f"{n} us"
        for n, _ in tsx_data
    ]

    counts = [
        count
        for _, count in tsx_data
    ]

    # --------------------------------------------------
    # グラフ作成
    # --------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(
        labels,
        counts
    )

    ax.set_xlabel("time slice extension 延長時間")
    ax.set_ylabel("実行時間が延長された回数")

    # ax.set_title(
    #     "time slice extension による実行時間延長回数"
    # )

    ax.grid(
        axis="y",
        linestyle=":",
        alpha=0.5
    )

    # --------------------------------------------------
    # 各棒の上に回数を表示
    # --------------------------------------------------
    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{int(bar.get_height())}",
            ha="center",
            va="bottom"
        )

    # --------------------------------------------------
    # 保存
    # --------------------------------------------------
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()

    print(f"グラフを出力しました: {output_file}")


if __name__ == "__main__":
    main()