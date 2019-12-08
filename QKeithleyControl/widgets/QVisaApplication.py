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
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QFileDialog, QLabel, QLineEdit, QPushButton, QComboBox

# The purpouse of the QVisaApplication object is to bind a list pyVisaDevices to a QWidget 
# It provides a basic framework for constructing user interfaces for nteracting with GPIB 
# hardware. QVisaApplication also contains a structure to manipulate data and some basic 
# tools to render controls. QVisaAppication also embeds two standard widget templates for 
# saving data and to managing insturments.

class QVisaApplication(QWidget):

	# Initialization: Note that _config is a QVisaConfig object 
	# which contains a list of pyVisaDevices	
	def __init__(self, _config):

		QWidget.__init__(self)
		self._config = _config 
		self._data = {}
		self._meta = {}

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

	# Method to add metadata
	def _set_meta(self, _key, _meta):
		self._meta[_key]=_meta
	
	# Method to get metadata
	def _get_meta(self, _key):
		return self._meta[_key] if _key in self._meta.keys() else None

	# Method to reset data	
	def _reset_data(self):
		self._data = {}	


	#####################################
	#  CONFIG WRAPPER METHODS
	#	

	# Method to get insturment handles
	def _get_inst_handles(self):
		return self._config._get_inst_handles()

	# Method to get insturment names
	def _get_inst_names(self):
		return self._config._get_inst_names()

	# Method to get insturment handles
	def _get_inst_byname(self, _name):
		return self._config._get_inst_byname(_name)	


	#####################################
	#  INST METHODS and WIDGET
	#	
	
	# Method to generate insturment widget
	def _gen_inst_widget(self):

		# Save widget and layout
		_widget = QWidget()
		_layout = QHBoxLayout()

		# Widget label and comboBox
		_widget_label = QLabel("Select Insturment")
		_widget_select =  QComboBox()
		_widget_select.setFixedWidth(200)

		# Widget select
		if self._get_inst_names() is not None:
			_widget_select.addItems(self._get_inst_names())

		# Add widgets to layout
		return self._gen_hbox_widget([_widget_select, _widget_label])

	# Get insturment text	
	def _get_inst_widget_text(self, _widget):
		_widget_select = _widget.findChild(QComboBox)
		return _widget_select.currentText()

	# Method to refresh insurment widget
	def _refresh_inst_widget(self, _widget):
	
		# If there are insturment handles
		_widget_select = _widget.findChild(QComboBox)
		_widget_select.clear()
		_widget_select.addItems(self._get_inst_names())
		
	#####################################
	#  SAVE METHODS and WIDGET
	#	

	# Enable and disable save button
	def _set_save_enabled(self, _widget, _bool):
		_widget_button = _widget.findChild(QPushButton)
		_widget_button.setEnabled(_bool)

	# Method to generate the standard save widget
	def _gen_save_widget(self):

		# Save widget and layout
		_widget = QWidget()
		_layout = QVBoxLayout()

		# Save note
		_widget_note_label = QLabel("Measurement Note")
		_widget_note = QLineEdit()
		_widget_note.setFixedWidth(200)
		
		# Save button
		_widget_button = QPushButton("Save Data")
		_widget_button.clicked.connect(self._gen_data_file)

		# Pack the widget layout
		_layout.addWidget(self._gen_hbox_widget([_widget_note, _widget_note_label]))
		_layout.addWidget(_widget_button)
		_layout.setContentsMargins(0,0,0,0)

		# Set layout and return the widget
		_widget.setLayout(_layout)

		return _widget

	# Sace traces method (same as sweep control)	
	def _gen_data_file(self):

		# If data is empty display warning message
		if  self._data == {}:

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


			# Check if filenames is not empty 
			# 	*) for cancel button
			if filenames != []:
				
				# Open file pointer	
				f = open(filenames[0], 'w+')

				# Start write sequence
				with f:	
		
					# Write data header
					f.write("*! QVisaWidget v1.1\n")
					if self._save_note.text() != "":
						f.write("*! NOTE %s\n"%self._save_note.text())
					
					# Only save if data exists on a given key
					for _meas_key, _meas_data in self._data.items():

						# If measurement data exists on key
						if _meas_data is not None:

							# Write measurement key header
							f.write("#! %s\n"%str(_meas_key))

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
				msg.setWindowTitle("Application Info")
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
