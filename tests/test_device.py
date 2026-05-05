from typing import Optional, get_type_hints

import pytest

from pfeiffer_turbo import TC110, TM700
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


def test_tc110_write_only_parameter_can_be_set_and_not_read() -> None:
    response = (
        create_telegram(
            parameter=Parameters.ErrorAckn,
            address=1,
            read_write="W",
            data=True,
        ).message
        + "\r"
    ).encode("ascii")

    pump = TC110(address=1, transport=FakeTransport([response]))

    pump.error_ackn = True

    written = pump.transport._writes[0].decode("ascii").strip()
    assert written[5:8] == "009"
    with pytest.raises(AttributeError, match="write-only"):
        _ = pump.error_ackn


def test_tm700_generated_property_annotations_match_parameter_types() -> None:
    pump = TM700(address=1, transport=FakeTransport([]))
    pumpg_statn = type(pump).pumpg_statn
    set_rot_spd = type(pump).set_rot_spd
    stby_sval = type(pump).stby_sval
    actual_spd = type(pump).actual_spd
    drv_current = type(pump).drv_current
    fw_version = type(pump).fw_version

    assert pumpg_statn.fget is not None
    assert pumpg_statn.fset is not None
    assert get_type_hints(pumpg_statn.fget)["return"] is bool
    assert get_type_hints(pumpg_statn.fset)["value"] is bool

    assert set_rot_spd.fget is not None
    assert set_rot_spd.fset is not None
    assert get_type_hints(set_rot_spd.fget)["return"] is int
    assert get_type_hints(set_rot_spd.fset)["value"] is int

    assert stby_sval.fget is not None
    assert stby_sval.fset is not None
    assert get_type_hints(stby_sval.fget)["return"] is float
    assert get_type_hints(stby_sval.fset)["value"] is float

    assert actual_spd.fget is not None
    assert actual_spd.fset is None
    assert get_type_hints(actual_spd.fget)["return"] is int

    assert drv_current.fget is not None
    assert drv_current.fset is None
    assert get_type_hints(drv_current.fget)["return"] is float

    assert fw_version.fget is not None
    assert fw_version.fset is None
    assert get_type_hints(fw_version.fget)["return"] is str


def test_tc110_write_only_parameter_setter_annotation_matches_parameter_type() -> None:
    pump = TC110(address=1, transport=FakeTransport([]))
    error_ackn = type(pump).error_ackn

    assert error_ackn.fget is not None
    assert error_ackn.fset is not None
    assert "return" not in get_type_hints(error_ackn.fget)
    assert get_type_hints(error_ackn.fset)["value"] is bool


def test_generated_property_validation_still_enforces_parameter_types() -> None:
    pump = TM700(address=1, transport=FakeTransport([]))

    with pytest.raises(TypeError, match="expects bool"):
        pump.pumpg_statn = 1
    with pytest.raises(TypeError, match="expects int"):
        pump.set_rot_spd = True
    with pytest.raises(TypeError, match="expects float"):
        pump.stby_sval = True


def test_generated_float_property_still_accepts_int_and_float_values() -> None:
    int_response = (
        create_telegram(
            parameter=Parameters.StbySval,
            address=1,
            read_write="W",
            data=1.0,
        ).message
        + "\r"
    ).encode("ascii")
    float_response = (
        create_telegram(
            parameter=Parameters.StbySval,
            address=1,
            read_write="W",
            data=1.5,
        ).message
        + "\r"
    ).encode("ascii")

    transport = FakeTransport([int_response, float_response])
    pump = TM700(address=1, transport=transport)

    pump.stby_sval = 1
    pump.stby_sval = 1.5

    assert len(transport._writes) == 2
