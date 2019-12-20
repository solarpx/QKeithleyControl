# ---------------------------------------------------------------------------------
# 	QKeithleyBiasWidget -> QWidget
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
import numpy as np
import threading
import time

# Import QT backends
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QPushButton, QLabel, QStackedWidget
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject
from PyQt5.QtGui import QIcon


# Import PyQtVisa widgets
from PyQtVisa.widgets import QVisaUnitSelector
from PyQtVisa.widgets import QVisaDynamicPlot 

# Container class for Keithley to render keithley controls in the bias appicaton. 
# QKeithleyBiasWidget is not itself a widget, but it contains several widgets. Note 
# that _app must be QVisaApplication widget

class QKeithleyBiasWidget:

	def __init__(self, _app, _name):

		# Cache a reference to the calling application 
		self._app  = _app
		self._name = _name

		# Set thread variables 
		self.thread, self.thread_running = None, False

		# Generate widgets
		self.gen_ctrl_widget()
		self.gen_plot_widget()
		self.gen_output_widget()

		# Reset the keithley
		if self._name != "__none__":
			
			self.keithley().rst()
			self.keithley().set_voltage( self.voltage_bias.value() )
			self.keithley().current_cmp( self.voltage_cmpl.value() )

	def keithley(self):		
		return self._app.get_device_by_name( self._name )

	#####################################
	# APPLICATION HELPER METHODS
	#

	def get_output_widget(self):
		return self.output_widget[0]

	def get_ctrl_widget(self):
		return 	self.ctl_widget

	def get_plot_widget(self):
		return 	self.plot_stack

	# Create a QStateMachine and output button for each connected insturment
	def gen_output_widget(self):
		
		if self._name != "__none__":

			# Each output is a tuple [QPushButton, QStateMachine]
			self.output_widget = ( QPushButton(),  QStateMachine() )
			self.output_widget[0].setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )			
				
			# Create output states
			output_off = QState()
			output_on  = QState()

			# Attach states to output button and define state transitions
			output_off.assignProperty(self.output_widget[0], 'text', "%s Output On"%self._name.split()[1])
			output_off.addTransition(self.output_widget[0].clicked, output_on)
			output_off.entered.connect(self.exec_output_off)

			output_on.assignProperty(self.output_widget[0], 'text','%s Output Off'%self._name.split()[1])
			output_on.addTransition(self.output_widget[0].clicked, output_off)
			output_on.entered.connect(self.exec_output_on)
				
			# Add states, set initial state, and start machine
			self.output_widget[1].addState(output_off)
			self.output_widget[1].addState(output_on)
			self.output_widget[1].setInitialState(output_off)
			self.output_widget[1].start()	

		else:
			
			self.output_widget = ( QPushButton(), False )
			self.output_widget[0].setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )	
			self.output_widget[0].setEnabled(False)
			self.output_widget[0].setText("Keithley not Initialized")
	
	# Generate bias control widget
	def gen_ctrl_widget(self):

		# Control layout
		self.ctl_widget = QWidget()
		self.ctl_layout = QVBoxLayout()
		
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

		# Disable controls if "__none__ passed as name"
		if self._name == "__none__":
			self.src_select_label.setEnabled(False)
			self.src_select.setEnabled(False)
			self.src_pages.setEnabled(False)

		#####################################
		#  ADD CONTROLS
		#

		# Main output and controls
		self.ctl_layout.addWidget(self._app._gen_hbox_widget([self.src_select, self.src_select_label]))
		self.ctl_layout.addWidget(self.src_pages)
		self.ctl_layout.setContentsMargins(0,0,0,0)
				
		# Set layouth
		self.ctl_widget.setLayout(self.ctl_layout)

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
		self.voltage_bias = QVisaUnitSelector.QVisaUnitSelector(self.voltage_bias_config)
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
		self.voltage_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.voltage_cmpl_config)	
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
		self.voltage_delay = QVisaUnitSelector.QVisaUnitSelector(self.voltage_delay_config)

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
		self.current_bias = QVisaUnitSelector.QVisaUnitSelector(self.current_bias_config)
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
		self.current_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.current_cmpl_config)	
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
		self.current_delay = QVisaUnitSelector.QVisaUnitSelector(self.current_delay_config)

		# Pack selectors into layout
		self.current_layout.addWidget(self.current_bias)
		self.current_layout.addWidget(self.current_cmpl)
		self.current_layout.addWidget(self.current_delay)
		self.current_layout.setContentsMargins(0,0,0,0)
	
		# Set layout 
		self.current_src.setLayout(self.current_layout)	

	# Dynamic Plotting Capability
	def gen_plot_widget(self): 		

		# Create QVisaDynamicPlot Object (inherits QWidget) 
		self.voltage_plot = QVisaDynamicPlot.QVisaDynamicPlot(self._app)
		self.voltage_plot.add_subplot("111")
		self.voltage_plot.set_axes_labels("111", "Time (s)", "Current (A)")

		self.voltage_plot.refresh_canvas(supress_warning=True)	

		# Create QVisaDynamicPlot Object (inherits QWidget) 
		self.current_plot = QVisaDynamicPlot.QVisaDynamicPlot(self._app)
		self.current_plot.add_subplot("111")
		self.current_plot.set_axes_labels("111", "Time (s)", "Voltage (V)")
		self.current_plot.refresh_canvas(supress_warning=True)	

		# Add to plot stack
		self.plot_stack = QStackedWidget()
		self.plot_stack.addWidget(self.voltage_plot)
		self.plot_stack.addWidget(self.current_plot)
		self.plot_stack.setCurrentIndex(0)

		# Sync plot clear data button with application data
		self.voltage_plot.sync_application_data(True)
		self.current_plot.sync_application_data(True)


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

			# Update src_pages and plot
			self.src_pages.setCurrentIndex(0)
			self.plot_stack.setCurrentIndex(0)

			# Keithley to voltage source
			if self.keithley() is not None:

				self.keithley().voltage_src()
				self.update_bias()
				self.update_cmpl()

		# Switch to current page	
		if self.src_select.currentText() == "Current":

			# Update src_pages and plot
			self.src_pages.setCurrentIndex(1)
			self.plot_stack.setCurrentIndex(1)

			# Keithley to current source
			if self.keithley() is not None:
	
				self.keithley().current_src()
				self.update_bias()
				self.update_cmpl()


	#####################################
	#  MEASUREMENT EXECUTION THREADS
	#			

	# Measurement thread
	def exec_output_thread(self):	

		# Check mesurement type for datafile
		if self.src_select.currentText() == "Voltage":
			_type = "v-bias"

		if self.src_select.currentText() == "Current":
			_type = "i-bias"


		# Get QVisaDataObject
		data = self._app._get_data_object()
		key  = data.add_hash_key(_type)

		# Add data fields to key
		data.set_subkeys(key, ["t", "V", "I", "P"])
		data.set_metadata(key, "__type__", _type)
	
		# Voltage and current arrays	
		_plot  = self.plot_stack.currentWidget()
		handle = _plot.add_axes_handle("111", key)
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
			_now = float(time.time() - start)

			# Append measured values to data arrays
			data.append_subkey_data(key, "t", _now )
			data.append_subkey_data(key, "V", float(_buffer[0]) )
			data.append_subkey_data(key, "I", float(_buffer[1]) )
			data.append_subkey_data(key, "P", float(_buffer[0]) * float(_buffer[1]) ) 

			# Append data to handle
			_plot.append_handle_data("111", key, _now, float(_p))
			_plot.update_canvas()


	# UI output on state (measurement)
	def exec_output_on(self):

		if self.keithley() is not None:

			# Update UI for ON state
			self.output_widget[0].setStyleSheet(
				"background-color: #cce6ff; border-style: solid; border-width: 1px; border-color: #1a75ff; padding: 7px;")
			
			# Disable controls
			self.src_select.setEnabled(False)
			self.voltage_cmpl.setEnabled(False)
			self.current_cmpl.setEnabled(False)
			_plot = self.plot_stack.currentWidget()
			_plot.mpl_refresh_setEnabled(False)

			# Disable save widget if it exists
			if hasattr(self._app, 'save_widget'):
				self._app.save_widget.setEnabled(False)

			# Turn output ON
			self.keithley().output_on()

			# Each output is a list [QPushButton, QStateMachine, thrading.Thread, threadRunning(bool)]
			# Create execution thread for measurement
			self.thread = threading.Thread(target=self.exec_output_thread, args=())
			self.thread.daemon = True		# Daemonize thread
			self.thread.start()			# Start the execution
			self.thread_running = True

	# UI output on state
	def exec_output_off(self):

		if self.keithley() is not None:

			# Get output name from inst_widget
			self.output_widget[0].setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )			

			# Set thread halt boolean
			self.thread_running = False

			# Wait for thread termination
			if self.thread is not None:
				self.thread.join()
	
			# Enable controls
			self.src_select.setEnabled(True)
			self.voltage_cmpl.setEnabled(True)
			self.current_cmpl.setEnabled(True)
			_plot = self.plot_stack.currentWidget()
			_plot.mpl_refresh_setEnabled(True)

			# Enable save widget if it exists
			if hasattr(self._app, 'save_widget'):
				self._app.save_widget.setEnabled(True)


			# Turn output OFF
			self.keithley().output_off()
