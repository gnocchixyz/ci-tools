FROM ubuntu:18.04
ENV GNOCCHI_SRC /home/tester/src
ENV DEBIAN_FRONTEND noninteractive

RUN apt-key adv --recv-keys --keyserver keyserver.ubuntu.com F23C5A6CF475977595C89F51BA6932366A755776
RUN apt-get update -y && apt-get install -qy \
        locales \
        git \
        wget \
        nodejs \
        nodejs-legacy \
        npm \
        python \
        python3 \
        python3.7 \
        python-dev \
        python3-dev \
        python3.7-dev \
        redis-server \
# Needed for uwsgi core routing support
        libpcre3-dev \
        python-pip \
        build-essential \
        libffi-dev \
        libpq-dev \
        postgresql \
        memcached \
        mysql-client \
        mysql-server \
# For Ceph
        librados-dev \
        liberasurecode-dev \
        python-rados \
        ceph \
# For prometheus
        libsnappy-dev \
        libprotobuf-dev \
        && rm -rf /var/lib/apt/lists/*

#NOTE(sileht): really no utf-8 in 2017 !?
ENV LANG en_US.UTF-8
RUN update-locale
RUN locale-gen $LANG

#NOTE(sileht): Upgrade python dev tools
RUN pip install -U pip tox virtualenv

RUN npm install s3rver@1.0.3 --global

RUN groupadd --gid 2000 tester
RUN useradd --uid 2000 --gid 2000 --create-home --shell /bin/bash tester
USER tester

WORKDIR $GNOCCHI_SRC
