#!/usr/bin/env python3
# Copyright 2018-2020 AT&T Intellectual Property, Inc. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright 2020 Deutsche Telekom. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#  Author  Prakash Hosangady(ph553f@att.com)
#    CBS Polling
#    Set the hb_common table with state="RECONFIGURATION" periodically
#    to get the new configuration downloaded

import os
import socket
import sys
import time
import get_logger
import misshtbtd as db

_logger = get_logger.get_logger(__name__)


def pollCBS(current_pid):
    jsfile = db.fetch_json_file()
    ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval = db.read_hb_properties(jsfile)
    hbc_pid, hbc_state, hbc_srcName, hbc_time = db.read_hb_common(user_name, password, ip_address, port_num, db_name)
    msg = "CBSP:Main process ID in hb_common is %d", hbc_pid
    _logger.info(msg)
    msg = "CBSP:My parent process ID is %d", current_pid
    _logger.info(msg)
    msg = "CBSP:CBS Polling interval is %d", cbs_polling_interval
    _logger.info(msg)
    envPytest = os.getenv('pytest', "")
    if (envPytest == 'test'):
        cbs_polling_interval = "30"
    time.sleep(int(cbs_polling_interval))
    hbc_pid, hbc_state, hbc_srcName, hbc_time = db.read_hb_common(user_name, password, ip_address, port_num, db_name)
    # connection_db = pm.postgres_db_open(user_name,password,ip_address,port_num,db_name)
    # cur = connection_db.cursor()
    source_name = socket.gethostname()
    source_name = source_name + "-" + str(os.getenv('SERVICE_NAME', ""))
    result = True
    if (int(current_pid) == int(hbc_pid) and source_name == hbc_srcName and hbc_state == "RUNNING"):
        _logger.info("CBSP:ACTIVE Instance:Change the state to RECONFIGURATION")
        state = "RECONFIGURATION"
        update_flg = 1
        db.create_update_hb_common(update_flg, hbc_pid, state, user_name, password, ip_address, port_num, db_name)
    else:
        _logger.info("CBSP:Inactive instance or hb_common state is not RUNNING")
    return result


if __name__ == "__main__":
    current_pid = sys.argv[1]
    while (True):
        pollCBS(current_pid)
