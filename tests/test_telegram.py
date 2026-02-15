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
