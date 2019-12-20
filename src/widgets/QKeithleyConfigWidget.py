# ---------------------------------------------------------------------------------
# 	QKeithleyConfigWidget -> QWidget
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

# Import QT backends
from PyQt5.QtWidgets import QWidget, QMessageBox, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QStackedWidget, QDoubleSpinBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

# Container class for Keithley to render keithley controls in the configuration script. 
# Note that _app must be QVisaConfigure widget or QVisaApplication widget

class QKeithleyConfigWidget(QWidget):

	def __init__(self, _app, _name):

		# Extends QWidget
		QWidget.__init__(self)

		# Cache a reference to the calling application 
		self._app  = _app
		self.name = _name

		# Generate main layout
		self.gen_main_layout()

	def gen_main_layout(self):
	
		self.layout = QVBoxLayout()
		self.name_label = QLabel("<b>Configure %s</b>"%str(self.name))

		self.sense_mode_label = QLabel("<b>Sense Mode</b>")
		self.sense_mode = QComboBox()
		self.sense_mode.addItems(["2-wire", "4-wire"])

		self.output_route_label = QLabel("<b>Output Route</b>")
		self.output_route = QComboBox()
		self.output_route.addItems(["Front", "Rear"])

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

		# Update button
		self.inst_update = QPushButton("Update Configuration")
		self.inst_update.clicked.connect(self.update_config)

		# Add widgets to layout
		self.layout.addWidget(self.name_label)
		self.layout.addWidget(self.sense_mode_label)
		self.layout.addWidget(self.sense_mode)
		self.layout.addWidget(self.output_route_label)
		self.layout.addWidget(self.output_route)
		self.layout.addWidget(self.config_nplc_label)
		self.layout.addWidget(self.config_nplc_note)
		self.layout.addWidget(self.config_nplc)
		self.layout.addWidget(self.inst_update)

		# Set layout
		self.setLayout(self.layout)

	# Callback for sense mode
	def update_config(self):

		# Check to see if Keithley has been initilaized
		if self._app.get_device_by_name(self.name) is not None:

			# Update sense mode
			if self.sense_mode.currentText() == "2-wire":
				self._app.get_device_by_name(self.name).four_wire_sense_off()
			
			if self.sense_mode.currentText() == "4-wire":
				self._app.get_device_by_name(self.name).four_wire_sense_on()

			# Update output route
			if self.output_route.currentText() == "Front":
				self._app.get_device_by_name(self.name).output_route_front()
			
			if self.output_route.currentText() == "Rear":
				self._app.get_device_by_name(self.name).output_route_rear()

			# Update integration time
			self._app.get_device_by_name(self.name).update_nplc(self.config_nplc.value())

		# Message box to indicate successful update
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)
		msg.setText("Keithley Configuration Updated")
		msg.setWindowTitle("QKeithleyControl")
		msg.setWindowIcon(self._app._icon)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()	
