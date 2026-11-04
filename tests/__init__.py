"""Suite-wide rule: if a test needs the network, the test is wrong.

Importing this package (which unittest and pytest both do before running any
test in it) makes every outbound connection and DNS lookup raise immediately.
"""

import socket


class NetworkAccessError(AssertionError):
    pass


def _refuse(*_args, **_kwargs):
    raise NetworkAccessError("Network access attempted in a test. Use a fake gateway instead.")


import _socket

# Anything that can open a connection, send a datagram, or resolve a name.
for _name in ("connect", "connect_ex", "sendto", "sendmsg"):
    setattr(socket.socket, _name, _refuse)
for _name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
    setattr(socket, _name, _refuse)
    setattr(_socket, _name, _refuse)
socket.create_connection = _refuse
# A raw `_socket.socket` is a C type that cannot be patched: test_suite_is_offline
# forbids importing `_socket` (and subprocess, ssl, ...) from tests instead.
