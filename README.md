# QKeithleyControl
QKeithleyControl is a user interface designed for automation of common laboratory measurement routines using Keithley 2400 
sourcemeters. The software offers three operational modes to interact with the Keithely: A configuration mode, IV-bias mode, 
and IV-Sweep mode. The program flow is designed to be intuitive, allowing for users to easily configure and operate laboratory
hardware. 

### Hardware Configuration
When first running the program, the user will first be greeted with basic hardware configuration options as shown in the screenshot 
below. 


This page allows the user to configure essential hardware globals for insturment operation. 

Control          | Input              | Comment  
------------     | -------------      | -------------
GPIB Address     | `0-30`             | The GPIB address *must* be initialized prior to changing other settings. 
Sense Mode       | `2-wire OR 4-wire` | Configuration option to select 2-wire or 4-wire measurements
Output Route     | `Front OR Rear`    | Select front or rear output terminals on device
Integration Time | `0.01-10.0`        | Specified in *Power Line Cycles*(PLCs). 1PLC = 20ms(50Hz) OR 16.7ms(60Hz)  

### IV-Bias Mode

### IV-Sweep Mode


 
# Installation

Since QKeithleyControl is written in [python](https://www.python.org/downloads/), be sure to install [python](https://www.python.org/downloads/) before 
continuing. To get QKeithleyControl simply clone the [repository](https://github.com/mwchalmers/QKeithleyControl). Alternatively you can '
download `.zip` file. Assuming you have all dependencies installed properly you can run QKeithleyControl directly out of the source
directory. 

```
cd QKeithleyControl/
python QKeithleyControl
```

# Dependencies

QKeithleyControl requires both hardware and software dependencies prior to installation and operation. To communicate with Keithely over 
GPIB the following resources are needed.

1. [NI 488.2](https://www.ni.com/sv-se/support/downloads/drivers/download.ni-488-2.html#329025) NI-488.2 is an NI instrument driver with several utilities that help in developing and debugging an application program. NI-488.2 includes high-level commands that automatically handle all bus management, so you do not have to learn the programming details of the GPIB hardware product or the IEEE 488.2 protocol.
2. [NI VISA](https://www.ni.com/sv-se/support/downloads/drivers/download.ni-visa.html#329456) NI-VISA is an NI instrument driver that is an implementation of the Virtual Instrument Software Architecture (VISA) I/O standard. VISA is a standard for configuring, programming, and troubleshooting instrumentation systems comprising GPIB, VXI, PXI, serial (RS232/RS485), Ethernet/LXI, and/or USB interfaces.

The following python dependencies are also required.

1. [pyVisa](https://pyvisa.readthedocs.io/en/latest/) Python bindings for NI-VISA driver
2. [PyQt5](https://wiki.python.org/moin/PyQt) Python bindings for Qt development framework
3. [numpy](https://numpy.org/) Python numerics library
4. [matplotlib](https://matplotlib.org/) Python plotting library

The python modules can be installed using pip. To get pip run the following commands:
```
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
```

To install the python dependencies simply run the following commands
```
pip install pyvisa
pip install PyQt5
pip install numpy
pip install matplotlib
```
