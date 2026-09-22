#!/usr/bin/env python3
"""
Tkinter GUI for Pfeiffer Turbo Molecular Pump Control

Provides a user-friendly interface for connecting to and controlling
Pfeiffer turbo pumps via serial port. Supports TM700 and TC110 controllers.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import re
import time
from typing import Optional
import serial.tools.list_ports

from pfeiffer_turbo import TM700, TC110, Access
from pfeiffer_turbo.parameters import Parameters, parameters
from pfeiffer_turbo.errors import PfeifferTurboError, PfeifferProtocolError
from pfeiffer_turbo.telegram import create_telegram


class PfeifferTurboGUI:
    """Main GUI window for Pfeiffer Turbo control"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Pfeiffer Turbo Pump Control")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        self.pump: Optional[TM700 | TC110] = None
        self.connected = False
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._io_lock = threading.RLock()

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        # Create main frames
        connection_frame = ttk.LabelFrame(
            self.root, text="Connection Settings", padding=10
        )
        connection_frame.pack(fill=tk.X, padx=10, pady=5)

        control_frame = ttk.LabelFrame(self.root, text="Pump Control", padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        readout_frame = ttk.LabelFrame(self.root, text="Pump Status", padding=10)
        readout_frame.pack(fill=tk.X, padx=10, pady=5)

        parameters_frame = ttk.LabelFrame(
            self.root, text="Parameter Interface", padding=10
        )
        parameters_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Connection Settings
        self._setup_connection_frame(connection_frame)

        # Pump Control
        self._setup_control_frame(control_frame)

        # Status Readout
        self._setup_readout_frame(readout_frame)

        # Parameters
        self._setup_parameters_frame(parameters_frame)

    def _setup_connection_frame(self, frame: ttk.LabelFrame) -> None:
        """Setup connection settings frame"""
        # Serial Port Selection
        port_frame = ttk.Frame(frame)
        port_frame.pack(fill=tk.X, pady=5)

        ttk.Label(port_frame, text="Serial Port:").pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(
            port_frame, textvariable=self.port_var, state="readonly", width=20
        )
        self.port_combo.pack(side=tk.LEFT, padx=5)
        self._refresh_ports()

        ttk.Button(port_frame, text="Refresh Ports", command=self._refresh_ports).pack(
            side=tk.LEFT, padx=5
        )

        # Controller Model Selection
        model_frame = ttk.Frame(frame)
        model_frame.pack(fill=tk.X, pady=5)

        ttk.Label(model_frame, text="Controller Model:").pack(side=tk.LEFT, padx=5)
        self.model_var = tk.StringVar(value="TM700")
        model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            values=["TM700", "TC110"],
            state="readonly",
            width=20,
        )
        model_combo.pack(side=tk.LEFT, padx=5)

        # Connection Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)

        self.connect_btn = ttk.Button(
            button_frame, text="Connect", command=self._connect
        )
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.disconnect_btn = ttk.Button(
            button_frame, text="Disconnect", command=self._disconnect, state=tk.DISABLED
        )
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(
            frame, text="Status: Disconnected", foreground="red"
        )
        self.status_label.pack(fill=tk.X, pady=5)

    def _setup_control_frame(self, frame: ttk.LabelFrame) -> None:
        """Setup pump control frame"""
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)

        self.start_btn = ttk.Button(
            button_frame, text="Start Pump", command=self._start_pump, state=tk.DISABLED
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            button_frame, text="Stop Pump", command=self._stop_pump, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

    def _setup_readout_frame(self, frame: ttk.LabelFrame) -> None:
        """Setup pump status readout frame"""
        readout_grid = ttk.Frame(frame)
        readout_grid.pack(fill=tk.X, pady=5)

        # Actual Speed in Hz
        ttk.Label(readout_grid, text="Actual Speed (Hz):").grid(
            row=0, column=0, sticky=tk.W, padx=5
        )
        self.speed_hz_label = ttk.Label(
            readout_grid, text="0", foreground="blue", font=("Arial", 12, "bold")
        )
        self.speed_hz_label.grid(row=0, column=1, sticky=tk.W, padx=5)

        # Actual Speed in RPM
        ttk.Label(readout_grid, text="Actual Speed (RPM):").grid(
            row=0, column=2, sticky=tk.W, padx=5
        )
        self.speed_rpm_label = ttk.Label(
            readout_grid, text="0", foreground="blue", font=("Arial", 12, "bold")
        )
        self.speed_rpm_label.grid(row=0, column=3, sticky=tk.W, padx=5)

        # Drive Current
        ttk.Label(readout_grid, text="Drive Current (A):").grid(
            row=1, column=0, sticky=tk.W, padx=5
        )
        self.current_label = ttk.Label(
            readout_grid, text="0", foreground="blue", font=("Arial", 12, "bold")
        )
        self.current_label.grid(row=1, column=1, sticky=tk.W, padx=5)

        # Drive Voltage
        ttk.Label(readout_grid, text="Drive Voltage (V):").grid(
            row=1, column=2, sticky=tk.W, padx=5
        )
        self.voltage_label = ttk.Label(
            readout_grid, text="0", foreground="blue", font=("Arial", 12, "bold")
        )
        self.voltage_label.grid(row=1, column=3, sticky=tk.W, padx=5)

        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Auto-refresh readouts (every 500ms)",
            variable=self.auto_refresh_var,
            command=self._toggle_monitoring,
        ).pack(fill=tk.X, pady=5)

    def _setup_parameters_frame(self, frame: ttk.LabelFrame) -> None:
        """Setup parameter interface frame"""
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Label(control_frame, text="Parameter:").pack(side=tk.LEFT, padx=5)

        self.param_var = tk.StringVar()
        self.param_combo = ttk.Combobox(
            control_frame, textvariable=self.param_var, state="readonly", width=30
        )
        self.param_combo.pack(side=tk.LEFT, padx=5)
        self.param_combo.bind("<<ComboboxSelected>>", self._on_parameter_selected)

        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)

        self.get_btn = ttk.Button(
            button_frame,
            text="Get Value",
            command=self._get_parameter,
            state=tk.DISABLED,
        )
        self.get_btn.pack(side=tk.LEFT, padx=5)

        self.set_btn = ttk.Button(
            button_frame,
            text="Set Value",
            command=self._set_parameter,
            state=tk.DISABLED,
        )
        self.set_btn.pack(side=tk.LEFT, padx=5)

        # Value input frame
        value_frame = ttk.Frame(frame)
        value_frame.pack(fill=tk.X, pady=5)

        ttk.Label(value_frame, text="Value:").pack(side=tk.LEFT, padx=5)
        self.param_value_var = tk.StringVar()
        self.param_value_entry = ttk.Entry(
            value_frame, textvariable=self.param_value_var, width=30
        )
        self.param_value_entry.pack(side=tk.LEFT, padx=5)

        # Parameter info frame
        info_frame = ttk.LabelFrame(frame, text="Parameter Information", padding=5)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.param_info_text = scrolledtext.ScrolledText(
            info_frame, height=8, width=80, state=tk.DISABLED, wrap=tk.WORD
        )
        self.param_info_text.pack(fill=tk.BOTH, expand=True)

    def _refresh_ports(self) -> None:
        """Refresh available serial ports"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports:
            self.port_combo.current(0)

    def _connect(self) -> None:
        """Connect to the selected serial port and controller"""
        port = self.port_var.get()
        model = self.model_var.get()

        if not port:
            messagebox.showerror("Error", "Please select a serial port")
            return

        self._run_task(
            lambda: (
                TM700.from_serial(port) if model == "TM700" else TC110.from_serial(port)
            ),
            on_success=lambda pump: self._on_connected(model, port, pump),
            error_title="Connection Error",
        )

    def _disconnect(self) -> None:
        """Disconnect from the pump"""
        self._toggle_monitoring(stop=True)
        pump = self.pump
        self._run_task(
            lambda: pump.close() if pump else None,
            on_success=lambda _result: self._on_disconnected(),
        )

    def _start_pump(self) -> None:
        """Start the pump"""
        if not self.pump:
            return

        self._run_pump_task(
            lambda: self._with_pump_lock(lambda: self.pump.start()),
            on_success=lambda _result: messagebox.showinfo("Success", "Pump started"),
        )

    def _stop_pump(self) -> None:
        """Stop the pump"""
        if not self.pump:
            return

        self._run_pump_task(
            lambda: self._with_pump_lock(lambda: self.pump.stop()),
            on_success=lambda _result: messagebox.showinfo("Success", "Pump stopped"),
        )

    def _populate_parameters(self) -> None:
        """Populate parameter dropdown with available parameters"""
        if not self.pump:
            return

        param_names = []
        with self._io_lock:
            for param_id in self.pump._generated_parameter_ids:
                param = Parameters(param_id)
                name = self._camel_to_snake(param.name)
                param_names.append((name, param))

        param_names.sort(key=lambda x: x[0])
        self.param_combo["values"] = [name for name, _ in param_names]
        self._param_lookup = {name: param for name, param in param_names}

    def _camel_to_snake(self, name: str) -> str:
        """Convert CamelCase to snake_case"""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _on_parameter_selected(self, event: tk.Event) -> None:
        """Handle parameter selection"""
        param_name = self.param_var.get()
        if param_name not in self._param_lookup:
            return

        param = self._param_lookup[param_name]
        param_info = parameters[param]

        self.param_value_var.set("")

        info_text = f"Parameter: {param.name}\n"
        info_text += f"Description: {param_info.designation}\n"
        info_text += f"Data Type: {param_info.data_type.name}\n"
        info_text += f"Access: {param_info.access.name}\n"

        if param_info.min is not None:
            info_text += f"Min: {param_info.min}\n"
        if param_info.max is not None:
            info_text += f"Max: {param_info.max}\n"
        if param_info.unit is not None:
            info_text += f"Unit: {param_info.unit}\n"
        if param_info.default is not None:
            info_text += f"Default: {param_info.default}\n"

        if param_info.options:
            info_text += "\nOptions:\n"
            for opt_val, opt_desc in param_info.options.items():
                info_text += f"  {opt_val}: {opt_desc}\n"

        self.param_info_text.config(state=tk.NORMAL)
        self.param_info_text.delete("1.0", tk.END)
        self.param_info_text.insert("1.0", info_text)
        self.param_info_text.config(state=tk.DISABLED)

        # Update button states based on access level
        if param_info.access == Access.READ:
            self.get_btn.config(state=tk.NORMAL)
            self.set_btn.config(state=tk.DISABLED)
            self.param_value_entry.config(state=tk.DISABLED)
        elif param_info.access == Access.WRITE:
            self.get_btn.config(state=tk.DISABLED)
            self.set_btn.config(state=tk.NORMAL)
            self.param_value_entry.config(state=tk.NORMAL)
        else:  # READ_WRITE
            self.get_btn.config(state=tk.NORMAL)
            self.set_btn.config(state=tk.NORMAL)
            self.param_value_entry.config(state=tk.NORMAL)

    def _get_parameter(self) -> None:
        """Get parameter value"""
        if not self.pump:
            return

        param_name = self.param_var.get()
        if param_name not in self._param_lookup:
            messagebox.showerror("Error", "No parameter selected")
            return

        self._run_pump_task(
            lambda: self._with_pump_lock(lambda: getattr(self.pump, param_name)),
            on_success=lambda value: self._on_parameter_value(value),
            error_title="Error",
        )

    def _set_parameter(self) -> None:
        """Set parameter value"""
        if not self.pump:
            return

        param_name = self.param_var.get()
        value_str = self.param_value_var.get()

        if param_name not in self._param_lookup:
            messagebox.showerror("Error", "No parameter selected")
            return

        if not value_str:
            messagebox.showerror("Error", "Please enter a value")
            return

        try:
            param = self._param_lookup[param_name]
            param_info = parameters[param]

            # Convert value based on data type
            if param_info.data_type.name == "BOOL":
                value = value_str.lower() in ("true", "1", "yes")
            elif param_info.data_type.name in ("INT", "SHORT"):
                value = int(value_str)
            elif param_info.data_type.name == "FLOAT":
                value = float(value_str)
            else:
                value = value_str
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid value: {e}")
            return

        self._run_pump_task(
            lambda: self._write_parameter(param, param_name, value),
            on_success=lambda _result: messagebox.showinfo(
                "Success", f"Parameter set to: {value}"
            ),
        )

    def _toggle_monitoring(self, stop: bool = False) -> None:
        """Toggle automatic monitoring of pump status"""
        if stop or not self.auto_refresh_var.get():
            self.monitoring = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=1)
            self.monitor_thread = None
        else:
            if not self.monitoring and self.connected:
                self.monitoring = True
                self.monitor_thread = threading.Thread(
                    target=self._monitor_loop, daemon=True
                )
                self.monitor_thread.start()

    def _monitor_loop(self) -> None:
        """Background thread to monitor pump status"""
        while self.monitoring and self.connected:
            try:
                # Update readouts safely
                if self.pump:
                    with self._io_lock:
                        # Try to get actual speed in Hz
                        try:
                            speed_hz = self.pump.actual_spd
                            self.root.after(
                                0,
                                self._update_label,
                                self.speed_hz_label,
                                f"{speed_hz:.2f}",
                            )
                        except Exception:
                            pass

                        # Try to get actual speed in RPM
                        try:
                            speed_rpm = self.pump.actual_spd_rpm
                            self.root.after(
                                0,
                                self._update_label,
                                self.speed_rpm_label,
                                f"{speed_rpm:.2f}",
                            )
                        except Exception:
                            pass

                        # Try to get drive current
                        try:
                            current = self.pump.drv_current
                            self.root.after(
                                0,
                                self._update_label,
                                self.current_label,
                                f"{current:.2f}",
                            )
                        except Exception:
                            pass

                        # Try to get drive voltage
                        try:
                            voltage = self.pump.drv_voltage
                            self.root.after(
                                0,
                                self._update_label,
                                self.voltage_label,
                                f"{voltage:.2f}",
                            )
                        except Exception:
                            pass

                time.sleep(0.5)
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                self.monitoring = False

    def _run_task(self, func, on_success=None, error_title: str = "Error") -> None:
        def worker() -> None:
            try:
                result = func()
            except AttributeError as exc:
                error = str(exc)
                self.root.after(
                    0,
                    lambda error=error: messagebox.showerror(
                        error_title, f"Cannot read parameter: {error}"
                    ),
                )
            except PfeifferTurboError as exc:
                error = str(exc)
                self.root.after(
                    0,
                    lambda error=error: messagebox.showerror(
                        error_title, f"Communication error: {error}"
                    ),
                )
            except Exception as exc:
                error = str(exc)
                self.root.after(
                    0,
                    lambda error=error: messagebox.showerror(
                        error_title, f"Unexpected error: {error}"
                    ),
                )
            else:
                if on_success is not None:
                    self.root.after(0, lambda r=result: on_success(r))

        threading.Thread(target=worker, daemon=True).start()

    def _run_pump_task(self, func, on_success=None, error_title: str = "Error") -> None:
        if not self.pump:
            return
        self._run_task(func, on_success=on_success, error_title=error_title)

    def _with_pump_lock(self, func):
        with self._io_lock:
            return func()

    def _write_parameter(self, param: Parameters, param_name: str, value):
        validated = self._with_pump_lock(
            lambda: self.pump._validate_write_value(param, value)
        )
        telegram = create_telegram(
            parameter=param,
            address=self.pump.address,
            read_write="W",
            data=validated,
        )
        response = self._with_pump_lock(lambda: self.pump.query(telegram))

        if response.data != validated:
            raise PfeifferProtocolError(
                f"Controller rejected {param_name}: {response.data}"
            )

        return response.data

    def _on_connected(self, model: str, port: str, pump) -> None:
        self.pump = pump
        self.connected = True
        self.status_label.config(
            text=f"Status: Connected ({model} @ {port})", foreground="green"
        )
        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        self.port_combo.config(state=tk.DISABLED)
        self.param_combo.config(state="readonly")

        self._populate_parameters()
        self._toggle_monitoring()

        messagebox.showinfo("Success", f"Connected to {model}")

    def _on_disconnected(self) -> None:
        self.connected = False
        self.pump = None
        self.status_label.config(text="Status: Disconnected", foreground="red")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.port_combo.config(state="readonly")
        self.param_combo.config(state=tk.DISABLED)
        self.get_btn.config(state=tk.DISABLED)
        self.set_btn.config(state=tk.DISABLED)
        self.param_combo.set("")
        self.param_value_var.set("")

    def _on_parameter_value(self, value) -> None:
        self.param_value_var.set(str(value))
        messagebox.showinfo("Success", f"Value: {value}")

    def _update_label(self, label: ttk.Label, text: str) -> None:
        label.config(text=text)

    def run(self) -> None:
        """Start the GUI"""
        self.root.mainloop()


def main():
    root = tk.Tk()
    gui = PfeifferTurboGUI(root)
    gui.run()


if __name__ == "__main__":
    main()
