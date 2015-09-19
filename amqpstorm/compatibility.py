"""Python 2/3 Compatibility layer."""
__author__ = 'eandersson'

import sys

PYPY = '__pypy__' in sys.builtin_module_names
PYTHON3 = sys.version_info >= (3, 0, 0)

if PYTHON3:
    RANGE = range
else:
    RANGE = xrange


def is_string(obj):
    """Is this a string.

    :param object obj:
    :rtype: bool
    """
    if PYTHON3:
        str_type = (bytes, str)
    else:
        str_type = (bytes, str, unicode)
    return isinstance(obj, str_type)


def is_integer(obj):
    """Is this an integer.

    :param object obj:
    :return:
    """
    if PYTHON3:
        return isinstance(obj, int)
    return isinstance(obj, (int, long))


def is_unicode(obj):
    """Is this a unicode string.

        This always returns False if running on Python 3.

    :param object obj:
    :rtype: bool
    """
    if PYTHON3:
        return False
    return isinstance(obj, unicode)


def try_utf8_decode(value):
    """Try to decode an object.

    :param value:
    :return:
    """
    if not is_string(value):
        return value
    elif PYTHON3 and not isinstance(value, bytes):
        return value
    elif not PYTHON3 and not is_unicode(value):
        return value

    try:
        return value.decode('utf-8')
    except (UnicodeEncodeError, AttributeError):
        pass

    return value


def patch_uri(uri):
    """If a custom uri schema is used with python 2.6 (e.g. amqps),
    it will ignore some of the parsing logic.

        As a work-around for this we change the amqp/amqps schema
        internally to use http/https.

    :param str uri: AMQP Connection string
    :rtype: str
    """
    index = uri.find(':')
    if uri[:index] == 'amqps':
        uri = uri.replace('amqps', 'https', 1)
    elif uri[:index] == 'amqp':
        uri = uri.replace('amqp', 'http', 1)
    return uri
