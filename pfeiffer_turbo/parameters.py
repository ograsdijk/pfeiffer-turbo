from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union


class DataType(Enum):
    BOOL = 0
    INT = 1
    FLOAT = 2
    STR = 4
    SHORT = 7
    LONGSTR = 11
    QUERY = 12


@dataclass
class DataLength:
    BOOL: int = 6
    INT: int = 6
    FLOAT: int = 6
    STR: int = 6
    SHORT: int = 3
    LONGSTR: int = 16
    QUERY: int = 2


class Parameters(Enum):
    PumpgStatn = 10
    EnableVent = 12
    Brake = 13
    CfgDo2 = 19
    CfgDo1 = 24
    MotorPump = 23
    GasMode = 27
    CfgRemote = 28
    VentMode = 30
    CfgAccA1 = 35
    CfgAccB1 = 36
    CfgAccA2 = 37
    CfgAccB2 = 38
    CfgRelR1 = 45
    CfgRelR2 = 46
    CfgRelR3 = 47
    SealingGas = 50
    CfgAo1 = 55
    CfgAi1 = 57
    CtrlViaInt = 60
    CfgDi1 = 62
    CfgDi2 = 63
    CfgDi3 = 64
    RemotePrio = 300
    SpdSwPtAtt = 302
    ErrorCode = 303
    OvTempElec = 304
    OvTempPump = 305
    SetSpdAtt = 306
    PumpAccel = 307
    SetRotSpd = 308
    ActualSpd = 309
    DrvCurrent = 310
    OpHrsPump = 311
    FwVersion = 312
    DrvVoltage = 313
    OpHrsElec = 314
    NominalSpeed = 315
    DrvPower = 316
    PumpCycles = 319
    TempPwrStg = 324
    TempElec = 326
    BearngWear = 329
    TempPmpBot = 330
    AccelDecel = 336
    TempBearng = 342
    TempMotor = 346
    ElecName = 349
    HwVersion = 354
    RotorImbal = 358
    ErrHist1 = 360
    ErrHist2 = 361
    ErrHist3 = 362
    ErrHist4 = 363
    ErrHist5 = 364
    ErrHist6 = 365
    ErrHist7 = 366
    ErrHist8 = 367
    ErrHist9 = 368
    ErrHist10 = 369
    TempRotor = 384
    SetRotSpd_rpm = 397
    ActualSpd_rpm = 398
    NominalSpd_rpm = 399
    RuTimeSval = 700
    SpdSval = 707
    PwrSval = 708
    StbySval = 717
    VentSpd = 720
    VentTime = 721
    NomSpdConf = 777
    RS485Adr = 797


@dataclass
class ParameterInfo:
    designation: str
    data_type: DataType
    access: str
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    unit: Optional[str] = None
    default: Optional[Union[int, float, str]] = None
    options: Optional[dict[int, str]] = None


