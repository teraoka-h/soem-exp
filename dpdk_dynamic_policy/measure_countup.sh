COUNTUP_PROCESS=./countup_process
SOEM_PROCESS=./soem_dpdk

DAY=$1

# DAY のディレクトリを log ディレクトリ内に作成
mkdir -p log/${DAY}

# カウントアッププロセスを起動してPIDを取得 
# 1. カウントアッププロセスを起動 (core 0 に固定)
taskset -c 0 ${COUNTUP_PROCESS} ${DAY} &

# 2. カウントアッププロセスのPIDを取得し，nice値を設定
COUNTUP_PID=$!
renice -n 0 -p "$COUNTUP_PID"
echo "--- COUNTUP: process PID: $COUNTUP_PID"

# SOEMプロセスを起動 (core 0 に固定)
taskset -c 0 nice -n 0 ${SOEM_PROCESS} ${DAY} ${COUNTUP_PID}

# カウントアッププロセスを終了
pkill -KILL -P $COUNTUP_PID

echo "--- COUNTUP: process PID: $COUNTUP_PID terminated"
