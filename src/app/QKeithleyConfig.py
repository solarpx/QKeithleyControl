# ---------------------------------------------------------------------------------
# 	QKeithleyConfigure -> QVisaConfigure
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

		# Set application icon
		self._icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico"))

		# Insturment initialization widget
		self._device_widget = self._gen_device_control()
		self._device_widget.set_init_callback("init_keithley")
		self._device_widget.set_select_callback("updatedevice_pages")

		# QStackedWidget for insturment configurations
		self.device_pages = QStackedWidget()

		# Add comm widget and inst pages
		self._layout.addWidget(self._device_widget)
		self._layout.addStretch(1)
		self._layout.addWidget(self.device_pages)

		# Set application layout
		self.setLayout(self._layout)
		self.setFixedWidth(350)


	# Callback to handle addr initialization
	def init_keithley(self):

		# Initialize Keithley
		Device = self._device_widget.init( keithley2400.keithley2400 )

		# Build configuration widget for Keithley
		if Device is not None:
			self.device_pages.addWidget( QKeithleyConfigWidget( self, Device.get_property("name") ) )


	# This will update the QStackedWidget to show the correct QKeithleyWidget
	def update_device_pages(self):
		
		# Get current text
		Device = self._device_widget.get_current_inst()
		if Device is not None:
			
			# Loop through QStacked widget children
			for _page in list( self.device_pages.findChildren(QKeithleyConfigWidget) ):

				# If insturment name matches page name
				if _page.name == Device.get_property("name"):

					# Set widget page
					self.device_pages.setCurrentWidget(_page)