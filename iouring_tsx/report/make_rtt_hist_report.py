#!/usr/bin/env python3

import sys
from pathlib import Path
from collections import Counter


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <log_file>")
        sys.exit(1)

    log_file = Path(sys.argv[1])

    if not log_file.is_file():
        print(f"Error: file not found: {log_file}")
        sys.exit(1)

    # 出力ファイル名
    # 例: rtt.log -> rtt_hist.report
    output_file = Path.cwd() / f"{log_file.stem}_hist.report"

    histogram = Counter()
    total = 0

    # ログを読み込む
    with log_file.open("r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # 空行は無視
            if not line:
                continue

            try:
                rtt = float(line)
            except ValueError:
                print(
                    f"Warning: line {line_num} is not a valid RTT: {line}",
                    file=sys.stderr
                )
                continue

            # 1 us 刻みで集計
            # 例:
            # 50.2 -> 50
            # 50.9 -> 50
            # 51.0 -> 51
            rtt_us = int(rtt)

            histogram[rtt_us] += 1
            total += 1

    # レポート出力
    with output_file.open("w") as f:
        f.write("# RTT(us) Frequency\n")

        if histogram:
            min_rtt = min(histogram)
            max_rtt = max(histogram)

            # 0 us からではなく、実際の最小値～最大値を1 us刻みで出力
            for rtt_us in range(min_rtt, max_rtt + 1):
                count = histogram.get(rtt_us, 0)
                f.write(f"{rtt_us} {count}\n")

    print(f"Input : {log_file}")
    print(f"Output: {output_file}")
    print(f"Samples: {total}")


if __name__ == "__main__":
    main()
