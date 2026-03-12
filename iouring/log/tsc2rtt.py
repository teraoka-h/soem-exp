#!/usr/bin/env python3
import sys
import os

# ===== ユーザ設定 =====
TSC_HZ = 2_000_000_000  
# =====================

def convert_file(input_path):
    base = os.path.basename(input_path)

    if not base.startswith("tsc_"):
        raise ValueError("input filename must start with 'tsc_'")

    output_name = "rtt_" + base[len("tsc_"):]
    output_path = os.path.join(os.path.dirname(input_path), output_name)

    with open(input_path, "r") as fin, open(output_path, "w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue

            tsc_diff = float(line)

            # 秒
            sec = tsc_diff / TSC_HZ

            # µs
            rtt_us = sec * 1e6

            fout.write(f"{rtt_us:.2f}\n")

    print(f"output: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <tsc_log_file>")
        sys.exit(1)

    convert_file(sys.argv[1])