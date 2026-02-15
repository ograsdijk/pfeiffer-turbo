from __future__ import annotations

import socket
import time
from typing import Literal, Optional

import serial

from .errors import PfeifferTransportError, PfeifferUnsupportedTransportOperationError


class BaseTransport:
    """Minimal transport interface used by drive units."""

    supports_serial_reconfigure: bool = False

    def open(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    @property
    def is_open(self) -> bool:
        raise NotImplementedError

    @property
    def timeout_s(self) -> float:
        raise NotImplementedError

    @timeout_s.setter
    def timeout_s(self, value: float) -> None:
        raise NotImplementedError

    def write(self, data: bytes) -> None:
        raise NotImplementedError

    def read_until(self, terminator: bytes, timeout_s: Optional[float] = None) -> bytes:
        raise NotImplementedError

    def flush_input(self) -> None:
        raise NotImplementedError

    def flush_output(self) -> None:
        raise NotImplementedError

    def set_baudrate(self, baudrate: int) -> None:
        raise PfeifferUnsupportedTransportOperationError(
            "Transport does not support runtime baudrate changes."
        )

    def set_parity(self, parity: Literal["N", "O", "E"]) -> None:
        raise PfeifferUnsupportedTransportOperationError(
            "Transport does not support runtime parity changes."
        )


class SerialTransport(BaseTransport):
    """Local serial transport based on pyserial."""

    supports_serial_reconfigure = True

    def __init__(
        self,
        port: str,
        *,
        baudrate: int = 9600,
        timeout_s: float = 0.25,
        bytesize: int = serial.EIGHTBITS,
        parity: str = serial.PARITY_NONE,
        stopbits: int = serial.STOPBITS_ONE,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self._timeout_s = timeout_s
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self._ser: Optional[serial.Serial] = None

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    @timeout_s.setter
    def timeout_s(self, value: float) -> None:
        self._timeout_s = value
        if self._ser is not None and self._ser.is_open:
            self._ser.timeout = value
            self._ser.write_timeout = value

    def open(self) -> None:
        if self._ser is not None and self._ser.is_open:
            return
        try:
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout_s,
                write_timeout=self.timeout_s,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
            )
            self.flush_input()
            self.flush_output()
        except serial.SerialException as exc:
            raise PfeifferTransportError(
                f"Failed opening serial port {self.port}: {exc}"
            ) from exc

    def close(self) -> None:
        if self._ser is not None and self._ser.is_open:
            self._ser.close()

    @property
    def is_open(self) -> bool:
        return bool(self._ser is not None and self._ser.is_open)

    def _require_open(self) -> serial.Serial:
        if self._ser is None or not self._ser.is_open:
            raise PfeifferTransportError("SerialTransport is not open.")
        return self._ser

    def write(self, data: bytes) -> None:
        ser = self._require_open()
        try:
            ser.write(data)
            ser.flush()
        except serial.SerialException as exc:
            raise PfeifferTransportError(f"Serial write failed: {exc}") from exc

    def read_until(self, terminator: bytes, timeout_s: Optional[float] = None) -> bytes:
        ser = self._require_open()
        old_timeout = ser.timeout
        try:
            if timeout_s is not None:
                ser.timeout = timeout_s
            return ser.read_until(terminator)
        except serial.SerialException as exc:
            raise PfeifferTransportError(f"Serial read failed: {exc}") from exc
        finally:
            ser.timeout = old_timeout

    def flush_input(self) -> None:
        self._require_open().reset_input_buffer()

    def flush_output(self) -> None:
        self._require_open().reset_output_buffer()

    def set_baudrate(self, baudrate: int) -> None:
        ser = self._require_open()
        ser.baudrate = baudrate
        self.baudrate = baudrate

    def set_parity(self, parity: Literal["N", "O", "E"]) -> None:
        ser = self._require_open()
        if parity == "N":
            ser.parity = serial.PARITY_NONE
            self.parity = serial.PARITY_NONE
        elif parity == "O":
            ser.parity = serial.PARITY_ODD
            self.parity = serial.PARITY_ODD
        elif parity == "E":
            ser.parity = serial.PARITY_EVEN
            self.parity = serial.PARITY_EVEN
        else:
            raise ValueError("parity must be one of 'N', 'O', 'E'")


class TcpTransport(BaseTransport):
    """TCP socket transport for serial-over-IP devices."""

    def __init__(self, host: str, port: int, timeout_s: float = 0.25) -> None:
        self.host = host
        self.port = port
        self._timeout_s = timeout_s
        self._sock: Optional[socket.socket] = None

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    @timeout_s.setter
    def timeout_s(self, value: float) -> None:
        self._timeout_s = value
        if self._sock is not None:
            self._sock.settimeout(value)

    def open(self) -> None:
        if self._sock is not None:
            return
        try:
            self._sock = socket.create_connection(
                (self.host, self.port), self.timeout_s
            )
            self._sock.settimeout(self.timeout_s)
        except OSError as exc:
            raise PfeifferTransportError(
                f"Failed opening TCP connection {self.host}:{self.port}: {exc}"
            ) from exc

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    @property
    def is_open(self) -> bool:
        return self._sock is not None

    def _require_open(self) -> socket.socket:
        if self._sock is None:
            raise PfeifferTransportError("TcpTransport is not open.")
        return self._sock

    def write(self, data: bytes) -> None:
        sock = self._require_open()
        try:
            sock.sendall(data)
        except OSError as exc:
            raise PfeifferTransportError(f"TCP write failed: {exc}") from exc

    def read_until(self, terminator: bytes, timeout_s: Optional[float] = None) -> bytes:
        sock = self._require_open()
        old_timeout = sock.gettimeout()
        if timeout_s is not None:
            sock.settimeout(timeout_s)

        deadline = None if timeout_s is None else (time.monotonic() + timeout_s)
        chunks = bytearray()

        try:
            while True:
                if deadline is not None and time.monotonic() > deadline:
                    break
                try:
                    chunk = sock.recv(1)
                except socket.timeout:
                    break

                if not chunk:
                    break

                chunks.extend(chunk)
                if chunks.endswith(terminator):
                    break
            return bytes(chunks)
        except OSError as exc:
            raise PfeifferTransportError(f"TCP read failed: {exc}") from exc
        finally:
            sock.settimeout(old_timeout)

    def flush_input(self) -> None:
        sock = self._require_open()
        old_timeout = sock.gettimeout()
        try:
            sock.setblocking(False)
            while True:
                try:
                    if not sock.recv(4096):
                        break
                except BlockingIOError:
                    break
        finally:
            sock.setblocking(True)
            sock.settimeout(old_timeout)

    def flush_output(self) -> None:
        # No output buffer control for plain TCP sockets.
        return
