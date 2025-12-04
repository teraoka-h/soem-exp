#!/usr/bin/zsh

COMPETITION_PROCESS=./competition_process
SOEM_PROCESS=./soem_exp

SOEM_COMM_COUNT=$1
SOEM_LOG_FILE=$2
COMPETITION_COUNT=(0 4 8 16 24)
# COMPETITION_COUNT=(0)

# ログファイル作成
touch ${SOEM_LOG_FILE}
echo "# 競合プロセス数,RTT合計(us),RTT平均(us),less 500 us RTT平均(us),総処理時間(us),非通信時間(us)" >> ${SOEM_LOG_FILE}

for COUNT in ${COMPETITION_COUNT[@]}
do
  echo "--- Measurement start: competition process count = ${COUNT} ---"

  TRACE_FILE=tracecmd/trace_${SOEM_LOG_FILE}_c${COUNT}.dat

  # 指定個数だけ競合プロセスを起動
  if [ $COUNT -ne 0 ]; then
    for i in $(seq 1 $COUNT)
    do 
      systemd-run --scope ${COMPETITION_PROCESS} &
      pid=$!
      renice -n 0 -p "$pid"
    done
  fi

  # PROC_REAL_PATH=$(readlink -f ${COMPETITION_PROCESS})

  retry=0
  max_retry=10
  while true
  do
    running=$(pgrep -f "${COMPETITION_PROCESS}" | wc -l)
    echo "競合プロセス実行数: ${running}"
    if [ $running -eq $COUNT ]; then
      echo "競合プロセス数 OK: ${running}/${COUNT}"
      break
    fi

    if [ "$retry" -ge "$max_retry" ]; then
      echo "ERROR: 想定数の競合プロセスが起動していません (実際: ${running}, 想定: ${COUNT})"
      exit 1
    fi

    echo "競合プロセスを待機中… (現在: ${running}/${COUNT})"
    sleep 0.2
    retry=$((retry+1))
  done

  # soem processを起動
  # soem プログラムもログファイルに情報を記録する
  # sudo trace-cmd -o ${TRACE_FILE} -e sched_switch -- nice -n 0 ${SOEM_PROCESS} ${SOEM_COMM_COUNT} ${SOEM_LOG_FILE} ${COUNT}
  # nice -n 0 ${SOEM_PROCESS} ${SOEM_COMM_COUNT} ${SOEM_LOG_FILE} ${COUNT}
  sudo chrt -f 1 ${SOEM_PROCESS} ${SOEM_COMM_COUNT} ${SOEM_LOG_FILE} ${COUNT}

  # 競合プロセスを全て終了
  sudo pkill -KILL -f ${COMPETITION_PROCESS}
  echo "--- Measurement completed: competition process count = ${COUNT} ---"
done

# echo "--- SOEM: loop-cnt=$SOEM_COMM_COUNT, prefix=$SOEM_LOG_PREFIX"
# echo "--- COMPETITION: process: $COMPETITION_COUNT"

# # 指定個数だけ競合プロセスを起動
# for i in {1..$COMPETITION_COUNT} 
# do 
#   systemd-run --scope ${COMPETITION_PROCESS} &
#   pid=$!
#   renice -n 0 -p "$pid"
#   nice=
#   # ${COMPETITION_PROCESS} &
# done

# # soem processを起動
# nice -n 0 ${SOEM_PROCESS} $SOEM_COMM_COUNT $SOEM_LOG_PREFIX

# # 競合プロセスを全て終了
# sudo pkill -KILL -f ${COMPETITION_PROCESS}

# echo "--- Measurement completed."
