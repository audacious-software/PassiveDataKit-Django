# Docker Setup

These Docker files are a reference implementation for downstream projects using Passive Data Kit to serve as the beginning of their respective Docker containers.

This implementation may also be used to stand up a *basic* Passive Data Kit server for testing and evaluation.

**This implementation is *NOT* intended to be used as-is in production settings!**

## Setup

1. Check out the Passive Data Kit repository:

    ```git clone https://github.com/audacious-software/PassiveDataKit-Django.git```

2. Navigate to the included `docker` folder and copy the `template.env` file to `.env` in the same directory.

    ```cp template.env .env```

3. Open the `.env` file and update the relevant options as needed. Note that if you are serving static files using a web server such as Apache or Nginx, the `DJANGO_MEDIA_FILES` and `DJANGO_STATIC_FILES` paths should reflect where you checked out the Git repository.

4. This configuration is intended to run with an Nginx web server on the container host providing SSL and static file serving services. An example site definition is provided in the `docker/hosts/host.nginx` file to illustrate both how to map to the relevant static file path, and how to set up a proxy tunnel to the application server on the Docker container.

5. If you are running this server on your local machine, open the `run.sh` file and comment out the lines containing with `gunicorn` and uncomment the lines below to use Django's built-in web server:

   ```python3 manage.py runserver 0.0.0.0:$WEB_PORT```

6. Start your local Docker server (if not already running) or launch Docker Desktop (if working on a local machine). From the `docker` folder, run

    ```docker compose up```

Docker will set-up a suitable Postgres server with the PostGIS extensions and it will set up a full Django installation that includes Passive Data Kit. This process can take some time, so be patient until it completes.

7. Once you see the container running, visit it at

    [http://localhost:8000/admin/](http://localhost:8000/admin/) (replace `8000` with the port you selected in the `.env` file if needed)

Login with the username `admin` and the password `admin12345`.

8. If enough time elapses (a minute or two), verify that the background CRON jobs are running by visiting

    [http://localhost:8000/admin/passive_data_kit/datapoint/](http://localhost:8000/admin/passive_data_kit/datapoint/)

If you see a `pdk-docker-test` data point in the table, the background processing jobs are running properly.

## Notes

* If you have trouble connecting to the local web server, try using a different browser first. Many browsers silently and automaticaly will rewrite HTTP URLs into HTTPS URLs, which can interfere with testing.

* You can speed up the web container launch by commenting out the following lines:

    ```python3 manage.py test```
    ```python3 manage.py check```
    ```pylint passive_data_kit```
    ```bandit -r .```

  These are code-correctness checks to verify that the Docker container is running properly and the Passive Data Kit server is fully functional.

## Contact Us

This is an early-stage implementation, so if you have any questions or comments, please mail them to [chris@audacious-software.com](mailto:chris@audacious-software.com).
