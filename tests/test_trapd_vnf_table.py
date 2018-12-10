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
test_trapd_vnf_table contains test cases related to DB Tables and cbs polling.
"""

import unittest
import sys
import pytest
import logging
import misshtbtd as db
import htbtworker as pm
import get_logger
from trapd_vnf_table import verify_DB_creation_1,verify_DB_creation_2,verify_DB_creation_hb_common,verify_cbsPolling_required,hb_properties,verify_cbspolling

_logger = get_logger.get_logger(__name__)


class test_vnf_tables(unittest.TestCase):
    """
    Test the DB Creation
    """
    global ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval
    ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval = hb_properties()
    def test_validate_vnf_table_1(self):
        result =verify_DB_creation_1(user_name,password,ip_address,port_num,db_name)
        self.assertEqual(result, True)
        
    def test_validate_vnf_table_2(self):
        result =verify_DB_creation_2(user_name,password,ip_address,port_num,db_name)
        self.assertEqual(result, True)
        
    def test_validate_hb_common(self):
        result =verify_DB_creation_hb_common(user_name,password,ip_address,port_num,db_name)
        self.assertEqual(result, True)

    def test_validate_hbcommon_processId(self):
        result =verify_DB_creation_hb_common(user_name,password,ip_address,port_num,db_name)
        self.assertEqual(result, True)
        connection_db = pm.postgres_db_open(user_name,password,ip_address,port_num,db_name)
        cur = connection_db.cursor()
        query_value = "SELECT process_id,source_name,last_accessed_time,current_state FROM hb_common;"
        cur.execute(query_value)
        rows = cur.fetchall()
        msg = "Common: row ", rows
        _logger.info(msg)
        hbc_pid = rows[0][0]
        pm.commit_and_close_db(connection_db)
        cur.close()
        self.assertNotEqual(hbc_pid, None , msg="Process ID is not Present is hb_common")
        
    def test_validate_hbcommon_sourceName(self):
        result =verify_DB_creation_hb_common(user_name,password,ip_address,port_num,db_name)
        self.assertEqual(result, True)

        connection_db = pm.postgres_db_open(user_name,password,ip_address,port_num,db_name)
        cur = connection_db.cursor()
        query_value = "SELECT process_id,source_name,last_accessed_time,current_state FROM hb_common;"
        cur.execute(query_value)
        rows = cur.fetchall()
        msg = "Common: row ", rows
        _logger.info(msg)
        hbc_srcName = rows[0][1]
        pm.commit_and_close_db(connection_db)
        cur.close()
        self.assertNotEqual(hbc_srcName, None , msg="Process ID is not Present is hb_common")
        
    def test_validate_sourceidcount_table1(self):
        result_connection =verify_DB_creation_1(user_name,password,ip_address,port_num,db_name)
        self.assertEqual(result_connection, True)
        #result=verify_sourceidcount_vnftable1(user_name,password,ip_address,port_num,db_name)
        connection_db = pm.postgres_db_open(user_name,password,ip_address,port_num,db_name)
        cur = connection_db.cursor()
        try:
            query = "select source_id_count from vnf_table_1;"
            cur.execute(query)
            rows = cur.fetchall()
            q_count = "SELECT COUNT(*) FROM vnf_table_1;"
            cur.execute(q_count)
            r_count = cur.fetchall()
            r_c = r_count[0][0]
            for r in r_c:
                output = rows[r][0]
            for res in output:
                self.assertNotEqual(output, 0)
        except Exception as e:
            return None       
            
    def test_validate_cbspolling_required(self):
        result = verify_cbsPolling_required()
        self.assertEqual(result, True)
    
#    def test_cbspolling(self):
#        result= verify_cbspolling()
#        _logger.info(result)
#        self.assertEqual(result, True)
        
#if __name__ == '__main__':
#    unittest.main()
