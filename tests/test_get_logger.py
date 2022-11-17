# ============LICENSE_START=======================================================
# Copyright (c) 2020-2021 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2021 Fujitsu Ltd.
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
import logging
import os
from pathlib import Path

from miss_htbt_service import get_logger

log = logging.getLogger(__name__)


def test_configure_logger():
    # logpath = (os.path.dirname(__file__))+"hb_logs.txt"
    # expected_log_path = Path(logpath)
    expected_log_path = Path("./hb_logs.txt")
    if expected_log_path.exists():
        os.remove(expected_log_path)
    get_logger.configure_logger("")
    log.info("hi there")
    assert expected_log_path.exists()
    os.remove(expected_log_path)


def test_configure_logger_with_name():
    # logpath = (os.path.dirname(__file__))+"hb_htbtworker_logs.txt"
    # expected_log_path = Path(logpath)
    expected_log_path = Path("./hb_htbtworker_logs.txt")
    if expected_log_path.exists():
        os.remove(expected_log_path)
    get_logger.configure_logger("htbtworker")
    log.info("hi there")
    assert expected_log_path.exists()
    os.remove(expected_log_path)
