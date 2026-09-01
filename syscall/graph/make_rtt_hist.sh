#! /usr/bin/zsh

file=$1
if [ ! -f $file ]; then
  echo "File $file does not exist."
  exit 1
fi

base=${file%.*}
over=$base.over

touch $over
python3 ./make_rtt_hist.py $file > $over
