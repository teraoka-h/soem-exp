#!/usr/bin/env python3

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def main():

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <report.log>")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    if not input_file.exists():
        print(f"File not found: {input_file}")
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    output_file = script_dir / f"{input_file.stem}_3dhist.png"

    # ヘッダ
    with open(input_file) as f:
        header = f.readline().split()

    competition_values = [int(c[1:]) for c in header[1:]]

    # データ
    data = np.loadtxt(input_file, skiprows=1)
    tsx_values = data[:, 0]

    xpos, ypos, zpos = [], [], []
    dx, dy, dz = [], [], []

    for i, tsx in enumerate(tsx_values):
        for j in range(len(competition_values)):

            xpos.append(tsx)
            ypos.append(j)

            # ★重要：barの底は0でOK
            zpos.append(0)

            dx.append(0.8)
            dy.append(0.6)

            # ★生値のまま
            dz.append(data[i, j + 1])

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    ax.bar3d(
        xpos, ypos, zpos,
        dx, dy, dz,
        shade=True
    )

    # =========================
    # Z軸を log 表示に“見せる”
    # =========================

    ax.set_zscale("linear")

    ax.set_zticks([1, 10, 100, 1000])
    ax.set_zticklabels(["1", "10", "100", "1000"])

    ax.set_zlim(1, 300) # 1us ~ 1000us

    ax.set_zlabel(f"{input_file.stem} (log scale)")

    # ax.zaxis.set_major_locator(
    #     mticker.LogLocator(base=10)
    # )

    # ax.zaxis.set_major_formatter(
    #     mticker.LogFormatter(base=10)
    # )

    # =========================
    # 軸設定
    # =========================

    ax.set_xlabel("Time Slice Extension (us)")
    ax.set_ylabel("Competition Processes")

    ax.set_xticks(tsx_values[::5])

    ax.set_yticks(range(len(competition_values)))
    ax.set_yticklabels(competition_values)

    ax.view_init(elev=25, azim=-60)

    # 3Dはtight_layout禁止
    plt.subplots_adjust(
        left=0.1,
        right=0.95,
        top=0.95,
        bottom=0.1
    )

    plt.savefig(output_file, dpi=300)
    print(f"Saved: {output_file}")


if __name__ == "__main__":
    main()