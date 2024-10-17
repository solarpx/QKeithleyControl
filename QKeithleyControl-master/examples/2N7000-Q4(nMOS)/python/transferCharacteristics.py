#!/usr/bin/env python 
import os
import numpy as np

# Import QVisaDataObject
from PyQtVisa.utils import QVisaDataObject

# Import matplotlib
import matplotlib.pyplot as plt
import matplotlib as mpl
if __name__ == "__main__":

	# Path to data files
	#path = "../dat/BJT-BC547C-CE(npn).dat"
	path = "../dat/2N7000-Q4(nMOS)-TC.dat"

	# Read data object
	data = QVisaDataObject.QVisaDataObject()
	data.read_from_file( path )

	# Extract current bias steps
	vds_step = []

	for _key in data.keys():
	
		if data.get_key_data(_key) != {}:

			vds_step.append( float( data.get_metadata(_key, "__step__") ) )


	# Use the base current to create a colormap for traces. Normalize 
	# colobar values to minimum and maximum base current
	norm = mpl.colors.Normalize( vmin=min(vds_step), vmax=max(vds_step) )
	cmap = mpl.cm.ScalarMappable( norm=norm, cmap=mpl.cm.cividis )
	cmap.set_array([])

	# Set up mpl figure
	fig = plt.figure()
	ax0 = fig.add_subplot(111)

	# # Loop through data keys and plot traces
	for _key in data.keys():

		if data.get_key_data(_key) != {}:

			# Extract current bias step
			vds = ( float( data.get_metadata(_key, "__step__") ) )

			# Extract voltage and current
			vgs = data.get_subkey_data(_key, "V0")
			ids = data.get_subkey_data(_key, "I1")

			# plot the data
			ax0.plot( vgs[1:], [ 1e3 * _ for _ in ids[1:] ], color = cmap.to_rgba(vds) )


	# Add axes lables and show plot
	ax0.set_title("2N7000-Q4(nMOS) : Transfer Characteristics")
	ax0.set_xlabel("$V_{gs}$ $(V)$")
	ax0.set_ylabel("$I_{ds}$ $(mA)$")

	# Add the colorbar			
	cbar = fig.colorbar(cmap, ticks=vds_step)
	cbar.ax.get_yaxis().labelpad = 20
	cbar.ax.set_ylabel("$V_{ds}$ $(V)$", rotation=270)

	# Show plot
	plt.tight_layout()
	plt.show()
