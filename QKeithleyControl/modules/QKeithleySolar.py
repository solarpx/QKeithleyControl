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
import threading 
import numpy as np

# Import d_plot and keithley driver
import drivers.keithley_2400

# Import widgets
import widgets.QDynamicPlot 
import widgets.QUnitSelector

# Import QT backends
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel, QFileDialog, QSizePolicy, QLineEdit
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject
from PyQt5.QtGui import QIcon

# Container class to construct solar measurement widget
class QKeithleySolar(QWidget):

	def __init__(self):

		QWidget.__init__(self)

		# Create Icon for QMessageBox
		self.icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico"))	

		# Initialize Keithley Object
		self.keithley = None

		# Create dictionary to hold data
		self._data = {"IV" : None, "Voc" : None, "MPP" : None}
			
		# Create layout objects and set layout
		self.layout = QHBoxLayout()
		self.layout.addLayout(self._gen_solar_control())
		self.layout.addWidget(self._gen_solar_plots())
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
		self._data = {"IV" : None, "Voc" : None, "MPP" : None}

	# Update bias from spinbox
	def _update_bias(self, _value):
		self.keithley.set_voltage(_value)		

	def _update_current_plot(self):

		if self.plot_select.currentText() == "IV":
			self.plot_stack.setCurrentIndex(0)

		if self.plot_select.currentText() == "Voc":
			self.plot_stack.setCurrentIndex(1)

		if self.plot_select.currentText() == "MPP":
			self.plot_stack.setCurrentIndex(2)

	# Method to generate solar characterization controls
	def _gen_solar_control(self):

		self.ctl_layout = QVBoxLayout()

		#####################################
		#  SWEEP MEASUREMENT STATE MACHINE
		#
		
		# Sweep measurement Button. This will be a state machine which 
		# alternates between 'measure' and 'abort' states
		self.sweep_meas_state  = QStateMachine()
		self.sweep_meas_button = QPushButton()
		self.sweep_meas_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create measurement states
		self.sweep_meas_run  = QState()
		self.sweep_meas_stop = QState()

		# Assign state properties and transitions
		self.sweep_meas_run.assignProperty(self.sweep_meas_button, 'text', 'Abort Sweep')
		self.sweep_meas_run.addTransition(self.sweep_meas_button.clicked, self.sweep_meas_stop)
		self.sweep_meas_run.entered.connect(self._exec_sweep_run)

		self.sweep_meas_stop.assignProperty(self.sweep_meas_button, 'text', 'Measure Sweep')
		self.sweep_meas_stop.addTransition(self.sweep_meas_button.clicked, self.sweep_meas_run)
		self.sweep_meas_stop.entered.connect(self._exec_sweep_stop)

		# Add states, set initial state, and state machine
		self.sweep_meas_state.addState(self.sweep_meas_run)
		self.sweep_meas_state.addState(self.sweep_meas_stop)
		self.sweep_meas_state.setInitialState(self.sweep_meas_stop)
		self.sweep_meas_state.start()


		#####################################
		#  SWEEP MEASUREMENT CONFIGURATION
		#
		 
		# Sweep control layout
		self.sweep_start_config={
			"unit" 		: "V", 
			"min"		: "m",
			"max"		: "",
			"label"		: "Sweep Start (V)",
			"limit"		: 2.0, 
			"signed"	: True,
			"default"	: -0.5
		} 
		self.sweep_start = widgets.QUnitSelector.QUnitSelector(self.sweep_start_config)

		# Configuration for bias level unit box
		self.sweep_stop_config={
			"unit" 		: "V", 
			"min"		: "m",
			"max"		: "",
			"label"		: "Sweep Stop (V)",
			"limit"		: 2.0, 
			"signed"	: True,
			"default"	: 0.5
		} 
		self.sweep_stop = widgets.QUnitSelector.QUnitSelector(self.sweep_stop_config)

		
		# Compliance Spinbox
		self.sweep_cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (A)",
			"limit"		: 1.0, 
			"signed"	: False,
			"default"	: 0.001
		} 
		self.sweep_cmpl = widgets.QUnitSelector.QUnitSelector(self.sweep_cmpl_config)	

		# Compliance
		self.sweep_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"limit"		: 256.0, 
			"signed"	: False,
			"default"	: 51.0
		}
		self.sweep_npts = widgets.QUnitSelector.QUnitSelector(self.sweep_npts_config)


		#####################################
		#  TRACKING MEASUREMENT STATE MACHINE
		#

		# Create QStateMachine for output state
		self.tmode_state = QStateMachine()
		self.tmode_meas_button = QPushButton()
		self.tmode_meas_button.setStyleSheet(
			"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )

		# Create output states
		self.tmode_meas_off = QState()
		self.tmode_meas_on  = QState()

		# Attach states to output button and define state transitions
		self.tmode_meas_off.assignProperty(self.tmode_meas_button, 'text', 'Monitor Off')
		self.tmode_meas_off.addTransition(self.tmode_meas_button.clicked, self.tmode_meas_on)
		self.tmode_meas_off.entered.connect(self._exec_tmode_off)

		self.tmode_meas_on.assignProperty(self.tmode_meas_button, 'text', 'Monitor On')
		self.tmode_meas_on.addTransition(self.tmode_meas_button.clicked, self.tmode_meas_off)
		self.tmode_meas_on.entered.connect(self._exec_tmode_on)
		
		# Add states, set initial state, and start machine
		self.tmode_state.addState(self.tmode_meas_off)
		self.tmode_state.addState(self.tmode_meas_on)
		self.tmode_state.setInitialState(self.tmode_meas_off)
		self.tmode_state.start()


		#####################################
		#  TRACKING MEASUREMENT CONFIGURATION
		#

		# Tracking mode control
		self.tmode_select_label = QLabel("Parameter Tracking")
		self.tmode_select = QComboBox()
		self.tmode_select.setFixedWidth(200)
		self.tmode_select.addItems(["Voc", "MPP"])	

		
		# Tracking mode initialization
		# Note this example of passing arguments to a callback
		self.tmode_bias_config={
			"unit" 		: "V", 
			"min"		: "m",
			"max"		: "",
			"label"		: "Initialization (V)",
			"limit"		: 2.0, 
			"signed"	: True,
			"default"	: 0.4
		} 
		self.tmode_bias = widgets.QUnitSelector.QUnitSelector(self.tmode_bias_config)
		self.tmode_bias.unit_value.valueChanged.connect(lambda arg=self.tmode_bias.value(): self._update_bias(arg))
		
		# Tracking mode convergence
		self.tmode_conv_config={
			"unit" 		: "A", 
			"min"		: "n",
			"max"		: "u",
			"label"		: "Convergence (A)",
			"limit"		: 100, 
			"signed"	: False,
			"default"	: 0.015
		} 
		self.tmode_conv = widgets.QUnitSelector.QUnitSelector(self.tmode_conv_config)


		# Delay
		self.tmode_pgain_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Proportional Gain (%)",
			"limit"		: 100, 
			"signed"	: False,
			"default"	: 3
		}
		self.tmode_pgain = widgets.QUnitSelector.QUnitSelector(self.tmode_pgain_config)


		# Delay
		self.tmode_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: 1.0
		}
		self.tmode_delay = widgets.QUnitSelector.QUnitSelector(self.tmode_delay_config)

		#####################################
		#  PLOT AND SAVE MEASUREMENTS
		#

		# Plotting and save control
		self.plot_select_label = QLabel("Measurement Plot")
		self.plot_select = QComboBox()
		self.plot_select.addItems(["IV", "Voc", "MPP"])
		self.plot_select.setFixedWidth(200)
		self.plot_select.currentTextChanged.connect(self._update_current_plot)

		# Save traces 
		self.save_note_label = QLabel("Measurement Note")
		self.save_note = QLineEdit()
		self.save_note.setFixedWidth(200)
		
		self.save_button = QPushButton("Save Characterization")
		#self.save_button.clicked.connect(self._save_traces)	

		#####################################
		#  ADD CONTROLS
		#

		# Add sweep controls	
		self.ctl_layout.addWidget(self.sweep_meas_button)
		self.ctl_layout.addWidget(self.sweep_start)
		self.ctl_layout.addWidget(self.sweep_stop)
		self.ctl_layout.addWidget(self.sweep_cmpl)
		self.ctl_layout.addWidget(self.sweep_npts)

		# Add tracking controls
		self.ctl_layout.addStretch(1)
		self.ctl_layout.addWidget(self.tmode_meas_button)
		_layout = self._gen_hboxlayout([self.tmode_select, self.tmode_select_label])
		self.ctl_layout.addLayout(_layout)
		self.ctl_layout.addWidget(self.tmode_bias)
		self.ctl_layout.addWidget(self.tmode_conv)
		self.ctl_layout.addWidget(self.tmode_pgain)
		self.ctl_layout.addWidget(self.tmode_delay)

		# Add save control 
		self.ctl_layout.addStretch(1)
		_layout = self._gen_hboxlayout([self.plot_select, self.plot_select_label])
		self.ctl_layout.addLayout(_layout)
		_layout = self._gen_hboxlayout([self.save_note, self.save_note_label])
		self.ctl_layout.addLayout(_layout)
		self.ctl_layout.addWidget(self.save_button)

		# Positioning
		self.ctl_layout.setContentsMargins(0,15,0,20)
		return self.ctl_layout

	# Method to generate solar cell plots. This will be implemented 
	# as three QDynamicPlots packed into a QStackedWidget
	def _gen_solar_plots(self):

		# Call QStackedWidget constructor
		self.plot_stack = QStackedWidget()

		# Plot IV-Sweep mode
		self.sweep_plot =  widgets.QDynamicPlot.QDynamicPlot()
		self.sweep_plot.set_axes_labels('Voltage (V)', 'Current (mA)', 'Power (mW)')
		self.sweep_plot.add_axes(_twinx=True)
		
		self.voc_plot =  widgets.QDynamicPlot.QDynamicPlot()
		self.voc_plot.set_axes_labels('Time (s)', 'Voc (V)')
		self.voc_plot.add_axes()

		self.mpp_plot =  widgets.QDynamicPlot.QDynamicPlot()
		self.mpp_plot.set_axes_labels('Time (s)', 'MPP (V)')
		self.mpp_plot.add_axes()


		# Add QDynamicPlots to QStackedWidget
		self.plot_stack.addWidget(self.sweep_plot)
		self.plot_stack.addWidget(self.voc_plot)
		self.plot_stack.addWidget(self.mpp_plot)

		# Return the stacked widget
		self.plot_stack.setCurrentIndex(0);
		return self.plot_stack

	#################################	
	# Sweep State Machine Callbacks #	
	#################################

	# Set sweep parameters
	def _set_sweep_params(self):
		_start = self.sweep_start.value()
		_stop  = self.sweep_stop.value()
		_npts  = self.sweep_npts.value()
		return np.linspace(float(_start), float(_stop), int(_npts))

	# Get sweep parameters
	def _get_sweep_params(self):
		return self.sweep if self.sweep != [] else None

	# Sweep measurement EXECUTION
	def _exec_sweep_thread(self):

		# Initialize IV Sweep dictionary and plot
		self._data["IV"] = {"t" : [], "V" : [], "I" : [], "P" : []}

		# Refresh axes (clears handle)
		self.sweep_plot._refresh_axes()
		self.plot_select.setCurrentIndex(0) 
		h0 = self.sweep_plot.add_handle(_axes_index=0, _color='b')
		h1 = self.sweep_plot.add_handle(_axes_index=1, _color='r')
		start  = float(time.time())

		# Set compliance and turn output on
		self.keithley.current_cmp(self.sweep_cmpl.value())	
		self.keithley.output_on()

		# Loop through all voltage values
		for _v in self._get_sweep_params():

			# Check if measurement has been aborted
			if self.sweep_thread_abort is True:

				# If aborted, kill output and return
				self.keithley.set_voltage(0.0)
				self.keithley.output_off()
				return	

			# Otherwise continue measureing
			else:

				# Set bias
				self.keithley.set_voltage(_v)

				# Get data from buffer
				_buffer = self.keithley.meas().split(",")

				# Extract data from buffer
				self._data["IV"]["t"].append( float(time.time() ) - start )
				self._data["IV"]["V"].append( float(_buffer[0]) )
				self._data["IV"]["I"].append( float(_buffer[1]) )
				self._data["IV"]["P"].append( float(_buffer[0]) * (-1.0 * float(_buffer[1]) ) )

				# Update current and output power plots. 
				# Note photocurrents are interpreted as positive
				self.sweep_plot.update_handle( 
					h0, 
					float(_buffer[0]), 
					-1000.0 * float(_buffer[1]), 
					_axes_index=0
				)


				self.sweep_plot.update_handle( 
					h1, 
					float(_buffer[0]), 
					-1000.0 * float(_buffer[1]) * float(_buffer[0]), 
					_axes_index=1
				)
		
				self.sweep_plot._draw_canvas()

		# Set output off after measurement
		self.sweep_meas_button.click() 
		self.keithley.set_voltage(0.0)
		self.keithley.output_off()		

	# Sweep measurement ON
	def _exec_sweep_run(self):

		if self.keithley is not None:

			# Put measurement button in abort state
			self.sweep_meas_button.setStyleSheet(
				"background-color: #ffcccc; border-style: solid; border-width: 1px; border-color: #800000; padding: 7px;")
			self.save_button.setEnabled(False)

			# Set sweep parameters in memory
			self.sweep = self._set_sweep_params()
			
			# Disable the tracking mode button
			self.tmode_meas_button.setEnabled(False)

			# Run the measurement thread function
			self.sweep_thread = threading.Thread(target=self._exec_sweep_thread, args=())
			self.sweep_thread.daemon = True				# Daemonize thread
			self.sweep_thread_abort = False				# Flag to abort measurement
			self.sweep_thread.start()         			# Start the execution

	# Sweep measurement OFF
	def _exec_sweep_stop(self):

		if self.keithley is not None:

			# Put measurement button in measure state
			self.sweep_meas_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )
			self.save_button.setEnabled(True)

			# Enable the tracking mode button
			self.tmode_meas_button.setEnabled(True)

			# Set thread running to False. This will break the sweep measurements
			# execution loop on next iteration.  
			self.sweep_thread_abort = True
			self.sweep_thread.join()  # Waits for thread to complete

			# Zero storage arrays for IV data
			self._data["IV"] = {"t" : [], "V" : [], "I" : [], "P" : []}


	####################################
	# Tracking State Machine Callbacks #
	####################################
	# These are modified  "bias mode" loops with embedded voltage/power tracking algorithms
	def _exec_tmode_voc_thread(self):
		
		# Initialize Voc data-structure
		self._data["Voc"] = {"t" : [], "Voc" : [], "Ioc" : []}

		# Initialize Voc plot
		self.voc_plot._refresh_axes()
		self.plot_select.setCurrentIndex(1)
		handle = self.voc_plot.add_handle()
		start  = float(time.time())

		# Set bias to initial value in voltas and turn output ON
		self.keithley.current_cmp( self.sweep_cmpl.value() )	 	# Using sweep compliance
		self.keithley.set_voltage( self.tmode_bias.value() )
		self.keithley.output_on()

		# Thread loop
		while self.tmode_thread_running is True:
			
			# Voc TRACKING ALGORITHM LOOP GOES HERE
			_iter_start = float(time.time())
			while True:
				
				# Get data from buffer
				_buffer = self.keithley.meas().split(",")
				
				# Check if current is below convergence value
				# note that convergence is specified in mA 
				if (abs(float( _buffer[1]))) <= float(self.tmode_conv.value()):					
					break
				
				# If convergence takes too long paint a value (10s)
				elif  float( time.time() - _iter_start ) >= 3.0:
					break

				# Otherwise, adjust the voltage proportionally
				else:

					# Create 1mV sense amplitude
					_v, _i = np.add(float(_buffer[0]), np.linspace(-0.0005, 0.0005, 3)), []
					
					# Measure current over sense amplitude
					for _ in _v:
						self.keithley.set_voltage(_)
						_b = self.keithley.meas().split(",")
						_i.append( float( _b[1] ) )

					# Reset the voltage
					self.keithley.set_voltage( float(_buffer[0] ) )

					# Porportional gain controller
					if np.mean(_i) >= 0.0:
						self._update_bias( float(_buffer[0]) * float( 1.0 - self.tmode_pgain.value()/100. ) ) 

					else:
						self._update_bias( float(_buffer[0]) * float( 1.0 + self.tmode_pgain.value()/100. ) )
	

			# Extract data from buffer
			self._data["Voc"]["t"].append(float( time.time() - start ))
			self._data["Voc"]["Voc"].append( float(_buffer[0]) )
			self._data["Voc"]["Ioc"].append( float(_buffer[1]) ) # Sanity check

			self.voc_plot.update_handle(handle, float(time.time() - start), float(_buffer[0]))
			self.voc_plot._draw_canvas()
	
			# Measurement delay	
			if self.tmode_delay.value() != 0: 
				time.sleep(self.tmode_delay.value())

	# Tracking measurement ON
	def _exec_tmode_on(self):
		
		if self.keithley is not None:

			# Update UI for ON state
			self.tmode_meas_button.setStyleSheet(
				"background-color: #cce6ff; border-style: solid; border-width: 1px; border-color: #1a75ff; padding: 7px;")
			self.save_button.setEnabled(False)
			
			# Create execution threads for measurement
			# Voc monitoring
			if self.tmode_select.currentText() == "Voc":
				self.tmode_thread = threading.Thread(target=self._exec_tmode_voc_thread, args=())
			
			# MPP monitoring
			if self.tmode_select.currentText() == "MPP":
				pass

			#	
			self.tmode_thread.daemon = True		# Daemonize thread
			self.tmode_thread.start()         	# Start the execution
			self.tmode_thread_running = True	# Set execution flag	
			

	# Tracking measurement OFF
	def _exec_tmode_off(self):
		
		if self.keithley is not None:

			self.tmode_meas_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )			
			self.save_button.setEnabled(True)

			self.tmode_thread_running = False
			self.tmode_thread.join()  # Waits for thread to complete

			self.keithley.set_voltage(0.0)
			self.keithley.output_off()




	# Putting this here for now to avoid confusion
	def _exec_tmode_mpp_thread(self):
		
		# Initialize IV Sweep dictionary and plot
		self._data["MPP"] = {"t" : [], "VMPP" : [], "IMPP" : [], "MPP" : []}
		handle = self.sweep_plot.add_handle()
		start  = float(time.time())

		# Thread loop
		while self.tmode_thread_running is True:
			
			# MPP TRACKING ALGORITHM LOOP GOES HERE
			# Get data from buffer
			#while True:
			#if _buffer < convergence break
			_buffer = self.keithley.meas().split(",")

			# Extract data from buffer
			self._data["MPP"]["t"].append(float( time.time() - start ))
			self._data["MPP"]["MPP"].append( -1.0 * float(_buffer[0]) * float(_buffer[1]) )
			self._data["MPP"]["VMPP"].append( float(_buffer[0]) )
			self._data["MPP"]["IMPP"].append( float(_buffer[1]) )

			self.plot.update_handle(handle, float(time.time() - start), float(_plt_data))