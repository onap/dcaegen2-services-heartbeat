# ============LICENSE_START====================================================
# =============================================================================
# Copyright (c) 2017 AT&T Intellectual Property. All rights reserved.
# =============================================================================
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
# ============LICENSE_END======================================================

"""

This is a mock psycopg2 module.

"""

import os, psycopg2

FORCE_CONNECT_FAILURE = False
FORCE_CURSOR_FAILURE = False
FORCE_COMMIT_FAILURE = False
FORCE_CLOSE_FAILURE = False
DEFAULT_MULTI_DBINFO = { }

class MockConn(object):
    """
    mock Connection interface returned by psycopg2.connect()
    """

    def __init__(self, dbInfo = None):
        self.curCmd = None
        self.curCursor = None
        self.dbInfo = dbInfo

    def monkey_setDbInfo(self, dbInfo):
        self.dbInfo = dbInfo

    def commit(self):
        """
        mock commit
        """
        global FORCE_COMMIT_FAILURE
        if FORCE_COMMIT_FAILURE:
            raise psycopg2.DatabaseError(f"Unable to commit: force_commit_failure=<{FORCE_COMMIT_FAILURE}>")
    
    def close(self):
        """
        mock close
        """
        global FORCE_CLOSE_FAILURE
        if FORCE_CLOSE_FAILURE:
            raise psycopg2.DatabaseError(f"Unable to close: force_close_failure=<{FORCE_CLOSE_FAILURE}>")

    def __enter__(self):
        """
        method needed to implement a context manager
        """
        return self

    # pylint: disable=redefined-outer-name,redefined-builtin
    def __exit__(self, type, value, traceback):
        """
        method needed to implement a context manager
        """
        pass

    def cursor(self):
        """
        mock cursor
        """
        global FORCE_CURSOR_FAILURE
        if FORCE_CURSOR_FAILURE:
            raise psycopg2.DatabaseError(f"Unable to return cursor: force_cursor_failure=<{FORCE_CURSOR_FAILURE}>")

        print(f"cursor()")
        self.curCursor = None
        return self

    def execute(self, cmd, args = None):
        """
        mock execute
        """
        # pylint: disable=global-statement,no-self-use

        print(f"execute({cmd},{args})")
        self.curCmd = cmd
        if cmd == "BAD SELECT":
            raise Exception("postgres execute command throwing exception. cmd=<{}>".format(cmd))
        if self.dbInfo:
            for cmd, val in self.dbInfo.items():
                print(f"cmd={cmd}, val={val}")
                if cmd in self.curCmd:
                    self.curCursor = val
                    break

    def fetchone(self):
        """
        return a single row from the current cursor
        """
        if not self.curCursor:
            return None
        return self.curCursor[0]

    def fetchall(self):
        """
        return all rows from the current cursor
        """
        if not self.curCursor:
            return None
        return self.curCursor

def monkey_reset_forces(connect=False, cursor=False, commit=False, close=False):
    print(f"monkey_reset_forces({connect}, {cursor}, {commit}, {close})")
    global FORCE_CONNECT_FAILURE
    FORCE_CONNECT_FAILURE = connect
    global FORCE_CURSOR_FAILURE
    FORCE_CURSOR_FAILURE = cursor
    global FORCE_COMMIT_FAILURE
    FORCE_COMMIT_FAILURE = commit
    global FORCE_CLOSE_FAILURE
    FORCE_CLOSE_FAILURE = close


def monkey_psycopg2_set_defaults(multiDbInfo):
    global DEFAULT_MULTI_DBINFO
    DEFAULT_MULTI_DBINFO = multiDbInfo

def monkey_psycopg2_connect(database=None, host=None, port=None, user=None, password=None):
    """
    mock psycopg2 connection
    """
    # pylint: disable=global-statement
    global FORCE_CONNECT_FAILURE
    if password == "badpassword" or FORCE_CONNECT_FAILURE:
        raise Exception("Unable to connect to the database. password=<{}> force_connect_failure=<{}>".format(password, FORCE_CONNECT_FAILURE))
    ret = MockConn()
    if database in DEFAULT_MULTI_DBINFO:
        ret.monkey_setDbInfo(DEFAULT_MULTI_DBINFO[database])
    return ret
