#!/bin/bash


#### kill all server processes
echo "Kill processes"
for KILLPID in `ps ax | grep 'meteorcam.py' | awk ' { print $1;}'`; do 
  echo "kill $KILLPID"
  kill -9 $KILLPID 2> /dev/null
done

#### start new server
echo "Start meteorcam..."
python ./meteorcam.py
echo "done"
