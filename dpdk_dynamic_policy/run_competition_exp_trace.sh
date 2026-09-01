#!/usr/bin/zsh

COMPETITION_PROCESS=./competition_process
SOEM_PROCESS=./soem_exp

SOEM_COMM_COUNT=$1
SOEM_LOG=$2
COMPETITION_COUNT=$3

TRACE_FILE=tracecmd/trace_$SOEM_LOG.dat

echo "SOEM: loop-cnt=$SOEM_COMM_COUNT, prefix=$SOEM_LOG"
echo "COMPETITION: process: $COMPETITION_COUNT"

# 指定回数だけ競合プロセスを起動
if [ ${COMPETITION_COUNT} -ne 0 ]; then
  for i in {1..$COMPETITION_COUNT} 
  do 
    ${COMPETITION_PROCESS} &
    pid=$!
    renice -n 0 -p "$pid"
  done
fi

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


# printf "[INFO] trace event: ${EVENT_LABEL}\n"

# soem process
trace-cmd record -o ${TRACE_FILE} -e sched_switch -- ${SOEM_PROCESS} $SOEM_COMM_COUNT $SOEM_LOG $COMPETITION_COUNT
# 競合プロセスを停止
sudo pkill -KILL -f ${COMPETITION_PROCESS}
