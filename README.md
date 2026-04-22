# pfeiffer-turbo
[![Python versions on PyPI](https://img.shields.io/pypi/pyversions/pfeiffer-turbo.svg)](https://pypi.python.org/pypi/pfeiffer-turbo/)
[![pfeiffer-turbo version on PyPI](https://img.shields.io/pypi/v/pfeiffer-turbo.svg "pfeiffer-turbo on PyPI")](https://pypi.python.org/pypi/pfeiffer-turbo/)  
Python interface for RS485 connections to Pfeiffer HiPace turbo drive units. Supports the TM700 and TC110 electronic drive units, and can also communicate through a TCP/IP socket, for example when using a serial-to-TCP/IP converter for the turbo controller.

## Supported drive units

- TM700
- TC110

## Examples

### RS485 connection example
```python
from pfeiffer_turbo import TC110, SerialTransport

pump = TC110(address=1, transport=SerialTransport(port="COM9"))
# or: pump = TC110.from_serial("COM9", address=1)

# get the rotation speed in Hz
pump.actual_spd

# start the pump
pump.start()

# stop the pump
pump.stop()
```

### TCP/IP connection example
```python
from pfeiffer_turbo import TM700, TcpTransport

pump = TM700(address=1, transport=TcpTransport(host="10.10.222.8", port=12345))
# or: pump = TM700.from_tcp("10.10.222.8", 12345, address=1)

# get the rotation speed in Hz
pump.actual_spd

# start the pump
pump.start()

# stop the pump
pump.stop()
```

## Writable parameters and validation

Parameters marked read-write or write-only by the parameter metadata can be assigned.
When assigning values, the library validates:

- type (bool/int/float/str as defined per parameter)
- allowed options (`options` map when present)
- value limits (`min`/`max` when present)

Write-only parameters raise `AttributeError` when read.

Example:

```python
# writable
pump.set_rot_spd = 600
pump.error_ackn = True

# raises ValueError (invalid option)
# pump.gas_mode = 999

# raises AttributeError (write-only parameter)
# pump.error_ackn
```

## Implementation
A baseclass `DriveUnit`:
```Python
class DriveUnit:
    def __init__(
        self,
        transport: BaseTransport,
        address: int,
        supported_parameters: Sequence[int],
    ):
```
takes a set of integers that correspond to Pfeiffer vacuum parameters supported by a particular drive unit. Implemented vacuum parameters are defined in `parameters.py`. Getters and setters are then generated dynamically from `supported_parameters` and the metadata in `parameters.py`.

The enum `Parameters` contains all implemented Pfeiffer vacuum parameters, and the dictionary `parameters` maps `Parameters` values to `ParameterInfo` objects, where `ParameterInfo` is a dataclass containing the implementation details for a particular parameter:

```Python
@dataclass
class ParameterInfo:
    designation: str
    data_type: DataType
    access: Access | str
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    unit: Optional[str] = None
    default: Optional[Union[int, float, str]] = None
    options: Optional[dict[int, str]] = None
```

New drive units can be implemented by inheriting from `DriveUnit` and specifying which Pfeiffer parameters are supported by the model. New parameters can be implemented by extending the `Parameters` enum and the `parameters` dictionary. Generated class attributes are named similarly to the Pfeiffer parameter names, with underscores inserted between uppercase-to-lowercase transitions and all letters lowercased, for example `GasMode` becomes `gas_mode`.