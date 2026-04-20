"""Re-export pamqp APIs across pamqp 2.x–5.x.

pamqp 3+ removed ``pamqp.specification`` in favor of ``pamqp.commands`` with the
same command class layout. This module maps either layout to the name
``specification`` so the rest of AMQPStorm can keep v2-style imports.

Supported install range: ``pamqp>=2.0.0,<=5.0.0`` (see requirements.txt).
CI pins: 2.3.0, 3.3.0, 4.0.0 as of 2026 (pamqp 5 not yet on PyPI).
"""

from __future__ import absolute_import

_SUPPORTED_RANGE = 'pamqp>=2.0.0,<=5.0.0'


def _fail(exc, msg):
    raise ImportError(
        '%s AMQPStorm requires %s (%s)' % (msg, _SUPPORTED_RANGE, exc)
    ) from exc


try:
    from pamqp import body as body
    from pamqp import exceptions as exceptions
    from pamqp import frame as frame
    from pamqp import header as header
    from pamqp.heartbeat import Heartbeat
except Exception as err:
    _fail(err, 'Could not import pamqp core modules.')

try:
    from pamqp import specification as specification
except ImportError:
    try:
        from pamqp import commands as specification
    except ImportError as err:
        _fail(err, 'Could not import pamqp specification/commands.')

# v2 exposes AMQPFrameError on specification; v3+ only on exceptions.
if not hasattr(specification, 'AMQPFrameError'):
    specification.AMQPFrameError = exceptions.AMQPFrameError

try:
    from pamqp import ContentHeader
except ImportError:
    from pamqp.header import ContentHeader

try:
    from pamqp import ProtocolHeader
except ImportError:
    from pamqp.header import ProtocolHeader

__all__ = [
    'ContentHeader',
    'Heartbeat',
    'ProtocolHeader',
    'body',
    'exceptions',
    'frame',
    'header',
    'specification',
]
