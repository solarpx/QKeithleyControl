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
	path = "../dat/BJT-BC547C(npn)-CE-ice(vce).dat"

	# Read data object
	data = QVisaDataObject.QVisaDataObject()
	data.read_from_file( path )

	# Extract current bias steps
	ibe_step, ibe_unit, ice_unit = [], 1e6, 1e3
	
	for _key in data.keys():
	
		if data.get_key_data(_key) != {}:

			ibe_step.append( ibe_unit * float( data.get_metadata(_key, "__step__") ) )


	# Use the base current to create a colormap for traces. Normalize 
	# colobar values to minimum and maximum base current
	norm = mpl.colors.Normalize( vmin=min(ibe_step), vmax=max(ibe_step) )
	cmap = mpl.cm.ScalarMappable( norm=norm, cmap=mpl.cm.cividis )
	cmap.set_array([])

	# Set up mpl figure
	fig = plt.figure()
	ax0 = fig.add_subplot(111)

	# Loop through data keys and plot traces
	for _key in data.keys():

		if data.get_key_data(_key) != {}:

			# Extract current bias step
			ibe = ( ibe_unit * float( data.get_metadata(_key, "__step__") ) )

			# Extract voltage and current
			voltage = data.get_subkey_data(_key, "V0")
			current = data.get_subkey_data(_key, "I0")

			# plot the data
			ax0.plot( voltage[1:], [ ice_unit * _ for _ in current[1:] ], color = cmap.to_rgba(ibe) )


	# Add axes lables and show plot
	#ax0.set_title("BJT BC547C(npn) : Common Emitter")
	ax0.set_title("BJT BC547C(npn) : Output Characteristics")
	ax0.set_xlabel("$V_{ce}$ $(V)$")
	ax0.set_ylabel("$I_{ce}$ $(mA)$")

	# Add the colorbar			
	cbar = fig.colorbar(cmap, ticks=ibe_step)
	cbar.ax.get_yaxis().labelpad = 20
	cbar.ax.set_ylabel("$I_{be}$ $(\\mu A)$", rotation=270)

	# Show plot
	plt.tight_layout()
	plt.show()
