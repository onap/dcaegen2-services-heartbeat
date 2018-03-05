FROM python:3.6
MAINTAINER gs244f@att.com

ADD . /tmp

#need pip > 8 to have internal pypi repo in requirements.txt
RUN pip install --upgrade pip 
#do the install
WORKDIR /tmp
RUN pip install pyyaml --upgrade
RUN pip install -r requirements.txt
RUN pip install -e .

RUN mkdir /opt/config
RUN echo 1.2.3.4 > /opt/config/coll_ip.txt 
RUN echo 1234 > /opt/config/coll_port.txt 
RUN echo 4.5.6.7 > /opt/config/pol_ip.txt 
RUN echo 4567 > /opt/config/pol_port.txt 
EXPOSE 10000

ENV PYTHONPATH  /usr/local/lib/python3.6/site-packages
#CMD run.py
#ENTRYPOINT ["/bin/python", "./bin/run.py"]
#ENTRYPOINT ["/usr/bin/python","./bin/run.py" ]
ENTRYPOINT ["/usr/local/bin/python","./bin/run.py" ]
#ENTRYPOINT ["/bin/ls","-lR", "/usr/local"]
