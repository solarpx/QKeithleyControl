# QKeithleyControl
QKeithleyControl is a user interface designed for automation of common laboratory measurement routines using Keithley 2400 
sourcemeters. The software offers three operational modes to interact with the Keithely: **hardware configuration mode**, **IV-bias mode**, and **IV-Sweep mode**. The program flow is designed to be intuitive, allowing for users to easily configure and operate laboratory hardware. 

# Hardware Configuration
When first running the program, the user will first be greeted with basic hardware configuration options as shown in the screenshot 
below. To initialize your Keithley sourcemeter, simply enter the GPIB address and click on **Initialize Keithley GPIB**. 

![QKeithleyControl_Config](https://github.com/mwchalmers/QKeithleyControl/blob/master/doc/img/QKeithleyControl_Config.png)

After initialization, this page allows the user to configure essential hardware globals for insturment operation. Note that 
configuration parameters cannot be modified prior to initialization. The configuration page allows one to modify the following
system level parameters.

Control          | Input              | Comment  
------------     | -------------      | -------------
GPIB Address     | `0-30`             | The GPIB address *must* be initialized prior to changing other settings. 
Sense Mode       | `2-wire OR 4-wire` | Configuration option to select 2-wire or 4-wire measurements
Output Route     | `Front OR Rear`    | Select front or rear output terminals on device
Integration Time | `0.01-10.0`        | Specified in *Power Line Cycles*(PLCs). 1PLC = 20ms(50Hz) OR 16.7ms(60Hz)  

# IV-Bias Mode

IV bias mode allows one to use the Keithley as a **voltage source** or a **current source**. To enter IV-Bias mode, use the 
**IV-Bias Control** option in the **Select Measurement** menu. To operate the sourcemeter, select the level and corresponding compliance value in the configuration panel and click **Change Bias** followed by **Output**. Be sure to set a corresponding current(voltage) compliance level when operating in voltage(current) source mode respectively. The **compliance level** determines the maximum amount of current(voltage) to apply when operating the sourcementer in voltage(current) source mode. Voltage source or current source mode operation can be selected in the dropdown menu in the configuration panel.

### IV-Bias Controls
![QKeithleyControl_IVBias](https://github.com/mwchalmers/QKeithleyControl/blob/master/doc/img/QKeithleyControl_IVBias.PNG)

### IV-Bias Operation
The **Output** button reflects the state of the output on the insturment. When operating, it is possible to dynamically change
the output level without turning off the output. The plot shows the corresponding measured value as a function of time for the 
bias applied. To update a bias level and compliance, simply edit the corresponding values and click on **Change Bias**. The 
**Measurement Interval** parameter allows one to control the time between individual sense samples. When set to zero, the delay will reflect the insuturment integration time assinged in **Configuration** along with software runtime. In order to protect the unit, the 
following `20W` hard limits are placed on bias mode operation.

Mode             | Limit              | Compliance  
------------     | -------------      | -------------
Voltage Source   | `+/-20V`           | `1A`  
Current Source   | `+/-1A`            | `+/-20V`

### Saving Data
After performing a measurement in bias mode, QKeithleyControl gives you the option to save your data traces. This is done by 
selecting **Save Traces**. Bias mode data will be saved in a *tab deliminated file* with four columns: **elapsed time(s)**, **voltage(V)**, **current (A)**, **dissapated power (W)**. If multiple traces have been performed, each data trace will be saved 
in the selected file. Below is shown an extract of data produced via an IV Bias mode measurement. Note that it is not possible 
to save data while the device output is on.
```
*bias
t			V		I		P		
0.29004812240600586	0.7205986	0.001000028	0.0007206187767608	
0.6402521133422852	0.7205721	0.001000029	0.0007205929965909	
0.9899940490722656	0.720544	0.001000029	0.000720564895776	
1.320244550704956	0.7205217	0.00100003	0.000720543315651	
1.6602511405944824	0.7204945	0.001000029	0.0007205153943405	
2.0056159496307373	0.7204689	0.001000029	0.0007204897935980999	
2.3556177616119385	0.7204462	0.001000029	0.0007204670929398	
```

# IV-Sweep Mode

Operation of the sourcemeter in sweep mode is similar to bias mode operation. Sweep mode allows one to specify a **start value**,
**stop value** and the **number of points** to sweep. *QKeithleyControl* also offers a **Hysteresis Mode** which will configure the 
sweep to go from start value to stop value to start value in a forward sweep followed reverse sweep. It is also possible to set a 
time delay parameter between sweep measurement points of up to ten minutes. 

### IV-Sweep Controls
![QKeithleyControl_IVSweep](https://github.com/mwchalmers/QKeithleyControl/blob/master/doc/img/QKeithleyControl_IVSweep.PNG)

### IV-Sweep Operation
To create a sweep, enter your desired sweep parameters and select **Configure Sweep**. After this, click **Measure Sweep** to 
acquire data from your device under test. Note that in sweep mode, it is always possible to abort measurements by clicking 
the red **Abort Sweep** button mid measurement. In case of measurements with long measurement intervals, your measurement will 
terminate after the next data point has been collected. In order to save data traces, click on **Save Traces**. Note that it is
not possible to save data while measurements are underway. Below is shown an extract of data produced via an IV-Sweep mode measurement.
Note that the data format is identical to that of the IV-Bias mode measurement
```
*sweep
t			V		I		P		
0.23992514610290527	0.0	-1.417286e-11	-0.0	
0.5734109878540039	0.1	2.78345e-08	2.7834500000000004e-09	
0.8965251445770264	0.2	2.281799e-07	4.5635980000000006e-08	
1.3736143112182617	0.3	1.483972e-06	4.4519159999999996e-07	
1.6928954124450684	0.4	1.002846e-05	4.011384e-06	
2.1475539207458496	0.5	6.955527e-05	3.4777635e-05	
2.59263277053833	0.6	0.0003307777	0.00019846662	
```
 
 
# Installation

Since QKeithleyControl is written in [python](https://www.python.org/downloads/), be sure to install [python](https://www.python.org/downloads/) before continuing. To get QKeithleyControl, simply clone this [repository](https://github.com/mwchalmers/QKeithleyControl). Alternatively you can download `.zip` file. Assuming you have all dependencies installed properly you can run QKeithleyControl directly out of the source directory. 

```
cd QKeithleyControl/
python QKeithleyControl
```
It may be desired to create a softlink shortcut to the program contol. To do this in Windows, navigate to your `QKeithleyControl` directory, left click on `__main__.py` and create your shortcut. In Linux, execute the following commands with your specific source
and destination paths.
```
ln -s <src_path>/QKeithleyControl/__main__.py <dest_path>/QKeithleyControl.py
```

# Dependencies

QKeithleyControl requires both hardware and software dependencies prior to installation and operation. To communicate with Keithely over GPIB the following resources are needed.

1. [NI 488.2](https://www.ni.com/sv-se/support/downloads/drivers/download.ni-488-2.html#329025) is an NI instrument driver with several utilities that help in developing and debugging an application program. NI-488.2 includes high-level commands that automatically handle all bus management, so you do not have to learn the programming details of the GPIB hardware product or the IEEE 488.2 protocol.
2. [NI VISA](https://www.ni.com/sv-se/support/downloads/drivers/download.ni-visa.html#329456) is an NI instrument driver that is an implementation of the Virtual Instrument Software Architecture (VISA) I/O standard. VISA is a standard for configuring, programming, and troubleshooting instrumentation systems comprising GPIB, VXI, PXI, serial (RS232/RS485), Ethernet/LXI, and/or USB interfaces.

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
