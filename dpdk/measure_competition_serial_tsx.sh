#!/usr/bin/zsh

# 競合プロセス数リスト
COMPETITION_PROCESSES=(0 4 8 16 24)

BASE_MEASURE_SCRIPT="./measure_competition.sh"
# 最大拡張タイムスライス時間
MAX_TSX_US=$2
# 最小拡張タイムスライス時間=5us
MIN_TSX_US=$1

# 最小拡張タイムスライス時間から最大拡張タイムスライス時間まで、1 マイクロ秒刻みで測定を行う
for tsx_us in $(seq $MIN_TSX_US $MAX_TSX_US)
do
  echo "=== Measuring with TSX US: $tsx_us ==="

  # time slice extension 時間を設定する
  TSX_NS=$((tsx_us * 1000))
  echo "Setting TSX time slice extension to ${TSX_NS} ns"
  echo $TSX_NS | sudo tee /sys/kernel/debug/rseq/slice_ext_nsec > /dev/null

  # check tsx time
  current_tsx_ns=$(cat /sys/kernel/debug/rseq/slice_ext_nsec)
  if [ "$current_tsx_ns" -ne "$TSX_NS" ]; then
    echo "ERROR: Failed to set TSX time slice extension (expected: ${TSX_NS} ns, actual: ${current_tsx_ns} ns)"
    exit 1
  fi

  # log ファイル用ディレクトリを作成
  log_dir="log/tsx_${tsx_us}us"
  mkdir -p $log_dir

  # 競合プロセス数ごとに測定を行う
  echo "TSX time slice extension set to ${current_tsx_ns} ns" 

  for num_processes in "${COMPETITION_PROCESSES[@]}"
  do
    # tsx_us と競合プロセス数を表示
    echo "=== Measuring with TSX US: $tsx_us and Competition Processes: $num_processes ==="
    $BASE_MEASURE_SCRIPT $num_processes $tsx_us
  done
done