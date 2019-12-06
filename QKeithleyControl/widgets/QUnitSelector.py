# ---------------------------------------------------------------------------------
# 	QUnitSelector.py
# 	Copyright (C) 2019 mwchalmers
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
import numpy as np
import collections

# Import QT backends
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox, QDoubleSpinBox, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QSize

# Unit selector widget
class QUnitSelector(QWidget):

	def __init__(self, config):

		# Inherits QWidget
		QWidget.__init__(self)
		self._base = collections.OrderedDict({"G" : 1e9, "M" : 1e6, "k" : 1e3, "": 1, "m" : 1e-3, "u" : 1e-6, "n" : 1e-9 })
			 
		# QUnitSelector configuration dictionary example
		# {
		#		"unit" 		: "V",
		#		"min"		: "u",
		#		"max"		: "",
		#		"label"		: "Bias Level",
		#		"limit"		: 20.0,
		#		"signed"	: True,
		#		"default"	: 0.0
		# } 
		self.config = config
	
		# If not generating a unitless value _gen_unit_range
		if self.config['unit'] not in ['__INT__', '__DOUBLE__']:
			self._gen_unit_range()
		
		# Generate the widget
		self.setLayout(self._gen_unit_selector())

	# Generate unit range based on user input
	def _gen_unit_range(self): 
	
		# Initialise 
		self._units, _append = {}, False

		# Loop through orderedDict (decending magnitude)
		for _k,_v in list(self._base.items()):
	
			if _k == self.config["max"]: 
				_append = True

			if _k == self.config["min"]:
				self._units[ str(_k) + str( self.config["unit"]) ] = _v
				break	

			if _append:
				self._units[ str(_k) + str( self.config["unit"]) ] = _v


	# Function to update spinbox range on unit maximum
	def _update_unit_limits(self):

		# If we are working with physical units
		if self.unit_select is not None:
	
			# This if is needed so clear() in update does not trigger this method
			if self.unit_select.currentText() != "":

				_limit = float(self.config["limit"]) / float( self._units[self.unit_select.currentText()] ) 

				# Set minimum takeing into account signed/unsigned input
				if self.config["signed"] == True:
					self.unit_value.setMinimum( max( -1.0  * _limit, -1000) ) 
				else: 
					self.unit_value.setMinimum( 0.0 )

				# Set minimum takeing into account signed/unsigned input
				self.unit_value.setMaximum( min(  1.0  * _limit,  1000) ) 
	

		# Otherwise ints or doubles		
		else:

			if self.config['unit'] == "__DOUBLE__":

				self.unit_value.setMaximum( self.config["limit"] )
				
				if self.config["signed"] == True:
					self.unit_value.setMinimum( self.config["limit"] ) 
				else: 
					self.unit_value.setMinimum( 0.0 )

			if self.config['unit'] == "__INT__":

				self.unit_value.setMaximum( int( self.config["limit"] ) )
				
				if self.config["signed"] == True:
					self.unit_value.setMinimum( int( self.config["limit"] ) )
				else: 
					self.unit_value.setMinimum( 0 )

	# Generate unit selector
	def _gen_unit_selector(self):

		# Unit selection box
		self.unit_layout = QHBoxLayout()
		self.unit_layout.setContentsMargins(0,0,0,0)

		# Generate unit box (double value)
		if self.config['unit'] == "__DOUBLE__":

			# Unit select first (see below)
			self.unit_select = None

			# Unit value Spinbox
			self.unit_value = QDoubleSpinBox()
			self.unit_value.setDecimals(3)		
			self.unit_value.setSingleStep(0.1)	
			self._update_unit_limits()
			self.unit_value.setValue(self.config["default"][0])
			self.unit_value.setFixedWidth(200)


		# Generate unit box (int value)		
		elif self.config['unit'] == "__INT__":

			# Unit select first (see below)
			self.unit_select = None

			# Unit value Spinbox
			self.unit_value = QSpinBox()
			self.unit_value.setFixedWidth(200)
			self.unit_value.setValue(int(self.config["default"][0]))

		# General case (physical units)
		else: 

			# Unit selection combobox: needs to be first so self.unit_select 
			# exists on _update_unit_limits call
			self.unit_select = QComboBox()
			self.unit_select.setFixedWidth(80)
			self.unit_select.addItems( list(self._units.keys()) )
			self.unit_select.setCurrentText(self.config["default"][1] + self.config["unit"])
			self.unit_select.currentTextChanged.connect(self._update_unit_limits)

			# Unit value Spinbox
			self.unit_value = QDoubleSpinBox()
			self.unit_value.setDecimals(3)		
			self.unit_value.setSingleStep(0.1)	
			self._update_unit_limits()
			self.unit_value.setValue(self.config["default"][0])
			self.unit_value.setFixedWidth(200)			
	
		# Add widgets to hbox
		self.unit_label=QLabel(self.config["label"]) # Pack this last

		# Pack units			
		self.unit_layout.addWidget(self.unit_value)
		if self.unit_select is not None:
			self.unit_layout.addWidget(self.unit_select)
		self.unit_layout.addWidget(self.unit_label)
		self.unit_layout.setContentsMargins(0,0,0,0)

		# Return layout
		return self.unit_layout

	# Method to re-render widget with new configuration
	def update_config(self, _config):
		
		# Update configuration and generate units
		self.config = _config
		self._gen_unit_range()

		# Clear combobox and add new unit values
		if self.unit_select is not None:
			self.unit_select.clear()
			self.unit_select.addItems( list(self._units.keys()) )

		# Call _update_unit_limits for new limits 
		# (it should be called on add_items)
		self._update_unit_limits()

		# Update default value
		self.unit_value.setValue(self.config["default"][0])
		if self.config["default"] == 2:
			self.unit_select.setCurrentText(self.config["default"][1] + self.config["unit"])

		
		# Set label text
		self.unit_label.setText(self.config["label"])

	# Wrapper for value method
	def value(self):
		
		if self.unit_select is not None: 
			return float( self._units[ self.unit_select.currentText() ] * self.unit_value.value() )
		
		else:
			return self.unit_value.value()