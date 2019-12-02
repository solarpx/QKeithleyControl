# -----------------------------------------------------------------------
# 	QKeithleyControl
# 	Copyright (C) 2019 mwchalmers
#	mwchalmers@protonmail.com
# -----------------------------------------------------------------------
# 
# 	This program is free software: you can redistribute it and/or modify
# 	it under the terms of the GNU General Public License as published by
# 	the Free Software Foundation, either version 3 of the License, or
# 	(at your option) any later version.
#
# 	This program is distributed in the hope that it will be useful,
# 	but WITHOUT ANY WARRANTY; without even the implied warranty of
# 	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 	GNU General Public License for more details.
#
# 	You should have received a copy of the GNU General Public License
# 	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#!/usr/bin/env python 
import visa
import time
import numpy as np
import threading

# Import d_plot and keithley driver
import drivers.keithley_2400

# Import widgets
import widgets.QDynamicPlot 
import widgets.QUnitSelector

# Import QT backends
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel, QFileDialog
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject

# Import matplotlibQT backends
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

# Container class to construct sweep measurement widget
class QKeithleyBias(QWidget):

	def __init__(self):

		# Inherits QWidget
		QWidget.__init__(self)

		# Initialize Keithley Object
		self.keithley = None

		# Create objects to hold data
		self._data = []
		
		# Create layout objects and set layout
		self.layout = QHBoxLayout()
		self.layout.addLayout(self._gen_bias_control())
		self.layout.addLayout(self._gen_bias_plot())
		self.setLayout(self.layout)

	# Set visa insturment handle for keithley
	def _set_keithley_handle(self, keithley):
		self.keithley=keithley
	
	# Update bias values 
	def _update_bias(self):

		if self.mode.currentText() == "Voltage":

			self.keithley.set_voltage(self.bias.value())
			self.keithley.current_cmp(self.cmpl.value())

		if self.mode.currentText() == "Current":

			self.keithley.set_current(self.bias.value())
			self.keithley.voltage_cmp(self.cmpl.value())


	# Update bias control selectors
	def _update_bias_control(self):

		# Voltage mode adjust lables and limits
		if self.mode.currentText() == "Voltage":

			# Bias spinbox (voltage mode)
			self.bias_config={
				"unit" 		: "V",
				"min"		: "u",
				"max"		: "",
				"label"		: "Bias Level",
				"limit"		: 20.0,
				"signed"	: True,
				"default"	: 0.0
			} 
			self.bias.update_config(self.bias_config)

			# Compliance Spinbox
			self.cmpl_config={
				"unit" 		: "A", 
				"min"		: "u",
				"max"		: "",
				"label"		: "Compliance",
				"limit"		: 1.0, 
				"signed"	: False,
				"default"	: 0.1
			} 
			self.cmpl.update_config(self.cmpl_config)

			# Send commands to keithley
			self.keithley.voltage_src()
			self.keithley.set_voltage(self.bias.value())
			self.keithley.current_cmp(self.cmpl.value())			

			# Update plot axes and refresh
			self.plot.set_axes_labels("Time (s)", "Current (A)")
			self.plot.refresh_axes()

		# Current mode adjust lables and limits
		if self.mode.currentText() == "Current":

			# Bias spinbox (current mode)
			self.bias_config={
				"unit" 		: "A", 
				"min"		: "u",
				"max"		: "",
				"label"		: "Bias Level",
				"limit"		: 1.0,
				"signed"	: True,
				"default" 	: 0.0
			} 
			self.bias.update_config(self.bias_config)

			# Compliance Spinbox
			self.cmpl_config={
				"unit" 		: "V", 
				"min"		: "u",
				"max"		: "",
				"label"		: "Compliance",
				"limit"		: 20.0,
				"signed"	: False,
				"default"	: 1.0
			} 
			self.cmpl.update_config(self.cmpl_config)

			# Send commands to keithley
			self.keithley.current_src()
			self.keithley.voltage_cmp(self.cmpl.value())
			self.keithley.set_current(self.bias.value())

			# Update plot axes and refresh
			self.plot.set_axes_labels("Time (s)", "Voltage (V)")
			self.plot.refresh_axes()

		# Enforce data/plot consistency
		if self.plot.hlist == []:
			self._data = []	

	# Generate bias control
	def _gen_bias_control(self):

		# Control layout
		self.ctl_layout = QVBoxLayout()

		# Create QStateMachine for output state
		self.output = QStateMachine()
		self.output_button = QPushButton()
		self.output_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create output states
		self.output_off = QState()
		self.output_on  = QState()

		# Attach states to output button and define state transitions
		self.output_off.assignProperty(self.output_button, 'text', 'Output Off')
		self.output_off.addTransition(self.output_button.clicked, self.output_on)
		self.output_off.entered.connect(self._exec_output_off)

		self.output_on.assignProperty(self.output_button, 'text', 'Output On')
		self.output_on.addTransition(self.output_button.clicked, self.output_off)
		self.output_on.entered.connect(self._exec_output_on)
		
		# Add states, set initial state, and start machine
		self.output.addState(self.output_off)
		self.output.addState(self.output_on)
		self.output.setInitialState(self.output_off)
		self.output.start()

		# Save Button 
		self.save_button = QPushButton("Save Traces")
		self.save_button.clicked.connect(self._save_traces)	

		# Current/Voltage Sweep Mode 
		self.mode_label = QLabel("Bias Mode")
		self.mode = QComboBox()
		self.mode.addItems(["Voltage", "Current"])	
		self.mode.currentTextChanged.connect(self._update_bias_control)


		# Configuration for bias level unit box
		self.bias_config={
			"unit" 		: "V", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Bias Level",
			"limit"		: 20.0, 
			"signed"	: True,
			"default"	: 0.0
		} 
		self.bias = widgets.QUnitSelector.QUnitSelector(self.bias_config)


		# Compliance Spinbox
		self.cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance",
			"limit"		: 1.0, 
			"signed"	: False,
			"default"	: 0.1
		} 
		self.cmpl = widgets.QUnitSelector.QUnitSelector(self.cmpl_config)	

		# Delay
		self.delay_label = QLabel("Interval (s)")
		self.delay = QDoubleSpinBox()
		self.delay.setDecimals(3)
		self.delay.setMinimum(0.0)
		self.delay.setMaximum(1.0)
		self.delay.setSingleStep(0.01)
		self.delay.setValue(0.1)

		# Update 
		self.update_button = QPushButton("Change Bias")
		self.update_button.clicked.connect(self._update_bias)	

		# Add output/save buttons to layout
		self.ctl_layout.addWidget(self.output_button)
		self.ctl_layout.addWidget(self.save_button)

		# Spacer
		self.ctl_layout.addStretch(1)
	
		# Add remaining controls to layout
		self.ctl_layout.addWidget(self.mode_label)
		self.ctl_layout.addWidget(self.mode)
		self.ctl_layout.addWidget(self.bias)
		self.ctl_layout.addWidget(self.cmpl)
		self.ctl_layout.addWidget(self.delay_label)
		self.ctl_layout.addWidget(self.delay)
		self.ctl_layout.addWidget(self.update_button)

		return self.ctl_layout

	# Measurement thread
	def _exec_output_thread(self):	

		# Voltage and current arrays
		self._time, self._voltage, self._current = [],[],[]
		handle = self.plot.add_handle()
		start  = time.time()
		
		# Thread loop
		while self.thread_running:

			# Get data from buffer
			_buffer = self.keithley.meas().split(",")

			if self.mode.currentText() == "Current":
				_plt_data = _buffer[0]

			if self.mode.currentText() == "Voltage":
				_plt_data = _buffer[1]

			# Extract data from buffer
			self._time.append(float( time.time() - start ))
			self._voltage.append(float(_buffer[0]))
			self._current.append(float(_buffer[1]))

			self.plot.update_handle(handle, float(time.time() - start), float(_plt_data))

			if self.delay.value() != 0: 
				time.sleep(self.delay.value())

	# UI output on state (measurement)
	def _exec_output_on(self):
		
		if self.keithley is not None:

			# Update UI for ON state
			self.output_button.setStyleSheet(
				"background-color: #cce6ff; border-style: solid; border-width: 1px; border-color: #1a75ff; padding: 7px;")
			self.save_button.setEnabled(False)
			self.mode.setEnabled(False)

			# Turn output ON
			self.keithley.output_on()

			# Create execution thread for measurement
			self.thread = threading.Thread(target=self._exec_output_thread, args=())
			self.thread.daemon = True						# Daemonize thread
			self.thread.start()         					# Start the execution
			self.thread_running = True

	# UI output on state
	def _exec_output_off(self):

		if self.keithley is not None:

			# Update UI for OFF state
			self.output_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )			
			
			self.save_button.setEnabled(True)
			self.mode.setEnabled(True)

			# Kill measurement thread
			self.thread_running = False
			self.thread.join()  # Waits for thread to complete

			# If time variable contains data, append data to array
			if self._time != []:

				self._data.append({ 
						't' : self._time, 
						'V' : self._voltage, 
						'I' : self._current,  
						'P' : np.multiply(self._voltage, self._current)
				})

			# Turn output OFF
			self.keithley.output_off()	

	# Dynamic Plotting Capability
	def _gen_bias_plot(self): 		

		# Create QDynamicPlot Object
		self.plot = widgets.QDynamicPlot.QDynamicPlot(self)
		self.plot.set_axes_labels("Time (s)", "Current (A)")
		self.plot.add_axes()

		# Alias plot layout and return layout
		self.plt_layout = self.plot.layout
		return self.plt_layout

	# Sace traces method (same as sweep control)	
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
						f.write("*bias\n")
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