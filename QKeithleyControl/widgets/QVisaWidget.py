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

# Import QT backends
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel, QFileDialog, QSizePolicy, QLineEdit
from PyQt5.QtCore import Qt, QStateMachine, QState, QObject
from PyQt5.QtGui import QIcon

# The purpouse of this object is to bind a list pyVisaDevices to a QWidget 
# Thus, it provides a basic framework for constructing user interfaces for 
# interacting with GPIB hardware. QVisaWidget also contains a structure to 
# manipulate data and some basic tools to render controls. The QVisaWidget 
# object can also be used as a container for GPIB insturment handles to be
# used in other QVisaWidget objects in an application context.
#

class QVisaWidget(QWidget):

	# Initialization: Note that _config is a QVisaConfig object 
	# which contains a list of pyVisaDevices	
	def __init__(self, _config):

		QWidget.__init__(self)
		self._config = _config 
		self._data = {}	


	#####################################
	#  DATA MANAGEMENT METHODS
	#			

	# Method to add data keys	
	def _add_meas_keys(self, _meas_keys):
		for _ in _meas_keys:
			self._data[_] = None

	# Method to add single key
	def _add_meas_key(self, _meas_key):
		self._data[_meas_key] = None

	# Method set data keys
	def _set_meas_keys(self, _meas_keys):
		self._data = {_: None for _ in _meas_keys}

	# Method to add data fields
	def _set_data_fields(self, _meas_key, _data_keys):
		if _meas_key in self._data.keys():
			self._data[_meas_key]={_: [] for _ in _data_keys}

	def _reset_data(self):
		self._data = {}	
	

	#####################################
	#  SAVE METHOD
	#	

	# Sace traces method (same as sweep control)	
	def _gen_data_file(self):

		# If data is empty display warning message
		if  all( _ is None for _ in list(self._data.values()) ):

			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("No measurement data")
			msg.setWindowTitle("Bias Info")
			msg.setWindowIcon(self.icon)
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()

		# Otherwise save
		else:

			# Open file dialog
			dialog = QFileDialog(self)
			dialog.setFileMode(QFileDialog.AnyFile)
			dialog.setViewMode(QFileDialog.Detail)
			filenames = []

			# Select file
			if dialog.exec_():
				filenames = dialog.selectedFiles()

			# Open file pointer			
			f = open(filenames[0], 'w+')

			# Start write sequence
			with f:	
	
				# Write data header
				f.write("* QVisaWidget v1.1\n")
				if self.save_note.text() != "":
					f.write("* NOTE %s\n"%self.save_note.text())
				
				# Only save if data exists on a given key
				for _meas_key, _meas_data in self._data.items():

					# If measurement data exists on key
					if _meas_data is not None:

						# Write measurement key header
						f.write("* %s\n*\n"%str(_meas_key))

						# Write data keys
						for _data_key in _meas_data.keys():
							f.write("%s\t\t"%str(_data_key))
						f.write("\n")
									
						# Write data values. 
						# Use length of first column for index iterator
						for i in range( len( _meas_data[ list(_meas_data.keys())[0] ] ) ):

							# Go across the dictionary keys on iterator
							for data_key in _meas_data.keys():
								f.write("%s\t"%str(_meas_data[data_key][i]))
							f.write("\n")

						f.write("\n\n")

				f.close()

			# Message box to indicate successful save
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Information)
			msg.setText("Measurement data saved")
			msg.setWindowTitle("Bias Info")
			msg.setWindowIcon(self.icon)
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()		


	#####################################
	#  LAYOUT SHORTCUTS
	#					

	# Helper method to pack widgets into hbox
	def _gen_hbox_widget(self, _widget_list):
	
		_widget = QWidget()
		_layout = QHBoxLayout()
		for _w in _widget_list:
			_layout.addWidget(_w)

		_layout.setContentsMargins(0,0,0,0)
		_widget.setLayout(_layout)
		return _widget	

	# Helper method to pack widgets into vbox
	def _gen_vbox_widget(self, _widget_list):
	
		_widget = QWidget()
		_layout = QVBoxLayout()
		for _w in _widget_list:
			_layout.addWidget(_w)

		_layout.setContentsMargins(0,0,0,0)
		_widget.setLayout(_layout)
		return _widget