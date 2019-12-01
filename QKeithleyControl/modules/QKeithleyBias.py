#!/bin/python 
import visa
import time
import numpy as np
import threading

# Import d_plot and keithley driver
import drivers.keithley_2400

import modules.QDynamicPlot 

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

			self.cmpl_label.setText("Compliance (A)")
			self.cmpl.setMinimum(0.0)
			self.cmpl.setMaximum(1.0)
			self.cmpl.setValue(0.1)

			self.bias_label.setText("Bias Level (V)")
			self.bias.setMinimum(-20.0)
			self.bias.setMaximum(20.0)
			self.bias.setSingleStep(0.1)
			self.bias.setValue(0.0)

			self.keithley.current_cmp(self.cmpl.value())
			self.keithley.voltage_src()

			self.plot.set_axes_labels("Time (s)", "Current (A)")
			self.plot.refresh_axes()

		# Current mode adjust lables and limits
		if self.mode.currentText() == "Current":
	
			self.cmpl_label.setText("Compliance (V)")
			self.cmpl.setMinimum(0.0)
			self.cmpl.setMaximum(20.0)
			self.cmpl.setValue(1.0)


			self.bias_label.setText("Bias Level (A)")
			self.bias.setMinimum(-20.0)
			self.bias.setMaximum(20.0)
			self.bias.setSingleStep(0.001)
			self.bias.setValue(0.0)

			self.keithley.voltage_cmp(self.cmpl.value())
			self.keithley.current_src()

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

		# Compliance Spinbox
		self.cmpl_label = QLabel("Compliance (A)")
		self.cmpl = QDoubleSpinBox()
		self.cmpl.setDecimals(3)
		self.cmpl.setMinimum(0.0)
		self.cmpl.setMaximum(1.0)
		self.cmpl.setSingleStep(0.001)
		self.cmpl.setValue(0.1)

		# Level 
		self.bias_label = QLabel("Voltage (V)")
		self.bias = QDoubleSpinBox()
		self.bias.setDecimals(3)
		self.bias.setMinimum(0.0)
		self.bias.setMaximum(1.0)
		self.bias.setSingleStep(0.1)
		self.bias.setValue(0.0)

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
		self.ctl_layout.addWidget(self.bias_label)
		self.ctl_layout.addWidget(self.bias)
		self.ctl_layout.addWidget(self.delay_label)
		self.ctl_layout.addWidget(self.delay)
		self.ctl_layout.addWidget(self.cmpl_label)
		self.ctl_layout.addWidget(self.cmpl)
		self.ctl_layout.addWidget(self.update_button)

		return self.ctl_layout

	# Measurement thread
	def _exec_measuremet(self):	

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
			self.thread = threading.Thread(target=self._exec_measuremet, args=())
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
			self.bias.setValue(0.0)
			self.keithley.set_voltage(0.0)
			self.keithley.output_off()	

	# Dynamic Plotting Capability
	def _gen_bias_plot(self): 		

		# Create QDynamicPlot Object
		self.plot = modules.QDynamicPlot.QDynamicPlot(self)
		self.plot.set_axes_labels("Time (s)", "Current (A)")
		self.plot.add_axes()

		# Alias plot layout and return layout
		self.plt_layout = self.plot.layout
		return self.plt_layout