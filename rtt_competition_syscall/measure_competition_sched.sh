#!/usr/bin/zsh

COMPETITION_PROCESS=./competition_process
SOEM_PROCESS=./soem_syscall

SOEM_COMM_COUNT=$1
SOEM_LOG_PREFIX=$2
COMPETITION_COUNT=$3

FIFO_PRIORITY=1

echo "--- SOEM: loop-cnt=$SOEM_COMM_COUNT, prefix=$SOEM_LOG_PREFIX"
echo "--- COMPETITION: process: $COMPETITION_COUNT"

# 指定個数だけ競合プロセスを起動
for i in {1..$COMPETITION_COUNT} 
do 
  systemd-run --scope ${COMPETITION_PROCESS} &
  pid=$!
  renice -n 0 -p "$pid"
  nice=
  # ${COMPETITION_PROCESS} &
done

# soem processを SCHED_FIFO の優先度1で実行 
chrt -f 1 ${SOEM_PROCESS} $SOEM_COMM_COUNT $SOEM_LOG_PREFIX

# 競合プロセスを全て終了
sudo pkill -KILL -f ${COMPETITION_PROCESS}

echo "--- Measurement completed."
