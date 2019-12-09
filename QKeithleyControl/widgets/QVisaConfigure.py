# ---------------------------------------------------------------------------------
# 	QKeithleyConnfigure -> QWidget
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
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox 

# The purpouse of this object is to bind a list pyVisaDevices to a QWidget 
# in a configuration context. The idea is to first construct a QVisaConifg
# object which contains the list of insturment handles, and then pass the 
# object to QVisaWidget objects which can interact with the insturments
#

class QVisaConfigure(QWidget):

	# Initialization
	def __init__(self, *args, **kwargs):

		QWidget.__init__(self)
		self._inst = []

	# Add an insturment handle. 
	# _inst is a pyVisaDevice object with 
	# 	1) pyVisaDevice.inst (inst handle)
	# 	2) pyVisaDevice.addr (gpib address)
	# 	3) pyVisaDevice.name (inst name)
	#
	def _add_inst_handle(self, _inst):
		self._inst.append(_inst)

	# Get all insturment handles	
	def _get_inst_handles(self):
	
		if self._inst != []:
			return self._inst
		else:
			return None 
			
	# Get all insturment names
	def _get_inst_names(self):

		if self._inst != []:
			return [_.name for _ in self._inst]	
		else:	
			return None

	# Get handle by addrress
	def _get_inst_byaddr(self, _addr):

		# Loop through insturment list
		for _ in self._inst:
			if _.addr == _addr:
				return _ 

		# If we do not find device return None		
		return None

	# Get handle by name
	def _get_inst_byname(self, _name):

		# Loop through insturment list
		for _ in self._inst:
			if _.name == _name:
				return _ 

		# If we do not find device return None		
		return None

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
	def _gen_hbox_widget(self, _widget_list):
	
		_widget = QWidget()
		_layout = QVBoxLayout()
		for _w in _widget_list:
			_layout.addWidget(_w)

		_layout.setContentsMargins(0,0,0,0)
		_widget.setLayout(_layout)
		return _widget
