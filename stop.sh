#!/usr/bin/env bash

if [[ -f log/gunicorn.pid ]];then
    pid=`cat log/gunicorn.pid`
    echo "program pid: $pid"
    kill "$pid"
    sleep 5
    echo "kill pid $pid done!"
else
    echo "server not start!"
fi