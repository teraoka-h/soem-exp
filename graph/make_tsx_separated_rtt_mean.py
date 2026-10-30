#!/usr/bin/env python3

import sys
import re
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib_fontja
import numpy as np


def read_rtt_log(path):
    """rtt_dpdk_countup.log から RTT を読み込む"""
    values = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            values.append(float(line))

    if not values:
        raise ValueError(f"RTT のデータがありません: {path}")

    return values


def read_tsx_io_cnt_log(path):
    """
    tsx_io_cnt.log から
    (サイクル数, RTT) の組を読み込む
    """
    values = []
    cycles = set()

    with open(path, "r") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            parts = line.split(",")

            if len(parts) != 2:
                continue

            cycle = int(parts[0].strip())
            rtt = float(parts[1].strip())

            if cycle in cycles:
                raise ValueError(
                    f"cycle {cycle} が重複しています: "
                    f"{path}, {line_number} 行目"
                )

            cycles.add(cycle)
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

        rtt_log = path / "rtt_dpdk_countup.log"
        tsx_io_cnt_log = path / "tsx_io_cnt.log"

        if not rtt_log.is_file():
            raise FileNotFoundError(
                f"rtt_dpdk_countup.log がありません: {rtt_log}"
            )

        if not tsx_io_cnt_log.is_file():
            raise FileNotFoundError(
                f"tsx_io_cnt.log がありません: {tsx_io_cnt_log}"
            )

        # 全 RTT
        rtt_values = read_rtt_log(rtt_log)

        # TSX により延長された RTT
        tsx_io_values = read_tsx_io_cnt_log(tsx_io_cnt_log)

        tsx_data.append(
            (n, rtt_values, tsx_io_values)
        )

    # n の小さい順に並べる
    tsx_data.sort(key=lambda x: x[0])

    if not tsx_data:
        raise ValueError(
            f"{tsx_dir} に tsx_{{n}}us 形式のディレクトリがありません"
        )

    # --------------------------------------------------
    # 各 TSX 条件について平均 RTT を計算
    # --------------------------------------------------
    extended_means = []
    non_extended_means = []

    # 箱ひげ図用のデータ
    extended_rtts_all = []
    non_extended_rtts_all = []

    labels = []

    for n, rtt_values, tsx_io_values in tsx_data:

        # ----------------------------------------------
        # TSX により延長された RTT
        #
        # cycle は 1 始まりなので、
        # rtt_values の index は cycle - 1
        # ----------------------------------------------

        extended_rtts = []

        # 延長された RTT のサイクル番号を保持
        extended_cycles = set()

        for cycle, tsx_rtt in tsx_io_values:

            # ------------------------------------------
            # cycle の範囲チェック
            # ------------------------------------------
            if cycle < 1 or cycle > len(rtt_values):
                raise ValueError(
                    f"cycle {cycle} が RTT ログの範囲外です: "
                    f"{path}"
                )

            # ------------------------------------------
            # 同じ cycle が複数回出現していないか確認
            # ------------------------------------------
            if cycle in extended_cycles:
                raise ValueError(
                    f"cycle {cycle} が tsx_io_cnt.log に "
                    f"複数回出現しています: {path}"
                )

            extended_cycles.add(cycle)

            # ------------------------------------------
            # cycle - 1 が RTT リストの index
            # ------------------------------------------
            rtt_index = cycle - 1

            original_rtt = rtt_values[rtt_index]

            # ------------------------------------------
            # tsx_io_cnt.log の RTT と
            # rtt_dpdk_countup.log の RTT が一致するか確認
            # ------------------------------------------
            if not np.isclose(
                original_rtt,
                tsx_rtt,
                rtol=1e-9,
                atol=1e-9
            ):
                raise ValueError(
                    f"RTT が一致しません: "
                    f"cycle={cycle}, "
                    f"index={rtt_index}, "
                    f"rtt_dpdk_countup.log={original_rtt}, "
                    f"tsx_io_cnt.log={tsx_rtt}, "
                    f"path={path}"
                )

            # ------------------------------------------
            # 延長RTTには元のRTTログから取得した値を使用
            # ------------------------------------------
            extended_rtts.append(original_rtt)

        # ----------------------------------------------
        # 延長された RTT の平均
        # ----------------------------------------------
        extended_mean = (
            sum(extended_rtts) / len(extended_rtts)
        )

        # ----------------------------------------------
        # 延長されていない RTT
        #
        # extended_cycles に含まれる cycle を除外
        # cycle は 1 始まりなので enumerate(start=1)
        # ----------------------------------------------
        non_extended_rtts = [
            rtt
            for cycle, rtt in enumerate(rtt_values, start=1)
            if cycle not in extended_cycles
        ]

        if not non_extended_rtts:
            raise ValueError(
                f"延長されていない RTT がありません: "
                f"{path}"
            )

        # ----------------------------------------------
        # 延長されていない RTT の平均
        # ----------------------------------------------
        non_extended_mean = (
            sum(non_extended_rtts) / len(non_extended_rtts)
        )

        # ----------------------------------------------
        # データ分割の保証
        #
        # extended_rtts と non_extended_rtts を合わせた
        # 件数が元の RTT 件数と一致することを確認
        # ----------------------------------------------
        if (
            len(extended_rtts)
            + len(non_extended_rtts)
            != len(rtt_values)
        ):
            raise ValueError(
                f"RTT の分割に不整合があります: "
                f"全RTT={len(rtt_values)}, "
                f"延長RTT={len(extended_rtts)}, "
                f"非延長RTT={len(non_extended_rtts)}, "
                f"path={path}"
            )

        # ----------------------------------------------
        # 延長RTTと非延長RTTの cycle が重複していない
        # ことを確認
        # ----------------------------------------------
        non_extended_cycles = {
            cycle
            for cycle in range(1, len(rtt_values) + 1)
            if cycle not in extended_cycles
        }

        if extended_cycles & non_extended_cycles:
            raise ValueError(
                f"延長RTTと非延長RTTのcycleが重複しています: "
                f"{path}"
            )

        # ----------------------------------------------
        # 全 cycle がどちらか一方に属することを確認
        # ----------------------------------------------
        all_cycles = set(
            range(1, len(rtt_values) + 1)
        )

        if (
            extended_cycles | non_extended_cycles
        ) != all_cycles:
            raise ValueError(
                f"RTTのcycleが完全に分割されていません: "
                f"{path}"
            )

        # ----------------------------------------------
        # データを保存
        # ----------------------------------------------
        extended_means.append(extended_mean)
        non_extended_means.append(non_extended_mean)

        # 箱ひげ図用
        extended_rtts_all.append(extended_rtts)
        non_extended_rtts_all.append(non_extended_rtts)

        labels.append(f"{n} us")

        print(
            f"[INFO] TSX {n} us: "
            f"全RTT={len(rtt_values)}, "
            f"延長RTT={len(extended_rtts)}, "
            f"非延長RTT={len(non_extended_rtts)}"
        )

    # --------------------------------------------------
    # グラフ作成
    # --------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))

    x = list(range(len(labels)))
    width = 0.35

    # --------------------------------------------------
    # 平均値の棒グラフ
    # --------------------------------------------------

    # 延長された RTT
    bars_extended = ax.bar(
        [i - width / 2 for i in x],
        extended_means,
        width,
        label="実行時間延長時の RTT"
    )

    # 延長されていない RTT
    bars_non_extended = ax.bar(
        [i + width / 2 for i in x],
        non_extended_means,
        width,
        label="実行時間が延長されていない RTT"
    )

    # --------------------------------------------------
    # 箱ひげ図
    # --------------------------------------------------

    # 棒の中央位置
    extended_positions = [
        i - width / 2
        for i in x
    ]

    non_extended_positions = [
        i + width / 2
        for i in x
    ]

    # 延長された RTT の箱ひげ図
    ax.boxplot(
        extended_rtts_all,
        positions=extended_positions,
        widths=width * 0.45,
        patch_artist=True,
        showfliers=False,
        boxprops=dict(
            facecolor="white",
            edgecolor="black",
            alpha=0.8
        ),
        medianprops=dict(
            color="black",
            linewidth=1.5
        ),
        whiskerprops=dict(
            color="black"
        ),
        capprops=dict(
            color="black"
        )
    )

    # 延長されていない RTT の箱ひげ図
    ax.boxplot(
        non_extended_rtts_all,
        positions=non_extended_positions,
        widths=width * 0.45,
        patch_artist=True,
        showfliers=False,
        boxprops=dict(
            facecolor="white",
            edgecolor="black",
            alpha=0.8
        ),
        medianprops=dict(
            color="black",
            linewidth=1.5
        ),
        whiskerprops=dict(
            color="black"
        ),
        capprops=dict(
            color="black"
        )
    )

    # --------------------------------------------------
    # 軸・ラベル
    # --------------------------------------------------

    ax.set_xlabel("time slice extension 延長時間")
    ax.set_ylabel("RTT 平均値 (us)")

    # ax.set_title(
    #     "time slice Extension による RTT への影響"
    # )

    ax.set_xticks(x)
    ax.set_xticklabels(labels)

    ax.legend()

    ax.grid(
        axis="y",
        linestyle=":",
        alpha=0.5
    )

    # --------------------------------------------------
    # 各棒の上に平均 RTT を表示
    # --------------------------------------------------

    for bar in bars_extended:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            (bar.get_height() / 2),
            f"{bar.get_height():.3f}",
            ha="center",
            va="bottom"
        )

    for bar in bars_non_extended:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            (bar.get_height() / 2),
            f"{bar.get_height():.3f}",
            ha="center",
            va="bottom"
        )

    # --------------------------------------------------
    # 保存
    # --------------------------------------------------

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()

    # 各延長時間における，実行時間の延長回数を表示
    for n, rtt_values, tsx_io_values in tsx_data:
        print(
            f"[INFO] TSX {n} us: "
            f"延長回数={len(tsx_io_values)}"
        )
    print(f"グラフを出力しました: {output_file}")


if __name__ == "__main__":
    main()