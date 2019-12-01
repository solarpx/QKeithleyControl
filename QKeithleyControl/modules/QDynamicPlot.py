import numpy as np

# Import QT backends
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, QCheckBox, QLabel
from PyQt5.QtCore import Qt

# Import matplotlibQT backends
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

class QDynamicPlot:

	# Note that from the main app, we must pass the pointer of the app 
	# instance to dynamic plotdynamic_plot.dynamic_plot(self)
	def __init__(self, _app_instance):

		self.layout = QVBoxLayout()

		# Create a figure object
		self.figure = plt.figure()

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


		self.figure.canvas.draw()
		self.figure.canvas.flush_events()

	def add_axes(self):	
		# Add axes object to widget and draw figure
		self.ax = self.figure.add_subplot(111)
		if self.xlabel is not None:
			self.ax.set_xlabel(self.xlabel)

		if self.ylabel is not None:
			self.ax.set_ylabel(self.ylabel)

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
	
		self.figure.canvas.draw()
		self.figure.canvas.flush_events()

