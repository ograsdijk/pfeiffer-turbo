# pfeiffer-turbo
[![Python versions on PyPI](https://img.shields.io/pypi/pyversions/pfeiffer-turbo.svg)](https://pypi.python.org/pypi/pfeiffer-turbo/)
[![pfeiffer-turbo version on PyPI](https://img.shields.io/pypi/v/pfeiffer-turbo.svg "pfeiffer-turbo on PyPI")](https://pypi.python.org/pypi/pfeiffer-turbo/)  
Python interface RS485 connections for Pfeiffer HiPace turbo drive units. Currently only the TM700 is implemented. Also supports connecting through a TCPIP socket, e.g. when using a serial to TCPIP converter for the turbo controller.

## Development (uv)

```bash
uv sync --extra dev
uv run pytest
```

## Example
### RS485 connection example
```python
from pfeiffer_turbo import TM700, SerialTransport

pump = TM700(address=1, transport=SerialTransport(port="COM9"))
# or: pump = TM700.from_serial("COM9", address=1)

# get the rotation speed in Hz
pump.actual_spd

# start the pump
pump.start()

# stop the pump
pump.stop()
```
### TCPIP connection example
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

Only parameters marked read-write by the parameter metadata can be assigned.
When assigning values, the library validates:

- type (bool/int/float/str as defined per parameter)
- allowed options (`options` map when present)
- value limits (`min`/`max` when present)

Example:

```python
# writable
pump.set_rot_spd = 600

# raises ValueError (invalid option)
# pump.gas_mode = 999
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
takes in a set of integers that correspond to pfeiffer vacuum parameters supported by the particular drive unit. Implemented vacuum parameters are seen in `parameters.py`. The getters and setters are then dynamically generated based on the `supported_parameters` and info in `parameters.py`; the enum `Parameters` contains all implemented pfeiffer vacuum parameters, and the dictionary `parameters` contains key, value pairs of `Parameters` and `ParameterInfo`, where `ParameterInfo` is a dataclass containing the implemenation information for a particular parameter:
```Python
@dataclass
class Parameter:
    designation: str
    data_type: DataType
    access: StopIteration
    min: Optional[int] = None
    max: Optional[int] = None
    unit: Optional[str] = None
    default: Optional[Union[int, float, str]] = None
    options: Optional[dict[int, str]] = None
```
Implementing new drive units is be done by inheriting from `DriveUnit` and specifying which pfeiffer parameters are supported by the specific model. New parameters can be implemented by extending the `Parameters` enum and `parameters` dictionary. The class attributes are named similarly to the Pfeiffer vacuum parameters, with underscores inserted between uppercase - lowercase transitions and all lowercase letters. E.g. `GasMode` -> `gas_mode`.