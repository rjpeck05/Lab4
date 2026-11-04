"""Suite-wide rule: if a test needs the network, the test is wrong.

Importing this package (which unittest and pytest both do before running any
test in it) makes every outbound connection and DNS lookup raise immediately.
"""

import socket


class NetworkAccessError(AssertionError):
    pass


def _refuse(*_args, **_kwargs):
    raise NetworkAccessError("Network access attempted in a test. Use a fake gateway instead.")


socket.socket.connect = _refuse
socket.socket.connect_ex = _refuse
socket.getaddrinfo = _refuse
socket.create_connection = _refuse
