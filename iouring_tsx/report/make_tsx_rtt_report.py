#!/usr/bin/env python3

from pathlib import Path
import numpy as np
import sys

LOG_ROOT = Path("../log")

TSX_VALUES = range(5, 51)
COMP_VALUES = [0, 4, 8, 16, 24]


def load_log(path: Path) -> np.ndarray:
    return np.loadtxt(path, dtype=float)


def calc_metrics(data):
    return {
        "mean": np.mean(data),
        "std": np.std(data),
        "max": np.max(data),
        "p99": np.percentile(data, 99),
        "p999": np.percentile(data, 99.9),
    }


def main():

    # 第１引数を LOG_ROOT に設定する
    LOG_ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../log")

    # LOG_ROOT の末尾要素の yyyymmdd を report のディレクトリ名として使用
    report_dir = LOG_ROOT.name
    print(f"report_dir: {report_dir}")

    # tsx_0us のログ id を引数から受け取る
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <tsx_0us_log_id>")
        sys.exit(1)

    # tsx_0us のログ id を指定する
    tsx_0us_log_id = sys.argv[2]

    metrics_table = {
        "mean": [],
        "std": [],
        "max": [],
        "p99": [],
        "p999": [],
    }

    # TSX_VALUES に，tsx_0us も加える
    # tsx_0us の結果は，tsx_0us/rtt_iouring_c*_n.log にある 
    tsx_values = [0] + list(TSX_VALUES)

    for tsx in tsx_values:

        row = {
            "mean": [tsx],
            "std": [tsx],
            "max": [tsx],
            "p99": [tsx],
            "p999": [tsx],
        }

        for comp in COMP_VALUES:

            # tsx_0us の場合は，tsx_0us/rtt_iouring_c*_{n}.log を使う
            if tsx == 0:
                log_file = (
                    LOG_ROOT
                    / "tsx_0us"
                    / f"rtt_iouring_c{comp}_{tsx_0us_log_id}.log"
                )
            else:
                log_file = (
                    LOG_ROOT
                    / f"tsx_{tsx}us"
                    / f"rtt_iouring_c{comp}.log"
                )

            data = load_log(log_file)
            stats = calc_metrics(data)

            for metric in metrics_table:
                row[metric].append(stats[metric])

        for metric in metrics_table:
            metrics_table[metric].append(row[metric])

    header = (
        "tsx_us "
        + " ".join(f"c{c}" for c in COMP_VALUES)
    )

    for metric, rows in metrics_table.items():

        # tsx_0us のログ id のディレクトリを作成する
        output_dir = Path(f"{report_dir}/tsx_0us_id{tsx_0us_log_id}")
        # 階層が存在しない場合は１つづつ作成する
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{metric}_tsx_0us_id{tsx_0us_log_id}.log"

        with open(output_file, "w") as f:
            f.write(header + "\n")

            for row in rows:
                f.write(
                    " ".join(f"{v:.6f}" for v in row)
                    + "\n"
                )

        print(f"generated: {output_file}")


if __name__ == "__main__":
    main()