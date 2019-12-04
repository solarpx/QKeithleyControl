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
import threading

# Import d_plot and keithley driver
import drivers.keithley_2400

# Import widgets
import widgets.QDynamicPlot 
import widgets.QUnitSelector

# Import QT backends
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel, QFileDialog, QLineEdit
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject
from PyQt5.QtGui import QIcon

# Container class to construct sweep measurement widget
class QKeithleyBias(QWidget):

	def __init__(self):

		# Inherits QWidget
		QWidget.__init__(self)

		# Create Icon for QMessageBox
		self.icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico"))	

		# Initialize Keithley Object
		self.keithley = None

		# Create objects to hold data
		self._data = []
		
		# Create layout objects and set layout
		self.layout = QHBoxLayout()
		self.layout.addLayout(self._gen_bias_control())
		self.layout.addWidget(self._gen_bias_plot())
		self.setLayout(self.layout)

	# Helper method to generate QHBoxLayouts
	def _gen_hboxlayout(self, _widget_list):
	
		_layout = QHBoxLayout()
		for _w in _widget_list:
			_layout.addWidget(_w)
		return _layout

	# Set visa insturment handle for keithley
	def _set_keithley_handle(self, keithley):
		self.keithley=keithley
	
	# Method to reset sweep on window switch
	def _reset_defaults(self):
		self.sweep = []
		self._data = []
		self.plot._refresh_axes() 

	# Generate bias control
	def _gen_bias_control(self):

		# Control layout
		self.ctl_layout = QVBoxLayout()


		#####################################
		#  OUTPUT STATE MACHINE AND BUTTON
		#		

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

		# Main mode selctor 
		self.mode_label = QLabel("Bias Mode")
		self.mode = QComboBox()
		self.mode.setFixedWidth(200)
		self.mode.addItems(["Voltage", "Current"])	
		self.mode.currentTextChanged.connect(self._update_bias_control)

		#####################################
		#  BIAS MEASUREMENT CONFIGURATION 
		#

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
		
		# Measurement Delay
		self.delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: 0.1
		}
		self.delay = widgets.QUnitSelector.QUnitSelector(self.delay_config)


		# Update 
		self.update_button = QPushButton("Change Bias")
		self.update_button.clicked.connect(self._update_bias)	

		#####################################
		#  SAVE BUTTON
		#

		# Save Button
		self.save_note_label = QLabel("Measurement Note")
		self.save_note = QLineEdit()
		self.save_note.setFixedWidth(200)
		self.save_button = QPushButton("Save Traces")
		self.save_button.clicked.connect(self._save_traces)	

		#####################################
		#  ADD CONTROLS
		#

		# Main output
		self.ctl_layout.addWidget(self.output_button)

		# Additional controls
		self.ctl_layout.addStretch(1)
		self.ctl_layout.addWidget(self.update_button)
		_layout = self._gen_hboxlayout([self.mode, self.mode_label])
		self.ctl_layout.addLayout(_layout)
		self.ctl_layout.addWidget(self.bias)
		self.ctl_layout.addWidget(self.cmpl)
		self.ctl_layout.addWidget(self.delay)
		
		# Spacer
		self.ctl_layout.addStretch(1)
		self.ctl_layout.addWidget(self.save_button)
		_layout = self._gen_hboxlayout([self.save_note, self.save_note_label])
		self.ctl_layout.addLayout(_layout)
	
		# Positioning
		self.ctl_layout.setContentsMargins(0,15,0,20)
		return self.ctl_layout

	# Update bias values 
	def _update_bias(self):

		if self.mode.currentText() == "Voltage":

			self.keithley.set_voltage(self.bias.value())
			self.keithley.current_cmp(self.cmpl.value())

		if self.mode.currentText() == "Current":

			self.keithley.set_current(self.bias.value())
			self.keithley.voltage_cmp(self.cmpl.value())

		# Message box to indicate successful save
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)
		msg.setText("%s bias updated"%self.mode.currentText())
		msg.setWindowTitle("Bias Info")
		msg.setWindowIcon(self.icon)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()		

	# Update bias control selectors
	def _update_bias_control(self):

		# Call refresh axes to engage dialogue
		self.plot.refresh_axes()

		# If answer is no, then revert state
		if self.plot.msg_clear == QMessageBox.No:

			# Revert back to current mode. Note we need to block signals on 
			# the QComboBox object so setCurrentIndex does not fire an unwanted
			# currentTextChanged signal creating unwanted recursive call in 
			# the self._update_bias_control function.
			if self.mode.currentText() == "Voltage":

				self.mode.blockSignals(True)
				self.mode.setCurrentIndex(1)
				self.mode.blockSignals(False)
				return

			# Revert back to voltage Mode
			if self.mode.currentText() == "Current":
				self.mode.blockSignals(True)
				self.mode.setCurrentIndex(0)
				self.mode.blockSignals(False)
				return

		# If answer is yes, then clear and update controls
		else:

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
				self.plot._refresh_axes() # Here we call the internal method (no dialogue)

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
				self.plot._refresh_axes() # Here we call the internal method (no dialogue)

			# Enforce data/plot consistency
			if self.plot.hlist == []:
				self._data = []	



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


			# Zero storage arrays
			self._time, self._voltage, self._current = [],[],[]	

			# Turn output OFF
			self.keithley.output_off()	

	# Dynamic Plotting Capability
	def _gen_bias_plot(self): 		

		# Create QDynamicPlot Object (inherits QWidget) 
		self.plot = widgets.QDynamicPlot.QDynamicPlot()
		self.plot.set_axes_labels("Time (s)", "Current (A)")
		self.plot.add_axes()

		return self.plot

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

			# Message box to indicate successful save
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Information)
			msg.setText("Measurement data saved")
			msg.setWindowTitle("Bias Info")
			msg.setWindowIcon(self.icon)
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()	

		# Warning box in case of no data
		else:		
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("No measurement data")
			msg.setWindowTitle("Bias Info")
			msg.setWindowIcon(self.icon)
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()