# ---------------------------------------------------------------------------------
# 	QKeithleySolar -> QVisaApplication 
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
import hashlib
import threading 

# Import visa and numpy
import visa
import numpy as np

# Import widgets
import widgets.QVisaApplication
import widgets.QVisaUnitSelector
import widgets.QVisaDynamicPlot 

# Import QT backends
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel, QFileDialog, QSizePolicy, QLineEdit
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject
from PyQt5.QtGui import QIcon

# Container class to construct photovoltaic characterization widget
class QKeithleySolar(widgets.QVisaApplication.QVisaApplication):

	
	def __init__(self, _config):

		# Inherits QVisaApplication -> QWidget
		super(QKeithleySolar, self).__init__(_config)

		# Generate Main Layout
		self.gen_main_layout()


	#####################################
	# WIDGET HELPER METHODS
	#

	# Wrapper method to get keitley write handle
	# 	Returns the pyVisaDevice object
	def keithley(self):
		return self._get_inst_byname( self.inst_widget.currentText() )

	# Method to refresh the widget
	def refresh(self):
	
		# If add insturments have been initialized
		if self._get_inst_handles() is not None:

			# Reset the widget and add insturments
			self.inst_widget.refresh( self )

			# Enable measurement buttons
			self.iv_meas_button.setEnabled(True)
			self.voc_meas_button.setEnabled(True)
			self.mpp_meas_button.setEnabled(True)

		else:
			
			# Disable measurement buttons
			self.iv_meas_button.setEnabled(False)
			self.voc_meas_button.setEnabled(False)
			self.mpp_meas_button.setEnabled(False)	



	#def set_sweep_params(self):
	# 	_start = self.iv_start.value()
	# 	_stop  = self.iv_stop.value()
	# 	_npts  = self.iv_npts.value()
	# 	return np.linspace(float(_start), float(_stop), int(_npts))


	# # Reset data function
	# def _reset_data(self):		

	# 	# Refresh data dictionary
	# 	self.iv_plot._refresh_axes()
	# 	self.voc_plot._refresh_axes()
	# 	self.mpp_plot._refresh_axes()
	# 	self._data = {"IV" : None, "Voc" : None, "MPP" : None}
	# # Set sweep parameters
	
	# # Get sweep parameters
	# def _get_sweep_params(self):
	# 	return self.sweep if self.sweep != [] else None	

	# # Update bias from spinbox
	# def _update_bias(self, _value):
	# 	self.keithley.set_voltage(_value)		


	#####################################
	# SOLAR APP MAIN LAYOUTS
	#
	# *) gen_main_layout()
	# 	1) gen_solar_ctrl()
	# 		a) gen_sweep_ctrl()
	#		b) gen_voc_ctrl()
	# 		c) gen_mpp_crtl()
	#	2) gen_solar_plot()
	#		

	def gen_main_layout(self):
	
		# Create Icon for QMessageBox
		self._set_icon( QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico")) )
		
		# Create layout objects and set layout
		self.layout = QHBoxLayout()
		self.layout.addLayout(self.gen_solar_ctrl())
		self.layout.addWidget(self.gen_solar_plot())
		self.setLayout(self.layout)
		

	# Method to generate solar characterization controls
	def gen_solar_ctrl(self):

		# Solar mode layout
		self.ctl_layout = QVBoxLayout()

		# Add insturement selector
		self.inst_widget = self._gen_inst_widget()
		self.save_widget = self._gen_save_widget()

		# Generate (IV, Voc, MPP) container widgets
		# These methods will pack self.inst_select
		self.gen_iv_ctrl()				# self.iv_ctrl
		self.gen_voc_ctrl() 			# self.voc_ctrl
		self.gen_mpp_ctrl()				# self.mpp_ctrl

		# Add measurement widgets to QStackedWidget
		self.meas_pages = QStackedWidget()
		self.meas_pages.addWidget(self.iv_ctrl)
		self.meas_pages.addWidget(self.voc_ctrl)
		self.meas_pages.addWidget(self.mpp_ctrl)
		self.meas_pages.setCurrentIndex(0);
	
		# Measurement select QComboBox
		self.meas_select_label = QLabel("Measurement Mode")
		self.meas_select = QComboBox()
		self.meas_select.setFixedWidth(200)
		self.meas_select.addItems(["IV", "Voc", "MPP"])
		self.meas_select.currentTextChanged.connect(self.update_meas_pages)


		#####################################
		#  ADD CONTROLS
		#

		# Add measurement select and measurement pages
		self.ctl_layout.addWidget(self.meas_pages)
		self.ctl_layout.addWidget(self._gen_hbox_widget([self.meas_select, self.meas_select_label]))
		self.ctl_layout.addWidget(self.inst_widget)

		# Pack the standard save widget
		self.ctl_layout.addStretch(1)
		self.ctl_layout.addWidget(self.save_widget)

		# Positioning
		self.ctl_layout.setContentsMargins(0,15,0,20)
		return self.ctl_layout

	
	#####################################
	# MEASUREMENT MODE CONTROLS
	#		
	
	# Method to generate sweep controls
	def gen_iv_ctrl(self):

		# Sweep control layout
		self.iv_ctrl = QWidget()
		self.iv_ctrl_layout = QVBoxLayout()
 		
		# Sweep measurement Button. This will be a state machine which 
		# alternates between 'measure' and 'abort' states
		self.iv_meas_state  = QStateMachine()
		self.iv_meas_button = QPushButton()
		self.iv_meas_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create measurement states
		self.iv_meas_run  = QState()
		self.iv_meas_stop = QState()

		# Assign state properties and transitions
		self.iv_meas_run.assignProperty(self.iv_meas_button, 'text', 'Abort Sweep')
		self.iv_meas_run.addTransition(self.iv_meas_button.clicked, self.iv_meas_stop)
		self.iv_meas_run.entered.connect(self.exec_iv_run)

		self.iv_meas_stop.assignProperty(self.iv_meas_button, 'text', 'Measure Sweep')
		self.iv_meas_stop.addTransition(self.iv_meas_button.clicked, self.iv_meas_run)
		self.iv_meas_stop.entered.connect(self.exec_iv_stop)

		# Add states, set initial state, and state machine
		self.iv_meas_state.addState(self.iv_meas_run)
		self.iv_meas_state.addState(self.iv_meas_stop)
		self.iv_meas_state.setInitialState(self.iv_meas_stop)
		self.iv_meas_state.start()		

		# Sweep start
		self.iv_start_config={
			"unit" 		: "V", 
			"min"		: "m",
			"max"		: "",
			"label"		: "Sweep Start (V)",
			"limit"		: 2.0, 
			"signed"	: True,
			"default"	: [-0.5, ""]
		} 
		self.iv_start = widgets.QVisaUnitSelector.QVisaUnitSelector(self.iv_start_config)

		# Sweep stop
		self.iv_stop_config={
			"unit" 		: "V", 
			"min"		: "m",
			"max"		: "",
			"label"		: "Sweep Stop (V)",
			"limit"		: 2.0, 
			"signed"	: True,
			"default"	: [0.5, ""]
		} 
		self.iv_stop = widgets.QVisaUnitSelector.QVisaUnitSelector(self.iv_stop_config)

		
		# Compliance Spinbox
		self.iv_cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (A)",
			"limit"		: 1.0, 
			"signed"	: False,
			"default"	: [20, "u"]
		} 
		self.iv_cmpl = widgets.QVisaUnitSelector.QVisaUnitSelector(self.iv_cmpl_config)	

		# Compliance
		self.iv_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"limit"		: 256.0, 
			"signed"	: False,
			"default"	: [51.0]
		}
		self.iv_npts = widgets.QVisaUnitSelector.QVisaUnitSelector(self.iv_npts_config)		

		# Add sweep widgets to layout
		self.iv_ctrl_layout.addWidget(self.iv_meas_button)
		self.iv_ctrl_layout.addWidget(self.iv_start)
		self.iv_ctrl_layout.addWidget(self.iv_stop)
		self.iv_ctrl_layout.addWidget(self.iv_cmpl)
		self.iv_ctrl_layout.addWidget(self.iv_npts)
		self.iv_ctrl_layout.setContentsMargins(0,0,0,0)
	
		# Set widget layout
		self.iv_ctrl.setLayout(self.iv_ctrl_layout)


	# Method to generate Voc controls
	def gen_voc_ctrl(self):

		# Voc control layout
		self.voc_ctrl = QWidget()
		self.voc_ctrl_layout = QVBoxLayout()

		# Create QStateMachine for output state
		self.voc_state = QStateMachine()
		self.voc_meas_button = QPushButton()
		self.voc_meas_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create output states
		self.voc_meas_off = QState()
		self.voc_meas_on  = QState()

		# Attach states to output button and define state transitions
		self.voc_meas_off.assignProperty(self.voc_meas_button, 'text', 'Voc Monitor Off')
		self.voc_meas_off.addTransition(self.voc_meas_button.clicked, self.voc_meas_on)
		self.voc_meas_off.entered.connect(self.exec_monitor_off)

		self.voc_meas_on.assignProperty(self.voc_meas_button, 'text', 'Voc Monitor On')
		self.voc_meas_on.addTransition(self.voc_meas_button.clicked, self.voc_meas_off)
		self.voc_meas_on.entered.connect(self.exec_monitor_on)
		
		# Add states, set initial state, and start machine
		self.voc_state.addState(self.voc_meas_off)
		self.voc_state.addState(self.voc_meas_on)
		self.voc_state.setInitialState(self.voc_meas_off)
		self.voc_state.start()

		# Tracking mode initialization
		# Note this example of passing arguments to a callback
		self.voc_bias_config={
			"unit" 		: "V", 
			"min"		: "m",
			"max"		: "",
			"label"		: "Voc Initialization (V)",
			"limit"		: 2.0, 
			"signed"	: True,
			"default"	: [0.3,""]
		} 
		self.voc_bias = widgets.QVisaUnitSelector.QVisaUnitSelector(self.voc_bias_config)
		self.voc_bias.unit_value.valueChanged.connect(lambda arg=self.voc_bias.value(): self._update_bias(arg))
		
		# Tracking mode convergence
		self.voc_conv_config={
			"unit" 		: "A", 
			"min"		: "n",
			"max"		: "u",
			"label"		: "Voc Convergence (A)",
			"limit"		: 100, 
			"signed"	: False,
			"default"	: [0.05,"u"]
		} 
		self.voc_conv = widgets.QVisaUnitSelector.QVisaUnitSelector(self.voc_conv_config)

		# Delay
		self.voc_gain_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Proportional Gain (%)",
			"limit"		: 100, 
			"signed"	: False,
			"default"	: [3]
		}
		self.voc_gain = widgets.QVisaUnitSelector.QVisaUnitSelector(self.voc_gain_config)


		# Delay
		self.voc_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: [1.0]
		}
		self.voc_delay = widgets.QVisaUnitSelector.QVisaUnitSelector(self.voc_delay_config)

		# Add voc widgets to layout
		self.voc_ctrl_layout.addWidget(self.voc_meas_button)
		self.voc_ctrl_layout.addWidget(self.voc_bias)
		self.voc_ctrl_layout.addWidget(self.voc_conv)
		self.voc_ctrl_layout.addWidget(self.voc_gain)
		self.voc_ctrl_layout.addWidget(self.voc_delay)
		self.voc_ctrl_layout.setContentsMargins(0,0,0,0)
	
		# Set widget layout
		self.voc_ctrl.setLayout(self.voc_ctrl_layout)


	# Method to generate MPP controls
	def gen_mpp_ctrl(self):

		#################################
		# mpp tracking controls
		#
		self.mpp_ctrl = QWidget()
		self.mpp_ctrl_layout = QVBoxLayout()


		# Create QStateMachine for output state
		self.mpp_state = QStateMachine()
		self.mpp_meas_button = QPushButton()
		self.mpp_meas_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create output states
		self.mpp_meas_off = QState()
		self.mpp_meas_on  = QState()

		# Attach states to output button and define state transitions
		self.mpp_meas_off.assignProperty(self.mpp_meas_button, 'text', 'MPP Monitor Off')
		self.mpp_meas_off.addTransition(self.mpp_meas_button.clicked, self.mpp_meas_on)
		self.mpp_meas_off.entered.connect(self.exec_monitor_off)

		self.mpp_meas_on.assignProperty(self.mpp_meas_button, 'text', 'MPP Monitor On')
		self.mpp_meas_on.addTransition(self.mpp_meas_button.clicked, self.mpp_meas_off)
		self.mpp_meas_on.entered.connect(self.exec_monitor_on)
		
		# Add states, set initial state, and start machine
		self.mpp_state.addState(self.mpp_meas_off)
		self.mpp_state.addState(self.mpp_meas_on)
		self.mpp_state.setInitialState(self.mpp_meas_off)
		self.mpp_state.start()



		# Tracking mode initialization
		# Note this example of passing arguments to a callback
		self.mpp_bias_config={
			"unit" 		: "V", 
			"min"		: "m",
			"max"		: "",
			"label"		: "MPP Initialization (V)",
			"limit"		: 2.0, 
			"signed"	: True,
			"default"	: [0.25,""]
		} 
		self.mpp_bias = widgets.QVisaUnitSelector.QVisaUnitSelector(self.mpp_bias_config)
		self.mpp_bias.unit_value.valueChanged.connect(lambda arg=self.mpp_bias.value(): self._update_bias(arg))
		
		# Tracking mode convergence
		self.mpp_ampl_config={
			"unit" 		: "V", 
			"min"		: "u",
			"max"		: "m",
			"label"		: "Sense amplitude (mV)",
			"limit"		: 100, 
			"signed"	: False,
			"default"	: [20.0,"m"]
		} 
		self.mpp_ampl = widgets.QVisaUnitSelector.QVisaUnitSelector(self.mpp_ampl_config)

		# Delay
		self.mpp_gain_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Proportional Gain (%)",
			"limit"		: 100, 
			"signed"	: False,
			"default"	: [3]
		}
		self.mpp_gain = widgets.QVisaUnitSelector.QVisaUnitSelector(self.mpp_gain_config)


		# Delay
		self.mpp_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: [1.0]
		}
		self.mpp_delay = widgets.QVisaUnitSelector.QVisaUnitSelector(self.mpp_delay_config)

		# Add mpp widgets to layout
		self.mpp_ctrl_layout.addWidget(self.mpp_meas_button)
		self.mpp_ctrl_layout.addWidget(self.mpp_bias)
		self.mpp_ctrl_layout.addWidget(self.mpp_ampl)
		self.mpp_ctrl_layout.addWidget(self.mpp_gain)
		self.mpp_ctrl_layout.addWidget(self.mpp_delay)
		self.mpp_ctrl_layout.setContentsMargins(0,0,0,0)
	
		# Set widget layout
		self.mpp_ctrl.setLayout(self.mpp_ctrl_layout)


	# Method to generate solar cell plots. This will be implemented 
	# as three QVisaDynamicPlots packed into a QStackedWidget
	def gen_solar_plot(self):

		# Call QStackedWidget constructor
		self.plot_stack = QStackedWidget()

		# Plot IV-Sweep mode
		self.iv_plot =  widgets.QVisaDynamicPlot.QVisaDynamicPlot()
		self.iv_plot.set_axes_labels('Voltage (V)', 'Current (mA)', 'Power (mW)')
		self.iv_plot.add_axes(_twinx=True)
		
		self.voc_plot =  widgets.QVisaDynamicPlot.QVisaDynamicPlot()
		self.voc_plot.set_axes_labels('Time (s)', 'Voc (V)')
		self.voc_plot.add_axes()

		self.mpp_plot =  widgets.QVisaDynamicPlot.QVisaDynamicPlot()
		self.mpp_plot.set_axes_labels('Time (s)', 'MPP (V)')
		self.mpp_plot.add_axes()


		# Add QVisaDynamicPlots to QStackedWidget
		self.plot_stack.addWidget(self.iv_plot)
		self.plot_stack.addWidget(self.voc_plot)
		self.plot_stack.addWidget(self.mpp_plot)

		# Return the stacked widget
		self.plot_stack.setCurrentIndex(0);
		return self.plot_stack

	# Flip between controls when measurement mode selector is updated
	def update_meas_pages(self):
		
		if self.meas_select.currentText() == "IV":		
			self.meas_pages.setCurrentIndex(0)

		if self.meas_select.currentText() == "Voc":
			self.meas_pages.setCurrentIndex(1)

		if self.meas_select.currentText() == "MPP":
			self.meas_pages.setCurrentIndex(2)


	#####################################
	#  SWEEP ALGORITHM
	#	

	# Sweep measurement EXECUTION
	def exec_iv_thread(self):
		
		# Set sweep parameters as simple linspace
		_params = np.linspace( float( self.iv_start.value() ), float( self.iv_stop.value() ), int( self.iv_npts.value() ) )

		# Create a unique data key
		m = hashlib.sha256()
		m.update(str("sweep@%s"%str(time.time())).encode() )		
		m.hexdigest()[:7]

		# Measurement key
		_meas_key = "sweep %s"%m.hexdigest()[:6]

		# Add to data
		self._add_meas_key(_meas_key)
		self._set_data_fields(_meas_key, ["t", "V", "I", "P"])

		# Clear plot and zero arrays
		handle = self.iv_plot.add_handle()
		start  = time.time()
		
		# Output on
		self.keithley().voltage_src()
		self.keithley().current_cmp(self.iv_cmpl.value())
		self.keithley().output_on()

		# Loop through sweep parameters
		for _bias in _params: 

			# If thread is running
			if self.thread_running:

				# Set bias
				self.keithley().set_voltage(_bias)

				# Get data from buffer
				_buffer = self.keithley().meas().split(",")

				# Extract data from buffer
				self._data[_meas_key]["t"].append( float( time.time() - start ) )
				self._data[_meas_key]["V"].append( float(_buffer[0]) )
				self._data[_meas_key]["I"].append( float(_buffer[1]) )
				self._data[_meas_key]["P"].append( float(_buffer[0]) * float(_buffer[1]) )

				self.iv_plot.update_handle(handle, float(_buffer[0]), float(_buffer[1]))
				self.iv_plot._draw_canvas()	

		self.keithley().set_voltage(0.0)
		self.keithley().output_off()	

		# Reset sweep control and update measurement state to stop. 
		# Post a button click event to the QStateMachine to trigger 
		# a state transition if thread is still running (not aborted)
		if self.thread_running:
			self.iv_meas_button.click() 







		# # Refresh axes (clears handle)
		# self.iv_plot._refresh_axes()
		# self.plot_select.setCurrentIndex(0) 
		# h0 = self.iv_plot.add_handle(_axes_index=0, _color='b')
		# h1 = self.iv_plot.add_handle(_axes_index=1, _color='r')
		# start  = float(time.time())

		# # Set compliance and turn output on
		# self.keithley.current_cmp(self.iv_cmpl.value())	
		# self.keithley.output_on()

		# # Loop through all voltage values
		# for _v in self._get_sweep_params():

		# 	# Check if measurement has been aborted
		# 	if self.iv_thread_abort is True:

		# 		# If aborted, kill output and return
		# 		self.keithley.set_voltage(0.0)
		# 		self.keithley.output_off()
		# 		return	

		# 	# Otherwise continue measureing
		# 	else:

		# 		# Set bias
		# 		self.keithley.set_voltage(_v)

		# 		# Get data from buffer
		# 		_buffer = self.keithley.meas().split(",")

		# 		# Extract data from buffer
		# 		self._data["IV"]["t"].append( float(time.time() ) - start )
		# 		self._data["IV"]["V"].append( float(_buffer[0]) )
		# 		self._data["IV"]["I"].append( float(_buffer[1]) )
		# 		self._data["IV"]["P"].append( float(_buffer[0]) * (-1.0 * float(_buffer[1]) ) )

		# 		# Update current and output power plots. 
		# 		# Note photocurrents are interpreted as positive
		# 		self.iv_plot.update_handle( 
		# 			h0, 
		# 			float(_buffer[0]), 
		# 			-1000.0 * float(_buffer[1]), 
		# 			_axes_index=0
		# 		)


		# 		self.iv_plot.update_handle( 
		# 			h1, 
		# 			float(_buffer[0]), 
		# 			-1000.0 * float(_buffer[1]) * float(_buffer[0]), 
		# 			_axes_index=1
		# 		)
		
		# 		self.iv_plot._draw_canvas()

		# # Set output off after measurement
		# self.iv_meas_button.click() 
		# self.keithley.set_voltage(0.0)
		# self.keithley.output_off()		

	# Sweep measurement ON
	def exec_iv_run(self):
	
		if self.keithley() is not None:

			# Put measurement button in abort state
			self.iv_meas_button.setStyleSheet(
				"background-color: #ffcccc; border-style: solid; border-width: 1px; border-color: #800000; padding: 7px;")
			self.save_widget.setEnabled(False)
				
			# Run the measurement thread function
			self.iv_thread = threading.Thread(target=self.exec_iv_thread, args=())
			self.iv_thread.daemon = True				# Daemonize thread
			self.iv_thread.start()         				# Start the execution
			self.thread_running = True

	# Sweep measurement OFF
	def exec_iv_stop(self):
		
		if self.keithley() is not None:

			# Put measurement button in measure state
			self.iv_meas_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )
			self.save_widget.setEnabled(True)
		
			# Set thread running to False. This will break the sweep measurements
			# execution loop on next iteration.  
			self.thread_running = False
			self.iv_thread.join()  # Waits for thread to complete






























	####################################
	# Tracking State Machine Callbacks #
	####################################
	# These are modified  "bias mode" loops with embedded voltage/power tracking algorithms

	#####################################
	#  Voc TRACKING ALGORITHM
	#	

	def exec_monitor_voc_thread(self):
		
		pass

		# # Initialize Voc data-structure
		# self._data["Voc"] = {"t" : [], "Voc" : [], "Ioc" : []}

		# # Initialize Voc plot
		# self.voc_plot._refresh_axes()
		# self.plot_select.setCurrentIndex(1)
		# handle = self.voc_plot.add_handle()
		# start  = float(time.time())

		# # Set bias to initial value in voltas and turn output ON
		# self.keithley.current_cmp( self.iv_cmpl.value() )	 	# Using sweep compliance
		# self.keithley.set_voltage( self.voc_bias.value() )
		# self.keithley.output_on()

		# # Thread loop
		# while self.monitor_thread_running is True:
			
		# 	# Voc TRACKING ALGORITHM LOOP GOES HERE
		# 	_iter_start = float(time.time())
		# 	while True:
				
		# 		# Get data from buffer
		# 		_buffer = self.keithley.meas().split(",")
				
		# 		# Check if current is below convergence value
		# 		# note that convergence is specified in mA 
		# 		if (abs(float( _buffer[1]))) <= float(self.voc_conv.value()):					
		# 			break
				
		# 		# If convergence takes too long paint a value (10s)
		# 		elif  float( time.time() - _iter_start ) >= 3.0:
		# 			break

		# 		# Otherwise, adjust the voltage proportionally
		# 		else:

		# 			# Create 1mV sense amplitude
		# 			_v, _i = np.add(float(_buffer[0]), np.linspace(-0.0005, 0.0005, 3)), []
					
		# 			# Measure current over sense amplitude
		# 			for _ in _v:
		# 				self.keithley.set_voltage(_)
		# 				_b = self.keithley.meas().split(",")
		# 				_i.append( float( _b[1] ) )

		# 			# Reset the voltage
		# 			self.keithley.set_voltage( float(_buffer[0] ) )

		# 			# Porportional gain controller
		# 			if np.mean(_i) >= 0.0:
		# 				self._update_bias( float(_buffer[0]) * float( 1.0 - self.voc_gain.value()/100. ) ) 

		# 			else:
		# 				self._update_bias( float(_buffer[0]) * float( 1.0 + self.voc_gain.value()/100. ) )	

		# 	# Extract data from buffer
		# 	self._data["Voc"]["t"].append(float( time.time() - start ))
		# 	self._data["Voc"]["Voc"].append( float(_buffer[0]) )
		# 	self._data["Voc"]["Ioc"].append( float(_buffer[1]) ) # Sanity check

		# 	self.voc_plot.update_handle(handle, float(time.time() - start), float(_buffer[0]))
		# 	self.voc_plot._draw_canvas()
	
		# 	# Measurement delay	
		# 	if self.voc_delay.value() != 0: 
		# 		time.sleep(self.voc_delay.value())


	#####################################
	#  MPP TRACKING ALGORITHM
	#	

	def exec_monitor_mpp_thread(self):
		pass
		
		# # Initialize IV Sweep dictionary and plot
		# self._data["MPP"] = {"t" : [], "VMPP" : [], "IMPP" : [], "MPP" : []}
	
		# # Initialize MPP plot
		# self.mpp_plot._refresh_axes()
		# self.plot_select.setCurrentIndex(2)
		# handle = self.mpp_plot.add_handle()
		# start  = float(time.time())

		# # Set bias to initial value in voltas and turn output ON
		# self.keithley.current_cmp( self.iv_cmpl.value() )	 	# Using sweep compliance
		# self.keithley.set_voltage( self.mpp_bias.value() )
		# self.keithley.output_on()

		# # Thread loop
		# while self.monitor_thread_running is True:
			
		# 	# Voc TRACKING ALGORITHM LOOP GOES HERE
		# 	_iter_start = float(time.time())

		# 	# Derivative array for checking convergence
		# 	_d = [] 
		# 	while True:
				
		# 		# Get data from buffer
		# 		_buffer = self.keithley.meas().split(",")
				
		# 		# Check if current is below convergence value
		# 		# note that convergence is specified in mA 
		# 		#if _d is not []:
		# 		#	break
				
		# 		# If convergence takes too long paint a value (10s)
		# 		if  float( time.time() - _iter_start ) >= 3.0:
		# 			break

		# 		# Otherwise, adjust the voltage proportionally
		# 		else:

		# 			# Create signal amplitude
		# 			_amplitude = self.mpp_ampl.value()
		# 			_v, _i = np.add(float(_buffer[0]), np.linspace(-1.0 * _amplitude, _amplitude, 5)), []
					
		# 			# Measure current over sense amplitude
		# 			for _ in _v:
		# 				self.keithley.set_voltage(_)
		# 				_b = self.keithley.meas().split(",")
		# 				_i.append( -1.0*float( _b[1] ) )

		# 			# Reset the voltage
		# 			self.keithley.set_voltage( float(_buffer[0] ) )

		# 			# Calculate derivative
		# 			_p = np.multiply(_i, _v)
		# 			_d = np.gradient(np.multiply(_i, _v))
		# 			_d = np.divide(_d, _amplitude)

		# 			# Differntial gain controller
		# 			if np.mean(_d) <= 0.0:
		# 				self._update_bias( float(_buffer[0]) * float( 1.0 - self.mpp_gain.value()/100. ) )  

		# 			else:
		# 				self._update_bias( float(_buffer[0]) * float( 1.0 + self.mpp_gain.value()/100. ) )

		# 	# Extract data from buffer
		# 	self._data["MPP"]["t"].append(float( time.time() - start ))
		# 	self._data["MPP"]["VMPP"].append( float(_buffer[0]) )
		# 	self._data["MPP"]["IMPP"].append( float(_buffer[1]) )
		# 	self._data["MPP"]["MPP"].append( -1.0 * float(_buffer[0]) * float(_buffer[1]) )
				
		# 	self.mpp_plot.update_handle(handle, float(time.time() - start), float(_buffer[0]))
		# 	self.mpp_plot._draw_canvas()
	
		# 	# Measurement delay	
		# 	if self.mpp_delay.value() != 0: 
		# 		time.sleep(self.mpp_delay.value())			

	# Tracking measurement ON
	def exec_monitor_on(self):
		pass
		# if self.keithley is not None:

		# 	# Update UI for ON state
		# 	self.monitor_meas_button.setStyleSheet(
		# 		"background-color: #cce6ff; border-style: solid; border-width: 1px; border-color: #1a75ff; padding: 7px;")
	
		# 	self.iv_meas_button.setEnabled(False)
		# 	self.save_button.setEnabled(False)
			
		# 	# Create execution threads for measurement
		# 	# Voc monitoring thread
		# 	if self.monitor_select.currentText() == "Voc":
		# 		self.monitor_thread = threading.Thread(target=self.exec_monitor_voc_thread, args=())
			
		# 	# MPP monitoring thread
		# 	if self.monitor_select.currentText() == "MPP":
		# 		self.monitor_thread = threading.Thread(target=self.exec_monitor_mpp_thread, args=())

		# 	# Run the thread	
		# 	self.monitor_thread.daemon = True		# Daemonize thread
		# 	self.monitor_thread.start()         	# Start the execution
		# 	self.monitor_thread_running = True	# Set execution flag	
			

	# Tracking measurement OFF
	def exec_monitor_off(self):
		pass
		
		# if self.keithley is not None:

		# 	self.monitor_meas_button.setStyleSheet(
		# 		"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )			
		# 	self.iv_meas_button.setEnabled(True)	
		# 	self.save_button.setEnabled(True)

		# 	self.monitor_thread_running = False
		# 	self.monitor_thread.join()  # Waits for thread to complete

		# 	self.keithley.set_voltage(0.0)
		# 	self.keithley.output_off()

