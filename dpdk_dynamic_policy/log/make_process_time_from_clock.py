#!/usr/bin/env python3
import sys
import os

# ==== CPUクロック周波数を定義（例: 3.0GHz）====
CPU_FREQ_HZ = 1.8e9  # 1.8 GHz

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <clock_*.log>")
        sys.exit(1)

    infile = sys.argv[1]

    if not os.path.isfile(infile):
        print(f"Error: file '{infile}' not found.")
        sys.exit(1)

    # 入力ファイル名が clock_*.log の場合 → 出力は pt_*.log
    dirname, filename = os.path.split(infile)
    if filename.startswith("clock_") and filename.endswith(".log"):
        outfile = os.path.join(dirname, "pt_" + filename[len("clock_"):])
    else:
        print("Error: input file must be named like 'clock_*.log'")
        sys.exit(1)

    with open(infile, "r") as fin, open(outfile, "w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                send_clk, poll_recv_clk, recv_clk, total_clk = map(int, line.split(","))
                # クロック数 → 秒 → マイクロ秒
                send_us = (send_clk / CPU_FREQ_HZ) * 1e6
                poll_recv_us = (poll_recv_clk / CPU_FREQ_HZ) * 1e6
                recv_us = (recv_clk / CPU_FREQ_HZ) * 1e6
                total_us = (total_clk / CPU_FREQ_HZ) * 1e6
                
                fout.write(f"{send_us:.6f},{poll_recv_us:.6f},{recv_us:.6f},{total_us:.6f}\n")
            except ValueError:
                # 数字でない行（ヘッダなど）はそのまま出力
                fout.write(line + "\n")

    print(f"Converted log written to: {outfile}")

if __name__ == "__main__":
    main()
