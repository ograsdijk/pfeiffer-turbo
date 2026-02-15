from typing import Optional

from pfeiffer_turbo import TM700
from pfeiffer_turbo.errors import PfeifferProtocolError
from pfeiffer_turbo.parameters import Parameters
from pfeiffer_turbo.telegram import create_telegram
from pfeiffer_turbo.transport import BaseTransport


class FakeTransport(BaseTransport):
    def __init__(self, responses: list[bytes]) -> None:
        self._responses = responses
        self._writes: list[bytes] = []
        self._open = False

    def open(self) -> None:
        self._open = True

    def close(self) -> None:
        self._open = False

    @property
    def is_open(self) -> bool:
        return self._open

    def write(self, data: bytes) -> None:
        self._writes.append(data)

    def read_until(self, terminator: bytes, timeout_s: Optional[float] = None) -> bytes:
        _ = terminator
        _ = timeout_s
        return self._responses.pop(0)

    def flush_input(self) -> None:
        return

    def flush_output(self) -> None:
        return


def test_tm700_getter_uses_transport() -> None:
    response = (
        create_telegram(
            parameter=Parameters.ActualSpd,
            address=1,
            read_write="W",
            data=321,
        ).message
        + "\r"
    ).encode("ascii")

    transport = FakeTransport([response])
    pump = TM700(address=1, transport=transport)

    assert getattr(pump, "actual_spd") == 321
    assert transport._writes[0].endswith(b"\r")


def test_tm700_start_and_stop() -> None:
    start_response = (
        create_telegram(
            parameter=Parameters.PumpgStatn,
            address=1,
            read_write="W",
            data=True,
        ).message
        + "\r"
    ).encode("ascii")
    stop_response = (
        create_telegram(
            parameter=Parameters.PumpgStatn,
            address=1,
            read_write="W",
            data=False,
        ).message
        + "\r"
    ).encode("ascii")

    transport = FakeTransport([start_response, stop_response])
    pump = TM700(address=1, transport=transport)

    pump.start()
    pump.stop()

    assert len(transport._writes) == 2


def test_query_on_closed_transport_raises() -> None:
    response = (
        create_telegram(
            parameter=Parameters.ActualSpd,
            address=1,
            read_write="W",
            data=321,
        ).message
        + "\r"
    ).encode("ascii")

    transport = FakeTransport([response])
    pump = TM700(address=1, transport=transport)
    pump.close()

    try:
        _ = getattr(pump, "actual_spd")
    except PfeifferProtocolError:
        return

    raise AssertionError(
        "Expected PfeifferProtocolError when querying closed transport"
    )


def test_setter_rejects_invalid_option_value() -> None:
    transport = FakeTransport([])
    pump = TM700(address=1, transport=transport)

    try:
        setattr(pump, "gas_mode", 999)
    except ValueError:
        return

    raise AssertionError("Expected ValueError for invalid gas_mode option")


def test_set_rot_spd_is_writable() -> None:
    response = (
        create_telegram(
            parameter=Parameters.SetRotSpd,
            address=1,
            read_write="W",
            data=600,
        ).message
        + "\r"
    ).encode("ascii")

    transport = FakeTransport([response])
    pump = TM700(address=1, transport=transport)

    setattr(pump, "set_rot_spd", 600)

    written = transport._writes[0].decode("ascii").strip()
    assert written[5:8] == "308"
