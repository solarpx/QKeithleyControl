# ---------------------------------------------------------------------------------
# 	keithley2400 insturment driver
# 	Copyright (C) 2019 Michael Winters
#	mwchalmers@protonmail.com
# ---------------------------------------------------------------------------------
# 
# 	Permission is hereby granted, free of charge, to any person obtaining a copy
# 	of this software and associated documentation files (the "Software"), to deal
# 	in the Software without restriction, including without limitation the rights
# 	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# 	copies of the Software, and to permit persons to whom the Software is
# 	furnished to do so, subject to the following conditions:
# 	
# 	The above copyright notice and this permission notice shall be included in all
# 	copies or substantial portions of the Software.
# 	
# 	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# 	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# 	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# 	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# 	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# 	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# 	SOFTWARE.
#

#!/usr/bin/env python 
import visa
import time

# Import pyVisaDevice
import drivers.pyVisaDevice

class keithley2400(drivers.pyVisaDevice.pyVisaDevice):

	# Initialize Driver
	def __init__(self, _addr, _name="Keithley"):

		super(keithley2400, self).__init__(_addr, _name)

	# Identify command
	def idn(self):
		return self.query('*IDN?')

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