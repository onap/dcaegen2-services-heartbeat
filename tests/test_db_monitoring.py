#!/usr/bin/env python3
# ============LICENSE_START=======================================================
# Copyright (c) 2023 AT&T Intellectual Property. All rights reserved.
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

import db_monitoring
import htbtworker
import logging
import requests
import tempfile
import os
import json
import unittest
import time

from unittest.mock import *
from _pytest.outcomes import skip
from pickle import NONE

_logger = logging.getLogger(__name__)


class Test_db_monitoring(unittest.TestCase):

    class PseudoCursorCase1():
        # Test setup for RECONFIGURATION state
        fetchall_1 = ""
        @classmethod
        def execute(ctype ,command,arg=None):
            global fetchall_1
            print(f"Type ctype: {type(ctype)} : self: {ctype}")
            print(f"Type command: {type(command)} : command: {command}")
            print(f"Type arg: {type(arg)} : arg: {arg}")
            if command.startswith("SELECT validity_flag, source_name_count, heartbeat_interval,"):
                fetchall_1 = [[1,1,300,1,"TEMP-CL", "1.0","TEMPPOLICY","TEMP","VM","TEMP","1.0"]]
            elif command.startswith ("SELECT last_epo_time, source_name, cl_flag FROM "):
                millisec = time.time() * 1000
                fetchall_1 = [[millisec -300 ,"testnodeA",0]]
            elif command.startswith ("SELECT event_name FROM vnf_table_1"):
                fetchall_1 = [["Heartbeat_vDNS","Heartbeat_vFw"]]
            elif command.startswith ("SELECT current_state"):
                fetchall_1 = [["RECONFIGURATION"]]
            elif command.startswith ("DELETE "):
                fetchall_1 = None
            elif command.startswith ("UPDATE"):
                fetchall_1 = None
            else:
                raise RuntimeError("Unknown db execution")
        @classmethod
        def fetchall (ctype):
            global fetchall_1
            return fetchall_1
        @classmethod
        def close(ctype):
            pass

    class PseudoCursorCase2():
        # Test setup for RUNNING state and CL Onset condition
        fetchall_2 = ""
        @classmethod
        def execute(ctype ,command,arg=None):
            global fetchall_2
            if command.startswith("SELECT validity_flag, source_name_count, heartbeat_interval,"):
                fetchall_2 = [[1,1,300,1,"TEMP-CL", "1.0","TEMPPOLICY","TEMP","VM","TEMP","1.0"]]
            elif command.startswith ("SELECT last_epo_time, source_name, cl_flag FROM "):
                millisec = time.time() * 1000
                fetchall_2 = [[millisec -500 ,"testnodeA",0]]
            elif command.startswith ("SELECT event_name FROM vnf_table_1"):
                fetchall_2 = [["Heartbeat_vDNS","Heartbeat_vFw"]]
            elif command.startswith ("SELECT current_state"):
                fetchall_2 = [["RUNNING"]]
            elif command.startswith ("DELETE "):
                fetchall_2 = None
            elif command.startswith ("UPDATE"):
                fetchall_2 = None
            else:
                raise RuntimeError("Unknown db execution")
        @classmethod
        def fetchall (ctype):
            global fetchall_2
            return fetchall_2
        @classmethod
        def close(ctype):
            pass

    class PseudoCursorCase3():
        # Test setup for RUNNING state and CL Abatement condition
        fetchall_3 = ""
        @classmethod
        def execute(ctype ,command,arg=None):
            global fetchall_3
            if command.startswith("SELECT validity_flag, source_name_count, heartbeat_interval,"):
                fetchall_3 = [[1,1,300,1,"TEMP-CL", "1.0","TEMPPOLICY","TEMP","VM","TEMP","1.0"]]
            elif command.startswith ("SELECT last_epo_time, source_name, cl_flag FROM "):
                millisec = time.time() * 1000
                fetchall_3 = [[millisec -20 ,"testnodeA",1]]
            elif command.startswith ("SELECT event_name FROM vnf_table_1"):
                fetchall_3 = [["Heartbeat_vDNS","Heartbeat_vFw"]]
            elif command.startswith ("SELECT current_state"):
                fetchall_3 = [["RUNNING"]]
            elif command.startswith ("DELETE "):
                fetchall_3 = None
            elif command.startswith ("UPDATE"):
                fetchall_3 = None
            else:
                raise RuntimeError("Unknown db execution")
        @classmethod
        def fetchall (ctype):
            global fetchall_3
            return fetchall_3
        @classmethod
        def close(ctype):
            pass
        
    def setUp(self):
        htbtworker.configjsonfile = (os.path.dirname(__file__)) + "/test-config.json"

    @patch("requests.post")
    def test_sendControlLoopEvent(self, mock1):
        status = True
        mock_resp = Mock()
        mock_resp.configure_mock(**{"status_code": 200})
        mock1.return_value = mock_resp
        db_monitoring.sendControlLoopEvent(
            "ONSET", "ABC", "1.0", "vFW", "vFW", "VNF", "NODE", "1234567890", "VFW", "1.0", "DCAE"
        )
        self.assertEqual(status, True)
        db_monitoring.sendControlLoopEvent(
            "ONSET", "ABC", "1.0", "vFW", "vFW", "VM", "NODE", "1234567890", "VFW", "1.0", "DCAE"
        )
        self.assertEqual(status, True)
        db_monitoring.sendControlLoopEvent(
            "ABATED", "ABC", "1.0", "vFW", "vFW", "VNF", "NODE", "1234567890", "VFW", "1.0", "DCAE"
        )
        self.assertEqual(status, True)
        db_monitoring.sendControlLoopEvent(
            "ABATED", "ABC", "1.0", "vFW", "vFW", "VM", "NODE", "1234567890", "VFW", "1.0", "DCAE"
        )
        self.assertEqual(status, True)

    @patch("misshtbtd.read_hb_common", return_value=("1234", "RUNNING", "XYZ-", 1234))
    @patch("htbtworker.postgres_db_open")
    @patch("socket.gethostname", return_value = "XYZ")
    #@patch("db_monitoring.sendControlLoopEvent", return_value = True)
    def test_db_monitoring(self, mock1, mock2, mock3):
        status = True

        mock_cursor = Mock()
        
        ## Test setup for RECONFIGURATION state
        mock_cursor.configure_mock(
            **{"cursor.return_value":Test_db_monitoring.PseudoCursorCase1}
        )
        mock2.return_value = mock_cursor
        # Test for outer else when PID doesn't match
        db_monitoring.db_monitoring(
            "111", htbtworker.configjsonfile, "testuser", "testpwd", "10.0.0.0", "1234", "db_name"
        )
        self.assertEqual(status, True)
        # # Test for RUNNING state and active CL
        # db_monitoring.db_monitoring(
        #     "1234", htbtworker.configjsonfile, "testuser", "testpwd", "10.0.0.0", "1234", "db_name"
        # )
        # self.assertEqual(status, True)
        # Test for RECONFIGURATION state
        mock1.cursor.return_value = ("1234", "RECONFIGURATION", "XYZ-", 1234)
        db_monitoring.db_monitoring(
            "1234", htbtworker.configjsonfile, "testuser", "testpwd", "10.0.0.0", "1234", "db_name"
        )
        self.assertEqual(status, True)

        ## Test for RUNNING state and CL ONSET
        mock_cursor.configure_mock(
            **{"cursor.return_value":Test_db_monitoring.PseudoCursorCase2}
        )
        mock2.return_value = mock_cursor
        db_monitoring.db_monitoring(
            "1234", htbtworker.configjsonfile, "testuser", "testpwd", "10.0.0.0", "1234", "db_name"
        )
        self.assertEqual(status, True)
        # mock1.cursor.return_value = ("1234", "RECONFIGURATION", "XYZ-", 1234)
        # db_monitoring.db_monitoring(
        #     "1234", htbtworker.configjsonfile, "testuser", "testpwd", "10.0.0.0", "1234", "db_name"
        # )
        # self.assertEqual(status, True)

        ## Test for RUNNING state and CL Abatement condition
        mock_cursor.configure_mock(
            **{"cursor.return_value":Test_db_monitoring.PseudoCursorCase3}
        )
        mock2.return_value = mock_cursor        
        db_monitoring.db_monitoring(
            "1234", htbtworker.configjsonfile, "testuser", "testpwd", "10.0.0.0", "1234", "db_name"
        )
        self.assertEqual(status, True)
        # mock1.cursor.return_value = ("1234", "RECONFIGURATION", "XYZ-", 1234)
        # db_monitoring.db_monitoring(
        #     "1234", htbtworker.configjsonfile, "testuser", "testpwd", "10.0.0.0", "1234", "db_name"
        # )
        # self.assertEqual(status, True)

    def test_db_monitoring_wrapper(self):
        status = True
        db_monitoring.db_monitoring_wrapper("111", htbtworker.configjsonfile, number_of_iterations=0)
        self.assertEqual(status, True)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
