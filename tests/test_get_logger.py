# ============LICENSE_START=======================================================
# Copyright (c) 2020 AT&T Intellectual Property. All rights reserved.
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

from miss_htbt_service import get_logger

import os

def test_get_logger():
    try:
        os.remove("hb_logs.txt")
    except:
        pass
    log = get_logger.get_logger()
    log.info("hi there")

def test_get_logger_node():
    try:
        os.remove("hb_logs.txt")
    except:
        pass
    log = get_logger.get_logger("node")
    log.info("hi there node")
