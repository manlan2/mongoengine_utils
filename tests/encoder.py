#!/usr/bin/env python
# coding=utf-8

"""Encodig tests."""

import re
from unittest import TestCase
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from bson.py3compat import PY3

from mongoengine_goodjson import GoodJSONEncoder


class NormalStuffEncodingTest(TestCase):
    """Normal stuff should be encoded."""

    def setUp(self):
        """Setup function."""
        self.encoder = GoodJSONEncoder()
        self.data = "test"

    @patch("json.JSONEncoder.default")
    def test_json_encoder(self, default):
        """The default json default function should be called."""
        self.encoder.default(self.data)
        default.assert_called_once_with(self.data)

    @patch("json.JSONEncoder.encode")
    def test_json_encode_class(self, encode):
        """The default json encode function should be called."""
        self.encoder.encode(self.data)
        encode.assert_called_once_with(self.data)


class ObjectIdEncodeTest(TestCase):
    """Object ID Encoding test."""

    def setUp(self):
        """Setup function."""
        from bson import ObjectId
        self.encoder = GoodJSONEncoder()
        self.oid = ObjectId()

    def test_object_id(self):
        """Encoder should return the object id as str."""
        result = self.encoder.default(self.oid)
        self.assertEqual(result, str(self.oid))


class DatetimeISOEncodeTest(TestCase):
    """datetime encoding test."""

    def setUp(self):
        """Setup funciton."""
        from datetime import datetime
        self.now = datetime.utcnow()
        self.encoder = GoodJSONEncoder()

    def test_datetime(self):
        """Datetime should be serialized into ISOFormat."""
        self.assertEqual(
            self.encoder.default(self.now), self.now.isoformat()
        )


class DatetimeEpochEncodeTest(TestCase):
    """datetime encoding test."""

    def setUp(self):
        """Setup funciton."""
        from datetime import datetime
        self.now = datetime.utcnow()
        self.encoder = GoodJSONEncoder(epoch_mode=True)

    def test_datetime(self):
        """Datetime should be serialized into ISOFormat."""
        from calendar import timegm
        self.assertEqual(
            self.encoder.default(self.now),
            int(
                (timegm(self.now.timetuple()) * 1000) +
                (self.now.microsecond / 1000)
            )
        )


class DBRefEncodingTestBase(TestCase):
    """DBRef test case base."""

    def setUp(self):
        """Setup function."""
        from bson.dbref import DBRef
        from bson import ObjectId
        self.DBRef = DBRef
        self.encoder = GoodJSONEncoder()
        self.custom_argument = {
            "test key %d" % counter: "Test value %d" % counter
            for counter in range(3)
        }
        self.collection_name = "test.collection"
        self.doc_id = ObjectId()
        self.database = "test.db"


class DBRefEncodeWithDBTest(DBRefEncodingTestBase):
    """DBRef with external database encoding test."""

    def setUp(self):
        """Setup function."""
        super(DBRefEncodeWithDBTest, self).setUp()
        self.data = self.DBRef(
            self.collection_name, self.doc_id,
            database=self.database, **self.custom_argument
        )
        self.expected_result = {
            "collection": self.collection_name,
            "db": self.database,
            "id": self.encoder.default(self.doc_id)
        }
        self.expected_result.update(self.custom_argument)

    def test_dbref(self):
        """The encoded dbref should be expected result."""
        self.assertDictEqual(
            self.expected_result, self.encoder.default(self.data)
        )


class DBRefEncodeWithoutDBTest(DBRefEncodingTestBase):
    """DBRef without external database encoding test."""

    def setUp(self):
        """Setup function."""
        super(DBRefEncodeWithoutDBTest, self).setUp()
        self.data = self.DBRef(
            self.collection_name, self.doc_id,
            **self.custom_argument
        )
        self.expected_result = {
            "collection": self.collection_name,
            "id": self.encoder.default(self.doc_id)
        }
        self.expected_result.update(self.custom_argument)

    def test_dbref(self):
        """The encoded dbref should be expected result."""
        self.assertDictEqual(
            self.expected_result, self.encoder.default(self.data)
        )


class RegexNativeWithoutFlagTest(TestCase):
    """Native Regex test class."""

    def setUp(self):
        """Setup function."""
        self.encoder = GoodJSONEncoder()
        self.regex = re.compile("^[0-9]+$")
        self.expected_result = {
            "regex": self.regex.pattern
        }

    def test_regex(self):
        """The encoded value should be the expected value."""
        self.assertDictContainsSubset(
            self.expected_result, self.encoder.default(self.regex)
        )


class BSONRegexWithoutFlagTest(RegexNativeWithoutFlagTest):
    """SON-wrapped regex test class."""

    def setUp(self):
        """Setup function."""
        from bson import Regex
        super(BSONRegexWithoutFlagTest, self).setUp()
        self.regex = Regex.from_native(self.regex)


regex_flags = {
    "i": re.IGNORECASE,
    "l": re.LOCALE,
    "m": re.MULTILINE,
    "s": re.DOTALL,
    "u": re.UNICODE,
    "x": re.VERBOSE
}

