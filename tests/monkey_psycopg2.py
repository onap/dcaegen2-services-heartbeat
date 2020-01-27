# ============LICENSE_START====================================================
# =============================================================================
# Copyright (c) 2017-2020 AT&T Intellectual Property. All rights reserved.
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

import psycopg2

# These FORCE variables are set by monkey_psycopg2.monkey_reset_forces().
# If set, they will cause a connection failure, cursor failure, execute failure,
# commit failure, and close failure, respectively.
FORCE_CONNECT_FAILURE = False
FORCE_CURSOR_FAILURE = False
FORCE_EXECUTE_FAILURE = False
FORCE_COMMIT_FAILURE = False
FORCE_CLOSE_FAILURE = False

# This variable is used by monkey_psycopg2.monkey_set_defaults(multiDbInfo)
# to set up default values to be returned by cursors statements.
DEFAULT_MULTI_DBINFO = { }

class MockConn(object):
    """
    mock Connection interface returned by psycopg2.connect()
    """

    def __init__(self, dbInfo = None):
        self.curCmd = None
        self.curCursor = None
        self.monkey_setDbInfo(dbInfo)

    def monkey_setDbInfo(self, dbInfo):
        """
        Set up a set of defaults for the cursors on "select" statements.
        The outer scope is a string that will be matched against the currently-active 
        select statement being executed.
        If there is a match, the specified values are returned by the cursor.
        dbconn.monkey_setDbInfo({
            "hb_common": [
                [ 1, "sn1", 31, "st1" ],
                [ 2, "sn2", 32, "st2" ]
            ]
        })
        """
        self.dbInfo = dbInfo

    def commit(self):
        """
        mock commit.
        Do nothing unless FORCE_COMMIT_FAILURE is set.

        Will raise an exception if value of 'FORCE_COMMIT_FAILURE' is true.
        Used to force failure for certain code paths.
        """
        if FORCE_COMMIT_FAILURE:
            raise psycopg2.DatabaseError(f"Unable to commit: force_commit_failure=<{FORCE_COMMIT_FAILURE}>")
    
    def close(self):
        """
        mock close
        Do nothing unless FORCE_CLOSE_FAILURE is set.

        Will raise an exception if value of 'FORCE_CLOSE_FAILURE' is true.
        Used to force failure for certain code paths.
        """
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

        Will raise an exception if value of 'FORCE_CURSOR_FAILURE' is true.
        Used to force failure for certain code paths.
        """
        if FORCE_CURSOR_FAILURE:
            raise psycopg2.DatabaseError(f"Unable to return cursor: force_cursor_failure=<{FORCE_CURSOR_FAILURE}>")

        print(f"cursor()")
        self.curCursor = None
        return self

    def execute(self, cmd, args = None):
        """
        mock execute

        Will raise an exception if value of 'FORCE_EXECUTE_FAILURE' is true.
        Used to force failure for certain code paths.

        A side affect is that the cursor's values will be set based on a match
        with the command (lower-cased) being executed.
        """
        # pylint: disable=global-statement,no-self-use

        print(f"execute({cmd},{args})")
        self.curCmd = cmd
        if FORCE_EXECUTE_FAILURE:
            raise Exception("postgres execute command throwing exception. cmd=<{}>".format(cmd))

        if self.dbInfo:
            curCmdLower = cmd.lower()
            for cmd, val in self.dbInfo.items():
                print(f"cmd={cmd}, val={val}")
                if cmd in curCmdLower:
                    self.curCursor = val
                    break

    def fetchone(self):
        """
        return a single row from the current cursor
        """
        if not self.curCursor:
            print(f"fetchone() returning None")
            return None
        print(f"fetchone() returning {self.curCursor[0]}")
        return self.curCursor[0]

    def fetchall(self):
        """
        return all rows from the current cursor
        """
        if not self.curCursor:
            print(f"fetchall() returning None")
            return None
        print(f"fetchall() returning {self.curCursor}")
        return self.curCursor

def monkey_reset_forces(connect=False, cursor=False, execute=False, commit=False, close=False):
    print(f"monkey_reset_forces({connect}, {cursor}, {execute}, {commit}, {close})")
    global FORCE_CONNECT_FAILURE
    FORCE_CONNECT_FAILURE = connect
    global FORCE_CURSOR_FAILURE
    FORCE_CURSOR_FAILURE = cursor
    global FORCE_EXECUTE_FAILURE
    FORCE_EXECUTE_FAILURE = cursor
    global FORCE_COMMIT_FAILURE
    FORCE_COMMIT_FAILURE = commit
    global FORCE_CLOSE_FAILURE
    FORCE_CLOSE_FAILURE = close

def monkey_set_defaults(multiDbInfo):
    """
    Set up a set of defaults for the cursors on "select" statements.
    The outer scope gives a database name.
    The next level is a string that will be matched against the currently-active 
    select statement being executed.
    If both match, the specified values are returned by the cursor.
    monkey_psycopg2.monkey_set_defaults({
        "testdb1": {
            "hb_common": [
                [ 1, "sn1", 31, "st1" ],
                [ 2, "sn2", 32, "st2" ]
            ]
        }
    })
    """
    global DEFAULT_MULTI_DBINFO
    DEFAULT_MULTI_DBINFO = multiDbInfo

def monkey_connect(database=None, host=None, port=None, user=None, password=None):
    """
    Mock psycopg2 connection.
    Returns a mock connection. 

    Will raise an exception if value of 'FORCE_CONNECT_FAILURE' is true.
    (Used to force failure for certain code paths.)

    Also set up any DbInfo values, based on the database name.
    (See monkey_set_defaults(), which must have been called prior to this being invoked.)
    """
    if FORCE_CONNECT_FAILURE:
        raise Exception("Unable to connect to the database. password=<{}> force_connect_failure=<{}>".format(password, FORCE_CONNECT_FAILURE))

    if database in DEFAULT_MULTI_DBINFO:
        return MockConn(DEFAULT_MULTI_DBINFO[database])
    else:
        return MockConn()
