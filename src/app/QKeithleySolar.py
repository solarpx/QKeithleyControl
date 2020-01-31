# ---------------------------------------------------------------------------------
# 	QKeithleySolar -> QVisaApplication 
#	Copyright (C) 2019 Michael Winters
#	github: https://github.com/mesoic
#	email:  mesoic@protonmail.com
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

# Import numpy
import numpy as np

# Import QVisaApplication
from PyQtVisa import QVisaApplication

# Import PyQtVisa widgets
from PyQtVisa.widgets import QVisaUnitSelector
from PyQtVisa.widgets import QVisaDynamicPlot 

# Import QT backends
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel, QFileDialog, QSizePolicy, QLineEdit
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject
from PyQt5.QtGui import QIcon

# Container class to construct photovoltaic characterization widget
class QKeithleySolar(QVisaApplication.QVisaApplication):

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
		return self.get_device_by_name( self.device_select.currentText() )

	# Update bias on keithley
	def update_bias(self, _value):
		if self.keithley() is not None:
			self.keithley().set_voltage(_value)	

	# Method to refresh the widget
	def refresh(self):
	
		# If add insturments have been initialized
		if self.get_devices() is not None:

			# Reset the widget and add insturments
			self.device_select.refresh( self )

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
		self.layout.addLayout(self.gen_solar_ctrl(), 1)
		self.layout.addWidget(self.gen_solar_plot(), 3)
		self.setLayout(self.layout)
		

	# Method to generate solar characterization controls
	def gen_solar_ctrl(self):

		# Solar mode layout
		self.ctl_layout = QVBoxLayout()

		# Add insturement selector
		self.device_select_label = QLabel("Select Device")
		self.device_select = self._gen_device_select()
		self.device_select.setFixedWidth(200)

		# Generate (IV, Voc, MPP) container widgets
		# These methods will pack self.inst_select
		self.gen_voc_ctrl() 			# self.voc_ctrl
		self.gen_mpp_ctrl()				# self.mpp_ctrl
		self.gen_iv_ctrl()				# self.iv_ctrl

		# Add measurement widgets to QStackedWidget
		self.meas_pages = QStackedWidget()
		self.meas_pages.addWidget(self.voc_ctrl)
		self.meas_pages.addWidget(self.mpp_ctrl)
		self.meas_pages.addWidget(self.iv_ctrl)
		self.meas_pages.setCurrentIndex(0);
	
		# Measurement select QComboBox
		self.meas_select_label = QLabel("Measurement Mode")
		self.meas_select = QComboBox()
		self.meas_select.setFixedWidth(200)
		self.meas_select.addItems(["Voc", "MPP", "IV"])
		self.meas_select.currentTextChanged.connect(self.update_meas_pages)

		# Meta widget for trace description
		self.meta_widget_label = QLabel("<b>Trace Description</b>")
		self.meta_widget = self._gen_meta_widget()
		self.meta_widget.set_meta_subkey("__desc__")
		self.save_widget = self._gen_save_widget()


		#####################################
		#  ADD CONTROLS
		#

		# Add measurement select and measurement pages
		self.ctl_layout.addWidget(self.meas_pages)
		self.ctl_layout.addWidget(self._gen_hbox_widget([self.meas_select, self.meas_select_label]))
		self.ctl_layout.addWidget(self._gen_hbox_widget([self.device_select,self.device_select_label]))

		# Pack the standard save widget
		self.ctl_layout.addStretch(1)
		self.ctl_layout.addWidget(self.meta_widget_label)
		self.ctl_layout.addWidget(self.meta_widget)
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
		self.iv_start = QVisaUnitSelector.QVisaUnitSelector(self.iv_start_config)

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
		self.iv_stop = QVisaUnitSelector.QVisaUnitSelector(self.iv_stop_config)

		
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
		self.iv_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.iv_cmpl_config)	

		# Compliance
		self.iv_npts_config={
			"unit" 		: "__INT__", 
			"label"		: "Number of Points",
			"limit"		: 256.0, 
			"signed"	: False,
			"default"	: [51.0]
		}
		self.iv_npts = QVisaUnitSelector.QVisaUnitSelector(self.iv_npts_config)		

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
		self.voc_meas_off.assignProperty(self.voc_meas_button, 'text', 'Voc Monitor OFF')
		self.voc_meas_off.addTransition(self.voc_meas_button.clicked, self.voc_meas_on)
		self.voc_meas_off.entered.connect(self.exec_voc_stop)

		self.voc_meas_on.assignProperty(self.voc_meas_button, 'text', 'Voc Monitor ON')
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
		self.voc_bias = QVisaUnitSelector.QVisaUnitSelector(self.voc_bias_config)
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
		self.voc_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.voc_cmpl_config)	

		# Tracking mode convergence
		self.voc_ampl_config={
			"unit" 		: "V", 
			"min"		: "u",
			"max"		: "m",
			"label"		: "Sense amplitude (mV)",
			"limit"		: 0.1, 
			"signed"	: False,
			"default"	: [1.0,"m"]
		} 
		self.voc_ampl = QVisaUnitSelector.QVisaUnitSelector(self.voc_ampl_config)

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
		self.voc_conv = QVisaUnitSelector.QVisaUnitSelector(self.voc_conv_config)

		# Delay
		self.voc_gain_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: html.unescape("Proportional Gain (&permil;)"),
			"limit"		: 1000, 
			"signed"	: False,
			"default"	: [30.0]
		}
		self.voc_gain = QVisaUnitSelector.QVisaUnitSelector(self.voc_gain_config)


		# Delay
		self.voc_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: [1.0]
		}
		self.voc_delay = QVisaUnitSelector.QVisaUnitSelector(self.voc_delay_config)

		# Add voc widgets to layout
		self.voc_ctrl_layout.addWidget(self.voc_meas_button)
		self.voc_ctrl_layout.addWidget(self.voc_bias)
		self.voc_ctrl_layout.addWidget(self.voc_cmpl)
		self.voc_ctrl_layout.addWidget(self.voc_ampl)
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
		self.mpp_meas_off.assignProperty(self.mpp_meas_button, 'text', 'MPP Monitor OFF')
		self.mpp_meas_off.addTransition(self.mpp_meas_button.clicked, self.mpp_meas_on)
		self.mpp_meas_off.entered.connect(self.exec_mpp_stop)

		self.mpp_meas_on.assignProperty(self.mpp_meas_button, 'text', 'MPP Monitor ON')
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
		self.mpp_bias = QVisaUnitSelector.QVisaUnitSelector(self.mpp_bias_config)
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
		self.mpp_cmpl = QVisaUnitSelector.QVisaUnitSelector(self.mpp_cmpl_config)	

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
		self.mpp_ampl = QVisaUnitSelector.QVisaUnitSelector(self.mpp_ampl_config)

		# Delay
		self.mpp_gain_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: html.unescape("Proportional Gain (&permil;)"),
			"limit"		: 10000, 
			"signed"	: False,
			"default"	: [30.0]
		}
		self.mpp_gain = QVisaUnitSelector.QVisaUnitSelector(self.mpp_gain_config)


		# Delay
		self.mpp_delay_config={
			"unit" 		: "__DOUBLE__", 
			"label"		: "Measurement Interval (s)",
			"limit"		: 60.0, 
			"signed"	: False,
			"default"	: [0.1]
		}
		self.mpp_delay = QVisaUnitSelector.QVisaUnitSelector(self.mpp_delay_config)

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
		self.iv_plot =  QVisaDynamicPlot.QVisaDynamicPlot(self)
		self.iv_plot.add_subplot(111, twinx=True)
		self.iv_plot.set_axes_labels("111" , "Voltage (V)", "Current (mA)")
		self.iv_plot.set_axes_labels("111t", "Voltage (V)", "Power (mW)")
		self.iv_plot.set_axes_adjust(_left=0.15, _right=0.85, _top=0.9, _bottom=0.1)
		self.iv_plot.refresh_canvas(supress_warning=True)

		self.voc_plot =  QVisaDynamicPlot.QVisaDynamicPlot(self)
		self.voc_plot.add_subplot(111, twinx=True)
		self.voc_plot.set_axes_labels("111", "Time (s)", "Voc (V)")
		self.voc_plot.set_axes_labels("111t", "Time (s)", "Ioc (V)")
		self.voc_plot.set_axes_adjust(_left=0.15, _right=0.85, _top=0.9, _bottom=0.1)
		self.voc_plot.refresh_canvas(supress_warning=True)		

		self.mpp_plot =  QVisaDynamicPlot.QVisaDynamicPlot(self)
		self.mpp_plot.add_subplot(111, twinx=True)
		self.mpp_plot.set_axes_labels("111", "Time (s)", "Vmpp (V)")
		self.mpp_plot.set_axes_labels("111t", "Time (s)", "Pmpp (mW)")
		self.mpp_plot.set_axes_adjust(_left=0.15, _right=0.85, _top=0.9, _bottom=0.1)
		self.mpp_plot.refresh_canvas(supress_warning=True)		

		# Sync plot clear data buttons with application data
		self.iv_plot.sync_application_data(True)
		self.voc_plot.sync_application_data(True)
		self.mpp_plot.sync_application_data(True)

		# Sync meta widget when clearing data from plots
		self.iv_plot.set_mpl_refresh_callback("_sync_meta_widget_to_data_object")
		self.voc_plot.set_mpl_refresh_callback("_sync_meta_widget_to_data_object")
		self.mpp_plot.set_mpl_refresh_callback("_sync_meta_widget_to_data_object")

		# Add QVisaDynamicPlots to QStackedWidget
		self.plot_stack.addWidget(self.voc_plot)
		self.plot_stack.addWidget(self.mpp_plot)
		self.plot_stack.addWidget(self.iv_plot)

		# Return the stacked widget
		self.plot_stack.setCurrentIndex(0);
		return self.plot_stack

	
	# Sync meta widget to data object
	def _sync_meta_widget_to_data_object(self):

		# Application keys
		_data_keys = self._get_data_object().keys()
		_widget_keys = self.meta_widget.get_meta_keys()

		# Check if widget keys are not in data keys
		for _key in _widget_keys:
			
			# If not then delete the key from meta_widget
			if _key not in _data_keys:

				self.meta_widget.del_meta_key(_key)


	# Flip between controls when measurement mode selector is updated
	def update_meas_pages(self):
		
		if self.meas_select.currentText() == "Voc":
			self.meas_pages.setCurrentIndex(0)
			self.plot_stack.setCurrentIndex(0)

		if self.meas_select.currentText() == "MPP":
			self.meas_pages.setCurrentIndex(1)
			self.plot_stack.setCurrentIndex(1)

		if self.meas_select.currentText() == "IV":		
			self.meas_pages.setCurrentIndex(2)
			self.plot_stack.setCurrentIndex(2)


	# Callback method to delete data when traces are cleared
	def sync_mpl_clear(self):
		
		# Extract plot and data object
		_plot = self.plot_stack.currentWidget()
		_data = self._get_data_object()

		# Note that plot subkeys map to data keys
		for _subkey in _plot.get_axes_handles().subkeys("111"):
			_data.del_key(_subkey)

	#####################################
	#  IV-SWEEP MEASUREMENT MODE
	#	

	# Sweep measurement EXECUTION
	def exec_iv_thread(self):
		
		# Set sweep parameters as simple linspace
		_params = np.linspace( 
			float( self.iv_start.value() ), 
			float( self.iv_stop.value() ), 
			int( self.iv_npts.value() ) 
		)


		# Get QVisaDataObject
		data = self._get_data_object()
		key  = data.add_hash_key("pv-bias")

		# Add data fields to key
		data.set_subkeys(key, ["t", "V", "I", "P"])
		data.set_metadata(key, "__type__", "pv-bias")

		# Add key to meta widget
		self.meta_widget.add_meta_key(key)

		# Generate colors
		_c0 = self.iv_plot.gen_next_color()
		_c1 = self.iv_plot.gen_next_color()

		# Clear plot and zero arrays
		self.iv_plot.add_axes_handle('111' , key, _color=_c0)
		self.iv_plot.add_axes_handle('111t', key, _color=_c1)
		
		# Thread start time
		start  = float(time.time())
		
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
				_now = float(time.time() - start)

				# Append measured values to data arrays
				data.append_subkey_data(key, "t", _now )
				data.append_subkey_data(key, "V", float(_buffer[0]) )
				data.append_subkey_data(key, "I", -1.0 * float(_buffer[1]) )
				data.append_subkey_data(key, "P", -1.0 * float(_buffer[1]) * float(_buffer[0]) )

				self.iv_plot.append_handle_data( "111" , key, float(_buffer[0]), -1.0 * float(_buffer[1]))
				self.iv_plot.append_handle_data( "111t", key, float(_buffer[0]), -1.0 * float(_buffer[0]) * float(_buffer[1]))
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
			self.device_select.setEnabled(False)
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
			self.device_select.setEnabled(True)
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
		
		# Get QVisaDataObject
		data = self._get_data_object()
		key  = data.add_hash_key("pv-voc")

		# Add data fields to key
		data.set_subkeys(key, ["t", "Voc", "Ioc"])
		data.set_metadata(key, "__type__", "pv-voc")

		# Add key to meta widget
		self.meta_widget.add_meta_key(key)

		# Generate colors
		_c0 = self.voc_plot.gen_next_color()
		_c1 = self.voc_plot.gen_next_color()

		# Clear plot and zero arrays
		self.voc_plot.add_axes_handle('111' , key, _color=_c0)
		self.voc_plot.add_axes_handle('111t', key, _color=_c1)

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
					_amplitude = self.voc_ampl.value()
					_v, _i = np.add(float(_buffer[0]), np.linspace(-0.5 * _amplitude, 0.5 * _amplitude, 3)), []
					
					# Measure current over sense amplitude array
					for _ in _v:
						self.keithley().set_voltage(_)
						_b = self.keithley().meas().split(",")
						_i.append( float( _b[1] ) )

					# Reset the voltage
					self.keithley().set_voltage( float(_buffer[0] ) )
					
					# Ambipolar tracking algorithm (zero-crossing)
					# Need to adjust bias in direction of lower current
					# Solar cell current is positive: bias is above Voc
					if np.mean(_i) >= 0.0:
						self.update_bias( float(_buffer[0]) - abs( float(_buffer[1]) ) * self.voc_gain.value() / 1000. ) 

					# Solar cell current is negative: bias is below Voc
					else:
						self.update_bias( float(_buffer[0]) + abs( float(_buffer[1]) ) * self.voc_gain.value() / 1000. )


			# Extract data from buffer
			_now = float(time.time() - start)

			data.append_subkey_data(key, "t"  , _now)
			data.append_subkey_data(key, "Voc",  1.0 * float(_buffer[0]) )
			data.append_subkey_data(key, "Ioc", -1.0 * float(_buffer[1]) ) # Sanity check

			# Append handle data and update canvas
			self.voc_plot.append_handle_data("111" , key, _now,  1.0 * float(_buffer[0]) )
			self.voc_plot.append_handle_data("111t", key, _now, -1.0 * float(_buffer[1]) )
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
			self.device_select.setEnabled(False)
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
			self.device_select.setEnabled(True)
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
		
		# Get QVisaDataObject
		data = self._get_data_object()
		key  = data.add_hash_key("pv-mpp")

		# Add data fields to key
		data.set_subkeys(key, ["t", "Vmpp", "Impp", "Pmpp"])
		data.set_metadata(key, "__type__", "pv-mpp")

		# Add key to meta widget
		self.meta_widget.add_meta_key(key)

		# Generate colors
		_c0 = self.mpp_plot.gen_next_color()
		_c1 = self.mpp_plot.gen_next_color()

		# Clear plot and zero arrays
		self.mpp_plot.add_axes_handle('111' , key, _color=_c0)
		self.mpp_plot.add_axes_handle('111t', key, _color=_c1)
		
		# Thread start time
		start  = float(time.time())

		# Set bias to initial value in volts and turn output ON
		self.keithley().set_voltage( self.mpp_bias.value() )
		self.keithley().current_cmp( self.mpp_cmpl.value() )
		self.keithley().output_on()

		# Thread loop
		while self.mpp_thread_running is True:

			# Iteration timer
			_iter_start = float(time.time())

			# Covergence loop
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
					_v, _i = np.add(float(_buffer[0]), np.linspace(-0.5 * _amplitude, 0.5 * _amplitude, 5)), []

					# Measure current over sense amplitude array
					for _ in _v:
						self.keithley().set_voltage(_)
						_b = self.keithley().meas().split(",")
						_i.append( -1.0 * float( _b[1] ) )

					# Reset the voltage
					self.keithley().set_voltage( float(_buffer[0] ) )

					# Calculate derivative of current and power
					_p  = np.multiply(_i, _v)
					_dp = np.divide( np.gradient(np.multiply(_i, _v)) , _amplitude)

					# Ambipolar tracking algorithm
					if np.mean(_dp) <= 0.0:
						self.update_bias( float(_buffer[0]) - abs( np.mean(_dp) ) * self.voc_gain.value() / 1000. ) 

					# Solar cell current is negative: bias is below Voc
					else:
						self.update_bias( float(_buffer[0]) + abs( np.mean(_dp) ) * self.voc_gain.value() / 1000. )


			# Extract data from buffer
			_now = float(time.time() - start)

			data.append_subkey_data(key, "t"	, _now)
			data.append_subkey_data(key, "Vmpp",  1.0 * float(_buffer[0]) )
			data.append_subkey_data(key, "Impp", -1.0 * float(_buffer[1]) ) 
			data.append_subkey_data(key, "Pmpp", -1.0 * float(_buffer[1]) * float(_buffer[0]) )

			# Append handle data and update canvas
			self.mpp_plot.append_handle_data("111" , key, _now, float(_buffer[0]))
			self.mpp_plot.append_handle_data("111t", key, _now, float(_buffer[0]) * -1.0 * float(_buffer[1]) * 1000.)
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
			self.device_select.setEnabled(False)
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
			self.device_select.setEnabled(True)
			self.mpp_bias.setEnabled(True)
			self.mpp_cmpl.setEnabled(True)
			self.iv_plot.mpl_refresh_setEnabled(True)
			self.voc_plot.mpl_refresh_setEnabled(True)	
			self.mpp_plot.mpl_refresh_setEnabled(True)

			# Set thread running to False. This will break the sweep measurements
			# execution loop on next iteration.  
			self.mpp_thread_running = False	
			self.mpp_thread.join()  # Waits for thread to complete
