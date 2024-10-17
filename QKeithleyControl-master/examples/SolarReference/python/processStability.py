#!/usr/bin/env python 
import os
import numpy as np

# Import QVisaDataObject
from PyQtVisa.utils import QVisaDataObject

# Import matplotlib
import matplotlib.pyplot as plt

if __name__ == "__main__":

	# Path to data files
	paths = [
		"../dat/Si/si-ref-stability.dat", 
		"../dat/GaAs/gaas-ref-stability.dat"
	]

	# Set up mpl figure
	fig = plt.figure()
	ax0 = fig.add_subplot(111)

	# Plot handle list
	hx 	= []
	
	# Loop through paths
	for path in paths: 

		# Build data object
		data = QVisaDataObject.QVisaDataObject()
		data.read_from_file( path )

		# Extract data
		for _key in data.keys():

			# Extract time
			time = data.get_subkey_data(_key, "t")
			
			# Extract voltage and current
			voltage = data.get_subkey_data(_key, "V")
			current = data.get_subkey_data(_key, "I")

			# Plot the data
			h, = ax0.plot(time, (1000. / 4.) * abs( np.array(current) ) )
			hx.append(h)

	# Add axes lables and show plot
	ax0.set_title("AM1.5G Spectrum Stabilization")
	ax0.set_xlabel("Time $(s)$")
	ax0.set_ylabel("$J_{sc}$ $(mA/cm^2)$")
	ax0.legend( hx, ["Reference: Si ($25^{\\circ}C$)", "Reference: GaAs ($25^{\\circ}C$)"] )

	# Show plot
	plt.show()