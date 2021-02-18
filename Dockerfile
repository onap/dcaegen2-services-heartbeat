FROM nexus3.onap.org:10001/onap/integration-python:8.0.0
LABEL maintainer="gs244f@att.com"

ARG user=heartbeat
ARG group=heartbeat

USER root
RUN addgroup -S $group && adduser -S -D -h /home/$user $user $group && \
    chown -R $user:$group /home/$user &&  \
    mkdir -p /var/log/$user && \
    chown -R $user:$group /var/log/$user && \
    mkdir -p /app && \
    chown -R $user:$group /app

WORKDIR /app

EXPOSE 10002

COPY --chown=$user:$group ./miss_htbt_service/ ./bin/
COPY --chown=$user:$group ./etc/ ./etc/
COPY --chown=$user:$group requirements.txt ./
COPY --chown=$user:$group setup.py ./

# install build dependencies for python packages,
# install python packages
# remove build dependencies
RUN apk add --no-cache --virtual build-deps \
    build-base libffi-dev postgresql-dev \
    openssl-dev musl-dev python3-dev curl && \
    apk add --no-cache libpq && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    export PATH="$HOME/.cargo/bin/:$PATH" && \
    source $HOME/.cargo/env && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    mkdir -p data logs tmp && \
    chown -R $user:$group . && \
    chmod g+w data logs tmp etc && \
    chmod -R 500 bin/*.py && \
    chmod 500 bin/*.sh && \
    apk del build-deps && \
    rustup self uninstall -y

USER $user
VOLUME logs

CMD ["./bin/misshtbt.sh"]

ENV PYTHONPATH="$PYTHONPATH:/usr/local/lib/python3.9/site-packages:/app/bin/mod:/app/bin"
ENV PATH="$PATH:/app/bin"
