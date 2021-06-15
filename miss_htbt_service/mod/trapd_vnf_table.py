# ============LICENSE_START=======================================================
# org.onap.dcae
# ================================================================================
# Copyright (c) 2017-2020 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright 2020 Deutsche Telekom. All rights reserved.
# Copyright 2021 Samsung Electronics. All rights reserved.
# ================================================================================
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============LICENSE_END=========================================================
#
##  Author Kiran Mandal (km386e)

"""
trapd_vnf_table verifies the successful creation of DB Tables.
"""

import os
import os.path as path
import subprocess
import time
import yaml

import cbs_polling as cbs
import config_notif as cf
import db_monitoring as dbmon
import get_logger
import htbtworker as pm
import misshtbtd as db

prog_name = os.path.basename(__file__)
hb_properties_file =  path.abspath(path.join(__file__, "../../config/hbproperties.yaml"))
_logger = get_logger.get_logger(__name__)

def hb_properties():
	#Read the hbproperties.yaml for postgress and CBS related data
	s=open(hb_properties_file, 'r')
	a=yaml.full_load(s)
	ip_address = a['pg_ipAddress']
	port_num = a['pg_portNum']
	user_name = a['pg_userName']
	password = a['pg_passwd']
	dbName = a['pg_dbName']
	db_name = dbName.lower()
	cbs_polling_required = a['CBS_polling_allowed']
	cbs_polling_interval = a['CBS_polling_interval']
	s.close()
	return ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval


def verify_DB_creation_1(user_name,password,ip_address,port_num,db_name):
    connection_db = pm.postgres_db_open(user_name,password,ip_address,port_num,db_name)
   # cur = connection_db.cursor()
    try:
        _db_status=pm.db_table_creation_check(connection_db,"vnf_table_1")
    except Exception as e:
        return None

    return _db_status

def verify_DB_creation_2(user_name,password,ip_address,port_num,db_name):

    connection_db = pm.postgres_db_open(user_name,password,ip_address,port_num,db_name)
   # cur = connection_db.cursor()
    try:
        _db_status=pm.db_table_creation_check(connection_db,"vnf_table_2")
    except Exception as e:
        return None

    return _db_status

def verify_DB_creation_hb_common(user_name,password,ip_address,port_num,db_name):

    connection_db = pm.postgres_db_open(user_name,password,ip_address,port_num,db_name)
    #cur = connection_db.cursor()
    try:
        _db_status=pm.db_table_creation_check(connection_db,"hb_common")
    except Exception as e:
        return None

    return _db_status


def verify_cbsPolling_required():
    _cbspolling_status = True
    os.environ['pytest']='test'
    #os.environ['CONSUL_HOST']='10.12.6.50' # Used this IP during testing
    os.environ['CONSUL_HOST']='localhost'
    os.environ['SERVICE_NAME']='mvp-dcaegen2-heartbeat-static'
    try:
        _cbspolling_status=cf.config_notif_run()
    except Exception as e:
        print("Config_notify error - %s" % e)
        #return None

    os.unsetenv('pytest')
    os.unsetenv('CONSUL_HOST')
    os.unsetenv('SERVICE_NAME')
    return _cbspolling_status

def verify_cbspolling():
    os.environ['pytest']='test'
    os.environ['SERVICE_NAME']='mvp-dcaegen2-heartbeat-static'
    try:
        _cbspolling=cbs.pollCBS(10)
    except Exception as e:
        # print("CBSP error - %s" % e)
        # print("CBSP error - %s" % e, file=sys.stderr)
        # print("Stack: {0}".format(traceback.format_exc()), file=sys.stderr)
        return None

    os.unsetenv('pytest')
    os.unsetenv('SERVICE_NAME')
    return _cbspolling

def verify_fetch_json_file():
    os.environ['pytest']='test'
    os.environ['SERVICE_NAME']='mvp-dcaegen2-heartbeat-static'
    #os.environ['CONSUL_HOST']='10.12.6.50' # Used this IP during testing
    os.environ['CONSUL_HOST']='localhost'
    os.environ['HOSTNAME']='mvp-dcaegen2-heartbeat-static'
    try:
       db.fetch_json_file()
       result = True
    except Exception as e:
       result = False
    print(result)
    os.unsetenv('pytest')
    os.unsetenv('SERVICE_NAME')
    os.unsetenv('CONSUL_HOST')
    os.unsetenv('HOSTNAME')
    return result

