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
import numpy as np

# Import d_plot and keithley driver
import drivers.keithley2400

# Import Keithley control widgets
import app.QKeithleyConfig
#import modules.QKeithleySweep 
#import modules.QKeithleyBias
#import modules.QKeithleySolar

# Import QT backends
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QAction, QStackedWidget, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# Import matplotlibQT backends
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

# Subclass QMainWindow to customise your application's main window
class QKeithleyControl(QMainWindow):

	def __init__(self, _application, *args, **kwargs):
		
		# Instantiate super
		super(QKeithleyControl, self).__init__(*args, **kwargs)

		# Application handle and window title	
		self.app = _application
		self.version = '1.1'
		self.setWindowTitle("QKeithleyControl (v%s)"%self.version)
		
		# Create Icon for QMainWindow and QMessageBox
		self.icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico"))
		self.setWindowIcon(self.icon)

		# Generate main menu and toplevel widget. We will 
		# Render our controls into self.toplevel on menu selection
		self._gen_menu()		
		self.ui_stack = QStackedWidget(self)

		# Create QVisaWidget for configuration mode
		self.ui_config = app.QKeithleyConfig.QKeithleyConfig()
		
		# Create QVisaWidget for each measurement mode
		#self.ui_bias   = modules.QKeithleyBias.QKeithleyBias(self.ui_config)
		#self.ui_sweep  = modules.QKeithleySweep.QKeithleySweep(self.ui_config)
		#self.ui_solar  = app.QKeithleySolar.QKeithleySolar(self.ui_config)

		# Add ui-mode widgets to stack
		self.ui_stack.addWidget(self.ui_config)
		#self.ui_stack.addWidget(self.ui_bias)
		#self.ui_stack.addWidget(self.ui_sweep)
		#self.ui_stack.addWidget(self.ui_solar)

		# Set window central widget to stacked widget
		self.setCentralWidget(self.ui_stack)

		# Create empty keithley object
		self.keithley = None

	# Callback to update menu
	def _menu_callback(self, q):		

		if q.text() == "Hardware Config" and self.ui_stack.currentIndex() != 0: 
			self.ui_stack.setCurrentIndex(0)

		# if q.text() == "IV-Bias Control" and self.ui_stack.currentIndex() != 1: 		

		# 	# Get Keithley handle
		# 	self.keithley=self.ui_config._get_keithley_handle()

		# 	# If Keitheley handle is initialized, pass to bias widget. 
		# 	if self.keithley is not None:
		# 		self.keithley.reset()
		# 		self.ui_bias._set_keithley_handle(self.keithley)
		# 		self.ui_bias._reset_defaults()
		# 		self.ui_stack.setCurrentIndex(1)

		# 	# Otherwise, display Keithley not initilized message
		# 	else:
		# 		self._gen_warning_box("pyVISA Error","Keitheley GPIB not Initialized")		
		# 		self.ui_stack.setCurrentIndex(0)

		# if q.text() == "IV-Sweep Control" and self.ui_stack.currentIndex() != 2:
			
		# 	# Get Keithley handle
		# 	self.keithley=self.ui_config._get_keithley_handle()

		# 	# If Keitheley handle is initialized, pass to sweep widget. 
		# 	if self.keithley is not None:
		# 		self.keithley.reset()
		# 		self.ui_sweep._set_keithley_handle(self.keithley)
		# 		self.ui_sweep._reset_defaults()
		# 		self.ui_stack.setCurrentIndex(2)

		# 	# Otherwise, display Keithley not initilized message
		# 	else:				
		# 		self._gen_warning_box("pyVISA Error","Keitheley GPIB not Initialized")		
		# 		self.ui_stack.setCurrentIndex(0)		


		# if q.text() == "PV-Characterization" and self.ui_stack.currentIndex() != 3:

		# 	# Get Keithley handle
		# 	self.keithley=self.ui_config._get_keithley_handle()

		# 	# If Keitheley handle is initialized, pass to sweep widget. 
		# 	if self.keithley is not None:
		# 		self.keithley.reset()
		# 		self.ui_solar._set_keithley_handle(self.keithley, 24)
		# 		self.ui_solar._reset_defaults()
		# 		self.ui_stack.setCurrentIndex(3)

		# 	# Otherwise, display Keithley not initilized message
		# 	else:				
		# 		self._gen_warning_box("pyVISA Error","Keitheley GPIB not Initialized")		
		# 		self.ui_stack.setCurrentIndex(0)		


		if q.text() == "Exit": 
			self.app.exit()		

	# Generate Menu
	def _gen_menu(self):

		# Main Menu
		self.menu_bar = self.menuBar()
		
		# Add a selector menu items
		self.menu_selector = self.menu_bar.addMenu('Select Measurement')

		# Add some various modes. These will generate windows in main layout
		self.menu_config = QAction("Hardware Config",self)
		self.menu_selector.addAction(self.menu_config)

		# # Bias Mode
		# self.menu_bias = QAction("IV-Bias Control",self)
		# self.menu_selector.addAction(self.menu_bias)

		# # Sweep Mode
		# self.menu_sweep = QAction("IV-Sweep Control",self)
		# self.menu_selector.addAction(self.menu_sweep)

		# # Solar Mode
		# self.menu_solar = QAction("PV-Characterization")
		# self.menu_selector.addAction(self.menu_solar)

		# Exit Application
		self.menu_exit = QAction("Exit",self)
		self.menu_selector.addAction(self.menu_exit)

		# Callback Trigge
		self.menu_selector.triggered[QAction].connect(self._menu_callback)

	# Method to generate warning box
	def _gen_warning_box(self, _title, _text): 
					
		# Message box to display error
		msg = QMessageBox()
		msg.setWindowTitle(_title)
		msg.setWindowIcon(self.icon)
		msg.setIcon(QMessageBox.Warning)
		msg.setText(_text)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()	