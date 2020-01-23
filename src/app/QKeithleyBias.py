# ---------------------------------------------------------------------------------
# 	QKeithleyBias -> QVisaApplication
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
import os

# Import QVisaApplication
from PyQtVisa import QVisaApplication

# Import QKeithleyWidget
from src.widgets.QKeithleyBiasWidget import QKeithleyBiasWidget

# Import QT backends
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel
from PyQt5.QtGui import QIcon


# Container class to construct bias measurement widget
class QKeithleyBias(QVisaApplication.QVisaApplication):

	def __init__(self, _config):

		# Inherits QVisaApplication -> QWidget
		super(QKeithleyBias, self).__init__(_config)

		# Generate Main Layout
		self.gen_main_layout()

	# Method to refresh the widget
	def refresh(self):
	
		# If add insturments have been initialized
		if self.get_devices() is not None:

			# Get all available insturment names
			for _name in self.get_device_names():

				# Check if name has already been registered to inst widget
				if self.device_select.isRegistered(_name) == False:

					# If not rgister it and add output widget to stack
					self.device_select.registerInst(_name)

					# Generate bias widget
					self.bias_widgets[_name] = QKeithleyBiasWidget(self, _name) 

					# Add widgets to layout
					self.outputs.addWidget(self.bias_widgets[_name].get_output_widget())
					self.ctrls.addWidget(self.bias_widgets[_name].get_ctrl_widget())
					self.plots.addWidget(self.bias_widgets[_name].get_plot_widget())

					# Force update bias pages
					self.update_bias_pages()
	
	# Update all widgets	
	def update_bias_pages(self):

		# Get current name
		_name = self.device_select.currentText()

		# Check if name has been added to bias widgets
		if _name in self.bias_widgets.keys():

			# Call set current widget method
			self.outputs.setCurrentWidget(self.bias_widgets[_name].get_output_widget())
			self.ctrls.setCurrentWidget(self.bias_widgets[_name].get_ctrl_widget())
			self.plots.setCurrentWidget(self.bias_widgets[_name].get_plot_widget())						

	# Sync meta widget to data object
	def _sync_meta_widget_to_data_object(self):

		# Application keys
		_data_keys = self._get_data_object().keys()
		_widget_keys = self.meta_widget.get_meta_keys()

		# Check if widget keys are not in data keys
		for _key in _widget_keys:
			
			# If not then delete the key from meta_widget
			if _key not in _data_keys:

				self.meta_widget.del_meta_key(_key)

	# Main Layout
	def gen_main_layout(self):	

		# Create Icon for QMessageBox
		self._set_icon( QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico")))

		# Dictionary to hold QKeithleyBiasWidgets
		self.bias_widgets = {}
		
		# Create layout objects and set layout
		self.layout = QHBoxLayout()

		#####################################
		#  CONTROLS LAYOUT
		#

		self.meas_layout = QVBoxLayout()

		# Create dummy widgets for visaul symmetry
		self.bias_widgets["__none__"] = QKeithleyBiasWidget(self, "__none__") 

		# Bias output buttons
		self.outputs  = QStackedWidget()
		self.outputs.addWidget(self.bias_widgets["__none__"].get_output_widget())

		# Insturement selector
		self.device_select_label  = QLabel("Select Output")
		self.device_select = self._gen_device_select()
		self.device_select.setFixedWidth(200)
		self.device_select.set_callback("update_bias_pages")

		# Controls for source
		self.ctrls = QStackedWidget()
		self.ctrls.addWidget(self.bias_widgets["__none__"].get_ctrl_widget())

		# Meta widget for trace description
		self.meta_widget_label = QLabel("<b>Trace Description</b>")
		self.meta_widget = self._gen_meta_widget()
		self.meta_widget.set_meta_subkey("__desc__")

		# Save widget
		self.save_widget = self._gen_save_widget()

		# Pack widgets
		self.meas_layout.addWidget(self.outputs)
		self.meas_layout.addWidget(self._gen_hbox_widget([self.device_select, self.device_select_label])) 
		self.meas_layout.addWidget(self.ctrls)
		self.meas_layout.addStretch(1)
		self.meas_layout.addWidget(self.meta_widget_label)
		self.meas_layout.addWidget(self.meta_widget)
		self.meas_layout.addWidget(self.save_widget)

		#####################################
		#  PLOT LAYOUT
		#

		# Plotting
		self.plot_layout = QVBoxLayout()
		self.plots = QStackedWidget()
		self.plots.addWidget(self.bias_widgets["__none__"].get_plot_widget())
		self.plot_layout.addWidget(self.plots)

		# Add layouts to main layout and set layout
		self.layout.addLayout(self.meas_layout, 1)
		self.layout.addLayout(self.plot_layout, 3)
		self.setLayout(self.layout)
