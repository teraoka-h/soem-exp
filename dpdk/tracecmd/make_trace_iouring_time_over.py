import sys
import re
import os

def parse_line(line):
    parts = line.strip().split(maxsplit=4)
    if len(parts) < 4:
        return None
    process, cpu, timestamp, event = parts[:4]
    description = parts[4] if len(parts) > 4 else ""
    return {
        "process": process,
        "cpu": cpu.strip("[]"),
        "timestamp": float(timestamp.strip("[]:")),
        "event": event.strip(":"),
        "description": description,
    }

def analyze_log(filepath, threshold_us):
    send_start_ts = None
    proc_name = None

    with open(filepath) as f:
        for line in f:
            entry = parse_line(line)
            if not entry:
                continue

            ts = entry["timestamp"]
            event = entry["event"]
            desc = entry["description"]

            # --- SEND submit 検出 ---
            if event == "io_uring_submit_req" and "opcode SEND" in desc:
            # if event == "sched_switch" and "==> rtt_competition" in desc:
                send_start_ts = ts
                proc_name = entry["process"]

            # --- RECV complete 検出 ---
            if event == "io_uring_complete" and "result 60" in desc:
                if send_start_ts is not None:
                    delta_us = (ts - send_start_ts) * 1_000_000
                    if delta_us > threshold_us:
                        print(f"[{proc_name}] delay={delta_us:.1f} us (> {threshold_us}) at {send_start_ts:.6f}")
                    # 一度ペアリングしたらリセット
                    send_start_ts = None
                    proc_name = None

def main():
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <logfile> <threshold_us>")
        sys.exit(1)

    logfile = sys.argv[1]
    threshold_us = float(sys.argv[2])
    analyze_log(logfile, threshold_us)

if __name__ == "__main__":
    main()