parameters = {
    Parameters.PumpgStatn: ParameterInfo(
        designation="Pumping station", data_type=DataType.BOOL, access="RW"
    ),
    Parameters.EnableVent: ParameterInfo("Enable venting", DataType.BOOL, "RW"),
    Parameters.Brake: ParameterInfo("Brake", DataType.BOOL, "RW"),
    Parameters.MotorPump: ParameterInfo("Motor pump", DataType.BOOL, "RW"),
    Parameters.GasMode: ParameterInfo(
        "Gas mode",
        DataType.SHORT,
        "RW",
        options={0: "heavy gas", 1: "light gas", 2: "helium"},
    ),
    Parameters.CfgRemote: ParameterInfo(
        "Configuration remote",
        DataType.SHORT,
        "RW",
        options={0: "standard", 4: "relais inverted"},
    ),
    Parameters.VentMode: ParameterInfo(
        "Venting mode",
        DataType.SHORT,
        "RW",
        options={0: "delayed venting", 1: "no venting", 2: "direct venting"},
    ),
    Parameters.CfgRelR1: ParameterInfo(
        "Configuration relay 1",
        DataType.SHORT,
        "RW",
        options={
            0: "rot. speed switch point attained",
            1: "no error",
            2: "error",
            3: "warning",
            4: "error and/or warning",
            5: "set speed attained",
            6: "pump on",
            7: "pump accelerates",
            8: "pump decelerates",
            9: "always 0",
            10: "always 1",
            11: "remote priority active",
            12: "heating",
            13: "backing pump",
            14: "sealing gas",
            15: "pumping station",
        },
    ),
    Parameters.CfgRelR2: ParameterInfo(
        "Configuration relay 2",
        DataType.SHORT,
        "RW",
        options={
            0: "rot. speed switch point attained",
            1: "no error",
            2: "error",
            3: "warning",
            4: "error and/or warning",
            5: "set speed attained",
            6: "pump on",
            7: "pump accelerates",
            8: "pump decelerates",
            9: "always 0",
            10: "always 1",
            11: "remote priority active",
            12: "heating",
            13: "backing pump",
            14: "sealing gas",
            15: "pumping station",
        },
    ),
    Parameters.CfgRelR3: ParameterInfo(
        "Configuration relay 3",
        DataType.SHORT,
        "RW",
        options={
            0: "rot. speed switch point attained",
            1: "no error",
            2: "error",
            3: "warning",
            4: "error and/or warning",
            5: "set speed attained",
            6: "pump on",
            7: "pump accelerates",
            8: "pump decelerates",
            9: "always 0",
            10: "always 1",
            11: "remote priority active",
            12: "heating",
            13: "backing pump",
            14: "sealing gas",
            15: "pumping station",
        },
    ),
    Parameters.SealingGas: ParameterInfo("Sealing gas", DataType.BOOL, "R"),
    Parameters.CfgAo1: ParameterInfo(
        "Configuration output AO1",
        DataType.SHORT,
        "RW",
        options={
            0: "actual rotation speed",
            1: "power",
            2: "current",
            3: "always 0 V",
            4: "always 10 V",
            5: "follows AI1",
        },
    ),
    Parameters.CfgAi1: ParameterInfo(
        designation="Configuration input AI1",
        data_type=DataType.SHORT,
        access="RW",
        options={0: "disconnected", 1: "set value rot. speed setting mode"},
    ),
    Parameters.CtrlViaInt: ParameterInfo(
        designation="Control via interface",
        data_type=DataType.SHORT,
        access="RW",
        options={
            0: "remote",
            1: "RS485",
            4: "PV.can",
            8: "field bus",
            16: "E74",
            255: "unlock interface selection",
        },
    ),
    Parameters.RemotePrio: ParameterInfo("Remote priority", DataType.BOOL, "R", 0, 1),
    Parameters.SpdSwPtAtt: ParameterInfo(
        "Rotation speed switch point attained ",
        DataType.BOOL,
        "R",
        0,
        1,
    ),
    Parameters.ErrorCode: ParameterInfo("Error code", DataType.STR, "R"),
    Parameters.OvTempElec: ParameterInfo(
        "Excess temperature electronic drive unit",
        DataType.BOOL,
        "R",
        0,
        1,
    ),
    Parameters.OvTempPump: ParameterInfo(
        "Excess temperature pump", DataType.BOOL, "R", 0, 1
    ),
    Parameters.SetSpdAtt: ParameterInfo(
        "Set rotation speed attained", DataType.BOOL, "R", 0, 1
    ),
    Parameters.PumpAccel: ParameterInfo("Pump accellerates", DataType.BOOL, "R", 0, 1),
    Parameters.SetRotSpd: ParameterInfo(
        "Set rotation speed [Hz]", DataType.INT, "R", 0, 999999, "Hz"
    ),
    Parameters.ActualSpd: ParameterInfo(
        "Active rotation speed [Hz]", DataType.INT, "R", 0, 999999, "Hz"
    ),
    Parameters.DrvCurrent: ParameterInfo(
        "Drive current [A]", DataType.FLOAT, "R", 0, 9999.99, "A"
    ),
    Parameters.OpHrsPump: ParameterInfo(
        "Operating hours pump [h]", DataType.INT, "R", 0, 65535, "h"
    ),
    Parameters.FwVersion: ParameterInfo(
        "Firmware version electronic drive unit", DataType.STR, "R"
    ),
    Parameters.DrvVoltage: ParameterInfo(
        "Drive voltage [V]", DataType.FLOAT, "R", 0, 9999.99, "V"
    ),
    Parameters.OpHrsElec: ParameterInfo(
        "Operating hours electronic drive unit [h]", DataType.INT, "R", 0, 65535, "h"
    ),
    Parameters.NominalSpeed: ParameterInfo(
        "Nominal rotation speed [Hz]", DataType.INT, "R", 0, 999999, "Hz"
    ),
    Parameters.DrvPower: ParameterInfo(
        "Drive power [W]", DataType.INT, "R", 0, 999999, "W"
    ),
    Parameters.PumpCycles: ParameterInfo("Pump cycles", DataType.INT, "R", 0, 65535),
    Parameters.TempPwrStg: ParameterInfo(
        "Temperature power stage [C]", DataType.INT, "R", unit="C"
    ),
    Parameters.TempElec: ParameterInfo(
        "Temperature electronic [C]", DataType.INT, "R", unit="C"
    ),
    Parameters.BearngWear: ParameterInfo(
        "Wear conditions safety bearing [%]", DataType.INT, "R", unit="%"
    ),
    Parameters.TempPmpBot: ParameterInfo(
        "Temperature pump bottom part [C]", DataType.INT, "R", unit="C"
    ),
    Parameters.AccelDecel: ParameterInfo(
        "Acceleration / Deceleration [rpm/s]", DataType.INT, "R", unit="rpm/s"
    ),
    Parameters.RotorImbal: ParameterInfo(
        "Rotor out-of-balance [%]", DataType.INT, "R", unit="%"
    ),
    Parameters.TempBearng: ParameterInfo(
        "Temperature bearing", DataType.INT, "R", unit="C"
    ),
    Parameters.TempMotor: ParameterInfo(
        "Temperature motor", DataType.INT, "R", unit="C"
    ),
    Parameters.ElecName: ParameterInfo(
        "Name of electronic drive unit", DataType.STR, "R"
    ),
    Parameters.HwVersion: ParameterInfo(
        "Name of electronic drive unit", DataType.STR, "R"
    ),
    Parameters.TempRotor: ParameterInfo(
        "Temperature rotor", DataType.INT, "R", unit="C"
    ),
    Parameters.SetRotSpd_rpm: ParameterInfo(
        "Set rotation speed [rpm]", DataType.INT, "R", unit="rpm"
    ),
    Parameters.ActualSpd_rpm: ParameterInfo(
        "Actual rotation speed [rpm]", DataType.INT, "R", unit="rpm"
    ),
    Parameters.NominalSpd_rpm: ParameterInfo(
        "Nominal rotation speed [rpm]", DataType.INT, "R", unit="rpm"
    ),
    Parameters.RuTimeSval: ParameterInfo(
        "Set value run-up time [min]",
        DataType.INT,
        "RW",
        unit="min",
    ),
    Parameters.SpdSval: ParameterInfo(
        "Set value in rot. speed setting mode [%]",
        DataType.INT,
        "RW",
        unit="%",
    ),
    Parameters.PwrSval: ParameterInfo(
        "Set value power consumption",
        DataType.SHORT,
        "RW",
        unit="%",
    ),
    Parameters.StbySval: ParameterInfo(
        "Set value roation speed at standby [%]",
        DataType.FLOAT,
        "RW",
        unit="%",
    ),
    Parameters.VentSpd: ParameterInfo(
        "Venting rot. speed at delayed venting",
        DataType.SHORT,
        "RW",
        unit="%",
    ),
    Parameters.VentTime: ParameterInfo(
        "Venting time at delayed venting [s]",
        DataType.INT,
        "RW",
        unit="[s]",
    ),
    Parameters.NomSpdConf: ParameterInfo(
        "Nominal rotation speed confirmation [Hz]",
        DataType.INT,
        "RW",
        unit="[Hz]",
    ),
    Parameters.RS485Adr: ParameterInfo("RS485 device address", DataType.INT, "RW"),
}

