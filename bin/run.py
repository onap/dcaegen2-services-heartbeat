#!/usr/bin/env python3

# ============LICENSE_START=======================================================
# Copyright (c) 2017-2018 AT&T Intellectual Property. All rights reserved.
# ================================================================================
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============LICENSE_END=========================================================
#
# ECOMP is a trademark and service mark of AT&T Intellectual Property.
# 
#  Author Gokul Singaraju gs244f@att.com 
# 

import os
import sys
import yaml
import multiprocessing
import logging
import subprocess
from miss_htbt_service import get_logger

mr_url = 'http://mrrouter.onap.org:3904'
pol_url = 'http://mrrouter.onap.org:3904'
intopic = 'VESCOLL-VNFNJ-SECHEARTBEAT-OUTPUT'
outopic = 'POLICY-HILOTCA-EVENT-OUTPUT'

#Checks heartbeat by calling worker thread
def checkhtbt(mr_url, intopic, pol_url, outopic, misshtbt,intvl):
        print('Doing some work',mr_url, misshtbt,intvl,intopic,outopic)
        subprocess.call(["/usr/bin/python","./miss_htbt_service/htbtworker.py" , mr_url , intopic, pol_url, outopic, str(misshtbt) , str(intvl) ])
        sys.stdout.flush()
        return

_logger = get_logger(__name__)

#main functon which reads yaml config and invokes heartbeat
#monitoring
if __name__ == '__main__':
    try:
      print("Heartbeat Microservice ...")
      if "INURL" in os.environ.keys():
        mr_url = os.environ['INURL']
      if "INTOPIC" in os.environ.keys():
        intopic = os.environ['INTOPIC']
      if "OUTURL" in os.environ.keys():
        pol_url = os.environ['OUTURL']
      if "OUTOPIC" in os.environ.keys():
        outopic = os.environ['OUTOPIC']
      print(outopic)
      multiprocessing.log_to_stderr()
      logger = multiprocessing.get_logger()
      logger.setLevel(logging.INFO)
      my_env = os.environ.copy()
      my_env["PYTHONPATH"] = my_env["PYTHONPATH"]+"/usr/local/lib/python3.6:"
      p = subprocess.Popen(['./bin/check_health.py'],stdout=subprocess.PIPE,env=my_env)
      #print(p.communicate())
      with open("./miss_htbt_service/config/config.yaml", 'r') as ymlfile:
         cfg = yaml.load(ymlfile)
      # Put some initial values into the queue
      for section in cfg:
       print(section)
      #print(cfg['global'])
      #print(cfg['global']['message_router_url'])
      jobs = []
      for vnf in (cfg['vnfs']):
        print(cfg['vnfs'][vnf])
        #print(cfg['vnfs'][vnf][0])
        #print(cfg['vnfs'][vnf][1])
        #print(cfg['vnfs'][vnf][2])
        #Start Heartbeat monitoring process worker thread on VNFs configured
        logger.info("Starting threads...")
        p = multiprocessing.Process(target=checkhtbt, args=( mr_url, intopic, pol_url, outopic, cfg['vnfs'][vnf][0],cfg['vnfs'][vnf][1]))
        jobs.append(p)
        p.start()
      for j in jobs:
        j.join()
        print('%s.exitcode = %s' % (j.name, j.exitcode))
    except Exception as e:
        _logger.error("Fatal error. Could not start missing heartbeat service due to: {0}".format(e))
