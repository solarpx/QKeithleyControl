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
import os
import sys
import time
import threading

# Import visa and numpy
import visa
import numpy as np

# Import custom widgets
import widgets.QVisaWidget
import widgets.QDynamicPlot 
import widgets.QUnitSelector

# Import QT backends
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QPushButton, QLabel, QFileDialog, QLineEdit, QStackedWidget
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject
from PyQt5.QtGui import QIcon

# Container class to construct sweep measurement widget
class QKeithleyBias(widgets.QVisaWidget.QVisaWidget):

	def __init__(self, _config):

		# Inherits QVisaWidget -> QWidget
		super(QKeithleyBias, self).__init__(_config)

		# Generate Main Layout
		self.gen_main_layout()

	#####################################
	# WIDGET HELPER METHODS
	#

	# Wrapper method to get keitley write handle
	# 	Returns the pyVisaDevice object
	def keithley(self):
		return self._config._get_inst_byname(self.inst_select.currentText())

	# Method to refresh the widget
	def refresh(self):

		# Reset the widget
		self.inst_select.clear()
		self.inst_select.addItems(self._config._get_inst_names())
	
		# Reset the keithley
		self.keithley().reset()
		self.keithley().set_voltage( self.voltage_bias.value() )
		self.keithley().current_cmp( self.voltage_cmpl.value() )


	#####################################
	# BIAS MODE MAIN LAYOUTS
	#
	# *) gem_main_layout()
	# 	1) gen_bias_ctrl()
	# 		a) gen_voltage_src()
	#		b) gen_current_src()
	#	2) gen_bias_plot()
	#

	# Main Layout
	def gen_main_layout(self):	

		# Create Icon for QMessageBox
		self.icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico"))	
		
		# Create layout objects and set layout
		self.layout = QHBoxLayout()
		self.layout.addLayout(self.gen_bias_ctrl())
		self.layout.addWidget(self.gen_bias_plot())
		self.setLayout(self.layout)

	# Generate bias control
	def gen_bias_ctrl(self):

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
		self.output_off.entered.connect(self.exec_output_off)

		self.output_on.assignProperty(self.output_button, 'text', 'Output On')
		self.output_on.addTransition(self.output_button.clicked, self.output_off)
		self.output_on.entered.connect(self.exec_output_on)
		
		# Add states, set initial state, and start machine
		self.output.addState(self.output_off)
		self.output.addState(self.output_on)
		self.output.setInitialState(self.output_off)
		self.output.start()

		# Add insturement selector
		self.inst_select_label = QLabel("Select Device")
		self.inst_select = QComboBox()
		self.inst_select.setFixedWidth(200)
	
		# Main mode selctor 
		self.src_select_label = QLabel("Bias Mode")
		self.src_select = QComboBox()
		self.src_select.setFixedWidth(200)
		self.src_select.addItems(["Voltage", "Current"])	
		self.src_select.currentTextChanged.connect(self.update_bias_ctrl)

		# Generate voltage and current source widgets
		self.gen_voltage_src()		# self.voltage_src
		self.gen_current_src()		# self.current_src

		# Add to stacked widget
		self.src_pages = QStackedWidget()
		self.src_pages.addWidget(self.voltage_src)
		self.src_pages.addWidget(self.current_src)
		self.src_pages.setCurrentIndex(0)

		#####################################
		#  SAVE BUTTON
		#

		# Save Button
		self.save_note_label = QLabel("Measurement Note")
		self.save_note = QLineEdit()
		self.save_note.setFixedWidth(200)
		self.save_button = QPushButton("Save Traces")
		self.save_button.clicked.connect(self._gen_data_file)	

		#####################################
		#  ADD CONTROLS
		#

		# Main output and controls
		self.ctl_layout.addWidget(self.output_button)
		self.ctl_layout.addWidget(self._gen_hbox_widget([self.inst_select, self.inst_select_label]))
		self.ctl_layout.addWidget(self._gen_hbox_widget([self.src_select, self.src_select_label]))
		self.ctl_layout.addWidget(self.src_pages)
		
		# Spacer
		self.ctl_layout.addStretch(1)
		self.ctl_layout.addWidget(self._gen_hbox_widget([self.save_note, self.save_note_label]))
		self.ctl_layout.addWidget(self.save_button)
	
		# Positioning
		self.ctl_layout.setContentsMargins(0,15,0,20)
		return self.ctl_layout
	
	# Generate voltage and current sources
	def gen_voltage_src(self):

		# New QWidget
		self.voltage_src = QWidget()
		self.voltage_layout = QVBoxLayout()

		# Configuration for bias level unit box
		self.voltage_bias_config={
			"unit" 		: "V", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Bias Level",
			"limit"		: 20.0, 
			"signed"	: True,
			"default"	: [0.0, ""]
		} 
		self.voltage_bias = widgets.QUnitSelector.QUnitSelector(self.voltage_bias_config)
		self.voltage_bias.unit_value.valueChanged.connect(self.update_bias)
		self.voltage_bias.unit_select.currentTextChanged.connect(self.update_bias)

		# Compliance Spinbox
		self.voltage_cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance",
			"limit"		: 1.0, 
			"signed"	: False,
			"default"	: [100, "m"]
		} 
		self.voltage_cmpl = widgets.QUnitSelector.QUnitSelector(self.voltage_cmpl_config)	
		self.voltage_cmpl.unit_value.valueChanged.connect(self.update_cmpl)
		self.voltage_cmpl.unit_select.currentTextChanged.connect(self.update_cmpl)

		# Measurement Delay
		self.voltage_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: [0.1]
		}
		self.voltage_delay = widgets.QUnitSelector.QUnitSelector(self.voltage_delay_config)

		# Pack selectors into layout
		self.voltage_layout.addWidget(self.voltage_bias)
		self.voltage_layout.addWidget(self.voltage_cmpl)
		self.voltage_layout.addWidget(self.voltage_delay)
		self.voltage_layout.setContentsMargins(0,0,0,0)

		# Set layout 
		self.voltage_src.setLayout(self.voltage_layout)

	def gen_current_src(self):

		# New QWidget
		self.current_src = QWidget()
		self.current_layout = QVBoxLayout()

		# Configuration for bias level unit box
		self.current_bias_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Bias Level",
			"limit"		: 1.0,
			"signed"	: True,
			"default" 	: [1.0, "m"]
		} 
		self.current_bias = widgets.QUnitSelector.QUnitSelector(self.current_bias_config)
		self.current_bias.unit_value.valueChanged.connect(self.update_bias)
		self.current_bias.unit_select.currentTextChanged.connect(self.update_bias)

		# Compliance Spinbox
		self.current_cmpl_config={
			"unit" 		: "V", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance",
			"limit"		: 1.0, 
			"signed"	: False,
			"default"	: [1, ""]
		} 
		self.current_cmpl = widgets.QUnitSelector.QUnitSelector(self.current_cmpl_config)	
		self.current_cmpl.unit_value.valueChanged.connect(self.update_cmpl)
		self.current_cmpl.unit_select.currentTextChanged.connect(self.update_cmpl)

		# Measurement Delay
		self.current_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: [0.1]
		}
		self.current_delay = widgets.QUnitSelector.QUnitSelector(self.current_delay_config)

		# Pack selectors into layout
		self.current_layout.addWidget(self.current_bias)
		self.current_layout.addWidget(self.current_cmpl)
		self.current_layout.addWidget(self.current_delay)
		self.current_layout.setContentsMargins(0,0,0,0)
	
		# Set layout 
		self.current_src.setLayout(self.current_layout)	

	# Dynamic Plotting Capability
	def gen_bias_plot(self): 		

		# Create QDynamicPlot Object (inherits QWidget) 
		self.plot = widgets.QDynamicPlot.QDynamicPlot()
		self.plot.set_axes_labels("Time (s)", "Current (A)")
		self.plot.add_axes()

		return self.plot

	#####################################
	#  BIAS CONTROL UPDATE METHODS
	#	

	# Update bias values 
	def update_bias(self):

		if self.src_select.currentText() == "Voltage":
		 	self.keithley().set_voltage( self.voltage_bias.value() )

		if self.src_select.currentText() == "Current":
		 	self.keithley().set_current( self.current_bias.value() )

	# Update compliance values 
	def update_cmpl(self):

		if self.src_select.currentText() == "Voltage":
		 	self.keithley().current_cmp( self.voltage_cmpl.value() )

		if self.src_select.currentText() == "Current":
		 	self.keithley().voltage_cmp( self.current_cmpl.value() )
	
	# Update bias control selectors
	def update_bias_ctrl(self):
	
		# Switch to voltage page
		if self.src_select.currentText() == "Voltage":
			self.src_pages.setCurrentIndex(0)

			# Keithley to voltage source
			self.keithley().voltage_src()
			self.update_bias()
			self.update_cmpl()

			# Update plot axes and refresh
			self.plot.set_axes_labels("Time (s)", "Current (A)")
			self.plot._refresh_axes() # Here we call the internal method (no dialogue)

		# Switch to current page	
		if self.src_select.currentText() == "Current":

			self.src_pages.setCurrentIndex(1)

			# Keithley to current source
			self.keithley().current_src()
			self.update_bias()
			self.update_cmpl()

			# Update plot axes and refresh
			self.plot.set_axes_labels("Time (s)", "Voltage (V)")
			self.plot._refresh_axes() # Here we call the internal method (no dialogue)


		# Enforce data/plot consistency
		if self.plot.hlist == []:
			self._reset_data()	


	#####################################
	#  MEASUREMENT EXECUTION THREADS
	#			

	# Measurement thread
	def exec_output_thread(self):	

		# Create a unique data key
		m = hashlib.sha256()
		m.update(str("bias@%s"%str(time.time())).encode() )		
		m.hexdigest()[:7]

		# Measurement key
		_meas_key = "bias %s"%m.hexdigest()[:6]

		# Add to data
		self._add_meas_key(_meas_key)
		self._set_data_fields(_meas_key, ["t", "V", "I", "P"])

		# Voltage and current arrays
		handle = self.plot.add_handle()
		start  = time.time()
		
		# Thread loop
		while self.thread_running:

			# Get data from buffer
			_buffer = self.keithley().meas().split(",")

			# If in current mode, plot voltage
			if self.src_select.currentText() == "Current":
				_p = _buffer[0]

				# Measurement delay 
				if self.current_delay.value() != 0: 
					time.sleep(self.current_delay.value())

			# It in voltage mode plot current		
			if self.src_select.currentText() == "Voltage":
				_p = _buffer[1]

				# Measurement delay 
				if self.voltage_delay.value() != 0: 
					time.sleep(self.voltage_delay.value())

			# Extract data from buffer
			self._data[_meas_key]["t"].append( float( time.time() - start ) )
			self._data[_meas_key]["V"].append( float(_buffer[0]) )
			self._data[_meas_key]["I"].append( float(_buffer[1]) )
			self._data[_meas_key]["P"].append( float(_buffer[0]) * float(_buffer[1]) )

			self.plot.update_handle(handle, float(time.time() - start), float(_p))
			self.plot._draw_canvas()


	# UI output on state (measurement)
	def exec_output_on(self):

		if self.keithley() is not None:

			# Update UI for ON state
			self.output_button.setStyleSheet(
				"background-color: #cce6ff; border-style: solid; border-width: 1px; border-color: #1a75ff; padding: 7px;")
			self.save_button.setEnabled(False)
			self.src_select.setEnabled(False)

			# Turn output ON
			self.keithley().output_on()

			# Create execution thread for measurement
			self.thread = threading.Thread(target=self.exec_output_thread, args=())
			self.thread.daemon = True						# Daemonize thread
			self.thread.start()         					# Start the execution
			self.thread_running = True

	# UI output on state
	def exec_output_off(self):

		if self.keithley() is not None:

			# Update UI for OFF state
			self.output_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )			
			
			self.save_button.setEnabled(True)
			self.src_select.setEnabled(True)

			# Kill measurement thread
			self.thread_running = False
			self.thread.join()  # Waits for thread to complete

			# Turn output OFF
			self.keithley().output_off()
