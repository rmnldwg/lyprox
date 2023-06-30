# base image
FROM python:3.10

# install git, since it is required by DVC
RUN apt update && apt install git -y

# set some env variables
ENV LYPROX_HOME /srv/www/lyprox
ENV PYTHONDONOTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set the working directory to the home directory
WORKDIR $LYPROX_HOME

# upgrade pip and setuptools
RUN pip install --upgrade pip setuptools

# copy the repo content to the home directory
COPY . $LYPROX_HOME

# install LyProX
RUN pip install .

# expose the port 8000
EXPOSE $DJANGO_GUNICORN_PORT
