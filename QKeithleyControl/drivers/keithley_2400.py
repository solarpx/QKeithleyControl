import visa
import time

class keithley_2400:

	# Initialize
	def __init__(self, GPIB):	

		# Extract SPCI handle for Keithley
		rm = visa.ResourceManager()
		rm.list_resources()

		# Attempt to open resource. __init__ should appear in try except block
		self.spci = rm.open_resource('GPIB0::%s::INSTR'%GPIB)
		self.spci.timeout = 5000
		self.spci.clear()

		# GPIB address 
		self.GPIB = int(GPIB)

		# Create buffer object
		self.buffer = ""

	# Close instrument on pogram termination
	def close(self): 
		self.spci.close()

	# Write command
	def write(self, _data):
		self.spci.write(_data)
	
	# Query command. Only use when reading data	
	def query(self, _data, print_buffer=False):

		# Try to communicate with device
		self.buffer = self.spci.query(_data)

		# Option to print buffer
		if print_buffer:
			print(self.buffer)

		return self.buffer	

	# All other methods are shortcut methods for 
	# Keithley control

	# Reset command
	def reset(self):
		self.write('*RST')

	# Trigger output state
	def output_on(self): 
		self.write(":OUTP:STAT ON")

	def output_off(self): 
		self.write(":OUTP:STAT OFF")

	# Methods for two/four wire sense mode
	def four_wire_sense_on(self):	
		self.write(":SYST:RSEN ON")

	def four_wire_sense_off(self):	
		self.write(":SYST:RSEN OFF")	

	# Front versus rear output
	def output_route_front(self):
		self.write(":ROUT:TERM FRON")

	def output_route_rear(self):
		self.write(":ROUT:TERM REAR")

	# Set integration time nPLCs
	# PLCs = power line cycles (50/60Hz)
	def update_nplc(self, _value):
		self.write(":SENS:CURR:NPLC %s"%str(_value))
		self.write(":SENS:VOLT:NPLC %s"%str(_value))

	# VOLTAGE SOURCE MODE FUNCTIONS
	# Set fixed voltage level and compliance
	def voltage_src(self):
		self.write(':SOUR:FUNC VOLT')
		self.write(':SOUR:VOLT:MODE FIX')
		self.write(':SENS:FUNC \"CURR\"')

	# Set current compliance
	def current_cmp(self, _level):
		self.write(':SENS:CURR:PROT %s'%str(_level))
		self.write(':SENS:CURR:RANG:AUTO ON')

	# CURRENT SOURCE MODE FUNCTIONS
	# Set fixed current level and compliance
	def current_src(self):
		self.write(':SOUR:FUNC CURR')
		self.write(':SOUR:CURR:MODE FIX')
		self.write(':SENS:FUNC \"VOLT\"')

	def voltage_cmp(self, _level):
		self.write(':SENS:VOLT:PROT %s'%str(_level))
		self.write(':SENS:VOLT:RANG:AUTO ON')

	# Set complicance value before applying bias
	def set_voltage(self, _level):
		self.write(':SOUR:VOLT:LEV %s'%str(_level))

	# Set complicance value before applying bias
	def set_current(self, _level):
		self.write(':SOUR:CURR:LEV %s'%str(_level))

	# Initiate measurement	
	def meas(self):
		self.write(":INIT")
		self.write("*WAI")

		# Create server loop for data in order to 
		# capture long integration times
		while True:
			try:
				return self.query(":READ?")
			except visa.VisaIOError:
				time.sleep(0.1)	