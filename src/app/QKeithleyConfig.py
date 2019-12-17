# ---------------------------------------------------------------------------------
# 	QKeithleyConfigure -> QVisaConfigure
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
import time
import pyvisa
import numpy as np

# Import device drivers
from PyQtVisa.drivers import keithley2400

# Import QVisaConfigure
from PyQtVisa import QVisaConfigure

# Import QKeithleyWidget
from src.widgets.QKeithleyConfigWidget import QKeithleyConfigWidget

# Import QT backends
import os
import sys
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox, QPushButton, QLabel, QStackedWidget, QDoubleSpinBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

# Configuration application to initalize and manage multiple Keithley insturments 
# in a single context handles. Devices are uniquely addressable via QVisaConfigure
# built-ins
class QKeithleyConfig(QVisaConfigure.QVisaConfigure):

	def __init__(self):

		# Inherits QVisaConfigure -> QWidget
		super(QKeithleyConfig, self).__init__()	

		# Create Icon for QMessageBox
		self.gen_main_layout()

	# Main layout	
	def gen_main_layout(self):	

		# Create configuration layout	
		self._layout = QVBoxLayout()

		# addr address spinbox and button
		self._addr_label = QLabel("<b>GPIB Address</b>")
		self._addr_value = QSpinBox()
		self._addr_value.setMinimum(0)
		self._addr_value.setMaximum(30)
		self._addr_value.setValue(24)
		self._addr_button = QPushButton("Initialize Keithley GPIB")
		self._addr_button.clicked.connect(self.initialize_addr)

		# Generate QVisaInstWidget
		self._inst_widget_label = QLabel("<b>Select Instrument</b>")
		self._inst_widget = self._gen_inst_widget()
		self._inst_widget.set_callback("update_inst_pages")
		self._inst_pages = QStackedWidget()

		# Add widgets to layout
		self._layout.addWidget(self._addr_label)
		self._layout.addWidget(self._addr_value)
		self._layout.addWidget(self._addr_button)
		self._layout.addWidget(self._inst_widget_label)
		self._layout.addWidget(self._inst_widget)
		self._layout.addStretch(1)
		self._layout.addWidget(self._inst_pages)

		# Set application layout
		self.setLayout(self._layout)
		self.setFixedWidth(350)

		# Set application icon
		self._icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico"))

	
	# This will update the QStackedWidget to show the correct QKeithleyWidget
	def update_inst_pages(self):
		
		# Get current text
		_name = self._inst_widget.currentText()
		if _name is not None:
			
			# Loop through QStacked widget children
			for _inst in list( self._inst_pages.findChildren(QKeithleyWidget) ):

				# If insturment name matches name
				if _inst._name == _name:

					# Set widget page
					self._inst_pages.setCurrentWidget(_inst)


	# Callback to handle addr initialization
	def initialize_addr(self):

		# Build local value and name of insturment
		_addr = self._addr_value.value()
		_name = str("Keithley GPIB::%s"%_addr) 

		# Try to initialize Keithley
		try: 

			# Check if Keithley has already been initialized at address
			if self._get_inst_byname(_name) is not None:

				# Message box to display error
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Warning)
				msg.setText("Device exists at GPIB::%s"%str(_addr))
				msg.setWindowTitle("pyVISA Error")
				msg.setWindowIcon(self._icon)
				msg.setStandardButtons(QMessageBox.Ok)
				msg.exec_()

			# Otherwise try to add the keithley	
			else:

				# Initialize insturment driver
				_inst = keithley2400.keithley2400(_addr, _name)
	
				# Check if insturement is actially a keithley 24xx	
				if "KEITHLEY INSTRUMENTS INC.,MODEL 24" not in str(_inst.idn()):
					
					msg = QMessageBox()
					msg.setIcon(QMessageBox.Warning)
					msg.setText("Device at GPIB::%s is NOT a Keithley"%str(_addr))
					msg.setWindowTitle("pyVISA Error")
					msg.setWindowIcon(self._icon)
					msg.setStandardButtons(QMessageBox.Ok)
					msg.exec_()	

				# If so then continure with initialization
				else: 
					# Add insturment handles
					self._add_inst_handle(_inst)
					self._get_inst_byaddr(_addr).reset()

					# Supress signals to not fire callback on text changed
					self._inst_widget.blockSignals(True)
					self._inst_widget.refresh( self )
					self._inst_widget.blockSignals(False)
					
					self._inst_pages.addWidget( QKeithleyConfigWidget( self, _name ) )

					# Message box to display success
					msg = QMessageBox()
					msg.setIcon(QMessageBox.Information)
					msg.setText("Initialized device at GPIB::%s"%_addr)
					msg.setWindowTitle("pyVISA Connection")
					msg.setWindowIcon(self._icon)
					msg.setStandardButtons(QMessageBox.Ok)
					msg.exec_()

		# Display error message if connection error
		except pyvisa.VisaIOError:

			# Message box to display error
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("No deivce at GPIB::%s"%str(_addr))
			msg.setWindowTitle("pyVISA Error")
			msg.setWindowIcon(self._icon)
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()
