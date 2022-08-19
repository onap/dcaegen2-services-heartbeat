# ============LICENSE_START=======================================================
# Copyright (c) 2017-2022 AT&T Intellectual Property. All rights reserved.
# Copyright (c) 2019 Pantheon.tech. All rights reserved.
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

# code loosely based on
# https://stackoverflow.com/questions/25369068/python-how-to-unit-test-a-custom-http-request-handler

from miss_htbt_service import check_health

import io


class MockSocket(object):
    def getsockname(self):
        return ("sockname",)


class MockRequest(object):
    _sock = MockSocket()

    def __init__(self, rqtype, path, body=None):
        self._path = path
        self._rqtype = rqtype if rqtype else "GET"
        self._body = body

    def makefile(self, *args, **kwargs):
        if args[0] == "rb":
            if self._rqtype == "GET":
                return io.BytesIO(bytes("%s %s HTTP/1.0" % (self._rqtype, self._path), "utf-8"))
            else:
                return io.BytesIO(
                    bytes(
                        "%s %s HTTP/1.0\r\nContent-Length: %s\r\n\r\n%s"
                        % (self._rqtype, self._path, len(self._body), self._body),
                        "utf-8",
                    )
                )
        elif args[0] == "wb":
            return io.BytesIO(b"")
        else:
            raise ValueError("Unknown file type to make", args, kwargs)

    def sendall(self, bstr):
        pass


class MockServer(object):
    def __init__(self, rqtype, path, ip_port, Handler, body=None):
        handler = Handler(MockRequest(rqtype, path, body), ip_port, self)


def test_check_health_get():
    """
    test the check_health GET and POST handlers using a mock server
    """
    server = MockServer("GET", "/", ("0.0.0.0", 8888), check_health.GetHandler)


def test_check_health_post():
    """
    test the check_health GET and POST handlers using a mock server
    """
    server = MockServer("POST", "/", ("0.0.0.0", 8888), check_health.GetHandler, '{ "health": "" }')
