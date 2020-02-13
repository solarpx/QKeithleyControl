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
		data_path = "../dat/Si/si-ref-sweep.dat"

		# Path to dump extracted measurement parameters
		extract_path = "../dat/Si/si-ref-extract.dat"

	if ref_cell == "GaAs":
	
		# Path to reference data file
		data_path = "../dat/GaAs/gaas-ref-sweep.dat"

		# Path to dump extracted measurement parameters
		extract_path = "../dat/GaAs/gaas-ref-extract.dat"

	# Build data object
	data = QVisaDataObject.QVisaDataObject()
	data.read_from_file( data_path )

	# Set up mpl figure
	fig = plt.figure()
	ax0 = fig.add_subplot(111)
	ax1 = ax0.twinx()

	# List of measurements to exclude from plotting
	exclude = ["AM9.0", "AM10.0", "DARK"]

	# Extract data
	for _key in data.keys():

		# Exclude certain keys
		if data.get_metadata(_key, "__desc__") not in exclude:

			# Extract time
			time = data.get_subkey_data(_key, "t")
			
			# Extract voltage and current
			voltage = data.get_subkey_data(_key, "V")
			current = data.get_subkey_data(_key, "I")

			# Plot the AM1.5G spectrum solid
			if data.get_metadata(_key, "__desc__") == "AM1.5G":

				ax0.plot(
					voltage, 
					(-1000. / ref_cell_area) * np.array(current), 
					color="tab:blue" 
				)

				ax1.plot(
					voltage, 
					(-1000. ) * np.array(current) * voltage, 
					color="tab:orange"
				)

				# Approximate Voc and Jsc from measurement data
				idx = np.argmax( np.array(current) > 0.0)
				Voc = ( voltage[ idx ] + voltage[ idx - 1 ] ) / 2.0
				Jsc = ( current[ 0 ] ) * ( -1000. / ref_cell_area )

				# Find max power
				P   = np.array(voltage) * np.array(current) * (-1000 )
				idx = np.where(P == np.amax(P))[0][0]
				Vm 	= voltage[idx]
				Jm  = current[idx] * ( -1000. / ref_cell_area )
				
				# Use pandas to create a dataframe
				ref_data = {
					"Voc"  : Voc,	
					"Isc"  : current[ 0 ] * ( -1000.),
					"Jsc"  : Jsc,
					"Vm"   : Vm,
					"Im"   : current[idx] * ( -1000.),
					"Jm"   : Jm,
					"FF"   : (Vm * Jm) / (Voc * Jsc),
					"ETA"  : Vm * Jm
				}

				# Print ref_data into file
				with open( extract_path, "w" ) as f:

					f.write( "#! %s Reference: Extract\n\n"%(ref_cell) )

					for key, val in ref_data.items():

						f.write("%s\t\t %s\n"%(key, val) )

				f.close()

			else: 
			
				ax0.plot(
					voltage, 
					(-1000. / ref_cell_area) * np.array(current), 
					color="tab:blue", linestyle=":", linewidth=0.5 )
				
				ax1.plot(
					voltage, 
					(-1000 ) * np.array(current) * voltage, 
					color="tab:orange", linestyle=":", linewidth=0.5 )

	
	# Clean up the plot limits
	ax0.set_xlim(min(voltage), max(voltage))
	
	# Si Reference
	if ref_cell == "Si": 
		
		ax0.set_title("Si Reference : $AM[0.0\\ldots 8.0]$ : $T = 25^{\\circ}C$")
		ax0.set_ylim(0.0, 40)
		ax1.set_ylim(0.0, 60)

	# GaAs Reference
	if ref_cell == "GaAs":

		ax0.set_title("GaAs Reference : $AM[0.0\\ldots 8.0]$ : $T = 25^{\\circ}C$")
		ax0.set_ylim(0.0, 35)
		ax1.set_ylim(0.0, 110)

	# Set plot lables
	ax0.set_xlabel("Voltage $(V)$")
	ax0.set_ylabel("Current Density $(mA/cm^2)$")
	ax1.set_ylabel("Output Power $(mW)$")

	# Show the plot
	fig.tight_layout()
	plt.show()
