#!/usr/bin/env python3

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib_fontja

def main():

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <report.log>")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    script_dir = Path(__file__).resolve().parent
    output_file = script_dir / f"heatmap/{input_file.stem}_heatmap.png"

    # ヘッダ読み込み
    with open(input_file) as f:
        header = f.readline().split()

    competition_values = [int(c[1:]) for c in header[1:]]

    # データ読み込み
    data = np.loadtxt(input_file, skiprows=1)

    tsx_values = data[:, 0].astype(int)
    # tsx=0us の場合は，"拡張なし" のラベルに変更
    tsx_values = ["拡張\nなし" if x == 0 else f"{x}" for x in tsx_values]

    # Z: (競合 × TSX)
    Z = data[:, 1:].T   # shape = (comp, tsx)

    # ===== グリッド作成（セル表示用）=====
    x = np.arange(len(tsx_values) + 1)
    y = np.arange(len(competition_values) + 1)

    fig, ax = plt.subplots(figsize=(10, 4))

    # 上限，下限の log10 を指定
    vmin, vmax = 1, 4.1


    # ===== ヒートマップ（logなし）=====
    mesh = ax.pcolormesh(
        x,
        y,
        np.log10(Z),
        shading="auto",
        cmap="viridis",
        vmin=vmin,
        vmax=vmax
    )

    cbar = plt.colorbar(mesh, ax=ax)

    ticks = [np.log10(10), np.log10(50), np.log10(100), np.log10(500), np.log10(1000), np.log10(5000), np.log10(10000)]
    cbar.set_ticks(ticks)

    cbar.set_ticklabels([
        r"10",
        r"50",
        r"100",
        r"500",
        r"$1000$",
        r"$5000$",
        r"$10000$"
    ])

    # ===== 軸ラベル調整（セル中央）=====
    ax.set_xticks(np.arange(len(tsx_values)) + 0.5)
    ax.set_xticklabels(tsx_values)
    ax.tick_params(axis='x', labelsize=8)

    ax.set_yticks(np.arange(len(competition_values)) + 0.5)
    ax.set_yticklabels(competition_values)

    ax.set_xlabel("time slice extension の拡張時間 (us)")
    ax.set_ylabel("競合プロセス数")

    # ax.set_title("io_uring 実装における，競合プロセス数と time slice extension の拡張時間による RTT の最大値 ヒートマップ")

    # ===== カラーバー =====
    # cbar = plt.colorbar(mesh, ax=ax)
    cbar.set_label("RTT (us) (log scale)")

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)

    print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()
