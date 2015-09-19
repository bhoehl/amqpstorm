"""AMQP-Storm Uri wrapper for Connection."""
__author__ = 'eandersson'

import logging

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

try:
    import ssl
except ImportError:
    ssl = None

from amqpstorm import compatibility
from amqpstorm.connection import Connection

LOGGER = logging.getLogger(__name__)

if ssl:
    SSL_VERSIONS = {}
    if hasattr(ssl, 'PROTOCOL_TLSv1_2'):
        SSL_VERSIONS['protocol_tlsv1_2'] = ssl.PROTOCOL_TLSv1_2
    if hasattr(ssl, 'PROTOCOL_TLSv1_1'):
        SSL_VERSIONS['protocol_tlsv1_1'] = ssl.PROTOCOL_TLSv1_1
    if hasattr(ssl, 'PROTOCOL_TLSv1'):
        SSL_VERSIONS['protocol_tlsv1'] = ssl.PROTOCOL_TLSv1
    if hasattr(ssl, 'PROTOCOL_SSLv3'):
        SSL_VERSIONS['protocol_sslv3'] = ssl.PROTOCOL_SSLv3

    SSL_CERT_MAP = {
        'cert_none': ssl.CERT_NONE,
        'cert_optional': ssl.CERT_OPTIONAL,
        'cert_required': ssl.CERT_REQUIRED
    }

    SSL_OPTIONS = [
        'keyfile',
        'certfile',
        'cert_reqs',
        'ssl_version',
        'ca_certs'
    ]


class UriConnection(Connection):
    """Wrapper of the Connection class that takes the AMQP uri schema."""

    def __init__(self, uri, lazy=False):
        """Create a new Connection instance using an AMQP Uri string.

            e.g.
                amqp://guest:guest@localhost:5672/%2F?heartbeat=60
                amqps://guest:guest@localhost:5671/%2F?heartbeat=60

        :param str uri: AMQP Connection string
        """
        uri = compatibility.patch_uri(uri)
        parsed_uri = urlparse.urlparse(uri)
        use_ssl = parsed_uri.scheme == 'https'
        hostname = parsed_uri.hostname or 'localhost'
        port = parsed_uri.port or 5672
        username = parsed_uri.username or 'guest'
        password = parsed_uri.password or 'guest'
        kwargs = self._parse_uri_options(parsed_uri, use_ssl, lazy)
        super(UriConnection, self).__init__(hostname, username,
                                            password, port,
                                            **kwargs)

    def _parse_uri_options(self, parsed_uri, use_ssl, lazy):
        """Parse the uri options.

        :param parsed_uri:
        :param bool use_ssl:
        :return:
        """
        kwargs = urlparse.parse_qs(parsed_uri.query)
        options = {
            'ssl': use_ssl,
            'virtual_host': urlparse.unquote(parsed_uri.path[1:]) or '/',
            'heartbeat': int(kwargs.get('heartbeat', [60])[0]),
            'timeout': int(kwargs.get('timeout', [30])[0]),
            'lazy': lazy
        }
        if ssl and use_ssl:
            options['ssl_options'] = self._parse_ssl_options(kwargs)
        return options

    def _parse_ssl_options(self, ssl_kwargs):
        """Parse SSL Options.

        :param ssl_kwargs:
        :rtype: dict
        """
        ssl_options = {}
        for key in ssl_kwargs:
            if key not in SSL_OPTIONS:
                continue
            if 'ssl_version' in key:
                value = self._get_ssl_version(ssl_kwargs[key][0])
            elif 'cert_reqs' in key:
                value = self._get_ssl_validation(ssl_kwargs[key][0])
            else:
                value = ssl_kwargs[key][0]
            ssl_options[key] = value
        return ssl_options

    def _get_ssl_version(self, value):
        """Get the SSL Version.

        :param str value:
        :return: SSL Version
        """
        return self._get_ssl_attribute(value, SSL_VERSIONS, ssl.PROTOCOL_TLSv1,
                                       'ssl_options: ssl_version \'%s\' not '
                                       'found falling back to PROTOCOL_TLSv1.')

    def _get_ssl_validation(self, value):
        """Get the SSL Validation option.

        :param str value:
        :return: SSL Certificate Options
        """
        return self._get_ssl_attribute(value, SSL_CERT_MAP, ssl.CERT_NONE,
                                       'ssl_options: cert_reqs \'%s\' not '
                                       'found falling back to CERT_NONE.')

    @staticmethod
    def _get_ssl_attribute(value, mapping, default_value, warning_message):
        """Get the SSL attribute based on the mapping.

            If no valid attribute can be found, fall-back on default and
            display a warning.

        :param str value:
        :param dict mapping: Dictionary based mapping
        :param default_value: Default fall-back value
        :param str warning_message: Warning message
        :return:
        """
        for key in mapping:
            if not key.endswith(value.lower()):
                continue
            return mapping[key]
        LOGGER.warning(warning_message, value)
        return default_value
