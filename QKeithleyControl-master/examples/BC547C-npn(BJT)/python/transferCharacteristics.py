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
	path = "../dat/BJT-BC547C(npn)-CE-ice(vbe).dat"

	# Read data object
	data = QVisaDataObject.QVisaDataObject()
	data.read_from_file( path )

	# Extract voltage bias steps
	vce_step, ice_unit = [], 1e3
	
	for _key in data.keys():
	
		if data.get_key_data(_key) != {}:

			vce_step.append( float( data.get_metadata(_key, "__step__") ) )


	# Use the base current to create a colormap for traces. Normalize 
	# colobar values to minimum and maximum base current
	norm = mpl.colors.Normalize( vmin=min(vce_step), vmax=max(vce_step) )
	cmap = mpl.cm.ScalarMappable( norm=norm, cmap=mpl.cm.cividis )
	cmap.set_array([])

	# Set up mpl figure
	fig = plt.figure()
	ax0 = fig.add_subplot(111)

	# Loop through data keys and plot traces
	for _key in data.keys():

		if data.get_key_data(_key) != {}:

			# Extract current bias step
			vce = ( float( data.get_metadata(_key, "__step__") ) )

			# Extract voltage and current
			vbe = data.get_subkey_data(_key, "V0")
			ice = data.get_subkey_data(_key, "I1")


			# plot the data
			ax0.plot( vbe[1:], [ ice_unit * _ for _ in ice[1:] ], color = cmap.to_rgba(vce) )


	# Add axes lables and show plot
	#ax0.set_title("BJT BC547C(npn) : Common Emitter")
	ax0.set_title("BJT BC547C(npn) : Transfer Characteristics")
	ax0.set_xlabel("$V_{be}$ $(V)$")
	ax0.set_ylabel("$I_{ce}$ $(mA)$")

	# Add the colorbar			
	cbar = fig.colorbar(cmap, ticks=vce_step)
	cbar.ax.get_yaxis().labelpad = 20
	cbar.ax.set_ylabel("$V_{ce}$ $(V)$", rotation=270)

	# Show plot
	plt.tight_layout()
	plt.show()
