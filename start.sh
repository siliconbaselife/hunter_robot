#!/usr/bin/env bash

if [[ ! -d log ]];then
    mkdir log
fi

sh stop.sh

echo "will start server"
gunicorn -c config/gunicorn_config.py web.python_template_server:app
echo "start server done!"

