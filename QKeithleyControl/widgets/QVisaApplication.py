# ---------------------------------------------------------------------------------
# 	QVisaApplication -> QWidget
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

#!/usr/bin/env python 
import time
import hashlib 

# Import QT backends
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QIcon

# Import QVisaWidgets
import widgets.QVisaInstWidget
import widgets.QVisaSaveWidget

#####################################
#  VISA APPLICATION CLASS
#	

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

	# Keygen
	def _meas_keygen(self, _key):
		m = hashlib.sha256()
		m.update( str( "%s@%s"%( _key, str(time.time())) ).encode() )
		return ( str(m.hexdigest()[:7]) ,"%s %s"%(_key, str( m.hexdigest()[:7] ) ) )

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
	#  INST/SAVE WIDGET CONSTRUCTORS
	#	
	
	# Method to generate insturment widget
	def _gen_inst_widget(self):
		return widgets.QVisaInstWidget.QVisaInstWidget(self)

	# Method to generate the standard save widget
	def _gen_save_widget(self):
		return widgets.QVisaSaveWidget.QVisaSaveWidget(self)


	#####################################
	#  LAYOUT SHORTCUTS
	#					

	# Helper methods to handle icons
	def _set_icon(self, _icon):
		
		self._icon = _icon

	def _get_icon(self):
		
		try:
			return self._icon
		except AttributeError:
			return QIcon()

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
