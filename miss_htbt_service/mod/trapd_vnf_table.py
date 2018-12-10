# ============LICENSE_START=======================================================
# org.onap.dcae
# ================================================================================
# Copyright (c) 2017-2018 AT&T Intellectual Property. All rights reserved.
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
# ECOMP is a trademark and service mark of AT&T Intellectual Property.
#
##  Author Kiran Mandal (km386e)
"""
trapd_vnf_table verifies the successful creation of DB Tables.
"""


import psycopg2
import os
import sys
import htbtworker as pm
import misshtbtd as db
import config_notif as cf
import cbs_polling as cbs
import logging
import get_logger
import yaml
import os.path as path
hb_properties_file =  path.abspath(path.join(__file__, "../../config/hbproperties.yaml"))

prog_name = os.path.basename(__file__)

def hb_properties():
	#Read the hbproperties.yaml for postgress and CBS related data
	s=open(hb_properties_file, 'r')
	a=yaml.load(s)
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

ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval = hb_properties()	
	
def verify_DB_creation_1(user_name,password,ip_address,port_num,db_name):
    connection_db = pm.postgres_db_open(user_name,password,ip_address,port_num,db_name)
    cur = connection_db.cursor()
    try:
        _db_status=pm.db_table_creation_check(connection_db,"vnf_table_1")
    except Exception as e:
        return None
    
    return _db_status
    
def verify_DB_creation_2(user_name,password,ip_address,port_num,db_name):

    connection_db = pm.postgres_db_open(user_name,password,ip_address,port_num,db_name)
    cur = connection_db.cursor()
    try:
        _db_status=pm.db_table_creation_check(connection_db,"vnf_table_2")
    except Exception as e:
        return None
    
    return _db_status
    
def verify_DB_creation_hb_common(user_name,password,ip_address,port_num,db_name):

    connection_db = pm.postgres_db_open(user_name,password,ip_address,port_num,db_name)
    cur = connection_db.cursor()
    try:
        _db_status=pm.db_table_creation_check(connection_db,"hb_common")
    except Exception as e:
        return None
    
    return _db_status
    
    
def verify_cbsPolling_required():
    try:
        _cbspolling_status=cf.config_notif_run()
    except Exception as e:
        return None
        
    return _cbspolling_status

def verify_cbspolling():
    try:
        _cbspolling=cbs.currentpidMain(10)
    except Exception as e:
        return None
        
    return _cbspolling
