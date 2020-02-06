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
	path = "../dat/BC547C-BJT(npn).dat"

	# Read data object
	data = QVisaDataObject.QVisaDataObject()
	data.read_from_file( path )

	# Extract current bias steps
	base_currents = []
	
	for _key in data.keys():
	
		if data.get_key_data(_key) != {}:

			base_currents.append( 1000. * float( data.get_metadata(_key, "__step__") ) )


	# Use the base current to create a colormap for traces. Normalize 
	# colobar values to minimum and maximum base current
	norm = mpl.colors.Normalize( vmin=min(base_currents), vmax=max(base_currents) )
	cmap = mpl.cm.ScalarMappable( norm=norm, cmap=mpl.cm.cividis )
	cmap.set_array([])

	# Set up mpl figure
	fig = plt.figure()
	ax0 = fig.add_subplot(111)

	# Loop through data keys and plot traces
	for _key in data.keys():

		if data.get_key_data(_key) != {}:

			# Extract current bias step
			base_current = ( 1000. * float( data.get_metadata(_key, "__step__") ) )

			# Extract voltage and current
			voltage = data.get_subkey_data(_key, "V0")
			current = data.get_subkey_data(_key, "I0")

			# plot the data
			ax0.plot( voltage[1:], [ 1000. * np.abs(_) for _ in current[1:] ], color = cmap.to_rgba(base_current) )


	# Add axes lables and show plot
	ax0.set_title("BJT BC547C(npn) : Common Emitter")
	ax0.set_xlabel("$V_{CE}$ $(V)$")
	ax0.set_ylabel("$I_{CE}$ $(mA)$")

	# Add the colorbar			
	cbar = fig.colorbar(cmap, ticks=base_currents)
	cbar.ax.get_yaxis().labelpad = 20
	cbar.ax.set_ylabel("$I_{BE}$ $(mA)$", rotation=270)

	# Show plot
	plt.tight_layout()
	plt.show()
