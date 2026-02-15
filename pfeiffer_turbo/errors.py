from enum import Enum


class PfeifferTurboError(Exception):
    """Base exception for the pfeiffer_turbo package."""


class PfeifferTransportError(PfeifferTurboError):
    """Raised when transport I/O operations fail."""


class PfeifferUnsupportedTransportOperationError(PfeifferTransportError):
    """Raised when a transport does not support a requested operation."""


class PfeifferProtocolError(PfeifferTurboError):
    """Raised when telegram encoding/decoding fails."""


# Backward-compatible aliases
TransportError = PfeifferTransportError
UnsupportedTransportOperationError = PfeifferUnsupportedTransportOperationError
ProtocolError = PfeifferProtocolError


class ErrorCodes(Enum):
    ERR001 = "excess rotation speed"
    ERR002 = "overvoltage"
    ERR006 = "run-up time error"
    ERR008 = "connection electronic drive unit-pump faulty"
    ERR010 = "internal device fault"
    ERR021 = "electronic drive unit does not recognize pump"
    ERR041 = "excess motor current"
    ERR043 = "internal configuration fault"
    ERR045 = "excess temperature motor"
    ERR046 = "initial initialization fault"
    ERR073 = "overload axial bearing"
    ERR074 = "overload radial bearing"
    ERR089 = "rotor out of target aread, stabilization impossible"
    ERR091 = "internal device fault"
    ERR092 = "unknown connection panel"
    ERR093 = "temperature analysis motor faulty"
    ERR094 = "temperature analysis electronic faulty"
    ERR098 = "internal communication fault"
    ERR107 = "collective fault power stage"
    ERR108 = "rotation speed measuruement faulty"
    ERR109 = "firmware not configured"
    ERR114 = "temperature analysis power stage faulty"
    ERR117 = "excess temperature pump bottom part"
    ERR118 = "excess temperature power stage"
    ERR119 = "excess temprature bearing"
    ERR777 = "nominal rotation speed not confirmed"
    ERR800 = "excess current position sensors"
    ERR802 = "calibration of position sensors faulty"
    ERR810 = "data set missing in the pump"
    ERR815 = "excess current magnetic bearing output stage"
    ERR890 = "safety bearing stress > 100%"
    ERR891 = "rotor unbalnace > 100%"
    WRN007 = "low voltage / mains power failure"
    WRN018 = "remote priority conflict"
    WRN048 = "high temperature motor"
    WRN076 = "high temperature elecronic"
    WRN089 = "rotor out of target area, stabilization was possible"
    WRN097 = "pump information invalid"
    WRN098 = "pump information incomplete"
    WRN100 = "rotation speed raised to minimum value"
    WRN115 = "temperature analysis pump bottom part faulty"
    WRN116 = "temperature analysis bearing faulty"
    WRN117 = "high temperature pump bottom part"
    WRN118 = "high temperature power stage"
    WRN119 = "high temperature bearing"
    WRN168 = "high deceleration"
    WRN801 = "brake electronics defective"
    WRN806 = "brake resistor defective"
    WRN807 = "calibration position sensors required"
    WRN890 = "safety bearing stress > 75%"
    WRN891 = "rotor unbalance > 75%"
