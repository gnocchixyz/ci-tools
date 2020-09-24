FROM ubuntu:20.04
ENV GNOCCHI_SRC /home/tester/src
ENV DEBIAN_FRONTEND noninteractive

#NOTE(tobias-urdin): need gnupg for apt-key
RUN apt-get update -y && apt-get install -qy gnupg
RUN echo 'deb http://ppa.launchpad.net/deadsnakes/ppa/ubuntu focal main' >> /etc/apt/sources.list
RUN apt-key adv --recv-keys --keyserver keyserver.ubuntu.com F23C5A6CF475977595C89F51BA6932366A755776
RUN apt-get update -y && apt-get install -qy \
        locales \
        git \
        wget \
        curl \
        nodejs \
        npm \
        python3 \
        python3.6 \
        python3-dev \
        python3.6-dev \
        python3-pip \
# Needed for uwsgi core routing support
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
        python3-rados \
        ceph \
# For prometheus
        libsnappy-dev \
        libprotobuf-dev \
# For redis
        redis-server \
        && rm -rf /var/lib/apt/lists/*

#NOTE(sileht): really no utf-8 in 2017 !?
ENV LANG en_US.UTF-8
RUN update-locale
RUN locale-gen $LANG

#NOTE(sileht): Upgrade python dev tools
RUN python3 -m pip install -U pip tox virtualenv

RUN npm install s3rver@1.0.3 --global

RUN groupadd --gid 2000 tester
RUN useradd --uid 2000 --gid 2000 --create-home --shell /bin/bash tester
USER tester

WORKDIR $GNOCCHI_SRC
