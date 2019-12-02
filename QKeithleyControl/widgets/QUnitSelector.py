# -----------------------------------------------------------------------
# 	QUnitSelector.py
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
import numpy as np
import collections

# Import QT backends
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QDoubleSpinBox, QLabel,QSizePolicy
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

		# This if is needed so clear() in update does not trigget this method
		if self.unit.currentText() != "":

			_limit = float(self.config["limit"]) / float( self._units[self.unit.currentText()] ) 

			# Set minimum takeing into account signed/unsigned input
			if self.config["signed"] == True:
				self.unit_value.setMinimum( max( -1.0  * _limit, -1000) ) 
			else: 
				self.unit_value.setMinimum(0.0)

			# Set minimum takeing into account signed/unsigned input
			self.unit_value.setMaximum( min(  1.0  * _limit,  1000) ) 
	
	# Generate unit selector
	def _gen_unit_selector(self):

		# Unit selection box
		self.unit_layout = QHBoxLayout()
		self.unit_layout.setContentsMargins(0,0,0,0)

		# Unit selection combobox
		self.unit = QComboBox()
		self.unit.addItems( list(self._units.keys()) )
		self.unit.currentTextChanged.connect(self._update_unit_limits)

		# Level Spinbox
		self.unit_value = QDoubleSpinBox()
		self.unit_value.setDecimals(3)
		self.unit_value.setSingleStep(0.001)
		self._update_unit_limits()
		self.unit_value.setValue(self.config["default"])

		# Size the spinbox
		self.unit_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding);
		self.unit_value.setMinimumSize(QSize(200, 10))

		# Add widgets to hbox
		self.unit_label=QLabel(self.config["label"]) # Pack this last
		self.unit_layout.addWidget(self.unit_value)
		self.unit_layout.addWidget(self.unit)

		# Main layout for Widget
		self.main_layout = QVBoxLayout()
		self.main_layout.addWidget(self.unit_label)
		self.main_layout.addLayout(self.unit_layout)

		# Resize margins of main layout
		self.main_layout.setContentsMargins(0,0,0,0)
		return self.main_layout

	# Method to re-render widget with new configuration
	def update_config(self, _config):
		
		# Update configuration and generate units
		self.config = _config
		self._gen_unit_range()

		# Clear combobox and add new unit values
		self.unit.clear()
		self.unit.addItems( list(self._units.keys()) )

		# Call _update_unit_limits for new limits 
		# (it should be called on add_items)
		self._update_unit_limits()

		# Update default value
		self.unit_value.setValue(self.config["default"])
		
		# Set label text
		self.unit_label.setText(self.config["label"])

	# Wrapper for value method
	def value(self):
		return float( self._units[ self.unit.currentText() ] * self.unit_value.value() )