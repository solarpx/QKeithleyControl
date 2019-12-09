# ---------------------------------------------------------------------------------
# 	QVisaDynamicPlot -> QWidget
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
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QLabel, QMessageBox,  QSizePolicy
from PyQt5.QtGui import QIcon

# Import matplotlibQT backends
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import FormatStrFormatter
import matplotlib.pyplot as plt


class QVisaDynamicPlot(QWidget):

	def __init__(self, _app):

		QWidget.__init__(self)

		# Dictionaries to add handles and configuration data
		self._handles = {}
		self._axes 	 = {}

		# Dictionary to hold plot adjust values
		self._adjust = {'l': 0.15, 'r': 0.90, 't': 0.90, 'b' : 0.10}

		# Generate main layout
		self._gen_main_layout()

		# Cache a reference to the calling application
		self._app = _app

	def _gen_main_layout(self):

		self._layout = QVBoxLayout()

		# Generate widgets
		self._gen_mpl_widgets()

		# HBoxLayout for toolbar and clear button
		self._layout_toolbar = QHBoxLayout()	
		self._layout_toolbar.addWidget(self.mpl_toolbar)
		self._layout_toolbar.addWidget(self.mpl_refresh)

		# HBoxLayout for plot object 
		self._layout_plot = QHBoxLayout()
		self._layout_plot.addWidget(self.mpl_canvas)
		
		# Add layouts
		self._layout.addLayout(self._layout_toolbar)
		self._layout.addLayout(self._layout_plot)

		# Set widget layout
		self.setLayout( self._layout )

	# Generate matplotlib widgets	
	def _gen_mpl_widgets(self):
	
		# Generate matplotlib figure and canvas
		self.mpl_figure  = plt.figure(figsize=(8,5))
		self.mpl_canvas  = FigureCanvas(self.mpl_figure)
		self.mpl_toolbar = NavigationToolbar(self.mpl_canvas, self)		

		# Refresh button
		self.mpl_refresh = QPushButton("Clear Data")
		self.mpl_refresh.clicked.connect(self.refresh_canvas)

	# Add axes object to widget 
	def add_subplot(self, _key=111):	
		self._axes[str(_key)] = self.mpl_figure.add_subplot(_key)

	# Add twin object for axes on key		 
	def twin_subplot(self, _key):
		self._axes[str(_key)+'t'] = self._axes[_key].twinx()

	# Add axes xlabels
	def set_axes_xlabel(self, _key, _xlabel):
		self._axes[str(_key)].set_xlabel( str(_xlabel) ) 

	# Add axes ylabels
	def set_axes_ylabel(self, _key, _ylabel):
		self._axes[str(_key)].set_ylabel( str(_ylabel) ) 

	# Convenience method to set axes labels
	def set_axes_labels(self, _xlabel, _ylabel, _key='111'):
		self.set_axes_xlabel(_key, _xlabel)
		self.set_axes_ylabel(_key, _ylabel)	

	# Set axes adjust 
	def set_axes_adjust(self, _left, _right, _top, _bottom):
		self._adjust = {'l': _left, 'r': _right, 't': _top, 'b' : _bottom}	

	# Add handle to axes
	def add_axes_handle(self, _key, _handle_key, _color=None):

		if _color is not None:
			h, = self._axes[str(_key)].plot([], [], color=_color)
		else:
			h, = self._axes[str(_key)].plot([], [])

		self._handles[_handle_key] = h

	# Method to get axes handles
	def get_axes_handles(self):
		return self._handles

	# Update axes handle
	def update_axes_handle(self, _handle_key, x_value, y_value):

		# Append new values to handle data
		_x = np.append(self._handles[_handle_key].get_xdata(), x_value)
		_y = np.append(self._handles[_handle_key].get_ydata(), y_value)

		# Set xdata and ydata to handle
		self._handles[_handle_key].set_xdata(_x)
		self._handles[_handle_key].set_ydata(_y)

	# Method to update canvas dynamically
	def update_canvas(self):

		# Loop through all figure axes and relimit
		for _key, _axes in self._axes.items():
			_axes.relim()
			_axes.autoscale_view()
			_axes.ticklabel_format(style='sci', scilimits=(0,0), axis='y', useOffset=False)

		# Adjust subplots	
		plt.subplots_adjust(
			left 	= self._adjust['l'], 
			right 	= self._adjust['r'], 
			top  	= self._adjust['t'],
			bottom	= self._adjust['b']
		)
	
		# Draw and flush_events
		self.mpl_canvas.draw()
		self.mpl_canvas.flush_events()

	# Refresh canvas. Note callback will expose args as False
	def refresh_canvas(self, supress_warning=False):
		
		# Only ask to redraw if there is data present
		if (self._handles != {}) and (supress_warning == False):

			msg = QMessageBox()
			msg.setIcon(QMessageBox.Information)
			msg.setText("Clear all measurement data?")
			msg.setWindowTitle("QDynamicPlot")
			msg.setWindowIcon(self._app._get_icon())
			msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			self.msg_clear = msg.exec_()

			if self.msg_clear == QMessageBox.Yes:
				self._refresh_canvas()		
	
		else:
			self._refresh_canvas()		

	# Internal method to clear axes		
	def _refresh_canvas(self):

		# Clear the axes 
		for _key, _axes in self._axes.items():

			# Pull labels
			_xlabel = _axes.get_xlabel()
			_ylabel = _axes.get_ylabel()
			
			# clear axes and reset labels
			_axes.clear()
			_axes.set_xlabel(_xlabel)
			_axes.set_ylabel(_ylabel)

		# Clear all handles
		self._handles = {}

		# Update canvas
		self.update_canvas()