for i in range(1, 11):
    parameters[Parameters[f"ErrHist{i}"]] = ParameterInfo(
        f"Error code history, pos. {i}", DataType.STR, "R"
    )


_options = {
    0: "fan (continuous operation)",
    1: "venting value, normally closed",
    2: "heating",
    3: "backing pump",
    4: "fan (temperature controlled)",
    5: "sealing gas",
    6: "always 0",
    7: "always 1",
    8: "power failure venting unit",
}
for i in range(1, 3):
    parameter = Parameters[f"CfgAccA{i}"]
    parameters[parameter] = ParameterInfo(
        f"Configuration accessory connection A{i}",
        DataType.SHORT,
        "RW",
        options=_options,
    )
    parameter = Parameters[f"CfgAccB{i}"]
    parameters[parameter] = ParameterInfo(
        f"Configuration accessory connection B{i}",
        DataType.SHORT,
        "RW",
        options=_options,
    )

_options = {
    0: "deactivated",
    1: "enable venting",
    2: "heating",
    3: "sealing gas",
    4: "run-up time control",
    5: "rotation speed setting mode",
}
for i in range(1, 4):
    parameter = Parameters[f"CfgDi{i}"]
    parameters[parameter] = ParameterInfo(
        f"Configuration input DI{i}",
        DataType.SHORT,
        "RW",
        options=_options,
    )

_options = {
    0: "rot. speed switch point attained",
    1: "no error",
    2: "error",
    3: "warning",
    4: "error and/or warning",
    5: "set speed attained",
    6: "pump on",
    7: "pump accelerates",
    8: "pump decelerates",
    9: "always 0",
    10: "always 1",
    11: "remote priority active",
    12: "heating",
    13: "backing pump",
    14: "sealing gas",
    15: "pumping station",
}
for i in range(1, 3):
    parameter = Parameters[f"CfgDo{i}"]
    parameters[parameter] = ParameterInfo(
        designation=f"Configuration output DO{i}",
        data_type=DataType.SHORT,
        access="RW",
        options=_options,
    )
