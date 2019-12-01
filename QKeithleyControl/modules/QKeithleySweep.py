#!/bin/python 
import visa
import time
import numpy as np

# Import d_plot and keithley driver
import drivers.keithley_2400
import modules.QDynamicPlot 

# Import QT backends
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel, QFileDialog
from PyQt5.QtCore import Qt

# Import matplotlibQT backends
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

# Container class to construct sweep measurement widget
class QKeithleySweep(QWidget):

	def __init__(self):

		# Inherits QWidget
		QWidget.__init__(self)	

		# Initialize Keithley Object
		self.keithley = None

		# Create objects to hold data
		self._data = []
		self.sweep = []

		# Create layout objects and set layout
		self.layout = QHBoxLayout()
		self.layout.addLayout(self._gen_sweep_layout())
		self.layout.addLayout(self._gen_sweep_plot())
		self.setLayout(self.layout)

	# Set visa insturment handle for keithley
	def _set_keithley_handle(self, keithley):
		self.keithley=keithley

	# Method to set sweep parameters
	def _set_sweep_params(self, _start, _stop, _points, _hist=False):
		_ = np.linspace(float(_start), float(_stop), int(_points))
		self.sweep = np.concatenate((_,_[-2::-1])) if _hist else _

	# Method to get sweep parameters
	def _get_sweep_params(self):
		return self.sweep if self.sweep != [] else None

	# Sweep control layout
	def _gen_sweep_layout(self): 

		self.ctl_layout = QVBoxLayout()

		# Current/Voltage Sweep Mode 
		self.mode_label = QLabel("Sweep Mode")
		self.mode = QComboBox()
		self.mode.addItems(["Voltage", "Current"])
		self.mode.currentTextChanged.connect(self._update_sweep_control)

		# Compliance Spinbox
		self.cmpl_label = QLabel("Compliance (A)")
		self.cmpl = QDoubleSpinBox()
		self.cmpl.setDecimals(3)
		self.cmpl.setMinimum(0.0)
		self.cmpl.setMaximum(1.0)
		self.cmpl.setSingleStep(0.01)
		self.cmpl.setValue(0.1)

		# Start Spinbox
		self.start_label = QLabel("Sweep Start (V)")
		self.start = QDoubleSpinBox()
		self.start.setDecimals(3)
		self.start.setMinimum(-20.0)
		self.start.setMaximum(20.0)
		self.start.setSingleStep(0.1)
		self.start.setValue(0.0)

		# Stop Spinbox
		self.stop_label = QLabel("Sweep Stop (V)")
		self.stop = QDoubleSpinBox()
		self.stop.setDecimals(3)
		self.stop.setMinimum(-20.0)
		self.stop.setMaximum(20.0)
		self.stop.setSingleStep(0.1)
		self.stop.setValue(1.0)

		# Step Spinbox
		self.npts_label = QLabel("Number of Points")
		self.npts = QSpinBox()
		self.npts.setMinimum(1)
		self.npts.setMaximum(100)
		self.npts.setValue(11)

		# Hysteresis
		self.hist = QCheckBox("Hysteresis Mode")

		# Measure button
		self.submit = QPushButton("Configure Measurement")
		self.submit.clicked.connect(self._config_sweep_measurement)

		# Save data button
		self.meas_button = QPushButton("Measure")
		self.meas_button.clicked.connect(self._exec_sweep_measurement)

		# Save traces 
		self.save_button = QPushButton("Save Traces")
		self.save_button.clicked.connect(self._save_traces)	

		# Measurement Button
		self.ctl_layout.addWidget(self.meas_button)
		self.ctl_layout.addWidget(self.save_button)
		self.ctl_layout.addStretch(1)		

		# Add buttons to box
		self.ctl_layout.addWidget(self.mode_label)
		self.ctl_layout.addWidget(self.mode)
		self.ctl_layout.addWidget(self.cmpl_label)
		self.ctl_layout.addWidget(self.cmpl)
		self.ctl_layout.addWidget(self.start_label)
		self.ctl_layout.addWidget(self.start)
		self.ctl_layout.addWidget(self.stop_label)
		self.ctl_layout.addWidget(self.stop)
		self.ctl_layout.addWidget(self.npts_label)
		self.ctl_layout.addWidget(self.npts)
		self.ctl_layout.addWidget(self.hist)
		self.ctl_layout.addWidget(self.submit)

		# Return the layout
		return self.ctl_layout

	def _save_traces(self):

		# Enforce data/plot consistency
		if self.plot.hlist == []:
			self._data = []

		# Only save if data exists
		if self._data != []:

			dialog = QFileDialog(self)
			dialog.setFileMode(QFileDialog.AnyFile)
			dialog.setViewMode(QFileDialog.Detail)
			filenames = []

			if dialog.exec_():
				filenames = dialog.selectedFiles()
				f = open(filenames[0], 'w+')	

				with f:
				
					for _m in self._data: 

						# Write data header
						f.write("*sweep\n")
						for key in _m.keys():
							f.write("%s\t\t"%str(key))
						f.write("\n")
								
						# Write data values
						for i,_ in enumerate(_m[list(_m.keys())[0]]):
							for key in _m.keys():
								f.write("%s\t"%str(_m[key][i]))
							f.write("\n")

						f.write("\n\n")

				f.close()

		# Warning box in case of no data
		else:		

			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("No measurement data")
			msg.setWindowTitle("Sweep Info")
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()


	# Sweep control dynamic update
	def _update_sweep_control(self):

		# Voltage mode adjust lables and limits
		if self.mode.currentText() == "Voltage":
			self.cmpl_label.setText("Compliance (A)")
			self.cmpl.setMinimum(0.0)
			self.cmpl.setMaximum(1.0)

			self.start_label.setText("Sweep Start (V)")
			self.start.setMinimum(-20.0)
			self.start.setMaximum(20.0)
			self.start.setValue(0.0)

			self.stop_label.setText("Sweep Stop (V)")
			self.stop.setMinimum(-20.0)
			self.stop.setMaximum(20.0)
			self.stop.setValue(1.0)

		# Current mode adjust lables and limits
		if self.mode.currentText() == "Current":
			
			self.cmpl_label.setText("Compliance (V)")
			self.cmpl.setMinimum(0.0)
			self.cmpl.setMaximum(20.0)
			
			self.start_label.setText("Sweep Start (A)")
			self.start.setMinimum(-1.0)
			self.start.setMaximum(1.0)
			self.start.setValue(0.0)

			self.stop_label.setText("Sweep Stop (A)")
			self.stop.setMinimum(-1.0)
			self.stop.setMaximum(1.0)
			self.stop.setValue(0.1)

	# Dynamic Plotting Capability
	def _gen_sweep_plot(self): 		

		# Create QDynamicPlot Object
		self.plot = modules.QDynamicPlot.QDynamicPlot(self)
		self.plot.set_axes_labels("Voltage (V)", "Current (A)")
		self.plot.add_axes()

		# Alias plot layout and return layout
		self.plt_layout = self.plot.layout
		return self.plt_layout

	# Create Measurement 
	def _config_sweep_measurement(self):

		# Enforce data/plot consistency
		if self.plot.hlist == []:
			self._data = []

		# Set up v-source(i-compliance) on keithley 
		if self.mode.currentText() == "Voltage":
			self.keithley.voltage_src()
			self.keithley.current_cmp(self.cmpl.value())

		# Set up i-source(v-compliance) on keithley 
		if self.mode.currentText() == "Current":
			self.keithley.current_src()
			self.keithley.voltage_cmp(self.cmpl.value())

		# Set up measurement object
		self._set_sweep_params(
			self.start.value(), 
			self.stop.value(), 
			self.npts.value(), 
			True if self.hist.checkState()==2 else False)

		# Message box to indicate that sweep variable have been updated
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)
		msg.setText("Sweep Parameters Updated")
		msg.setWindowTitle("Sweep Info")
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()


	# Execute Sweep Measurement
	def _exec_sweep_measurement(self):

		# Enforce data/plot consistency
		if self.plot.hlist == []:
			self._data = []

		if self._get_sweep_params() is not None:

			voltage, current = [],[]
			handle = self.plot.add_handle()

			# Disable measurement button to avoid double click
			self.meas_button.setEnabled(False)

			# Sweep Voltage Mode
			if self.mode.currentText() == "Voltage":

				self.keithley.output_on()
				for _v in self._get_sweep_params():
					
					# Set bias
					self.keithley.set_voltage(_v)

					# Get data from buffer
					_buffer = self.keithley.meas().split(",")

					# Extract data from buffer
					voltage.append(float(_buffer[0]))
					current.append(float(_buffer[1]))

					self.plot.update_handle(handle, float(_buffer[0]), float(_buffer[1]))

				self._data.append({ 
					'V': voltage, 
					'I' : current, 
					'R' : np.gradient(voltage, current), 
					'P' : np.multiply(voltage, current)
				})
				self.keithley.set_voltage(0.0)
				self.keithley.output_off()

			# Sweep Current Mode
			if self.mode.currentText() == "Current":
				
				self.keithley.output_on()
				for _i in self._get_sweep_params():
					
					# Set bias
					self.keithley.set_current(_i)

					# Get data from buffer
					_buffer = self.keithley.meas().split(",")

					# Extract data from buffer
					voltage.append(float(_buffer[0]))
					current.append(float(_buffer[1]))

					self.plot.update_handle(handle, float(_buffer[0]), float(_buffer[1]))

				self._data.append({ 
					'V': voltage, 
					'I' : current, 
					'R' : np.gradient(voltage, current), 
					'P' : np.multiply(voltage, current)
				})
				self.keithley.set_current(0.0)
				self.keithley.output_off()

			# Disable measurement button to avoid double click
			self.meas_button.setEnabled(True)

		# Show warning message if sweep not configured
		else: 
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Sweep not configured")
			msg.setWindowTitle("Sweep Info")
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()