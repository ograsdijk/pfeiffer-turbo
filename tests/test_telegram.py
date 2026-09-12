from decimal import Decimal

import pytest

from pfeiffer_turbo.errors import PfeifferProtocolError
from pfeiffer_turbo.parameters import Parameters
from pfeiffer_turbo.telegram import create_telegram, decode_telegram


def _checksum(payload: str) -> str:
    return f"{sum(ord(char) for char in payload) % 256:03d}"


def test_telegram_roundtrip_int_response() -> None:
    response = create_telegram(
        parameter=Parameters.ActualSpd,
        address=1,
        read_write="W",
        data=123,
    )

    decoded = decode_telegram(response.message)
    assert decoded.parameter == Parameters.ActualSpd
    assert decoded.data == 123


def test_telegram_roundtrip_bool_response() -> None:
    response = create_telegram(
        parameter=Parameters.PumpgStatn,
        address=1,
        read_write="W",
        data=True,
    )

    decoded = decode_telegram(response.message)
    assert decoded.parameter == Parameters.PumpgStatn
    assert decoded.data is True


def test_decode_known_raw_response_frame() -> None:
    # Raw response frame (AAA A0 PPP LL D... CCC) for parameter 309 with value 321.
    payload = "0011030906000321"
    message = payload + _checksum(payload)

    decoded = decode_telegram(message)
    assert decoded.address == 1
    assert decoded.action == 1
    assert decoded.parameter == Parameters.ActualSpd
    assert decoded.data == 321


def test_decode_bearing_wear_divides_raw_value_by_100() -> None:
    payload = "0011032906007575"
    message = payload + _checksum(payload)

    decoded = decode_telegram(message)
    assert decoded.parameter == Parameters.BearngWear
    assert decoded.data == 75.75


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("0011031006000058025", 0.58),
        ("0011031006000057024", 0.57),
    ],
)
def test_decode_drv_current_raw_hundredths(message: str, expected: float) -> None:
    decoded = decode_telegram(message)

    assert decoded.parameter == Parameters.DrvCurrent
    assert decoded.data == expected


def test_decode_drv_current_rejects_corrupted_checksum() -> None:
    with pytest.raises(PfeifferProtocolError, match="Checksum incorrect"):
        decode_telegram("0011031006000058999")


@pytest.mark.parametrize(
    ("value", "expected_raw"),
    [
        (0.58, "000058"),
        (75.75, "007575"),
        (1.0, "000100"),
    ],
)
def test_float_serialization_uses_exact_hundredths(
    value: float, expected_raw: str
) -> None:
    telegram = create_telegram(
        parameter=Parameters.DrvCurrent,
        address=1,
        read_write="W",
        data=value,
    )

    assert telegram.message[10:16] == expected_raw


def test_float_serialization_rejects_unrepresentable_value() -> None:
    with pytest.raises(ValueError, match="0.01 resolution"):
        create_telegram(
            parameter=Parameters.DrvCurrent,
            address=1,
            read_write="W",
            data=0.583,
        )


@pytest.mark.parametrize("raw_value", [0, 1, 57, 58, 99, 100, 101, 7575, 999999])
def test_float_hundredths_roundtrip_preserves_raw_integer(raw_value: int) -> None:
    expected_value = Decimal(raw_value) / 100
    telegram = create_telegram(
        parameter=Parameters.DrvCurrent,
        address=1,
        read_write="W",
        data=float(expected_value),
    )

    assert telegram.message[10:16] == f"{raw_value:06d}"
    decoded = decode_telegram(telegram.message)
    assert Decimal(str(decoded.data)) == expected_value


def test_create_query_matches_documented_rotation_speed_request() -> None:
    telegram = create_telegram(
        parameter=Parameters.ActualSpd,
        address=123,
        read_write="R",
    )
    assert telegram.message == "1230030902=?112"


def test_create_write_matches_documented_set_rotation_speed() -> None:
    telegram = create_telegram(
        parameter=Parameters.SetRotSpd,
        address=123,
        read_write="W",
        data=633,
    )
    assert telegram.message == "1231030806000633036"


def test_decode_rejects_too_short_message() -> None:
    try:
        decode_telegram("123")
    except PfeifferProtocolError:
        return

    raise AssertionError("Expected PfeifferProtocolError for too-short telegram")
