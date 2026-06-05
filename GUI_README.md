# Pfeiffer Turbo Pump Control GUI

A comprehensive Tkinter-based graphical user interface for controlling Pfeiffer turbo molecular pumps via serial connection.

## Features

- **Connection Management**
  - Auto-detect available serial ports
  - Support for both TM700 and TC110 controller models
  - Easy connect/disconnect interface

- **Pump Control**
  - Start and stop the pump with single button clicks
  - Real-time status monitoring

- **Live Readouts**
  - Actual rotational speed in Hz
  - Actual rotational speed in RPM
  - Drive current (Amps)
  - Drive voltage (Volts)
  - Auto-refresh readouts every 500ms (toggleable)

- **Parameter Interface**
  - Dropdown menu to select from all available parameters
  - Support for read-only, write-only, and read-write parameters
  - Automatic parameter validation based on type and constraints
  - Detailed parameter information display including:
    - Description
    - Data type
    - Access level
    - Min/max constraints
    - Unit of measurement
    - Default value
    - Available options (for enumerated parameters)

## Installation

1. Ensure you have the pfeiffer-turbo package installed:
   ```bash
   uv sync
   ```

2. Tkinter should be included with Python. If not, install it:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-tk
   
   # macOS (Homebrew)
   brew install python-tk
   ```

## Running the GUI

```bash
uv run python pfeiffer_gui.py
```

Or make it executable:
```bash
chmod +x pfeiffer_gui.py
uv run ./pfeiffer_gui.py
```

## Usage Guide

### 1. Connect to a Pump

1. Click "Refresh Ports" to see available serial ports
2. Select the desired serial port from the dropdown
3. Choose the controller model (TM700 or TC110)
4. Click "Connect"
5. A success message will appear, and the status will show "Connected"

### 2. Control the Pump

- **Start Pump**: Click the "Start Pump" button to begin rotation
- **Stop Pump**: Click the "Stop Pump" button to stop rotation
- The buttons are only enabled when connected

### 3. Monitor Status

- The "Pump Status" section displays real-time measurements:
  - Actual Speed (Hz and RPM)
  - Drive Current and Voltage
- Check "Auto-refresh readouts" to enable continuous monitoring
- Readouts update every 500ms

### 4. Get/Set Parameters

1. Select a parameter from the "Parameter:" dropdown
2. The "Parameter Information" section shows details about the selected parameter
3. **To read a parameter:**
   - Click "Get Value" to read the current value
   - The value will appear in the "Value:" field and in a popup

4. **To write a parameter:**
   - Enter the desired value in the "Value:" field
   - Click "Set Value"
   - A confirmation message will appear

**Notes:**
- Read-only parameters will only show the "Get Value" button
- Write-only parameters will only show the "Set Value" button
- Read-write parameters will show both buttons
- Parameter validation occurs automatically (type checking, range checking, option validation)

## Supported Controllers

- **TM700**: Full support for all TM700 parameters
- **TC110**: Full support for all TC110 parameters

## Error Handling

The GUI provides informative error messages for:
- Serial port connection failures
- Invalid parameter values
- Communication timeouts
- Type mismatches
- Out-of-range values
- Missing serial port selection

## Notes

- The GUI runs the parameter monitoring in a background thread to keep the interface responsive
- All serial communication is handled safely with error checking
- Parameters are validated according to their data type and constraints before being sent to the pump
- The connection is maintained until you click "Disconnect"

## Troubleshooting

### Can't find serial port
- Ensure the pump controller is connected and powered on
- Click "Refresh Ports" to update the available ports list
- Check that you have permissions to access the serial port (on Linux: `sudo usermod -a -G dialout $USER`)

### No response from pump
- Verify the serial port settings (default: 9600 baud)
- Ensure the pump controller is powered on
- Try disconnecting and reconnecting

### GUI doesn't start
- Ensure Tkinter is installed
- Try running with: `uv run python pfeiffer_gui.py`

## Example Workflow

```
1. Launch the GUI
2. Select COM3 and TM700 model
3. Click Connect
4. Click "Start Pump"
5. Monitor the Hz/RPM in the Status section
6. Select "set_rot_spd" parameter
7. Enter "500" in the Value field
8. Click "Set Value"
9. Monitor the actual speed adjusting to the set speed
10. Click "Stop Pump" when finished
11. Click Disconnect
```

## API Reference

The GUI uses the following classes from pfeiffer_turbo:
- `TM700`: TM700 controller interface
- `TC110`: TC110 controller interface
- `SerialTransport`: Serial port communication
- `Parameters`: Parameter enumeration
- `Access`: Parameter access level (READ, WRITE, READ_WRITE)

See the main pfeiffer-turbo README for more details on the underlying API.
