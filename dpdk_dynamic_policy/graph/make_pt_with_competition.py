# #!/usr/bin/env python3
# import sys
# import os
# import matplotlib.pyplot as plt
# import japanize_matplotlib

# BAR_WIDTH = 0.2
# YLIM_MAX = 150  # Y軸の最大値

# def main():
#     if len(sys.argv) < 2:
#         print("Usage: python plot_log.py <logfile>")
#         sys.exit(1)

#     log_path = sys.argv[1]

#     # 出力ファイル名（拡張子を .png にする）
#     out_path = os.path.splitext(log_path)[0] + ".png"

#     comp_list = []      # 競合プロセス数（カテゴリとして使う）
#     rtt_sum_list = []   # RTT合計(us)
#     non_comm_list = []  # 非通信時間(us)

#     with open(log_path, "r") as f:
#         lines = f.readlines()

#     for line in lines:
#         if line.startswith("#"):
#             continue
        
#         line = line.strip()

#         # 空行・コメント行を無視
#         if not line or line.startswith("#"):
#             continue

#         parts = line.split(",")
#         if len(parts) < 6:
#             continue

#         comp = parts[0].strip()
#         rtt_sum = float(parts[1].strip())
#         non_comm = float(parts[5].strip())

#         comp_list.append(comp)
#         rtt_sum_list.append(rtt_sum / 1_000_000.0)     # 秒変換
#         non_comm_list.append(non_comm / 1_000_000.0)   # 秒変換

#     # プロット
#     plt.figure(figsize=(10, 6))

#     # 積み上げ棒グラフ
#     plt.bar(comp_list, rtt_sum_list, zorder=3, width=BAR_WIDTH, label="通信処理時間 (RTT合計)")
#     plt.bar(comp_list, non_comm_list, zorder=3, width=BAR_WIDTH, bottom=rtt_sum_list, label="非処理時間")

#     plt.grid(zorder=0, axis='y')

#      # Y軸の範囲設定
#     plt.ylim(0, YLIM_MAX)

#     plt.xlabel("競合プロセス数", fontsize=15)
#     plt.ylabel("処理時間 (秒)", fontsize=15)
#     plt.title("競合プロセス数による SOEM の処理時間の変化", fontsize=16)
#     plt.legend(bbox_to_anchor=(0, 1), loc='upper left')
    
#     plt.tight_layout()

#     # 保存
#     plt.savefig(out_path, dpi=150)
#     print(f"Saved graph to: {out_path}")

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
import sys
import os
import matplotlib.pyplot as plt
import japanize_matplotlib

BAR_WIDTH = 0.2
YLIM_MAX = 150  # Y軸の最大値

def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_log.py <logfile>")
        sys.exit(1)

    log_path = sys.argv[1]
    title_addition = sys.argv[2] if len(sys.argv) >= 3 else ""

    # 出力ファイル名（拡張子を .png にする）
    out_path = os.path.splitext(log_path)[0] + ".png"

    comp_list = []      # 競合プロセス数（カテゴリとして使う）
    rtt_sum_list = []   # RTT合計(秒)
    non_comm_list = []  # 非通信時間(秒)

    with open(log_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith("#"):
            continue
        
        line = line.strip()

        # 空行・コメント行を無視
        if not line or line.startswith("#"):
            continue

        parts = line.split(",")
        if len(parts) < 6:
            continue

        comp = parts[0].strip()
        rtt_sum = float(parts[1].strip())
        non_comm = float(parts[5].strip())

        comp_list.append(comp)
        rtt_sum_list.append(rtt_sum / 1_000_000.0)     # 秒変換
        non_comm_list.append(non_comm / 1_000_000.0)   # 秒変換

    # プロット
    plt.figure(figsize=(10, 6))

    # 積み上げ棒グラフ
    bar1 = plt.bar(comp_list, rtt_sum_list, 
                   zorder=3, width=BAR_WIDTH, label="通信往復時間 (RTT合計)")
    bar2 = plt.bar(comp_list, non_comm_list, 
                   zorder=3, width=BAR_WIDTH, bottom=rtt_sum_list, label="非 RTT 時間 (インターバル + 他プロセス実行時間)")

    plt.grid(zorder=0, axis='y')

    # Y軸の範囲設定
    plt.ylim(0, YLIM_MAX)
    plt.yticks(range(0, YLIM_MAX, 10))

    plt.xlabel("競合プロセス数", fontsize=15)
    plt.ylabel("処理時間 (秒)", fontsize=15)
    plt.title(f"競合プロセス数による処理時間の変化 ({title_addition})", fontsize=16)
    plt.legend(bbox_to_anchor=(0, 1), loc='upper left')
    
    plt.tight_layout()

    # # ======== 数値ラベルを追加する部分 ========
    for i, comp in enumerate(comp_list):

    #     # ----- 下段：通信処理時間 -----
    #     y_rtt = rtt_sum_list[i]
    #     plt.text(i + 0.2, y_rtt / 2,
    #              f"{y_rtt:.2f}s",
    #              ha='center', va='center', fontsize=10, color="black")

        # ----- 上段：非通信時間（積み上げ） -----
        y_total = rtt_sum_list[i] + non_comm_list[i]
        plt.text(i, y_total + 1,  # 少し上にずらす
                 f"{y_total:.2f}",
                 ha='center', va='bottom', fontsize=13, color="black")
    # # ========================================

    # 保存
    plt.savefig(out_path, dpi=150)
    print(f"Saved graph to: {out_path}")

if __name__ == "__main__":
    main()