for (flag_str, flag) in regex_flags.items():
    class RegexNativeWithFlagTest(RegexNativeWithoutFlagTest):
        """Native regex with flag test (individual)."""

        def setUp(self):
            """Setup class."""
            super(RegexNativeWithFlagTest, self).setUp()
            self.regex = re.compile(self.regex.pattern, flag)
            self.actual_result = self.encoder.default(self.regex)

        def test_regex(self):
            """The encoded value should be expected value."""
            self.assertDictContainsSubset(
                self.expected_result, self.actual_result,
            )

        def test_flags(self):
            """The flag should be proper."""
            self.assertIn(flag_str, self.actual_result["flags"])

    class BSONRegexWitFlagTest(RegexNativeWithFlagTest):
        """BSON regex with flag test (individual)."""

        def setUp(self):
            """Setup class."""
            super(BSONRegexWitFlagTest, self).setUp()
            from bson import Regex
            self.regex = Regex.from_native(self.regex)


class RegexNativeWithAllFlagsTest(RegexNativeWithoutFlagTest):
    """Native regex with flag test (ALL)."""

    def setUp(self):
        """Setup class."""
        super(RegexNativeWithAllFlagsTest, self).setUp()
        self.regex = re.compile(
            self.regex.pattern,
            re.IGNORECASE | re.LOCALE | re.MULTILINE |
            re.DOTALL | re.UNICODE | re.VERBOSE
        )
        self.actual_result = self.encoder.default(self.regex)

    def test_regex(self):
        """The encoded value should be expected value."""
        self.assertDictContainsSubset(
            self.expected_result, self.actual_result,
        )

    def test_flags(self):
        """The flag should be proper."""
        flags = regex_flags.keys()
        self.assertEqual(len(self.actual_result["flags"]), len(flags))
        for flag in flags:
            self.assertIn(flag, self.actual_result["flags"])


class BSONRegexWitAllFlagsTest(RegexNativeWithAllFlagsTest):
    """BSON regex with flag test (individual)."""

    def setUp(self):
        """Setup class."""
        super(BSONRegexWitAllFlagsTest, self).setUp()
        from bson import Regex
        self.regex = Regex.from_native(self.regex)


class MinKeyTest(TestCase):
    """MinKey test."""

    def setUp(self):
        """Setup class."""
        from bson.min_key import MinKey
        self.encoder = GoodJSONEncoder()
        self.data = MinKey()

    def test_minkey(self):
        """Minkey should be encoded."""
        self.assertDictEqual(
            {"minKey": True},
            self.encoder.default(self.data)
        )


class MaxKeyTest(TestCase):
    """MaxKey test."""

    def setUp(self):
        """Setup class."""
        from bson.max_key import MaxKey
        self.encoder = GoodJSONEncoder()
        self.data = MaxKey()

    def test_minkey(self):
        """Maxkey should be encoded."""
        self.assertDictEqual(
            {"maxKey": True},
            self.encoder.default(self.data)
        )


class TimeStampTest(TestCase):
    """Timestamp test."""

    def setUp(self):
        """Setup class."""
        from bson.timestamp import Timestamp
        from datetime import datetime
        from calendar import timegm
        from random import randint
        self.expected = {
            "time": timegm(datetime.utcnow().timetuple()),
            "inc": randint(0, 4294967295)
        }
        self.encoder = GoodJSONEncoder()
        self.data = Timestamp(**self.expected)

    def test_timestamp(self):
        """The timestamp should be expected value."""
        self.assertDictEqual(self.expected, self.encoder.default(self.data))


class CodeTest(TestCase):
    """Code test."""

    def setUp(self):
        """Setup class."""
        from bson.code import Code
        self.encoder = GoodJSONEncoder()
        self.expected = {
            "code": "console.log('HAAAAAAAAHHHH!!!')",
            "scope": {"data": "test"}
        }
        self.data = Code(**self.expected)

    def test_code(self):
        """Code should be expected value."""
        self.assertDictEqual(self.expected, self.encoder.default(self.data))


class BinaryTest(TestCase):
    """Binary test."""

    def setUp(self):
        """Setup class."""
        from bson.binary import Binary, BINARY_SUBTYPE
        from base64 import b64encode

        self.encoder = GoodJSONEncoder()
        self.test_str = "This is a test"
        self.expected = {
            "data": b64encode(self.test_str.encode("utf-8")).decode("utf-8"),
            "type": BINARY_SUBTYPE
        }
        self.data = Binary(self.test_str.encode("utf-8"))

    def test_binary(self):
        """Binary data should be encoded properly."""
        self.assertDictEqual(self.expected, self.encoder.default(self.data))


class UUIDTest(TestCase):
    """UUID Test."""

    def setUp(self):
        """Setup class."""
        from uuid import uuid5, NAMESPACE_DNS
        self.encoder = GoodJSONEncoder()
        self.data = uuid5(NAMESPACE_DNS, "This is a test")
        self.expected = str(self.data)

    def test_uuid(self):
        """The uuid should converted into str."""
        self.assertEqual(self.expected, self.encoder.default(self.data))


if PY3:
    class BytesTest(TestCase):
        """Bytes test."""

        def setUp(self):
            """Setup class."""
            from base64 import b64encode
            self.encoder = GoodJSONEncoder()
            self.data = b"This is a test."
            self.expected = {
                "data": b64encode(self.data).decode("utf-8"),
                "type": 0
            }

        def test_bytes(self):
            """The given bytes should be proper."""
            self.assertDictEqual(
                self.expected, self.encoder.default(self.data)
            )
