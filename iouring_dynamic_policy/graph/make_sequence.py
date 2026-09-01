#!/usr/bin/env python3
import sys
import os
import matplotlib.pyplot as plt

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <rtt_log_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    # 出力ファイル名作成
    base, _ = os.path.splitext(input_file)
    base = os.path.basename(base)
    output_file = f"{base}_seq.png"

    rtts = []

    # ログ読み込み
    with open(input_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rtts.append(float(line))
            except ValueError:
                continue

    if not rtts:
        print("No valid RTT data found.")
        sys.exit(1)

    # sequence index
    seq = range(len(rtts))

    # plot
    plt.figure(figsize=(10,5))
    plt.plot(seq, rtts, linewidth=1)
    # plt.scatter(seq, rtts, s=10)
    plt.xlabel("Sequence")
    plt.ylabel("RTT (us)")
    plt.title("RTT Sequence Plot")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)

    print(f"Saved: {output_file}")

if __name__ == "__main__":
    main()