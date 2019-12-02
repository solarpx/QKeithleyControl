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

# Import d_plot and keithley driver
import drivers.keithley_2400

# Import QT backends
import sys
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel
from PyQt5.QtCore import Qt

# Container class to construct sweep measurement widget
class QKeithleyConfig(QWidget):

	def __init__(self):

		# Inherits QWidget
		QWidget.__init__(self)	

		# Create configuration layout
		self.layout = QHBoxLayout()
		self.layout.addLayout(self._gen_config_layout())
		self.layout.addStretch(2)
		self.setLayout(self.layout)

		# Keithley object
		self.keithley = None

	def _get_keithley_handle(self):
		return self.keithley	

	# Callback to handle GPIB initialization
	def _initialize_gpib(self):

		try: 
			# Try to initialize Keithley
			self.GPIB = self.config_gpib.value()
			self.keithley = drivers.keithley_2400.keithley_2400(self.GPIB)
			self.keithley.reset()

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
			msg.setText("Initialized device at GPIB address %s"%str(self.GPIB))
			msg.setWindowTitle("pyVISA Connection")
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()

		# Display error message if connection error
		except visa.VisaIOError:

			# Set Keithley as None
			self.keithley = None	

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
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()
 			

	# Callback for sense mode
	def _update_config(self):

		# Check to see if Keithley has been initilaized
		if self.keithley is not None:	

			# Update sense mode
			if self.config_sense_mode.currentText() == "2-wire":
				self.keithley.four_wire_sense_off()
			
			if self.config_sense_mode.currentText() == "4-wire":
				self.keithley.four_wire_sense_on()

			# Update output route
			if self.config_output_route.currentText() == "Front":
				self.keithley.output_route_front()
			
			if self.config_output_route.currentText() == "Rear":
				self.keithley.output_route_rear()

			# Update integration time
			self.keithley.update_nplc(self.config_nplc.value())


	# Configuration modes for Keithley
	def _gen_config_layout(self):

		self.config_layout = QVBoxLayout()

		# GPIB Address Spinbox
		self.configlgpib = QLabel("<b>GPIB Address</b>")
		self.config_gpib = QSpinBox()
		self.config_gpib.setMinimum(0)
		self.config_gpib.setMaximum(36)
		self.config_gpib.setValue(24)

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
		return self.config_layout