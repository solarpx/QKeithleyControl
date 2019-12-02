# ---------------------------------------------------------------------------------
# 	QKeithleyControl
# 	Copyright (C) 2019 Michael Winters
#	mwchalmers@protonmail.com
# ---------------------------------------------------------------------------------
# 
# 	Permission is hereby granted, free of charge, to any person obtaining a copy
# 	of this software and associated documentation files (the "Software"), to deal
# 	in the Software without restriction, including without limitation the rights
# 	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# 	copies of the Software, and to permit persons to whom the Software is
# 	furnished to do so, subject to the following conditions:
# 	
# 	The above copyright notice and this permission notice shall be included in all
# 	copies or substantial portions of the Software.
# 	
# 	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# 	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# 	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# 	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# 	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# 	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# 	SOFTWARE.
#

#!/usr/bin/env python 
import visa
import time
import numpy as np

# Import d_plot and keithley driver
import drivers.keithley_2400
import widgets.QDynamicPlot 

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

		# Save data button
		self.meas_button = QPushButton("Measure")
		self.meas_button.clicked.connect(self._exec_sweep_measurement)

		# Save traces 
		self.save_button = QPushButton("Save Traces")
		self.save_button.clicked.connect(self._save_traces)	

		# Current/Voltage Sweep Mode 
		self.mode_label = QLabel("Sweep Mode")
		self.mode = QComboBox()
		self.mode.addItems(["Voltage", "Current"])
		self.mode.currentTextChanged.connect(self._update_sweep_control)

		# Sweep Start
		self.start_config={
			"unit" 		: "V",
			"min"		: "u",
			"max"		: "",
			"label"		: "Sweep Start (V)",
			"limit"		: 20.0,
			"signed"	: True,
			"default"	: 0.0
		} 
		self.start = widgets.QUnitSelector.QUnitSelector(self.start_config)

		# Sweep Stop
		self.stop_config={
			"unit" 		: "V",
			"min"		: "u",
			"max"		: "",
			"label"		: "Sweep Start (V)",
			"limit"		: 20.0,
			"signed"	: True,
			"default"	: 1.0
		} 
		self.stop = widgets.QUnitSelector.QUnitSelector(self.stop_config)

		# Compliance Spinbox
		self.cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (A)",
			"limit"		: 1.0, 
			"signed"	: False,
			"default"	: 0.1
		} 
		self.cmpl = widgets.QUnitSelector.QUnitSelector(self.cmpl_config)	

		# Step Spinbox
		self.npts_label = QLabel("Number of Points")
		self.npts = QSpinBox()
		self.npts.setMinimum(1)
		self.npts.setMaximum(100)
		self.npts.setValue(11)

		# Hysteresis
		self.delay_label = QLabel("Measurement Interval (s)")
		self.delay = QDoubleSpinBox()
		self.delay.setDecimals(3)
		self.delay.setMinimum(0.0)
		self.delay.setMaximum(600.0)
		self.delay.setSingleStep(0.1)
		self.delay.setValue(0.1)

		# Hysteresis
		self.hist = QCheckBox("Hysteresis Mode")

		# Measure button
		self.config_button = QPushButton("Configure Sweep")
		self.config_button.clicked.connect(self._config_sweep_measurement)

		# Measurement Button
		self.ctl_layout.addWidget(self.meas_button)
		self.ctl_layout.addWidget(self.save_button)
		self.ctl_layout.addStretch(1)		

		# Add buttons to box
		self.ctl_layout.addWidget(self.mode_label)
		self.ctl_layout.addWidget(self.mode)
		self.ctl_layout.addWidget(self.start)
		self.ctl_layout.addWidget(self.stop)
		self.ctl_layout.addWidget(self.cmpl)
		self.ctl_layout.addWidget(self.npts_label)
		self.ctl_layout.addWidget(self.npts)
		self.ctl_layout.addWidget(self.delay_label)
		self.ctl_layout.addWidget(self.delay)
		self.ctl_layout.addWidget(self.hist)
		self.ctl_layout.addWidget(self.config_button)

		# Return the layout
		return self.ctl_layout

	# Sweep control dynamic update
	def _update_sweep_control(self):

		# Voltage mode adjust lables and limits
		if self.mode.currentText() == "Voltage":

			# Sweep Start
			self.start_config={
				"unit" 		: "V",
				"min"		: "u",
				"max"		: "",
				"label"		: "Sweep Start (V)",
				"limit"		: 20.0,
				"signed"	: True,
				"default"	: 0.0
			} 
			self.start.update_config(self.start_config)

			# Sweep Stop
			self.stop_config={
				"unit" 		: "V",
				"min"		: "u",
				"max"		: "",
				"label"		: "Sweep Start (V)",
				"limit"		: 20.0,
				"signed"	: True,
				"default"	: 1.0
			} 
			self.stop.update_config(self.stop_config)

			# Compliance Spinbox
			self.cmpl_config={
				"unit" 		: "A", 
				"min"		: "u",
				"max"		: "",
				"label"		: "Compliance (A)",
				"limit"		: 1.0, 
				"signed"	: False,
				"default"	: 0.1
			} 
			self.cmpl.update_config(self.cmpl_config)

		# Current mode adjust lables and limits
		if self.mode.currentText() == "Current":
			
			# Sweep Start
			self.start_config={
				"unit" 		: "A",
				"min"		: "u",
				"max"		: "",
				"label"		: "Sweep Start (A)",
				"limit"		: 1.0,
				"signed"	: True,
				"default"	: 0.0
			} 
			self.start.update_config(self.start_config)

			# Sweep Stop
			self.stop_config={
				"unit" 		: "A",
				"min"		: "u",
				"max"		: "",
				"label"		: "Sweep Stop (A)",
				"limit"		: 1.0,
				"signed"	: True,
				"default"	: 0.1
			} 
			self.stop.update_config(self.stop_config)

			# Compliance Spinbox
			self.cmpl_config={
				"unit" 		: "V", 
				"min"		: "u",
				"max"		: "",
				"label"		: "Compliance (V)",
				"limit"		: 20, 
				"signed"	: False,
				"default"	: 1.0
			} 
			self.cmpl.update_config(self.cmpl_config)

	# Dynamic Plotting Capability
	def _gen_sweep_plot(self): 		

		# Create QDynamicPlot Object
		self.plot = widgets.QDynamicPlot.QDynamicPlot(self)
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

			# Disable measurement and save buttons to avoid double click
			self.meas_button.setEnabled(False)
			self.save_button.setEnabled(False)

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

					# Update plot
					self.plot.update_handle(handle, float(_buffer[0]), float(_buffer[1]))

					# Measurement Interval
					if self.delay.value() != 0: 
						time.sleep(self.delay.value())

				self._data.append({ 
					'V': voltage, 
					'I' : current, 
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
	
					# Update plot
					self.plot.update_handle(handle, float(_buffer[0]), float(_buffer[1]))

					# Measurement Interval
					if self.delay.value() != 0: 
						time.sleep(self.delay.value())

				self._data.append({ 
					'V': voltage, 
					'I' : current, 
					'P' : np.multiply(voltage, current)
				})
				self.keithley.set_current(0.0)
				self.keithley.output_off()

			# Disable measurement button to avoid double click
			self.meas_button.setEnabled(True)
			self.save_button.setEnabled(True)

		# Show warning message if sweep not configured
		else: 
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Sweep not configured")
			msg.setWindowTitle("Sweep Info")
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()

	# Method to save data traces
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

			# Message box to indicate successful save
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Information)
			msg.setText("Sweep Data Saved")
			msg.setWindowTitle("Sweep Info")
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()		

		# Warning box in case of no data
		else:		

			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("No measurement data")
			msg.setWindowTitle("Sweep Info")
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()