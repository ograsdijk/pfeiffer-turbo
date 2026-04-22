from dataclasses import dataclass, field
from typing import Union, cast

from .errors import PfeifferProtocolError
from .parameters import DataLength, DataType, Parameters, parameters

# pfeiffer telegram has the following format:
# a2 a1 a0 | * 0 | n2 n1 n0 | l1 l0 | dn ... d0 | c2 c1 c0 | \r
# a2 a1 a0 = address, group address or global address
# * action, 0 for request, 1 for command or return from device
# n2 n1 n0 = pfeiffer vacuum parameter numbers
# l1 l0 = data length
# dn ... d0 = data return
# c2 c1 c0 checksum, sum of a2 to d0 modulo 256


@dataclass
class Telegram:
    address: int
    action: int
    parameter: Parameters
    data: Union[bool, str, int, float]
    data_type: DataType = field(init=False)
    message: str = field(init=False)
    data_length: int = field(init=False)
    checksum: int = field(init=False)

    def __post_init__(self):
        parameter_desc = parameters[self.parameter]

        # check if its a command/return message (1) or a query message (0)
        if self.action == 1:
            self.data_type = parameter_desc.data_type
        else:
            self.data_type = DataType.QUERY

        self.data_length = getattr(DataLength, self.data_type.name)

        pre_checksum_message = self._generate_payload()
        self.checksum = self._checksum(pre_checksum_message)

        self.message = pre_checksum_message + f"{self.checksum:03d}"

    def _generate_payload(self) -> str:
        data = self.data

        # check if its a command/return message (1) or a query message (0)
        if self.action == 1:
            if self.data_type == DataType.FLOAT:
                _data = str(int(cast(float, data) * 100))
            elif self.data_type == DataType.BOOL:
                _data = str(int(cast(bool, data))) * self.data_length
            else:
                _data = str(data)
        else:
            _data = str(data)

        message = (
            f"{self.address:03d}{self.action}0{self.parameter.value:03d}"
            f"{self.data_length:02d}"
        )
        if self.data_length != 0:
            message += _data.zfill(self.data_length)
        return message

    def _checksum(self, telegram: str) -> int:
        telegram = telegram.strip()
        return sum([ord(char) for char in telegram]) % 256


def create_telegram(
    parameter: Parameters,
    address: int,
    read_write: str = "R",
    data: Union[bool, str, int, float] = "=?",
) -> Telegram:
    """
    Construct a Telegram to send to a Pfeiffer turbo drive unit

    Args:
        parameter (Parameters): parameter type
        address (int): drive unit address
        read_write (str, optional): specify read or write action. Defaults to "R".
        data (optional): data to send to drive unit.
                        Defaults to Optional[Union[str, int, float]].

    Returns:
        Telegram: Telegram to send to drive unit.
    """
    if read_write == "R":
        telegram = Telegram(
            address=address,
            action=0,
            parameter=parameter,
            data="=?",
        )
    elif read_write == "W":
        telegram = Telegram(
            address=address,
            action=1,
            parameter=parameter,
            data=data,
        )
    else:
        raise ValueError("read_write has to be 'R' or 'W'")
    return telegram


def decode_telegram(message: str) -> Telegram:
    """
    Decode a string received from a Pfeiffer turbo drive unit into a Telegram

    Args:
        message (str): message from Pfeiffer turbo drive unit

    Raises:
        ValueError: Cannot decode boolean datatype
        ValueError: Checksum incorrect

    Returns:
        Telegram: Telegram containing all the message information
    """
    message = message.strip()
    if len(message) < 13:
        raise PfeifferProtocolError(
            f"Telegram too short: expected at least 13 chars, got {len(message)}"
        )

    try:
        address = int(message[:3])
        action = int(message[3])
    except ValueError as exc:
        raise PfeifferProtocolError(
            "Invalid address/action fields in telegram"
        ) from exc

    if action not in (0, 1):
        raise PfeifferProtocolError(f"Invalid action field: {action}")

    if message[4] != "0":
        raise PfeifferProtocolError(f"Invalid reserved field: {message[4]!r}")

    try:
        parameter = Parameters(int(message[5:8]))
        data_length = int(message[8:10])
    except (ValueError, KeyError) as exc:
        raise PfeifferProtocolError(
            "Invalid parameter/data-length fields in telegram"
        ) from exc

    expected_len = 3 + 1 + 1 + 3 + 2 + data_length + 3
    if len(message) != expected_len:
        raise PfeifferProtocolError(
            f"Telegram length mismatch: expected {expected_len}, got {len(message)}"
        )

    data = message[10 : 10 + data_length]
    try:
        checksum = int(message[10 + data_length : 10 + data_length + 3])
    except ValueError as exc:
        raise PfeifferProtocolError("Invalid checksum field in telegram") from exc

    data_type = parameters[parameter].data_type

    _data: Union[bool, str, int, float]
    if data_type == DataType.FLOAT:
        _data = float(data) / 100
    elif data_type == DataType.BOOL:
        if data == "1" * data_length:
            _data = True
        elif data == "0" * data_length:
            _data = False
        else:
            raise PfeifferProtocolError(f"Cannot decode {data} as boolean")
    elif data_type in [DataType.INT, DataType.SHORT]:
        _data = int(data)
    else:
        _data = data

    telegram = Telegram(address=address, action=action, parameter=parameter, data=_data)

    if checksum != telegram.checksum:
        raise PfeifferProtocolError("Checksum incorrect")

    return telegram
