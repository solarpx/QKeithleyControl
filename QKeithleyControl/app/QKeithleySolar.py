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
import html
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
	# APPLICATION HELPER METHODS
	#

	# Wrapper method to get keitley write handle
	# 	Returns the pyVisaDevice object
	def keithley(self):
		return self._get_inst_byname( self.inst_widget.currentText() )

	# Update bias on keithley
	def update_bias(self, _value):
		if self.keithley() is not None:
			self.keithley().set_voltage(_value)	

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
		self.inst_widget_label = QLabel("Select Device")
		self.inst_widget = self._gen_inst_widget()
		self.inst_widget.setFixedWidth(200)
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
		self.ctl_layout.addWidget(self._gen_hbox_widget([self.inst_widget,self.inst_widget_label]))

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
			"default"	: [100, "m"]
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
		self.voc_meas_off.entered.connect(self.exec_voc_stop)

		self.voc_meas_on.assignProperty(self.voc_meas_button, 'text', 'Voc Monitor On')
		self.voc_meas_on.addTransition(self.voc_meas_button.clicked, self.voc_meas_off)
		self.voc_meas_on.entered.connect(self.exec_voc_run)
		
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
		self.voc_bias.unit_value.valueChanged.connect(lambda arg=self.voc_bias.value(): self.update_bias(arg))
		
		# Compliance Spinbox
		self.voc_cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (A)",
			"limit"		: 1.0, 
			"signed"	: False,
			"default"	: [100, "m"]
		} 
		self.voc_cmpl = widgets.QVisaUnitSelector.QVisaUnitSelector(self.voc_cmpl_config)	

		# Tracking mode convergence
		self.voc_conv_config={
			"unit" 		: "A", 
			"min"		: "n",
			"max"		: "m",
			"label"		: "Voc Convergence (A)",
			"limit"		: 0.05, 
			"signed"	: False,
			"default"	: [0.05,"u"]
		} 
		self.voc_conv = widgets.QVisaUnitSelector.QVisaUnitSelector(self.voc_conv_config)

		# Delay
		self.voc_gain_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: html.unescape("Proportional Gain (&permil;)"),
			"limit"		: 1000, 
			"signed"	: False,
			"default"	: [30.0]
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
		self.voc_ctrl_layout.addWidget(self.voc_cmpl)
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
		self.mpp_meas_off.entered.connect(self.exec_mpp_stop)

		self.mpp_meas_on.assignProperty(self.mpp_meas_button, 'text', 'MPP Monitor On')
		self.mpp_meas_on.addTransition(self.mpp_meas_button.clicked, self.mpp_meas_off)
		self.mpp_meas_on.entered.connect(self.exec_mpp_run)
		
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
			"default"	: [0.30,""]
		} 
		self.mpp_bias = widgets.QVisaUnitSelector.QVisaUnitSelector(self.mpp_bias_config)
		self.mpp_bias.unit_value.valueChanged.connect(lambda arg=self.mpp_bias.value(): self.update_bias(arg))
		
		# Compliance Spinbox
		self.mpp_cmpl_config={
			"unit" 		: "A", 
			"min"		: "u",
			"max"		: "",
			"label"		: "Compliance (A)",
			"limit"		: 1.0, 
			"signed"	: False,
			"default"	: [100, "m"]
		} 
		self.mpp_cmpl = widgets.QVisaUnitSelector.QVisaUnitSelector(self.mpp_cmpl_config)	

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
			"label"		: html.unescape("Proportional Gain (&permil;)"),
			"limit"		: 1000, 
			"signed"	: False,
			"default"	: [30.0]
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
		self.mpp_ctrl_layout.addWidget(self.mpp_cmpl)
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
		self.iv_plot =  widgets.QVisaDynamicPlot.QVisaDynamicPlot(self)
		self.iv_plot.add_subplot(111, twinx=True)
		self.iv_plot.set_axes_labels("111" , "Voltage (V)", "Current (mA)")
		self.iv_plot.set_axes_labels("111t", "Voltage (V)", "Power (mW)")
		self.iv_plot.set_axes_adjust(_left=0.15, _right=0.85, _top=0.9, _bottom=0.1)
		self.iv_plot.refresh_canvas(supress_warning=True)
		self.iv_plot.set_mpl_refresh_callback( "_reset_data" )

		self.voc_plot =  widgets.QVisaDynamicPlot.QVisaDynamicPlot(self)
		self.voc_plot.add_subplot(111, twinx=True)
		self.voc_plot.set_axes_labels("111", "Time (s)", "Voc (V)")
		self.voc_plot.set_axes_labels("111t", "Time (s)", "Ioc (V)")
		self.voc_plot.set_axes_adjust(_left=0.15, _right=0.85, _top=0.9, _bottom=0.1)
		self.voc_plot.refresh_canvas(supress_warning=True)		
		self.voc_plot.set_mpl_refresh_callback( "_reset_data" )

		self.mpp_plot =  widgets.QVisaDynamicPlot.QVisaDynamicPlot(self)
		self.mpp_plot.add_subplot(111, twinx=True)
		self.mpp_plot.set_axes_labels("111", "Time (s)", "Vmpp (V)")
		self.mpp_plot.set_axes_labels("111t", "Time (s)", "Pmpp (mW)")
		self.mpp_plot.set_axes_adjust(_left=0.15, _right=0.85, _top=0.9, _bottom=0.1)
		self.mpp_plot.refresh_canvas(supress_warning=True)		
		self.mpp_plot.set_mpl_refresh_callback( "_reset_data" )

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
			self.plot_stack.setCurrentIndex(0)

		if self.meas_select.currentText() == "Voc":
			self.meas_pages.setCurrentIndex(1)
			self.plot_stack.setCurrentIndex(1)

		if self.meas_select.currentText() == "MPP":
			self.meas_pages.setCurrentIndex(2)
			self.plot_stack.setCurrentIndex(2)


	#####################################
	#  IV-SWEEP MEASUREMENT MODE
	#	

	# Sweep measurement EXECUTION
	def exec_iv_thread(self):
		
		# Refresh plot. supress_warning and supress_callback options will
		# just refresh plot so there will be no interaction with class data
		self.iv_plot.refresh_canvas(supress_warning=True, supress_callback=True)

		# Set sweep parameters as simple linspace
		_params = np.linspace( 
			float( self.iv_start.value() ), 
			float( self.iv_stop.value() ), 
			int( self.iv_npts.value() ) 
		)

		# Create a unique data key
		_meas_key, _meas_str = self._meas_keygen(_key="pv-bias")

		# Add to data
		self._add_meas_key(_meas_str)
		self._set_data_fields(_meas_str, ["t", "V", "I", "P"])

		# Clear plot and zero arrays
		h = self.iv_plot.add_axes_handle('111' , _meas_key, _color='b')
		t = self.iv_plot.add_axes_handle('111t', _meas_key+'t', _color='r')
		start  = time.time()
		
		# Output on
		self.keithley().voltage_src()
		self.keithley().current_cmp(self.iv_cmpl.value())
		self.keithley().output_on()

		# Loop through sweep parameters
		for _bias in _params: 

			# If thread is running
			if self.iv_thread_running:

				# Set bias
				self.keithley().set_voltage(_bias)

				# Get data from buffer
				_buffer = self.keithley().meas().split(",")

				# Extract data from buffer
				self._data[_meas_str]["t"].append( float( time.time() - start ) )
				self._data[_meas_str]["V"].append( float(_buffer[0]) )
				self._data[_meas_str]["I"].append( -1.0 * float(_buffer[1]) )
				self._data[_meas_str]["P"].append( -1.0 * float(_buffer[1]) * float(_buffer[0]) )

				self.iv_plot.append_handle_data( _meas_key    , float(_buffer[0]), -1.0 * float(_buffer[1]))
				self.iv_plot.append_handle_data( _meas_key+'t', float(_buffer[0]), -1.0 * float(_buffer[0]) * float(_buffer[1]))
				self.iv_plot.update_canvas()	

		self.keithley().set_voltage(0.0)
		self.keithley().output_off()	

		# Reset sweep control and update measurement state to stop. 
		# Post a button click event to the QStateMachine to trigger 
		# a state transition if thread is still running (not aborted)
		if self.iv_thread_running:
			self.iv_meas_button.click()

	# Sweep measurement ON
	def exec_iv_run(self):
	
		if self.keithley() is not None:

			# Put measurement button in abort state
			self.iv_meas_button.setStyleSheet(
				"background-color: #ffcccc; border-style: solid; border-width: 1px; border-color: #800000; padding: 7px;")

			# Disable controls
			self.save_widget.setEnabled(False)
			self.inst_widget.setEnabled(False)
			self.meas_select.setEnabled(False)
			self.iv_plot.mpl_refresh_setEnabled(False)
			self.voc_plot.mpl_refresh_setEnabled(False)	
			self.mpp_plot.mpl_refresh_setEnabled(False)
				
			# Run the measurement thread function
			self.iv_thread = threading.Thread(target=self.exec_iv_thread, args=())
			self.iv_thread.daemon = True				# Daemonize thread
			self.iv_thread.start()         				# Start the execution
			self.iv_thread_running = True

	# Sweep measurement OFF
	def exec_iv_stop(self):
		
		if self.keithley() is not None:

			# Put measurement button in measure state
			self.iv_meas_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )
			
			# Enable controls
			self.save_widget.setEnabled(True)
			self.inst_widget.setEnabled(True)
			self.meas_select.setEnabled(True)
			self.iv_plot.mpl_refresh_setEnabled(True)
			self.voc_plot.mpl_refresh_setEnabled(True)	
			self.mpp_plot.mpl_refresh_setEnabled(True)

			# Set thread running to False. This will break the sweep measurements
			# execution loop on next iteration.  
			self.iv_thread_running = False
			self.iv_thread.join()  # Waits for thread to complete


	#####################################
	#  VOC-MONITOR MEASUREMENT MODE
	#	
	def exec_voc_thread(self):
		
		# Create a unique data key
		_meas_key, _meas_str = self._meas_keygen(_key="pv-voc")

		# Add to data
		self._add_meas_key(_meas_str)
		self._set_data_fields(_meas_str, ["t", "Voc", "Ioc"])

		# Initialize Voc plot
		self.voc_plot.add_axes_handle('111'  , _meas_key, _color='b')
		self.voc_plot.add_axes_handle('111t' , _meas_key+'t', _color='r')

		# Thread start time
		start  = float(time.time())

		# Set bias to initial value in voltas and turn output ON
		self.keithley().set_voltage( self.voc_bias.value() )
		self.keithley().current_cmp( self.voc_cmpl.value() )
		self.keithley().output_on()

		# Thread loop
		while self.voc_thread_running is True:

			# Iteration timer
			_iter_start = float(time.time())

			# Covvergence loop
			while True:
				
				# Get data from buffer
				_buffer = self.keithley().meas().split(",")
				
				# Check if current is below convergence value
				# note that convergence is specified in mA 
				if (abs(float( _buffer[1]))) <= float(self.voc_conv.value()):					
					break
				
				# If convergence takes too long paint a value (10s)
				elif  float( time.time() - _iter_start ) >= 3.0:
					break

				# Otherwise, adjust the voltage proportionally
				else:

					# Create 1mV sense amplitude
					_v, _i = np.add(float(_buffer[0]), np.linspace(-0.0005, 0.0005, 3)), []
					
					# Measure current over sense amplitude array
					for _ in _v:
						self.keithley().set_voltage(_)
						_b = self.keithley().meas().split(",")
						_i.append( -1.0 * float( _b[1] ) )

					# Reset the voltage
					self.keithley().set_voltage( float(_buffer[0] ) )

					# Adjust bias in direction of lower current
					# If current is positive (photo-current) increase voltage
					if np.mean(_i) >= 0.0:
						self.update_bias( float(_buffer[0]) * float( 1.0 + self.voc_gain.value()/1000. ) ) 

					else:
						self.update_bias( float(_buffer[0]) * float( 1.0 - self.voc_gain.value()/1000. ) )	

			# Extract data from buffer
			_now = float(time.time() - start)

			self._data[_meas_str]["t"].append(_now)
			self._data[_meas_str]["Voc"].append( float(_buffer[0]) )
			self._data[_meas_str]["Ioc"].append( -1.0 * float(_buffer[1]) ) # Sanity check

			# Append handle data and update canvas
			self.voc_plot.append_handle_data(_meas_key    , _now, float(_buffer[0]))
			self.voc_plot.append_handle_data(_meas_key+'t', _now, -1.0 * float(_buffer[1]) )
			self.voc_plot.update_canvas()	

			# Measurement delay	
			if self.voc_delay.value() != 0: 
				time.sleep(self.voc_delay.value())

		# Cleanup after thread termination
		self.keithley().set_voltage(0.0)
		self.keithley().output_off()	
		
	# Tracking measurement ON
	def exec_voc_run(self):
		
		if self.keithley() is not None:

			# Update UI for ON state
			self.voc_meas_button.setStyleSheet(
				"background-color: #cce6ff; border-style: solid; border-width: 1px; border-color: #1a75ff; padding: 7px;")
			
			# Disable controls
			self.save_widget.setEnabled(False)
			self.inst_widget.setEnabled(False)
			self.meas_select.setEnabled(False)
			self.voc_bias.setEnabled(False)
			self.voc_cmpl.setEnabled(False)
			self.iv_plot.mpl_refresh_setEnabled(False)
			self.voc_plot.mpl_refresh_setEnabled(False)	
			self.mpp_plot.mpl_refresh_setEnabled(False)

			# Run the measurement thread function
			self.voc_thread = threading.Thread(target=self.exec_voc_thread, args=())
			self.voc_thread.daemon = True		# Daemonize thread
			self.voc_thread.start()				# Start the execution
			self.voc_thread_running = True		# Set execution flag	
			

	# Tracking measurement OFF
	def exec_voc_stop(self):
				
		if self.keithley() is not None:

			# Put measurement button in measure state
			self.voc_meas_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )	

			# Enable controls
			self.save_widget.setEnabled(True)
			self.meas_select.setEnabled(True)
			self.inst_widget.setEnabled(True)
			self.voc_bias.setEnabled(True)
			self.voc_cmpl.setEnabled(True)
			self.iv_plot.mpl_refresh_setEnabled(True)
			self.voc_plot.mpl_refresh_setEnabled(True)	
			self.mpp_plot.mpl_refresh_setEnabled(True)
	
			# Set thread running to False. This will break the sweep measurements
			# execution loop on next iteration.  
			self.voc_thread_running = False	
			self.voc_thread.join()  # Waits for thread to complete

	
	#####################################
	#  MPP-MONITOR MEASUREMENT MODE
	#	

	def exec_mpp_thread(self):
		
		# Create a unique data key
		_meas_key, _meas_str = self._meas_keygen(_key="pv-mpp")

		# Add to data
		self._add_meas_key(_meas_str)
		self._set_data_fields(_meas_str, ["t", "Vmpp", "Impp", "Pmpp"])

		# Initialize Voc plot
		self.mpp_plot.add_axes_handle('111'  , _meas_key, _color='b')
		self.mpp_plot.add_axes_handle('111t' , _meas_key+'t', _color='r')

		# Thread start time
		start  = float(time.time())

		# Set bias to initial value in voltas and turn output ON
		self.keithley().set_voltage( self.mpp_bias.value() )
		self.keithley().current_cmp( self.mpp_cmpl.value() )
		self.keithley().output_on()

		# Thread loop
		while self.mpp_thread_running is True:

			# Iteration timer
			_iter_start = float(time.time())

			# Covvergence loop
			_d = [] 
			while True:
				
				# Get data from buffer
				_buffer = self.keithley().meas().split(",")
				
				# If convergence takes too long paint a value (10s)
				if  float( time.time() - _iter_start ) >= 3.0:
					break

				# Otherwise, adjust the voltage proportionally
				else:

					# Create 1mV sense amplitude
					_amplitude = self.mpp_ampl.value()
					_v, _i = np.add(float(_buffer[0]), np.linspace(-1.0 * _amplitude, _amplitude, 5)), []

					# Measure current over sense amplitude array
					for _ in _v:
						self.keithley().set_voltage(_)
						_b = self.keithley().meas().split(",")
						_i.append( -1.0 * float( _b[1] ) )

					# Reset the voltage
					self.keithley().set_voltage( float(_buffer[0] ) )

					# Calculate derivative
					_p = np.multiply(_i, _v)
					_d = np.gradient(np.multiply(_i, _v))
					_d = np.divide(_d, _amplitude)

					# Differntial gain controller
					if np.mean(_d) <= 0.0:
						self.update_bias( float(_buffer[0]) * float( 1.0 - self.mpp_gain.value()/1000. ) )  

					else:
						self.update_bias( float(_buffer[0]) * float( 1.0 + self.mpp_gain.value()/1000. ) )

			# Extract data from buffer
			_now = float(time.time() - start)

			self._data[_meas_str]["t"].append(_now)
			self._data[_meas_str]["Vmpp"].append( float(_buffer[0]) )
			self._data[_meas_str]["Impp"].append( -1.0 * float(_buffer[1]) ) 
			self._data[_meas_str]["Pmpp"].append( -1.0 * float(_buffer[1]) * float(_buffer[0]) )

			# Append handle data and update canvas
			self.mpp_plot.append_handle_data(_meas_key    , _now, float(_buffer[0]))
			self.mpp_plot.append_handle_data(_meas_key+'t', _now, float(_buffer[0]) * -1.0 * float(_buffer[1]) * 1000.)
			self.mpp_plot.update_canvas()	

			# Measurement delay	
			if self.mpp_delay.value() != 0: 
				time.sleep(self.mpp_delay.value())

		# Cleanup after thread termination
		self.keithley().set_voltage(0.0)
		self.keithley().output_off()	

	# Tracking measurement ON
	def exec_mpp_run(self):
		
		if self.keithley() is not None:

			# Update UI for ON state
			self.mpp_meas_button.setStyleSheet(
				"background-color: #cce6ff; border-style: solid; border-width: 1px; border-color: #1a75ff; padding: 7px;")
			
			# Disable widgets
			self.save_widget.setEnabled(False)
			self.meas_select.setEnabled(False)
			self.inst_widget.setEnabled(False)
			self.mpp_bias.setEnabled(False)
			self.mpp_cmpl.setEnabled(False)
			self.iv_plot.mpl_refresh_setEnabled(False)
			self.voc_plot.mpl_refresh_setEnabled(False)	
			self.mpp_plot.mpl_refresh_setEnabled(False)
			
			# Run the measurement thread function
			self.mpp_thread = threading.Thread(target=self.exec_mpp_thread, args=())
			self.mpp_thread.daemon = True		# Daemonize thread
			self.mpp_thread.start()				# Start the execution
			self.mpp_thread_running = True		# Set execution flag				

	# Tracking measurement OFF
	def exec_mpp_stop(self):
				
		if self.keithley() is not None:

			# Put measurement button in measure state
			self.mpp_meas_button.setStyleSheet(
				"background-color: #dddddd; border-style: solid; border-width: 1px; border-color: #aaaaaa; padding: 7px;" )	
			
			# Enable widgets 
			self.save_widget.setEnabled(True)
			self.meas_select.setEnabled(True)
			self.inst_widget.setEnabled(True)
			self.mpp_bias.setEnabled(True)
			self.mpp_cmpl.setEnabled(True)
			self.iv_plot.mpl_refresh_setEnabled(True)
			self.voc_plot.mpl_refresh_setEnabled(True)	
			self.mpp_plot.mpl_refresh_setEnabled(True)

			# Set thread running to False. This will break the sweep measurements
			# execution loop on next iteration.  
			self.mpp_thread_running = False	
			self.mpp_thread.join()  # Waits for thread to complete
