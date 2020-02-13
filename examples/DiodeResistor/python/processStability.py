#!/usr/bin/env python 
import os
import numpy as np

# Import QVisaDataObject
from PyQtVisa.utils import QVisaDataObject

# Import matplotlib
import matplotlib.pyplot as plt

if __name__ == "__main__":


	# Path to data files
	path = "../dat/stability.dat"

	# Read data object
	data = QVisaDataObject.QVisaDataObject()
	data.read_from_file( path )

	# Set up mpl figure
	fig = plt.figure()
	ax0 = fig.add_subplot(111)

	# Extract time
	for _key in data.keys():

		time = data.get_subkey_data(_key, "t")
				
		# Extract voltage and current
		voltage = data.get_subkey_data(_key, "V")
		current = data.get_subkey_data(_key, "I")

		# Plot data 
		ax0.plot( time, voltage )

	# Add axes lables and show plot
	ax0.set_title("Diode Resistor Circuit Stability : Current Bias = 1mA")
	ax0.set_xlabel("Time $(s)$")
	ax0.set_ylabel("Voltage $(V)$")

	# Show plot
	plt.tight_layout()
	plt.show()
