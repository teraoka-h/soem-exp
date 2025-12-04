#!/usr/bin/zsh

COMPETITION_PROCESS=./competition_process
SOEM_PROCESS=./soem_iouring

SOEM_COMM_COUNT=$1
SOEM_LOG_PREFIX=$2
COMPETITION_COUNT=$3

TRACE_FILE=tracecmd/trace_$SOEM_LOG_PREFIX.dat

echo "SOEM: loop-cnt=$SOEM_COMM_COUNT, prefix=$SOEM_LOG_PREFIX"
echo "COMPETITION: process: $COMPETITION_COUNT"

# 指定回数だけ競合プロセスを起動
for i in {1..$COMPETITION_COUNT} 
do 
  systemd-run --scope ${COMPETITION_PROCESS} &
  pid=$!
  renice -n 0 -p "$pid"
done

printf "[INFO] trace event: ${EVENT_LABEL}\n"

# soem process
trace-cmd record -o ${TRACE_FILE} -e sched_switch -e io_uring_complete -e io_uring_submit_req -- ${SOEM_PROCESS} $SOEM_COMM_COUNT $SOEM_LOG_PREFIX 

