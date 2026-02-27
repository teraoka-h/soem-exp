import re
import sys
import csv

# ================================================
# 設定
# ================================================
TARGET_COMM = "soem_exp"   # 対象プロセス名
BEGIN_MARK = "MEASURE_BEGIN"
END_MARK   = "MEASURE_END"

# ================================================
# 正規表現
# ================================================
re_marker = re.compile(r"tracing_mark_write:\s+(\w+)")
re_sched = re.compile(
    r"sched_switch:\s+(.+?):(\d+)\s+\[\d+\]\s+\S+\s+==>\s+(.+?):(\d+)"
)
re_ts = re.compile(r"\s+(\d+\.\d+):")

# ================================================
# trace-cmd レポート解析
# ================================================
def analyze(path):
    in_measure = False
    last_ts = None
    running = False  # soem_exp が on-CPU か？
    run_time = 0.0
    off_time = 0.0

    start_ts = None
    end_ts = None

    with open(path) as f:
        for line in f:
            # タイムスタンプ
            m_ts = re_ts.search(line)
            if not m_ts:
                continue
            ts = float(m_ts.group(1))

            # マーカー
            m = re_marker.search(line)
            if m:
                mark = m.group(1)

                if mark == BEGIN_MARK:
                    in_measure = True
                    start_ts = ts
                    last_ts = ts
                    running = False  # 開始時点では実行していないとみなす
                    continue

                if mark == END_MARK and in_measure:
                    end_ts = ts
                    if last_ts is not None:
                        dt = ts - last_ts
                        if running:
                            run_time += dt
                        else:
                            off_time += dt
                    in_measure = False
                    continue

            if not in_measure:
                continue

            # sched_switch 処理
            s = re_sched.search(line)
            if not s:
                continue

            prev_comm, prev_pid, next_comm, next_pid = s.groups()

            # 前回からの時間差
            if last_ts is not None:
                dt = ts - last_ts
                if running:
                    run_time += dt
                else:
                    off_time += dt

            # 状態遷移
            if next_comm == TARGET_COMM:
                running = True
            if prev_comm == TARGET_COMM:
                running = False

            last_ts = ts

    total = (end_ts - start_ts) if (start_ts and end_ts) else None
    return run_time, off_time, total


# ================================================
# メイン
# ================================================
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python analyze.py trace_report.txt output.csv")
        exit()

    in_path = sys.argv[1]
    out_csv = sys.argv[2]

    run, off, total = analyze(in_path)

    with open(out_csv, "w", newline="") as cf:
        w = csv.writer(cf)
        w.writerow(["item", "value"])
        w.writerow(["run_time_sec", run])
        w.writerow(["off_time_sec", off])
        w.writerow(["total_interval_sec", total])
        w.writerow(["run_ratio", run / total if total else 0])
        w.writerow(["off_ratio", off / total if total else 0])

    print("CSV 出力完了:", out_csv)
    print(f"RUN: {run*1e6:.1f} us")
    print(f"OFF: {off*1e6:.1f} us")
    print(f"TOTAL: {total*1e6:.1f} us")
    print(f"RUN ratio: {run/total*100:.2f}%")
    print(f"OFF ratio: {off/total*100:.2f}%")
