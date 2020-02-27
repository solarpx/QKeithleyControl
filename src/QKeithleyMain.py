# ---------------------------------------------------------------------------------
# 	QKeithleyControl -> QMainWindow
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
import threading 

# Import Keithley control widgets
from src.app.QKeithleyConfig import QKeithleyConfig
from src.app.QKeithleyBias import QKeithleyBias
from src.app.QKeithleySweep import QKeithleySweep 
from src.app.QKeithleySolar import QKeithleySolar

# Import QT backends
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QAction, QStackedWidget, QMessageBox, QMenu
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices

# Subclass QMainWindow to customise your application's main window
class QKeithleyMain(QMainWindow):

	def __init__(self, _application, *args, **kwargs):
		
		# Instantiate super
		super(QKeithleyMain, self).__init__(*args, **kwargs)

		# Application handle and window title	
		self.app = _application
		self.version = '1.2'
		self.setWindowTitle("QKeithleyControl (v%s)"%self.version)
		
		# Create Icon for QMainWindow and QMessageBox
		self.icon = QIcon(os.path.join(os.path.dirname(os.path.realpath(__file__)), "python.ico"))
		self.setWindowIcon(self.icon)

		# Generate main menu and toplevel widget. We will 
		# Render our controls into self.toplevel on menu selection
		self._gen_menu()		
		self.ui_stack = QStackedWidget(self)

		# Create QVisaWidget for configuration mode
		self.ui_config = QKeithleyConfig()
		
		# Create QVisaWidget for each measurement mode
		self.ui_bias   = QKeithleyBias(self.ui_config)
		self.ui_sweep  = QKeithleySweep(self.ui_config)
		self.ui_solar  = QKeithleySolar(self.ui_config)

		# Add ui-mode widgets to stack
		self.ui_stack.addWidget(self.ui_config)
		self.ui_stack.addWidget(self.ui_bias)
		self.ui_stack.addWidget(self.ui_sweep)
		self.ui_stack.addWidget(self.ui_solar)

		# Set window central widget to stacked widget
		self.setCentralWidget(self.ui_stack)

	# Callback to handle main menu actions. For each menu action, need 
	# to check to see if there are any application threads running 
	# other than main thread (i.e. if there are ongoing measurements). 
	def main_menu_callback(self, q):

		if q.text() == "Hardware Config" and self.ui_stack.currentIndex() != 0: 

			if len( threading.enumerate() ) > 1:
				self.thread_running_msg()
			else:
				self.ui_stack.setCurrentIndex(0)

		if q.text() == "IV-Bias Control" and self.ui_stack.currentIndex() != 1: 		
		
			if len( threading.enumerate() ) > 1:
				self.thread_running_msg()
			else:		
				self.ui_bias.refresh()
				self.ui_stack.setCurrentIndex(1)

		if q.text() == "IV-Sweep Control" and self.ui_stack.currentIndex() != 2:

			if len( threading.enumerate() ) > 1:
				self.thread_running_msg()
			else:					
				self.ui_sweep.refresh()
				self.ui_stack.setCurrentIndex(2)

		if q.text() == "PV-Tracking" and self.ui_stack.currentIndex() != 3:

			if len( threading.enumerate() ) > 1:
				self.thread_running_msg()
			else: 	
				self.ui_solar.refresh()
				self.ui_stack.setCurrentIndex(3)

		if q.text() == "Exit":

			if len( threading.enumerate() ) > 1:
				self.thread_running_msg()

			# Otherwise enter the close dialog
			else:	
				self.ui_config.close_devices()
				self.app.exit()	

	# Message box for thread running
	def thread_running_msg(self):

		# Dialogue to check quit
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setText("Measurement is running")
		msg.setWindowTitle("QKeithleyControl")
		msg.setWindowIcon(self.icon)
		msg.setStandardButtons(QMessageBox.Ok)
		msg.exec_()

	# Callback to handle help menu actions
	def help_menu_callback(self, q):

		if q.text() == "Documentation":
			QDesktopServices.openUrl( QUrl( "https://github.com/mesoic/QKeithleyControl") )
		
		if q.text() == "About":
		
			# Message box to display error
			msg = QMessageBox()
			msg.setWindowTitle("QKeithleyControl")
			msg.setWindowIcon(self.icon)
			msg.setText("<h2>QKeithleyControl</h2><p>Version 1.1 &copy;2019-2020 by github.com/mesoic</p><p>QKeithleyControl is open source software built on the PyQtVisa framework.</p>")
			msg.setStandardButtons(QMessageBox.Ok)
			msg.exec_()	

	# Callback to handle x-button closeEvent
	def closeEvent(self, q):

		# Check to see if there are any threads running 
		# other than main thread
		if len( threading.enumerate() ) > 1:

			# Dialogue to check quit
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Warning)
			msg.setText("Measurement is running")
			msg.setWindowTitle("QKeithleyControl")
			msg.setWindowIcon(self.icon)
			msg.setStandardButtons(QMessageBox.Ok)
			self.msg_quit = msg.exec_()

			q.ignore()

		# Otherwise enter the close dialog
		else:	

			# Dialogue to check quit
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Information)
			msg.setText("Are you sure you want to quit?")
			msg.setWindowTitle("QKeithleyControl")
			msg.setWindowIcon(self.icon)
			msg.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
			self.msg_quit = msg.exec_()

			if self.msg_quit == QMessageBox.Yes:

				# Clean up pyvisa device sessions
				self.ui_config.close_devices()		
				q.accept()

			else:
				q.ignore()
	
	# Generate Menu
	def _gen_menu(self):

		# Main Menu
		self.menu_bar = self.menuBar()
		
		# Add a selector menu items
		self.main_menu = self.menu_bar.addMenu('Select Measurement')

		# Add submenu for applications
		self.app_submenu = QMenu("Applications", parent=self.main_menu)

		# Bias Mode
		self.app_bias = QAction("IV-Bias Control",self)
		self.app_submenu.addAction(self.app_bias)

		# Sweep Mode
		self.app_sweep = QAction("IV-Sweep Control",self)
		self.app_submenu.addAction(self.app_sweep)

		# Solar Mode
		self.app_solar = QAction("PV-Tracking")
		self.app_submenu.addAction(self.app_solar)

		# Add app submenu to main menu
		self.main_menu.addMenu(self.app_submenu)

		# Add hardware configuration app 
		self.app_config = QAction("Hardware Config",self)
		self.main_menu.addAction(self.app_config)

		# Add exit app
		self.app_exit = QAction("Exit",self)
		self.main_menu.addAction(self.app_exit)

		# Add a selector menu items
		self.help_menu = self.menu_bar.addMenu('Help')

		self.app_docs = QAction("Documentation",self)
		self.help_menu.addAction(self.app_docs)

		self.app_about = QAction("About",self)
		self.help_menu.addAction(self.app_about)

		# Close button cleanup
		self.finish = QAction("Quit", self)
		self.finish.triggered.connect(self.closeEvent)

		# Callback Triggered
		self.main_menu.triggered[QAction].connect(self.main_menu_callback)
		self.help_menu.triggered[QAction].connect(self.help_menu_callback)


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
