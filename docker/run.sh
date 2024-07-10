#!/bin/bash

echo Starting Passive Data Kit server...
source /app/venv/bin/activate

cd /app/live_site

echo Initializing database and static resources...

python3 manage.py migrate
python3 manage.py collectstatic --no-input
python3 manage.py loaddata /app/users.json
python3 manage.py loaddata /app/pdk-test-data.json

echo Validating installation...

python3 manage.py test
python3 manage.py check

pylint passive_data_kit
bandit -r .

echo Installing and starting gunicorn...

pip install gunicorn

/usr/local/bin/supercronic /app/crontab &

gunicorn live_site.wsgi --log-file - --bind="0.0.0.0:$WEB_PORT"