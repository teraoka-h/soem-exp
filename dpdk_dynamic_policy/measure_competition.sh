#!/usr/bin/zsh

COMPETITION_PROCESS=./competition_process
SOEM_PROCESS=./soem_dpdk

# SOEM_COMM_COUNT=$1
# SOEM_LOG_PREFIX=$2
# COMPETITION_COUNT=$1
DAY=$1
ID=$2

# 競合プロセス数リスト
COMPETITION_PROCESSES=(0 4 8 16 24)

# ログファイル用ディレクトリを作成
log_dir="log/${DAY}"
mkdir -p $log_dir

for num_processes in "${COMPETITION_PROCESSES[@]}"
do
  # 指定個数だけ競合プロセスを起動
    if [ $num_processes -ne 0 ]; then
      for i in $(seq 1 $num_processes)
      do 
        # systemd-run --scope ${COMPETITION_PROCESS} &
        ${COMPETITION_PROCESS} &
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
      if [ $running -eq $num_processes ]; then
        echo "競合プロセス数 OK: ${running}/${num_processes}"
        break
      fi

      if [ "$retry" -ge "$max_retry" ]; then
        echo "ERROR: 想定数の競合プロセスが起動していません (実際: ${running}, 想定: ${num_processes})"
        exit 1
      fi

      echo "競合プロセスを待機中… (現在: ${running}/${num_processes})"
      sleep 0.2
      retry=$((retry+1))
    done

  # soem processを起動
  nice -n 0 ${SOEM_PROCESS} ${num_processes} ${DAY} ${ID}

  # 競合プロセスを全て終了
  sudo pkill -KILL -f ${COMPETITION_PROCESS}

  echo "--- Measurement completed."

done


# # 指定個数だけ競合プロセスを起動
# for i in {1..$COMPETITION_COUNT} 
# do 
#   systemd-run --scope ${COMPETITION_PROCESS} &
#   pid=$!
#   renice -n 0 -p "$pid"
#   nice=
#   # ${COMPETITION_PROCESS} &
# done


