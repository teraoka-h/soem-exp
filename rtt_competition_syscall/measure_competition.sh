#!/usr/bin/zsh

COMPETITION_PROCESS=./competition_process
SOEM_PROCESS=./soem_syscall

SOEM_COMM_COUNT=$1
SOEM_LOG_PREFIX=$2
COMPETITION_COUNT=$3
TRACE_FILE=tracecmd/trace_${SOEM_LOG_PREFIX}.dat

echo "--- SOEM: loop-cnt=$SOEM_COMM_COUNT, prefix=$SOEM_LOG_PREFIX"
echo "--- COMPETITION: process: $COMPETITION_COUNT"

# 指定個数だけ競合プロセスを起動
if [ ${COMPETITION_COUNT} -ne 0 ]; then
for i in {1..$COMPETITION_COUNT} 
do 
  systemd-run --scope ${COMPETITION_PROCESS} &
  pid=$!
  renice -n 0 -p "$pid"
  # ${COMPETITION_PROCESS} &
done
fi

# soem processを起動
trace-cmd record -o ${TRACE_FILE} -e sched_switch -e sys_enter_ppoll -e sys_exit_ppoll -- nice -n 0 ${SOEM_PROCESS} $SOEM_COMM_COUNT $SOEM_LOG_PREFIX
# nice -n 0 ${SOEM_PROCESS} ${SOEM_COMM_COUNT} ${SOEM_LOG_PREFIX}

# 競合プロセスを全て終了
sudo pkill -KILL -f ${COMPETITION_PROCESS}

echo "--- Measurement completed."
