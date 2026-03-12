#!/usr/bin/zsh

COMPETITION_PROCESS=./competition_process
SOEM_PROCESS=./soem_dpdk

# SOEM_COMM_COUNT=$1
# SOEM_LOG_PREFIX=$2
COMPETITION_COUNT=$1

echo "--- SOEM: loop-cnt=$SOEM_COMM_COUNT, prefix=$SOEM_LOG_PREFIX"
echo "--- COMPETITION: process: $COMPETITION_COUNT"

# # 指定個数だけ競合プロセスを起動
# for i in {1..$COMPETITION_COUNT} 
# do 
#   systemd-run --scope ${COMPETITION_PROCESS} &
#   pid=$!
#   renice -n 0 -p "$pid"
#   nice=
#   # ${COMPETITION_PROCESS} &
# done

# 指定個数だけ競合プロセスを起動
  if [ $COMPETITION_COUNT -ne 0 ]; then
    for i in $(seq 1 $COMPETITION_COUNT)
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
    if [ $running -eq $COMPETITION_COUNT ]; then
      echo "競合プロセス数 OK: ${running}/${COMPETITION_COUNT}"
      break
    fi

    if [ "$retry" -ge "$max_retry" ]; then
      echo "ERROR: 想定数の競合プロセスが起動していません (実際: ${running}, 想定: ${COMPETITION_COUNT})"
      exit 1
    fi

    echo "競合プロセスを待機中… (現在: ${running}/${COMPETITION_COUNT})"
    sleep 0.2
    retry=$((retry+1))
  done

# soem processを起動
sudo nice -n 0 ${SOEM_PROCESS} ${COMPETITION_COUNT}

# 競合プロセスを全て終了
sudo pkill -KILL -f ${COMPETITION_PROCESS}

echo "--- Measurement completed."
