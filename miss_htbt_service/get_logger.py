# ============LICENSE_START=======================================================
# Copyright (c) 2017-2020 AT&T Intellectual Property. All rights reserved.
# Copyright 2021 Fujitsu Ltd.
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

import logging.handlers

LOG_LEVEL = logging.DEBUG
LOG_FORMAT = '%(asctime)s | %(levelname)5s | %(name)s | %(module)s | %(funcName)s | %(lineno)d | %(message)s'
LOG_MAXSIZE = 10485760 * 5
LOG_BACKUP_COUNT = 10


def configure_logger(proc_name: str) -> None:
    """Configures the module root logger"""

    # Clear handlers
    root = logging.getLogger()
    if root.handlers:
        del root.handlers[:]

    # Add stdout handler
    formatter = logging.Formatter(LOG_FORMAT)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Add rotating log file handler
    if proc_name:
        logfile_path = './hb_%s_logs.txt' % proc_name
    else:
        logfile_path = './hb_logs.txt'
    fhandler = logging.handlers.RotatingFileHandler(logfile_path, maxBytes=LOG_MAXSIZE, backupCount=LOG_BACKUP_COUNT)
    fhandler.setFormatter(formatter)
    root.addHandler(fhandler)
    root.setLevel(LOG_LEVEL)
