# Copyright 2014-2015 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test the server_description module."""

import sys

sys.path[0:0] = [""]

from pymongo.server_type import SERVER_TYPE
from pymongo.ismaster import IsMaster
from pymongo.server_description import ServerDescription
from test import unittest

address = ('localhost', 27017)


def parse_ismaster_response(doc):
    ismaster_response = IsMaster(doc)
    return ServerDescription(address, ismaster_response)


class TestServerDescription(unittest.TestCase):
    def test_unknown(self):
        # Default, no ismaster_response.
        s = ServerDescription(address)
        self.assertEqual(SERVER_TYPE.Unknown, s.server_type)
        self.assertFalse(s.is_writable)
        self.assertFalse(s.is_readable)

    def test_mongos(self):
        s = parse_ismaster_response({'ok': 1, 'msg': 'isdbgrid'})
        self.assertEqual(SERVER_TYPE.Mongos, s.server_type)
        self.assertEqual('Mongos', s.server_type_name)
        self.assertTrue(s.is_writable)
        self.assertTrue(s.is_readable)

    def test_primary(self):
        s = parse_ismaster_response(
            {'ok': 1, 'ismaster': True, 'setName': 'rs'})

        self.assertEqual(SERVER_TYPE.RSPrimary, s.server_type)
        self.assertEqual('RSPrimary', s.server_type_name)
        self.assertTrue(s.is_writable)
        self.assertTrue(s.is_readable)

    def test_secondary(self):
        s = parse_ismaster_response(
            {'ok': 1, 'ismaster': False, 'secondary': True, 'setName': 'rs'})

        self.assertEqual(SERVER_TYPE.RSSecondary, s.server_type)
        self.assertEqual('RSSecondary', s.server_type_name)
        self.assertFalse(s.is_writable)
        self.assertTrue(s.is_readable)

    def test_arbiter(self):
        s = parse_ismaster_response(
            {'ok': 1, 'ismaster': False, 'arbiterOnly': True, 'setName': 'rs'})

        self.assertEqual(SERVER_TYPE.RSArbiter, s.server_type)
        self.assertEqual('RSArbiter', s.server_type_name)
        self.assertFalse(s.is_writable)
        self.assertFalse(s.is_readable)

    def test_other(self):
        s = parse_ismaster_response(
            {'ok': 1, 'ismaster': False, 'setName': 'rs'})

        self.assertEqual(SERVER_TYPE.RSOther, s.server_type)
        self.assertEqual('RSOther', s.server_type_name)

        s = parse_ismaster_response({
            'ok': 1,
            'ismaster': False,
            'secondary': True,
            'hidden': True,
            'setName': 'rs'})

        self.assertEqual(SERVER_TYPE.RSOther, s.server_type)
        self.assertFalse(s.is_writable)
        self.assertFalse(s.is_readable)

    def test_ghost(self):
        s = parse_ismaster_response({'ok': 1, 'isreplicaset': True})

        self.assertEqual(SERVER_TYPE.RSGhost, s.server_type)
        self.assertEqual('RSGhost', s.server_type_name)
        self.assertFalse(s.is_writable)
        self.assertFalse(s.is_readable)

    def test_fields(self):
        s = parse_ismaster_response({
            'ok': 1,
            'ismaster': False,
            'secondary': True,
            'primary': 'a:27017',
            'tags': {'a': 'foo', 'b': 'baz'},
            'maxMessageSizeBytes': 1,
            'maxBsonObjectSize': 2,
            'maxWriteBatchSize': 3,
            'minWireVersion': 4,
            'maxWireVersion': 5,
            'setName': 'rs'})

        self.assertEqual(SERVER_TYPE.RSSecondary, s.server_type)
        self.assertEqual(('a', 27017), s.primary)
        self.assertEqual({'a': 'foo', 'b': 'baz'}, s.tags)
        self.assertEqual(1, s.max_message_size)
        self.assertEqual(2, s.max_bson_size)
        self.assertEqual(3, s.max_write_batch_size)
        self.assertEqual(4, s.min_wire_version)
        self.assertEqual(5, s.max_wire_version)

    def test_default_max_message_size(self):
        s = parse_ismaster_response({
            'ok': 1,
            'ismaster': True,
            'maxBsonObjectSize': 2})

        # Twice max_bson_size.
        self.assertEqual(4, s.max_message_size)

    def test_standalone(self):
        s = parse_ismaster_response({'ok': 1, 'ismaster': True})
        self.assertEqual(SERVER_TYPE.Standalone, s.server_type)

        # Mongod started with --slave.
        s = parse_ismaster_response({'ok': 1, 'ismaster': False})
        self.assertEqual(SERVER_TYPE.Standalone, s.server_type)
        self.assertTrue(s.is_writable)
        self.assertTrue(s.is_readable)

    def test_ok_false(self):
        s = parse_ismaster_response({'ok': 0, 'ismaster': True})
        self.assertEqual(SERVER_TYPE.Unknown, s.server_type)
        self.assertFalse(s.is_writable)
        self.assertFalse(s.is_readable)

    def test_all_hosts(self):
        s = parse_ismaster_response({
            'ok': 1,
            'ismaster': True,
            'hosts': ['a'],
            'passives': ['b:27018'],
            'arbiters': ['c']
        })

        self.assertEqual(
            [('a', 27017), ('b', 27018), ('c', 27017)],
            sorted(s.all_hosts))


if __name__ == "__main__":
    unittest.main()
