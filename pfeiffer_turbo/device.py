from __future__ import annotations

import re
from typing import Sequence, Union

from .errors import PfeifferProtocolError
from .parameters import Access, DataType, Parameters, parameters
from .telegram import Telegram, create_telegram, decode_telegram
from .transport import BaseTransport, SerialTransport, TcpTransport


def _make_property(parameter: Parameters):
    def function_property(cls: DriveUnit):
        telegram = create_telegram(
            parameter=parameter,
            address=cls.address,
            read_write="R",
        )
        telegram = cls.query(telegram)
        return telegram.data

    return function_property


def _make_setter(parameter: Parameters):
    def function_setter(cls: DriveUnit, value: Union[str, int, float]) -> None:
        validated_value = cls._validate_write_value(parameter, value)
        telegram = create_telegram(
            parameter=parameter,
            address=cls.address,
            read_write="W",
            data=validated_value,
        )
        cls.query(telegram)

    return function_setter


def _make_write_only_getter(parameter: Parameters):
    def function_getter(cls: DriveUnit):
        raise AttributeError(f"Parameter {parameter.name} is write-only")

    return function_getter


class DriveUnit:
    """
    Baseclass for Pfeiffer turbo drive units

    Dynamically generates getters and setters for Pfeiffer vacuum parameters based on
    supported_parameters, a sequence of integers which are then cross referenced against
    implemented parameters shown in Parameters from parameters.py
    """

    def __init__(
        self,
        transport: BaseTransport,
        address: int,
        supported_parameters: Sequence[int],
    ):
        """
        Initialization of the DriveUnit

        Args:
            transport (BaseTransport): openable transport implementation
            address (int): drive unit addresss
            allowed_parameters (Sequence[int]): Sequence of vacuum parameters supported
                                                by the drive unit
        """
        if not (1 <= address <= 255):
            raise ValueError("address must be in range [1, 255]")
        self.address = address

        self.transport = transport
        self.transport.open()

        self._ensure_parameters_created(supported_parameters)

    @classmethod
    def _ensure_parameters_created(cls, supported_parameters: Sequence[int]) -> None:
        generated_ids: set[int] = getattr(cls, "_generated_parameter_ids", set())
        for parameter_id in supported_parameters:
            if parameter_id in generated_ids:
                continue

            parameter = Parameters(parameter_id)
            parameter_desc = parameters[parameter]
            name = "_".join(
                [s for s in re.split("([A-Z][^A-Z]*)", parameter.name) if s]
            ).lower()

            if parameter_desc.access == Access.READ:
                function_property = _make_property(parameter)
                setattr(
                    cls,
                    name,
                    property(
                        fget=function_property,
                        doc=parameter_desc.designation,
                    ),
                )

            elif parameter_desc.access == Access.READ_WRITE:
                function_property = _make_property(parameter)
                function_setter = _make_setter(parameter)

                doc = parameter_desc.designation
                if parameter_desc.options is not None:
                    doc += "\nParameter options are:"
                    for value, desc in parameter_desc.options.items():
                        doc += f"\n{value} : {desc}"

                setattr(
                    cls,
                    name,
                    property(
                        fget=function_property,
                        fset=function_setter,
                        doc=doc,
                    ),
                )

            elif parameter_desc.access == Access.WRITE:
                # write-only parameter: provide setter, getter raises AttributeError
                function_setter = _make_setter(parameter)
                function_getter = _make_write_only_getter(parameter)

                doc = parameter_desc.designation
                if parameter_desc.options is not None:
                    doc += "\nParameter options are:"
                    for value, desc in parameter_desc.options.items():
                        doc += f"\n{value} : {desc}"

                setattr(
                    cls,
                    name,
                    property(
                        fget=function_getter,
                        fset=function_setter,
                        doc=doc,
                    ),
                )

            generated_ids.add(parameter_id)

        setattr(cls, "_generated_parameter_ids", generated_ids)

    def open(self) -> None:
        if not self.transport.is_open:
            self.transport.open()

    def close(self) -> None:
        self.transport.close()

    def __enter__(self) -> DriveUnit:
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def query(self, telegram: Telegram) -> Telegram:
        if not self.transport.is_open:
            raise PfeifferProtocolError(
                "Transport is closed. Call open() before query()."
            )

        self.transport.flush_input()
        self.transport.write((telegram.message + "\r").encode("ascii"))
        response = self.transport.read_until(b"\r")

        if not response:
            raise PfeifferProtocolError("No response received from transport.")

        try:
            return decode_telegram(response.decode("ascii").strip())
        except (UnicodeDecodeError, ValueError) as exc:
            raise PfeifferProtocolError(
                f"Failed to decode telegram response: {response!r}"
            ) from exc

    def _validate_write_value(
        self,
        parameter: Parameters,
        value: Union[str, int, float],
    ) -> Union[str, int, float]:
        info = parameters[parameter]

        if info.access != Access.READ_WRITE:
            raise ValueError(f"Parameter {parameter.name} is not writable")

        normalized: Union[str, int, float]
        if info.data_type == DataType.BOOL:
            if not isinstance(value, bool):
                raise TypeError(f"Parameter {parameter.name} expects bool")
            normalized = value
        elif info.data_type in (DataType.INT, DataType.SHORT):
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"Parameter {parameter.name} expects int")
            normalized = value
        elif info.data_type == DataType.FLOAT:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"Parameter {parameter.name} expects float")
            normalized = float(value)
        elif info.data_type in (DataType.STR, DataType.LONGSTR):
            if not isinstance(value, str):
                raise TypeError(f"Parameter {parameter.name} expects str")
            normalized = value
        else:
            normalized = value

        if info.options is not None:
            if not isinstance(normalized, int):
                raise TypeError(
                    f"Parameter {parameter.name} expects one of {tuple(info.options.keys())}"
                )
            if normalized not in info.options:
                raise ValueError(
                    f"Parameter {parameter.name} value must be one of {tuple(info.options.keys())}"
                )

        if info.min is not None and isinstance(normalized, (int, float)):
            if normalized < info.min:
                raise ValueError(
                    f"Parameter {parameter.name} value {normalized} < min {info.min}"
                )

        if info.max is not None and isinstance(normalized, (int, float)):
            if normalized > info.max:
                raise ValueError(
                    f"Parameter {parameter.name} value {normalized} > max {info.max}"
                )

        return normalized

    def start(self):
        """
        Start the turbo-molecular pump
        """
        self.pumpg_statn = True

    def stop(self):
        """
        Stop the turbo-molecular pump
        """
        self.pumpg_statn = False


