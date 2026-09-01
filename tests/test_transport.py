import socket

import pytest

import pfeiffer_turbo.transport as transport_module
from pfeiffer_turbo.errors import PfeifferTransportError
from pfeiffer_turbo.transport import TcpTransport


class FakeSocket:
    def __init__(self, reads=(), timeout=0.25, send_error=None):
        self.reads = list(reads)
        self.timeout = timeout
        self.send_error = send_error
        self.send_calls = 0
        self.closed = False
        self.shutdown_calls = 0

    def settimeout(self, value):
        self.timeout = value

    def gettimeout(self):
        return self.timeout

    def setblocking(self, enabled):
        self.timeout = None if enabled else 0.0

    def recv(self, _size):
        item = self.reads.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def sendall(self, _data):
        self.send_calls += 1
        if self.send_error is not None:
            raise self.send_error

    def shutdown(self, _how):
        self.shutdown_calls += 1

    def close(self):
        self.closed = True


def opened_transport(sock):
    transport = TcpTransport("127.0.0.1", 1234)
    transport._sock = sock
    return transport


@pytest.mark.parametrize("failure", [b"", ConnectionResetError("reset"), OSError("broken")])
def test_fatal_read_invalidates_socket(failure):
    sock = FakeSocket([failure])
    transport = opened_transport(sock)

    with pytest.raises(PfeifferTransportError):
        transport.read_until(b"\r")

    assert transport.is_open is False
    assert sock.closed is True


def test_fatal_write_invalidates_without_retry():
    sock = FakeSocket(send_error=ConnectionResetError("reset"))
    transport = opened_transport(sock)

    with pytest.raises(PfeifferTransportError):
        transport.write(b"command")

    assert sock.send_calls == 1
    assert transport.is_open is False
    assert sock.closed is True


def test_write_timeout_invalidates_without_retry():
    sock = FakeSocket(send_error=TimeoutError("timed out"))
    transport = opened_transport(sock)

    with pytest.raises(PfeifferTransportError):
        transport.write(b"command")

    assert sock.send_calls == 1
    assert transport.is_open is False
    assert sock.closed is True


def test_open_after_failure_uses_fresh_socket(monkeypatch):
    failed = FakeSocket([b""])
    fresh = FakeSocket()
    transport = opened_transport(failed)

    with pytest.raises(PfeifferTransportError):
        transport.read_until(b"\r")

    calls = []

    def create_connection(address, timeout):
        calls.append((address, timeout))
        return fresh

    monkeypatch.setattr(socket, "create_connection", create_connection)
    transport.open()

    assert calls == [(('127.0.0.1', 1234), 0.25)]
    assert transport.is_open is True
    assert transport._sock is fresh


def test_bounded_timeout_returns_partial_data_and_keeps_socket_open():
    sock = FakeSocket([b"a", socket.timeout("timed out")], timeout=0.25)
    transport = opened_transport(sock)

    assert transport.read_until(b"\r", timeout_s=0.1) == b"a"
    assert transport.is_open is True
    assert sock.timeout == 0.25


def test_flush_eof_invalidates_socket():
    sock = FakeSocket([b""])
    transport = opened_transport(sock)

    with pytest.raises(PfeifferTransportError):
        transport.flush_input()

    assert transport.is_open is False
    assert sock.closed is True


def test_flush_stops_at_byte_limit_under_continuous_input(monkeypatch):
    class ContinuousSocket(FakeSocket):
        def __init__(self):
            super().__init__(timeout=0.25)
            self.recv_calls = 0

        def recv(self, size):
            self.recv_calls += 1
            return b"x" * size

    monkeypatch.setattr(transport_module.time, "monotonic", lambda: 0.0)
    sock = ContinuousSocket()
    transport = opened_transport(sock)

    transport.flush_input()

    assert sock.recv_calls == TcpTransport._FLUSH_MAX_BYTES // 4096
    assert sock.timeout == 0.25
    assert transport.is_open is True
