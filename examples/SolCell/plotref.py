
#!/usr/bin/env python 
import os
import numpy as np

# Import QVisaDataObject
from PyQtVisa.utils import QVisaDataObject

# Import matplotlib
import matplotlib.pyplot as plt

if __name__ == "__main__":


	if False:	
		# Get data paths
		paths = []
		root  = "\\\\fysfile01\\ftfhome$\\mi6882wi\\Desktop\\SiRef\\sweeps\\"
		for item in os.listdir(root):
			if os.path.isfile(os.path.join(root, item)):
				paths.append(root + item)

		# Create figure
		fig = plt.figure(figsize=(8,5))
		ax0 = fig.add_subplot(111)
		ax0.set_xlabel("Voltage (V)")
		ax0.set_ylabel("Current (mA)")
		ax0.set_xlim([0,0.6])
		ax0.set_ylim([0,140])
		ax0.yaxis.set_ticks(np.arange(0, 175, 25))

		ax1 = ax0.twinx()
		ax1.set_xlabel("Voltage (V)")
		ax1.set_ylabel("Power (mW)")
		ax1.set_ylim([0,70])
		
		# Loop though paths and plot data
		for path in paths:

			data = QVisaDataObject.QVisaDataObject()
			data.read_from_file( path )

			# Get data key
			key = list( data.keys() )[0]

			# Plot the data
			_v = data.get_data_field(key, "V")
			_i = [1000 * _ for _ in data.get_data_field(key, "I")]
			_p = [1000 * _ for _ in data.get_data_field(key, "P")]

			if "AM1.5G" in path:
				ax1.plot(  _v, _p, 'r')
				ax0.plot(  _v, _i, 'b')
				

			else:
				ax1.plot(  _v, _p, 'r:', lw = 0.5 )
				ax0.plot(  _v, _i, 'b:', lw = 0.5 )

		ax0.set_title("Si Reference Cell : AM1.5G : 25$^\circ$C : 2019-12-11")
		plt.show()

	# Plot the dark current
	if False:
		
		path = "\\\\fysfile01\\ftfhome$\\mi6882wi\\Desktop\\SiRef\\calibration\\dark.dat"

		fig = plt.figure(figsize=(8,5))
		ax0 = fig.add_subplot(111)
		ax0.set_xlabel("Voltage (V)")
		ax0.set_ylabel("Current (mA)")
		ax0.set_xlim([0,0.6])
		#ax0.set_ylim([0,140])
		
		ax1 = ax0.twinx()
		ax1.set_xlabel("Voltage (V)")
		ax1.set_ylabel("Power (mW)")
		#ax1.set_ylim([0,70])

		data = QVisaDataObject.QVisaDataObject()
		data.read_from_file( path )

		# Get data key
		key = list( data.keys() )[0]

		# Plot the data
		_v = data.get_data_field(key, "V")
		_i = [1000 * _ for _ in data.get_data_field(key, "I")]
		_p = [1000 * _ for _ in data.get_data_field(key, "P")]

		ax1.plot(  _v, _p, 'r')
		ax0.plot(  _v, _i, 'b')

		ax0.set_title("Si Reference Cell : Dark Current : 25$^\circ$C : 2019-12-11")
		plt.show()

	# Plot the lamp stability
	if True:

		path = "\\\\fysfile01\\ftfhome$\\mi6882wi\\Desktop\\SiRef\\calibration\\stability.dat"

		fig = plt.figure(figsize=(8,5))
		ax0 = fig.add_subplot(111)
		ax0.set_ylabel("Current (mA)")
		ax0.set_xlabel("Time (s)")
		ax0.set_xlim([0,300])
		#ax0.set_ylim([0,140])

		data = QVisaDataObject.QVisaDataObject()
		data.read_from_file( path )

		# Get data key
		key = list( data.keys() )[0]

		# Plot the data
		_t = data.get_data_field(key, "t")
		_i = [-1000 * _ for _ in data.get_data_field(key, "I")]
	
		ax0.plot(  _t, _i, 'b')
		ax0.set_title("Si Reference Cell : $I_{sc}(t)$ : AM1.5G : 25$^\circ$C : 2019-12-11")
		plt.show()
