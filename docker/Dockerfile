FROM ubuntu:24.04

WORKDIR /app

RUN apt-get update
RUN apt-get install -y apt-utils curl
RUN apt-get install -y python3-dev gdal-bin python3-venv

RUN python3 -m venv /app/venv
RUN . /app/venv/bin/activate && pip install -U wheel pip
ADD ./requirements.txt /app/requirements.txt
RUN . /app/venv/bin/activate && pip install -r requirements.txt

RUN . /app/venv/bin/activate && django-admin startproject live_site
ADD . /app/live_site/passive_data_kit

ADD ./docker/site_settings.py /app/live_site/live_site/settings.py
ADD ./docker/site_urls.py /app/live_site/live_site/urls.py
ADD ./docker/wsgi.py /app/live_site/live_site/wsgi.py
ADD ./.pylintrc /app/live_site/.pylintrc

ADD ./docker/data/users.json /app/users.json
ADD ./docker/data/pdk-test-data.json /app/pdk-test-data.json

# Latest releases available at https://github.com/aptible/supercronic/releases
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.30/supercronic-linux-amd64 \
    SUPERCRONIC=supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=9f27ad28c5c57cd133325b2a66bba69ba2235799

RUN curl -fsSLO "$SUPERCRONIC_URL" \
 && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
 && chmod +x "$SUPERCRONIC" \
 && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
 && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

ADD ./docker/crontab /app/crontab

ADD ./docker/run.sh /app/run.sh

EXPOSE ${WEB_PORT}