import sys
from collections import defaultdict

BIN_SIZE = 100.0  # us

def load_bins(filename):
    bins = defaultdict(list)

    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            rtt = float(line)
            bin_index = int(rtt // BIN_SIZE)
            bins[bin_index].append(rtt)

    return bins


def print_bins(bins):
    results = []

    for bin_index in sorted(bins):
        values = bins[bin_index]

        start = bin_index * BIN_SIZE
        end = start + BIN_SIZE
        count = len(values)
        avg = sum(values) / count

        results.append((start, end, count, avg))

    return results


def main(filename):

    bins = load_bins(filename)
    results = print_bins(bins)

    print("=== ALL RANGES ===")
    print("range(us),count,avg_rtt(us)")

    for start, end, count, avg in results:
        print(f"[{start:.0f}-{end:.0f}(us)] ,count: {count}, ave: {avg:.2f}")

    print()
    print("=== COUNT >= 10 ===")
    print("range(us),count,avg_rtt(us)")

    for start, end, count, avg in results:
        if count >= 10:
            print(f"[{start:.0f}-{end:.0f}(us)],count: {count}, ave: {avg:.2f}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python rtt_hist.py logfile")
        sys.exit(1)

    main(sys.argv[1])