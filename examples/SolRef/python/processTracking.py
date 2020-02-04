#!/usr/bin/env python 
import os
import numpy as np

# Import QVisaDataObject
from PyQtVisa.utils import QVisaDataObject

# Import matplotlib
import matplotlib.pyplot as plt

# Routine to plot reference cell data and extract cell parameters
if __name__ == "__main__":

	# Define refence cell
	ref_cell, ref_cell_area = "Si", 4.0

	if ref_cell == "Si":

		# Path to reference data file
		data_path = "../data/Si/si-ref-tracking.dat"


	if ref_cell == "GaAs":
	
		# Path to reference data file
		data_path = "../data/GaAs/gaas-ref-tracking.dat"


	# Build data object
	data = QVisaDataObject.QVisaDataObject()
	data.read_from_file( data_path )

	# Extract data
	for _key in data.keys():

		# Voc tracking curves
		if data.get_metadata(_key, "__type__") == "pv-voc":

			# Set up mpl figure
			fig = plt.figure()
			ax0 = fig.add_subplot(111)
			ax1 = ax0.twinx()

			# Extract time
			time = data.get_subkey_data(_key, "t")
			
			# Extract voltage and current
			voltage = data.get_subkey_data(_key, "Voc")
			current = data.get_subkey_data(_key, "Ioc")

			# Plot Voc Data
			ax0.plot( time, voltage, "tab:blue")
			ax1.plot( time, (1000. / ref_cell_area) * np.array(current), "tab:orange" )

			# Axes lables
			ax0.set_xlabel("Time $(s)$")
			ax0.set_ylabel("$V_{oc}$ $(V)$")
			ax1.set_ylabel("$J_{sc}$ $(mA/cm^2)$")

			# Axes title
			ax0.set_title("%s Reference : $V_{oc}$ Tracking : $AM1.5G$ : $T = 25^{\\circ}C$"%(ref_cell))

		# Vmpp tracking curves
		if data.get_metadata(_key, "__type__") == "pv-mpp":

			# Set up mpl figure
			fig = plt.figure()
			ax0 = fig.add_subplot(111)
			ax1 = ax0.twinx()

			# Extract time
			time = data.get_subkey_data(_key, "t")
			
			# Extract voltage and current
			voltage = data.get_subkey_data(_key, "Vmpp")
			power 	= data.get_subkey_data(_key, "Pmpp")

			# Plot Voc Data
			ax0.plot( time, voltage, "tab:blue")
			ax1.plot( time, 1000. * np.array(power), "tab:orange" )

			# Axes lables
			ax0.set_xlabel("Time $(s)$")
			ax0.set_ylabel("$V_{mpp}$ $(V)$")
			ax1.set_ylabel("$P_{mpp}$ $(mW)$")
	
			# Axes title
			ax0.set_title("%s Reference : MPP Tracking : $AM1.5G$ : $T = 25^{\\circ}C$"%(ref_cell))


	plt.show()