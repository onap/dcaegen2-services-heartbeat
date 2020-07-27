FROM python:3.8.2-alpine3.11
MAINTAINER gs244f@att.com

ARG user=onap
ARG group=onap

RUN addgroup -S $group && adduser -S -D -h /home/$user $user $group && \
    chown -R $user:$group /home/$user &&  \
    mkdir /var/log/$user && \
    chown -R $user:$group /var/log/$user && \
    mkdir /app && \
    chown -R $user:$group /app
	
WORKDIR /app

#ADD . /tmp
#RUN mkdir /tmp/config

EXPOSE 10002

COPY ./miss_htbt_service/ ./bin/
COPY ./etc/ ./etc/
COPY requirements.txt ./
COPY setup.py ./

#need pip > 8 to have internal pypi repo in requirements.txt
#do the install
RUN apk add build-base libffi-dev postgresql-dev && \
    pip install --upgrade pip && \
    pip install pyyaml --upgrade && \
    pip install -r requirements.txt && \
    pip install -e .

RUN mkdir -p data \
 && mkdir -p logs \
 && mkdir -p tmp \
 && chown -R $user:$group . \
 && chmod a+w data \
 && chmod a+w logs \
 && chmod a+w tmp \
 && chmod a+w etc \
 && chmod 500 bin/*.py \
 && chmod 500 bin/*.sh \
 && chmod 500 bin/*/*.py

USER $user
VOLUME logs

CMD ["./bin/misshtbt.sh"]

#ENV PYTHONPATH="/usr/local/lib/python3.6:/usr/local/lib/python3.6/site-packages:${PATH}"
#ENV PYTHONPATH="/usr/local/lib/python3.6/site-packages:/usr/local/lib/python3.6"
#ENV PYTHONPATH=/usr/local/lib/python3.6/site-packages:.
#ENTRYPOINT ["/bin/python", "./bin/run.py"]
#ENTRYPOINT ["/usr/bin/python","./bin/run.py" ]
#ENTRYPOINT ["/usr/local/bin/python","./bin/misshtbtd.py" ]
#ENTRYPOINT ["/bin/ls","-lR", "."]
