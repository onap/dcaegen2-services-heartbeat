# ============LICENSE_START=======================================================
# Copyright (c) 2020-2022 AT&T Intellectual Property. All rights reserved.
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

from miss_htbt_service import htbtworker

import os
import tempfile
import json


def run_test(i):
    """
    read_json_file() opens the file CWD/prefix/test{j}.json and returns the json value found there
    """
    j = i + 1
    tdir = tempfile.TemporaryDirectory()
    prefix = "../../../../../../../../../../../../.."
    pdir = f"{prefix}{tdir.name}"
    fname = f"{tdir.name}/test{j}.json"
    with open(fname, "w") as fp:
        json.dump({"test": i}, fp)
    assert os.path.isfile(f"{tdir.name}/test{j}.json")
    assert os.path.isfile(f"{pdir}/test{j}.json")
    cfg = htbtworker.read_json_file(i, prefix=pdir)
    assert cfg["test"] == i


def test_read_json_file_0():
    run_test(0)


def test_read_json_file_1():
    run_test(1)


def test_read_json_file_2():
    run_test(2)
