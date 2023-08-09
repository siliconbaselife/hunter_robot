#!/usr/bin/env bash

if [[ ! -d log ]];then
    mkdir log
fi

./stop.sh

echo "will start server"
gunicorn -c config/gunicorn_config.py web.serv_main_v2:app
echo "start server done!"

