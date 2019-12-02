# ---------------------------------------------------------------------------------
# 	QDynamicPlot.py
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

# Import QT backends
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel
from PyQt5.QtCore import Qt

# Import matplotlibQT backends
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import FormatStrFormatter
import matplotlib.pyplot as plt

class QDynamicPlot(QWidget):

	# Note that from the main app, we must pass the pointer of the app 
	# instance to dynamic plotdynamic_plot.dynamic_plot(self)
	def __init__(self, _app_instance):

		# Inherits QWidget
		QWidget.__init__(self)

		self.layout = QVBoxLayout()

		# Create a figure object
		self.figure = plt.figure(figsize=(8,5))
		
		# this is the Canvas Widget that displays the `figure`
		# it takes the `figure` instance as a parameter to __init__
		self.canvas = FigureCanvas(self.figure)

		# this is the Navigation widget
		# it takes the Canvas widget and a parent
		self.controls = QHBoxLayout()
		self.toolbar = NavigationToolbar(self.canvas, _app_instance)

		self.refresh = QPushButton("Clear Axes")
		self.refresh.clicked.connect(self.refresh_axes)

		# Add the controls
		self.controls.addWidget(self.toolbar)
		self.controls.addWidget(self.refresh)
		
		# Add widgets to container
		self.layout.addWidget(self.canvas)
		self.layout.addLayout(self.controls)


		# Variables for axes labels
		self.xlabel = None
		self.ylabel = None

		# List of handles of plot into 
		self.hlist=[]

	# Add and refresh axes
	def refresh_axes(self):
		self.figure.clear()
		self.hlist=[]

		# Add axes and set axes labels
		self.ax = self.figure.add_subplot(111)	
		if self.xlabel is not None:
			self.ax.set_xlabel(self.xlabel)

		if self.ylabel is not None:
			self.ax.set_ylabel(self.ylabel)

		plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0), useOffset=False)
		plt.subplots_adjust(left=0.15, right=0.9, top=0.9, bottom=0.1)
		self.figure.canvas.draw()
		self.figure.canvas.flush_events()

	# Add axes object to widget and draw figure
	def add_axes(self):	

		self.ax = self.figure.add_subplot(111)
		if self.xlabel is not None:
			self.ax.set_xlabel(self.xlabel)

		if self.ylabel is not None:
			self.ax.set_ylabel(self.ylabel)

		plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0), useOffset=False)
		plt.subplots_adjust(left=0.15, right=0.9, top=0.9, bottom=0.1)
		self.figure.canvas.draw()
		self.figure.canvas.flush_events()

	# Add axes labels
	def set_axes_labels(self, _xlabel, _ylabel):
		self.xlabel = str(_xlabel)
		self.ylabel = str(_ylabel)

	# Add trace
	def add_handle(self):
		h, = self.ax.plot([], [])
		self.hlist.append(h)
		return h

	def update_handle(self, h, x_value, y_value):

		h.set_xdata(np.append(h.get_xdata(), x_value))
		h.set_ydata(np.append(h.get_ydata(), y_value))
		self.ax.relim()
		self.ax.autoscale_view()
		
		plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0), useOffset=False)
		plt.subplots_adjust(left=0.15, right=0.9, top=0.9, bottom=0.1)
		self.figure.canvas.draw()
		self.figure.canvas.flush_events()

