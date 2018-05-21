FROM python:3.6
MAINTAINER gs244f@att.com

ENV INSROOT /opt/app
ENV APPUSER misshtbt
ENV APPDIR ${INSROOT}/${APPUSER}

RUN useradd -d ${APPDIR} ${APPUSER}

WORKDIR ${APPDIR}

#ADD . /tmp
#RUN mkdir /tmp/config

EXPOSE 10001

COPY ./miss_htbt_service/ ./bin/
COPY ./etc/ ./etc/
COPY requirements.txt ./
COPY setup.py ./

#need pip > 8 to have internal pypi repo in requirements.txt
RUN pip install --upgrade pip 
#do the install
#WORKDIR /tmp
RUN pip install pyyaml --upgrade
RUN pip install -r requirements.txt
RUN pip install -e .

RUN mkdir -p ${APPDIR}/data \
 && mkdir -p ${APPDIR}/logs \
 && mkdir -p ${APPDIR}/tmp \
 && chown -R ${APPUSER}:${APPUSER} ${APPDIR} \
 && chmod a+w ${APPDIR}/data \
 && chmod a+w ${APPDIR}/logs \
 && chmod a+w ${APPDIR}/tmp \
 && chmod 500 ${APPDIR}/etc \
 && chmod 500 ${APPDIR}/bin/*.py \
 && chmod 500 ${APPDIR}/bin/*.sh \
 && chmod 500 ${APPDIR}/bin/*/*.py

USER ${APPUSER}
VOLUME ${APPDIR}/logs

CMD ["./bin/misshtbt.sh"]

#ENV PYTHONPATH="/usr/local/lib/python3.6:/usr/local/lib/python3.6/site-packages:${PATH}"
#ENV PYTHONPATH="/usr/local/lib/python3.6/site-packages:/usr/local/lib/python3.6"
#ENV PYTHONPATH=/usr/local/lib/python3.6/site-packages:.
#ENTRYPOINT ["/bin/python", "./bin/run.py"]
#ENTRYPOINT ["/usr/bin/python","./bin/run.py" ]
#ENTRYPOINT ["/usr/local/bin/python","./bin/misshtbtd.py" ]
#ENTRYPOINT ["/bin/ls","-lR", "."]
