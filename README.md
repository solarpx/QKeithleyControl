# QKeithleyControl
QKeithleyControl is a user interface designed for automation of common laboratory measurement routines using Keithley 2400 
sourcemeters. QKeithleyControl currently offers three applications which interact with the Keithely: The **IV-bias** application 
allows one to use the Keithley as a programable variable voltage(current) source, and the **IV-sweep** application allows one to make current/voltage sweeps of electronic devices and test structures. The **PV-characterization** application is oriented towards 
the characterization of photovoltaic devices. QKeithleyControl also contains a **Hardware Configuration** application which allows 
one to initialize and configure one or more Keithley sourcemeters for use in other applications.

# Hardware Configuration
When first running the program, the user will first be greeted with the hardware configuration application. This mode allows one 
to initialize Keithley sourcemeters. To initialize a device,  simply enter the GPIB address and click on **Initialize Keithley GPIB**. 
The device will then appear as selectable in the **Select Insturment** dropdown menu. 

![QKeithleyControl_Config](https://github.com/mwchalmers/QKeithleyControl/blob/master/doc/img/QKeithleyConfiguration.png)

When an insuremnt is selected, the user can modify several of its system parameters dynamically. For each Keithley initialized in the software, one has access to the following the following system level parameters.

Control          | Input              | Comment  
------------     | -------------      | -------------
GPIB Address     | `0-30`             | The GPIB address *must* be initialized prior to changing other settings. 
Sense Mode       | `2-wire OR 4-wire` | Configuration option to select 2-wire or 4-wire measurements
Output Route     | `Front OR Rear`    | Select front or rear output terminals on device
Integration Time | `0.01-10.0`        | Specified in *Power Line Cycles*(PLCs). 1PLC = 20ms(50Hz) OR 16.7ms(60Hz)  

# IV-Bias Mode

IV bias mode allows one to use the Keithley as a programable **voltage source** or a **current source**. To enter IV-Bias mode, 
select the **IV-Bias Control** application option in the **Select Measurement** menu. To operate the sourcemeter, select the level 
and corresponding compliance value in the configuration panel. These values will be transmitted dynamically to the Keithley. To turn 
on the output and monitor data, click the **Output** button. To turn off the output, simply clicking **Output** when operating. Since, the measurement will terminate after the next data point is aquired. The **Measurement Interval** setting can be used to determine how often the sourcemeter aquires data. Note that in the case of long, **Measurement Intervals** it will take one measurement interval before the output terminates. Be sure to set a corresponding current(voltage) compliance level when operating in voltage(current) source mode respectively. The **compliance level** determines the maximum amount of current(voltage) to apply when operating the sourcementer in voltage(current) source mode. Voltage source or current source mode operation can be selected in the dropdown menu in the configuration panel. The compliance cannot be changed dynamically while the output is on and measuring. 

### IV-Bias Operation
![QKeithleyControl_IVBias](https://github.com/mwchalmers/QKeithleyControl/blob/master/doc/img/QKeithleyBias.png)

The **Output** button reflects the state of the output on the insturment. When operating, it is possible to dynamically change
the output level without turning off the output by editing the **Bias Level** parameter. The plot shows the corresponding measured value as a function of time. The **Measurement Interval** parameter allows one to control the time between individual sense samples. When set to zero, the delay will reflect the insuturment integration time assinged in **Configuration** along with software runtime. 
In order to protect the unit, the following `20W` hard limits are placed on bias mode operation.
 
Mode             | Limit              | Compliance  
------------     | -------------      | -------------
Voltage Source   | `+/-20V`           | `1A`  
Current Source   | `+/-1A`            | `+/-20V`

After performing a measurement in bias mode, QKeithleyBias gives you the option to save your data traces. This is done by 
selecting **Save Data**. Bias mode data will be saved in a *tab deliminated* with four columns: **elapsed time(s)**, **voltage(V)**, **current (A)**, **dissapated power (W)**. 

**NOTE:** The data will be saved is tied to the traces that are shown in plot. When axes are cleared by invoking **Clear Data** in 
the plot, data will be deleted from memory. Be sure to save your data before clearing plots. Also, changing operation from voltage source to current source mode will invoke **Clear Data**. A dialogue is always presented to the user if data is to be deleted.

# IV-Sweep Mode

Operation of the sourcemeter in sweep mode is similar to bias mode operation. Sweep mode allows one to specify a **start value**,
**stop value** and the **number of points** to sweep. *QKeithleyControl* also offers a **Hysteresis Mode** which will configure the 
sweep to go from start value to stop value to start value in a forward sweep followed reverse sweep. It is also possible to set a 
time delay parameter between sweep measurement points of up to ten minutes. 

### IV-Sweep Controls
![QKeithleyControl_IVSweep](https://github.com/mwchalmers/QKeithleyControl/blob/master/doc/img/QKeithleySweep.png)

### IV-Sweep Operation
To create a sweep, enter your desired sweep parameters and select **Configure Sweep**. After this, click **Measure Sweep** to 
acquire data from your device under test. Note that in sweep mode, it is always possible to abort measurements by clicking 
the red **Abort Sweep** button mid measurement. In case of measurements with long measurement intervals, your measurement will 
terminate after the next data point has been collected. In order to save data traces, click on **Save Traces**. Note that it is
not possible to save data while measurements are underway. Below is shown an extract of data produced via an IV-Sweep mode measurement.
Note that the data format is identical to that of the IV-Bias mode measurement
```
*sweep
t			V	I		P		
0.23992514610290527	0.0	-1.417286e-11	-0.0	
0.5734109878540039	0.1	2.78345e-08	2.7834500000000004e-09	
0.8965251445770264	0.2	2.281799e-07	4.5635980000000006e-08	
1.3736143112182617	0.3	1.483972e-06	4.4519159999999996e-07	
1.6928954124450684	0.4	1.002846e-05	4.011384e-06	
2.1475539207458496	0.5	6.955527e-05	3.4777635e-05	
2.59263277053833	0.6	0.0003307777	0.00019846662	
```


# QVisaData Files
 When saving data using  
 
 
  If multiple traces have been performed, all data traces will be saved in the selected file. Below is shown an extract of data produced via an IV Bias mode measurement. 
```
*! QVisaDatafile v1.1
#! sweep 5168f9e
t		V		I		P		
0.3414440155029297	-1.0	-2.83979e-09	2.83979e-09	
0.6617891788482666	-0.99215	-2.830153e-09	2.80793629895e-09	
0.9994220733642578	-0.9843	-2.822867e-09	2.7785479881e-09	
1.3298373222351074	-0.97645	-2.817607e-09	2.7512523551500003e-09	
1.659815788269043	-0.96865	-2.80258e-09	2.714719117e-09	
1.989814043045044	-0.9608	-2.803379e-09	2.6934865431999998e-09	
2.3198494911193848	-0.95295	-2.790033e-09	2.6587619473499998e-09	
2.6498541831970215	-0.9451	-2.795675e-09	2.6421924425e-09	
2.9677672386169434	-0.93725	-2.790242e-09	2.6151543145e-09
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