def verify_misshtbtdmain():
    os.environ['pytest']='test'
    os.environ['SERVICE_NAME']='mvp-dcaegen2-heartbeat-static'
    #os.environ['CONSUL_HOST']='10.12.6.50'
    os.environ['CONSUL_HOST']='localhost'
    os.environ['HOSTNAME']='mvp-dcaegen2-heartbeat-static'

    try:
        db.main()
        result = True
    except Exception as e:
        result = False
    print(result)
    os.unsetenv('pytest')
    os.unsetenv('SERVICE_NAME')
    os.unsetenv('CONSUL_HOST')
    os.unsetenv('HOSTNAME')
    return result

def verify_dbmonitoring():
    os.environ['pytest']='test'
    os.environ['SERVICE_NAME']='mvp-dcaegen2-heartbeat-static'
    #os.environ['CONSUL_HOST']='10.12.6.50'
    os.environ['CONSUL_HOST']='localhost'
    os.environ['HOSTNAME']='mvp-dcaegen2-heartbeat-static'
    try:
        jsfile = db.fetch_json_file()
        ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval = hb_properties()
        hbc_pid, hbc_state, hbc_srcName, hbc_time = db.read_hb_common(user_name,password,ip_address,port_num,db_name)
        dbmon.db_monitoring(hbc_pid,jsfile,user_name,password,ip_address,port_num,db_name)
        result = True
    except Exception as e:
        print("Message process error - %s" % e)
        result = False
    print(result)
    os.unsetenv('pytest')
    os.unsetenv('SERVICE_NAME')
    os.unsetenv('CONSUL_HOST')
    os.unsetenv('HOSTNAME')
    return result

def verify_dbmon_startup():
    try:
        p = subprocess.Popen(['./miss_htbt_service/db_monitoring.py'], stdout=subprocess.PIPE,shell=True)
        time.sleep(1)
    except Exception as e:
        #print("Message process error - %s" % e)
        return None
    return True

def verify_sendControlLoop_VNF_ONSET():
    try:
#        _CL_return = sendControlLoopEvent(CLType, pol_url,  policy_version, policy_name, policy_scope, target_type, srcName, epoc_time, closed_control_loop_name, version, target)
        pol_url = "http://10.12.5.252:3904/events/unauthenticated.DCAE_CL_OUTPUT/"
        _CL_return = dbmon.sendControlLoopEvent("ONSET", pol_url,  "1.0", "vFireWall", "pscope", "VNF", "srcname1", 1541234567, "SampleCLName", "1.0", "genVnfName")
    except Exception as e:
        #msg = "Message process error - ",err
        #_logger.error(msg)
        return None
    return _CL_return

def verify_sendControlLoop_VM_ONSET():
    try:
        pol_url = "http://10.12.5.252:3904/events/unauthenticated.DCAE_CL_OUTPUT/"
        _CL_return = dbmon.sendControlLoopEvent("ONSET", pol_url,  "1.0", "vFireWall", "pscope", "VM", "srcname1", 1541234567, "SampleCLName", "1.0", "genVnfName")
    except Exception as e:
        #msg = "Message process error - ",err
        #_logger.error(msg)
        return None
    return _CL_return

def verify_sendControlLoop_VNF_ABATED():
    try:
        pol_url = "http://10.12.5.252:3904/events/unauthenticated.DCAE_CL_OUTPUT/"
        _CL_return = dbmon.sendControlLoopEvent("ABATED", pol_url,  "1.0", "vFireWall", "pscope", "VNF", "srcname1", 1541234567, "SampleCLName", "1.0", "genVnfName")
    except Exception as e:
        #msg = "Message process error - ",err
        #_logger.error(msg)
        return None
    return _CL_return

def verify_sendControlLoop_VM_ABATED():
    try:
        pol_url = "http://10.12.5.252:3904/events/unauthenticated.DCAE_CL_OUTPUT/"
        _CL_return = dbmon.sendControlLoopEvent("ABATED", pol_url,  "1.0", "vFireWall", "pscope", "VM", "srcname1", 1541234567, "SampleCLName", "1.0", "genVnfName")
    except Exception as e:
#        msg = "Message process error - ",err
#        _logger.error(msg)
        return None
    return _CL_return
