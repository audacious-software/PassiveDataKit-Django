#!/bin/bash

echo Starting Passive Data Kit server...
source /venv/bin/activate

echo Initializing database...

python /app/live_site/manage.py migrate

# Validate installation

echo Validating installation...

python /app/live_site/manage.py test
python /app/live_site/manage.py check

cd /app/live_site

pylint passive_data_kit
bandit -r .

echo Starting gunicorn...

gunicorn live_site.wsgi --log-file - --bind="0.0.0.0:$WEB_PORT"