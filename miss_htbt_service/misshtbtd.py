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
import json
import multiprocessing
import logging
import subprocess
import get_logger
from pathlib import Path

import mod.trapd_settings as tds
from mod.trapd_runtime_pid import save_pid, rm_pid
from mod.trapd_get_cbs_config import get_cbs_config
#from mod.trapd_exit import cleanup_and_exit
from mod.trapd_http_session import init_session_obj


mr_url = 'http://mrrouter.onap.org:3904'
pol_url = 'http://mrrouter.onap.org:3904'
intopic = 'VESCOLL-VNFNJ-SECHEARTBEAT-OUTPUT'
outopic = 'POLICY-HILOTCA-EVENT-OUTPUT'

#Checks heartbeat by calling worker thread
def checkhtbt(mr_url, intopic, pol_url, outopic, nfc, misshtbt,intvl, cl_loop):
        print('Doing some work',mr_url, misshtbt,intvl,intopic,outopic)
        my_file = Path("./miss_htbt_service/htbtworker.py")
        if my_file.is_file():
          subprocess.call(["python","./miss_htbt_service/htbtworker.py" , mr_url , intopic, pol_url, outopic, nfc, str(misshtbt) , str(intvl), cl_loop ])
        else:
          subprocess.call(["python","/opt/app/misshtbt/bin/htbtworker.py" , mr_url , intopic, pol_url, outopic, nfc, str(misshtbt) , str(intvl), cl_loop ])
        sys.stdout.flush()
        return

_logger = get_logger.get_logger(__name__)

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
      my_env["PYTHONPATH"] = my_env["PYTHONPATH"]+":/usr/local/lib/python3.6"+":./miss_htbt_service/"
      my_env["PATH"] = my_env["PATH"]+":./bin/:./miss_htbt_service/"
      p = subprocess.Popen(['check_health.py'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=my_env)
      #print(p.communicate())
      jsfile='empty'

      # re-request config from config binding service
      # (either broker, or json file override)
      if get_cbs_config():
        current_runtime_config_file_name = tds.c_config['files.runtime_base_dir'] + "../etc/download.json"
        msg = "current config logged to : %s" % current_runtime_config_file_name
        logger.error(msg)
        print(msg)
        with open(current_runtime_config_file_name, 'w') as outfile:
            json.dump(tds.c_config, outfile)
        jsfile = current_runtime_config_file_name
      else:
        msg = "CBS Config not available using local config"
        logger.error(msg)
        print(msg)
        my_file = Path("./etc/config.json")
        if my_file.is_file():
          jsfile = "./etc/config.json"
        else:
          jsfile = "../etc/config.json"

      print("opening %s " % jsfile)
      with open(jsfile, 'r') as outfile:
          cfg = json.load(outfile)
          # Put some initial values into the queue
          mr_url = cfg['streams_subscribes']['ves_heartbeat']['dmaap_info']['topic_url']
          pol_url = cfg['streams_publishes']['ves_heartbeat']['dmaap_info']['topic_url']
      jobs = []
      print(cfg['heartbeat_config'])
      for vnf in (cfg['heartbeat_config']['vnfs']):
        print(vnf)
        nfc = vnf['nfNamingCode']
        missed = vnf['heartbeatcountmissed']
        intvl = vnf['heartbeatinterval']
        clloop = vnf['closedLoopControlName']
        print('{0} {1} {2} {3}'.format(nfc,missed,intvl,clloop))
        #Start Heartbeat monitoring process worker thread on VNFs configured
        logger.info("Starting threads...")
        p = multiprocessing.Process(target=checkhtbt, args=( mr_url, intopic, pol_url, outopic, nfc, missed, intvl, clloop))
        jobs.append(p)
        p.start()
      for j in jobs:
        j.join()
        print('%s.exitcode = %s' % (j.name, j.exitcode))
    except Exception as e:
        _logger.error("Fatal error. Could not start missing heartbeat service due to: {0}".format(e))