class TM700(DriveUnit):
    def __init__(
        self,
        transport: BaseTransport,
        address: int = 1,
    ):
        tm700_supported = {
            1, 2, 10, 12, 13, 19, 23, 24, 27, 28, 30, 35, 36, 37, 38, 45, 46,
            47, 50, 55, 57, 60, 62, 63, 64, 300, 302, 303, 304, 305, 306, 307,
            308, 309, 310, 311, 312, 313, 314, 315, 316, 319, 324, 326, 329, 330,
            336, 342, 346, 349, 354, 358, 360, 361, 362, 363, 364, 365, 366, 367,
            368, 369, 384, 397, 398, 399, 700, 707, 708, 717, 720, 721, 777, 797,
        }
        supported_parameters = tuple(par.value for par in Parameters if par.value in tm700_supported)
        super().__init__(
            transport=transport,
            address=address,
            supported_parameters=supported_parameters,
        )

    @classmethod
    def from_serial(
        cls,
        port: str,
        *,
        address: int = 1,
        baudrate: int = 9600,
        timeout_s: float = 0.25,
    ) -> "TM700":
        return cls(
            transport=SerialTransport(
                port=port,
                baudrate=baudrate,
                timeout_s=timeout_s,
            ),
            address=address,
        )

    @classmethod
    def from_tcp(
        cls,
        host: str,
        port: int,
        *,
        address: int = 1,
        timeout_s: float = 0.25,
    ) -> "TM700":
        return cls(
            transport=TcpTransport(host=host, port=port, timeout_s=timeout_s),
            address=address,
        )


class TC110(DriveUnit):
    """
    Support for Pfeiffer TC 110 electronic drive unit.

    This class exposes the same parameter interface as other drive units. Defaults
    for serial communication (9600 baud, no parity) follow the TC 110 manual.
    """

    def __init__(
        self,
        transport: BaseTransport,
        address: int = 1,
    ):
        # TC 110 supports the Pfeiffer Vacuum parameter set defined in parameters.py.
        # Only a subset of parameters are available on the TC 110
        tc110_supported = {
            1, 2, 4, 9, 10, 12, 17, 19, 23, 24, 25, 26, 27, 30, 35, 36, 37, 38,
            50, 55, 60, 61, 62, 63, 100, 120, 255, 300, 302, 303, 304, 305, 306,
            307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 319, 326, 330, 336,
            342, 346, 349, 354, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369,
            397, 398, 399,
            # Set value and control parameters
            700, 701, 707, 708, 710, 711, 717, 719, 720, 721, 777, 797,
        }
        supported_parameters = tuple(par.value for par in Parameters if par.value in tc110_supported)
        super().__init__(
            transport=transport,
            address=address,
            supported_parameters=supported_parameters,
        )

    @classmethod
    def from_serial(
        cls,
        port: str,
        *,
        address: int = 1,
        baudrate: int = 9600,
        timeout_s: float = 0.25,
    ) -> "TC110":
        return cls(
            transport=SerialTransport(
                port=port,
                baudrate=baudrate,
                timeout_s=timeout_s,
            ),
            address=address,
        )
