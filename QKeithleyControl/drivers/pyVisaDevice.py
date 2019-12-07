# ---------------------------------------------------------------------------------
# 	QKeithleyControl
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

# Basic driver file for insturment
class pyVisaDevice:

	# Initialize
	def __init__(self, _addr, _name):	

		# Extract SPCI handle for Keithley
		rm = visa.ResourceManager()

		# Attempt to open resource. 
		# __init__ should appear in try except block
		self.inst = rm.open_resource('GPIB0::%s::INSTR'%_addr)
		self.inst.timeout = 2000
		self.inst.clear()

		# GPIB address and name
		self.addr = int(_addr)
		self.name = str(_name)

		# Create buffer object
		self.buffer = ""

	# Close instrument on program termination
	def close(self): 
		self.inst.close()

	# Write command
	def write(self, _data):
		self.inst.write(_data)
	
	# Query command. Only use when reading data	
	def query(self, _data, print_buffer=False):

		# Try to communicate with device
		self.buffer = self.inst.query(_data)

		# Option to print buffer
		if print_buffer:
			print(self.buffer)

		# Return buffer	
		return self.buffer