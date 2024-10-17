#!/usr/bin/env python 
import os
import numpy as np

# Import QVisaDataObject
from PyQtVisa.utils import QVisaDataObject

# Import matplotlib
import matplotlib.pyplot as plt

if __name__ == "__main__":

	# Path to data files
	path = "../dat/iv-sweep.dat"

	# Read data object
	data = QVisaDataObject.QVisaDataObject()
	data.read_from_file( path )

	# Set up mpl figure
	fig = plt.figure()
	ax0 = fig.add_subplot(111)

	# Extract time
	for _key in data.keys():
				
		# Extract voltage and current
		voltage = data.get_subkey_data(_key, "V")
		current = data.get_subkey_data(_key, "I")

		# Plot data 
		ax0.semilogy( voltage, [ np.abs(_) for _ in current ] )

	# Add axes lables and show plot
	ax0.set_title("Diode Resistor Circuit : IV Charachteristics")
	ax0.set_xlabel("Voltage $(V)$")
	ax0.set_ylabel("Current $(A)$")

	# Show plot
	plt.tight_layout()
	plt.show()
