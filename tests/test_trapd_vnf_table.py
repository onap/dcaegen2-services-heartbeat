# ============LICENSE_START=======================================================
# Copyright (c) 2017-2022 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
# Copyright (c) 2020 Deutsche Telekom. All rights reserved.
# Copyright (c) 2021 Fujitsu Ltd.
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
#  Author Prakask H (ph553f)
"""
test_trapd_vnf_table contains test cases related to DB Tables and cbs polling.
"""
import logging
import unittest
from mod.trapd_vnf_table import (
    verify_DB_creation_1,
    verify_DB_creation_2,
    verify_DB_creation_hb_common,
    hb_properties,
    verify_cbspolling,
    verify_sendControlLoop_VNF_ONSET,
    verify_sendControlLoop_VM_ONSET,
    verify_sendControlLoop_VNF_ABATED,
    verify_sendControlLoop_VM_ABATED,
    verify_fetch_json_file,
    verify_misshtbtdmain,
    verify_dbmonitoring,
    verify_dbmon_startup,
)

_logger = logging.getLogger(__name__)


class test_vnf_tables(unittest.TestCase):
    """
    Test the DB Creation
    """

    global ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval
    ip_address, port_num, user_name, password, db_name, cbs_polling_required, cbs_polling_interval = hb_properties()

    def test_validate_vnf_table_1(self):
        result = verify_DB_creation_1(user_name, password, ip_address, port_num, db_name)
        self.assertEqual(result, True)

    def test_validate_vnf_table_2(self):
        result = verify_DB_creation_2(user_name, password, ip_address, port_num, db_name)
        self.assertEqual(result, True)

    def test_validate_hb_common(self):
        result = verify_DB_creation_hb_common(user_name, password, ip_address, port_num, db_name)
        self.assertEqual(result, True)

    def test_cbspolling(self):
        # Check if no exception thrown
        verify_cbspolling()

    def test_fetch_json_file(self):
        result = verify_fetch_json_file()
        _logger.info(result)
        self.assertEqual(result, True)

    def test_misshtbtdmain(self):
        result = verify_misshtbtdmain()
        _logger.info(result)
        self.assertEqual(result, True)

    def test_dbmon_startup(self):
        result = verify_dbmon_startup()
        _logger.info(result)
        self.assertEqual(result, True)

    def test_dbmonitoring(self):
        result = verify_dbmonitoring()
        _logger.info(result)
        self.assertEqual(result, True)

    def test_sendControlLoop_VNF_ONSET(self):
        result = verify_sendControlLoop_VNF_ONSET()
        _logger.info(result)
        self.assertEqual(result, True)

    def test_sendControlLoop_VM_ONSET(self):
        result = verify_sendControlLoop_VM_ONSET()
        _logger.info(result)
        self.assertEqual(result, True)

    def test_sendControlLoop_VNF_ABATED(self):
        result = verify_sendControlLoop_VNF_ABATED()
        _logger.info(result)
        self.assertEqual(result, True)

    def test_sendControlLoop_VM_ABATED(self):
        result = verify_sendControlLoop_VM_ABATED()
        _logger.info(result)
        self.assertEqual(result, True)
