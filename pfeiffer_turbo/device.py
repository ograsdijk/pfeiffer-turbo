import re
from enum import Enum, auto
from typing import Sequence, Union, cast

import pyvisa
from pyvisa import constants

from .parameters import Parameters, parameters
from .telegram import Telegram, create_telegram, decode_telegram


class ConnectionType(Enum):
    RS485 = auto()
    TCPIP = auto()


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
    def function_setter(cls: DriveUnit, value: Union[str, int, float]):
        telegram = create_telegram(
            parameter=parameter, address=cls.address, read_write="W", data=value
        )
        telegram = cls.query(telegram)
        return telegram.data

    return function_setter


class DriveUnit:
    """
    Baseclass for Pfeiffer turbo drive units

    Dynamically generates getters and setters for Pfeiffer vacuum parameters based on
    supported_parameters, a sequence of integers which are then cross referenced against
    implemented parameters shown in Parameters from parameters.py
    """

    def __init__(
        self,
        resource_name: str,
        address: int,
        connection_type: ConnectionType,
        supported_parameters: Sequence[int],
    ):
        """
        Initialization of the DriveUnit

        Args:
            resource_name (str): resource name, either serial port or ip address
            address (int): drive unit addresss
            connection_type (ConnectionType): connection type,
                                            either ConnectionType.RS485 or
                                            ConnectionType.TCP
            allowed_parameters (Sequence[int]): Sequence of vacuum parameters supported
                                                by the drive unit
        """
        self.rm = pyvisa.ResourceManager()

        self.address = address

        if connection_type == ConnectionType.RS485:
            self.instrument: Union[
                pyvisa.resources.SerialInstrument, pyvisa.resources.TCPIPSocket
            ] = cast(
                pyvisa.resources.SerialInstrument,
                self.rm.open_resource(
                    resource_name=resource_name,
                    parity=constants.Parity.none,
                    data_bits=8,
                    baud_rate=9600,
                    read_termination="\r",
                    write_termination="\r",
                ),
            )
        elif connection_type == ConnectionType.TCPIP:
            self.instrument = cast(
                pyvisa.resources.TCPIPSocket,
                self.rm.open_resource(
                    resource_name=f"TCPIP::{resource_name}::SOCKET",
                    read_termination="\r",
                    write_termination="\r",
                ),
            )

        self._create_parameters(supported_parameters)

    def query(self, telegram: Telegram) -> Telegram:
        ret = self.instrument.query(telegram.message)
        telegram = decode_telegram(ret)
        return telegram

    def _create_parameters(self, supported_parameters: Sequence[int]):
        """
        Dynamically generate the getters and setters for the supported vacuum parameters

        Args:
            supported_parameters (Sequence[int]): supported vacuum parameters
        """
        for parameter_id in supported_parameters:
            parameter = Parameters(parameter_id)
            parameter_desc = parameters[parameter]

            name = "_".join(
                [s for s in re.split("([A-Z][^A-Z]*)", parameter.name) if s]
            ).lower()

            if parameter_desc.access == "R":
                function_property = _make_property(parameter)
                setattr(
                    self.__class__,
                    name,
                    property(fget=function_property, doc=parameter_desc.designation),
                )

            elif parameter_desc.access == "RW":
                function_property = _make_property(parameter)
                function_setter = _make_setter(parameter)

                doc = parameter_desc.designation
                if parameter_desc.options is not None:
                    doc += "\nParameter options are:"
                    for value, desc in parameter_desc.options.items():
                        doc += f"\n{value} : {desc}"
                setattr(
                    self.__class__,
                    name,
                    property(
                        fget=function_property,
                        fset=function_setter,
                        doc=doc,
                    ),
                )

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
        resource_name: str,
        address: int,
        connection_type: ConnectionType = ConnectionType.RS485,
    ):
        supported_parameters = tuple([par.value for par in Parameters])
        super().__init__(
            resource_name=resource_name,
            address=address,
            connection_type=connection_type,
            supported_parameters=supported_parameters,
        )
