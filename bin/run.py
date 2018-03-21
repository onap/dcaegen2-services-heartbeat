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

import sys
import yaml
import multiprocessing
import logging
import subprocess
from miss_htbt_service import get_logger

#Checks heartbeat by calling worker thread
def checkhtbt(mr_url, misshtbt,intvl,intopic,outtopic):
        print('Doing some work',mr_url, misshtbt,intvl,intopic,outtopic)
        subprocess.call(["/usr/bin/python","./miss_htbt_service/htbtworker.py" , mr_url , str(misshtbt) , str(intvl) , intopic , outtopic])
        sys.stdout.flush()
        return

_logger = get_logger(__name__)

#main functon which reads yaml config and invokes heartbeat
#monitoring
if __name__ == '__main__':
    try:
      print("Heartbeat Microservice ...")
      multiprocessing.log_to_stderr()
      logger = multiprocessing.get_logger()
      logger.setLevel(logging.INFO)
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
        p = multiprocessing.Process(target=checkhtbt, args=(cfg['global']['message_router_url'],cfg['vnfs'][vnf][0],cfg['vnfs'][vnf][1],cfg['vnfs'][vnf][2],cfg['vnfs'][vnf][3]))
        jobs.append(p)
        p.start()
      for j in jobs:
        j.join()
        print('%s.exitcode = %s' % (j.name, j.exitcode))
    except Exception as e:
        _logger.error("Fatal error. Could not start missing heartbeat service due to: {0}".format(e))
