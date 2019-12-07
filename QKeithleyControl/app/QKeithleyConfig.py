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

# Import device drivers
import drivers.keithley2400

# Import QVisaConfig
import widgets.QVisaConfig

# Import QT backends
import os
import sys
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon


class QKeithleyConfig(widgets.QVisaConfig.QVisaConfig):

	def __init__(self):

		# Inherits QVisaWidget -> QWidget
		super(QKeithleyConfig, self).__init__(self)	

		# Create Icon for QMessageBox
		self._gen_main_layout()

	# Main layout	
	def _gen_main_layout(self):	

		# Create configuration layout
		self.layout = QHBoxLayout()
		self.layout.addLayout(self._gen_config_layout())
		self.layout.addStretch(2)
		self.setLayout(self.layout)
	

		self.icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico"))

	# Callback to handle GPIB initialization
	def _initialize_gpib(self):

		try: 
			# Try to initialize Keithley
			self._add_inst_handle(drivers.keithley2400.keithley2400(self.config_gpib.value()))
			self._get_inst_byaddr(self.config_gpib.value()).reset()

			# Enable controls. Reset comboboxes to reflect current state
			self.config_sense_mode.setEnabled(True)
			self.config_sense_mode.setCurrentIndex(0)

			self.config_output_route.setEnabled(True)
			self.config_output_route.setCurrentIndex(0)

			self.config_nplc.setEnabled(True)
			self.config_nplc.setValue(1.0)
			
			self.submit_config.setEnabled(True)

			# Message box to display success
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Information)
			msg.setText("Initialized device at GPIB address %s"%self.config_gpib.value())
			msg.setWindowTitle("pyVISA Connection")
			msg.setWindowIcon(self.icon)
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()

		# Display error message if connection error
		except visa.VisaIOError:

			# Disable controls
			self.config_sense_mode.setEnabled(False)
			self.config_sense_mode.setCurrentIndex(0)

			self.config_output_route.setEnabled(False)
			self.config_output_route.setCurrentIndex(0)

			self.config_nplc.setEnabled(False)
			self.config_nplc.setValue(1.0)

			self.submit_config.setEnabled(False)

			# Message box to display error
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("No deivce at GPIB address %s"%str(self.GPIB))
			msg.setWindowTitle("pyVISA Error")
			msg.setWindowIcon(self.icon)
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()
 			
	# Callback for sense mode
	def _update_config(self):

		# Check to see if Keithley has been initilaized
		if self._get_inst_byaddr(self.config_gpib.value()) is not None:

			# Update sense mode
			if self.config_sense_mode.currentText() == "2-wire":
				self._get_inst_byaddr(self.config_gpib.value()).four_wire_sense_off()
			
			if self.config_sense_mode.currentText() == "4-wire":
				self._get_inst_byaddr(self.config_gpib.value()).four_wire_sense_on()

			# Update output route
			if self.config_output_route.currentText() == "Front":
				self._get_inst_byaddr(self.config_gpib.value()).output_route_front()
			
			if self.config_output_route.currentText() == "Rear":
				self._get_inst_byaddr(self.config_gpib.value()).output_route_rear()

			# Update integration time
			self._get_inst_byaddr(self.config_gpib.value()).update_nplc(self.config_nplc.value())

		# Message box to indicate successful update
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)
		msg.setText("Keithley Configuration Updated")
		msg.setWindowTitle("QKeithleyControl")
		msg.setWindowIcon(self.icon)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()	

	# Configuration modes for Keithley
	def _gen_config_layout(self):

		self.config_layout = QVBoxLayout()

		# GPIB Address Spinbox
		self.configlgpib = QLabel("<b>GPIB Address</b>")
		self.config_gpib = QSpinBox()
		self.config_gpib.setMinimum(0)
		self.config_gpib.setMaximum(30)
		self.config_gpib.setValue(24)

		# Size the spinbox (to fix QVBoxLayout Width)
		self.config_gpib.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding);
		self.config_gpib.setMinimumSize(QSize(250, 10))

		# GPIB Submit
		self.submit_gpib = QPushButton("Initialize Keithley GPIB")
		self.submit_gpib.clicked.connect(self._initialize_gpib)

		# Additional Configuration Methods
		self.config_sense_mode_label = QLabel("<b>Sense Mode</b>")
		self.config_sense_mode = QComboBox()
		self.config_sense_mode.addItems(["2-wire", "4-wire"])
		self.config_sense_mode.setEnabled(False)
		

		# Additional Configuration Methods
		self.config_output_route_label = QLabel("<b>Output Route</b>")
		self.config_output_route = QComboBox()
		self.config_output_route.addItems(["Front", "Rear"])
		self.config_output_route.setEnabled(False)
		
		# Intergration time control. Note that integration time 
		# is specified in power line cycles (50/60Hz)
		self.config_nplc_label = QLabel("<b>Integration Time (nPLC)</b>")
		self.config_nplc_note = QLabel("<i>Power Line Cycle (50|60)Hz</i>")
		self.config_nplc = QDoubleSpinBox()
		self.config_nplc.setDecimals(3)
		self.config_nplc.setMinimum(0.01)
		self.config_nplc.setMaximum(10.0)
		self.config_nplc.setSingleStep(0.01)
		self.config_nplc.setValue(1.00)
		self.config_nplc.setEnabled(False)

		# Update Configuration
		self.submit_config = QPushButton("Update Configuration")
		self.submit_config.setEnabled(False)
		self.submit_config.clicked.connect(self._update_config)

		# Add widgets to layout
		self.config_layout.addWidget(self.configlgpib)
		self.config_layout.addWidget(self.config_gpib)
		self.config_layout.addWidget(self.submit_gpib)

		self.config_layout.addStretch(1)

		# Add other system controls
		self.config_layout.addWidget(self.config_sense_mode_label)
		self.config_layout.addWidget(self.config_sense_mode)

		self.config_layout.addWidget(self.config_output_route_label)
		self.config_layout.addWidget(self.config_output_route)

		self.config_layout.addWidget(self.config_nplc_label)
		self.config_layout.addWidget(self.config_nplc_note)
		self.config_layout.addWidget(self.config_nplc)
		self.config_layout.addWidget(self.submit_config)

		# Return layout object
		self.config_layout.setContentsMargins(20,11,11,11)
		return self.config_layout