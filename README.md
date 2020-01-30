# QKeithleyControl
QKeithleyControl is a user interface designed for automation of common laboratory measurement routines using **Keithley 2400 sourcemeters**. QKeithleyControl currently offers three applications which interact with the Keithely: The **IV-bias** application allows one to use the Keithley as a programable variable voltage(current) source, and the **IV-sweep** application allows one to make current/voltage sweeps of electronic devices and test structures. The **PV-characterization** application is oriented towards the characterization of photovoltaic devices. QKeithleyControl also contains a **Hardware Configuration** application which allows one to initialize and configure one or more Keithley sourcemeters for use in other applications.

# Hardware Configuration
When first running the program, the user will first be greeted with the hardware configuration application. This mode allows one to initialize Keithley sourcemeters. To initialize a device,  simply enter the GPIB address and click on **Initialize Keithley GPIB**. The device will then appear as selectable in the **Select Insturment** dropdown menu. 

![QKeithleyConfiguration](https://github.com/mwchalmers/QKeithleyControl/blob/master/doc/img/QKeithleyConfiguration.png)

When an insuremnt is selected, the user can modify several of its system parameters dynamically. For each Keithley initialized in the software, one has access to the following the following system level parameters.

Control          | Input              | Comment  
------------     | -------------      | -------------
GPIB Address     | `0-30`             | The GPIB address *must* be initialized prior to changing other settings. 
Sense Mode       | `2-wire OR 4-wire` | Configuration option to select 2-wire or 4-wire measurements
Output Route     | `Front OR Rear`    | Select front or rear output terminals on device
Integration Time | `0.01-10.0`        | Specified in *Power Line Cycles*(PLCs). 1PLC = 20ms(50Hz) OR 16.7ms(60Hz)  

# IV-Bias Mode

IV bias mode allows one to use the Keithley as a programable **voltage source** or a **current source**. To enter IV-Bias mode, select the **IV-Bias Control** application option in the **Select Measurement** menu. To operate the sourcemeter, select the level and corresponding compliance value in the configuration panel. These values will be transmitted dynamically to the Keithley. To turn on the output and monitor data, click the **Output** button. To turn off the output, simply clicking **Output** when operating. Since, the measurement will terminate after the next data point is aquired. 

The **Measurement Interval** setting can be used to determine how often the sourcemeter aquires data. Note that in the case of long, **Measurement Intervals** it will take one measurement interval before the output terminates. Be sure to set a corresponding current(voltage) compliance level when operating in voltage(current) source mode respectively. The **compliance level** determines the maximum amount of current(voltage) to apply when operating the sourcementer in voltage(current) source mode. Voltage source or current source mode operation can be selected in the dropdown menu in the configuration panel. The compliance cannot be changed dynamically while the output is on and measuring. 

### IV-Bias Operation
![QKeithleyBias](https://github.com/mwchalmers/QKeithleyControl/blob/master/doc/img/QKeithleyBias.png)

The **Output** button reflects the state of the output on the insturment. When operating, it is possible to dynamically change the output level without turning off the output by editing the **Bias Level** parameter. The plot shows the corresponding measured value as a function of time. The **Measurement Interval** parameter allows one to control the time between individual sense samples. When set to zero, the delay will reflect the insuturment integration time assinged in **Configuration** along with software runtime. In order to protect the unit, the following `20W` hard limits are placed on bias mode operation.
 
Mode             | Limit              | Compliance  
------------     | -------------      | -------------
Voltage Source   | `+/-20V`           | `1A`  
Current Source   | `+/-1A`            | `+/-20V`

After performing a measurement in bias mode, QKeithleyBias gives you the option to save your data traces. This is done by selecting **Save Data**. Bias mode data will be saved in a *tab deliminated* with four columns: **elapsed time(s)**, **voltage(V)**, **current (A)**, **dissapated power (W)**. **NOTE:** The data will be saved is tied to the traces that are shown in plot. When axes are cleared by invoking **Clear Data** in the plot, data will be deleted from application memory. Be sure to save your data before clearing plots. Also, changing operation from voltage source to current source mode will invoke **Clear Data**. A dialogue is always presented to the user if data is to be deleted.

# IV-Characterization Mode

IV-characterization mode may be used to acquire the DC charachteristics of electronic devices and test circutis. Basic operation in this mode is similar to bias mode operation. To measure a device characteristic, first enter your desired parameters. After reviewing your measurement parameters, click **Measure Sweep** to acquire data from your device under test. Note that in IV-characterization mode, it is always possible to abort measurements by clicking the **Abort Sweep** button mid measurement. In case of measurements with long measurement intervals, the measurement will terminate after the next data point has been collected. In order to save data traces, click on **Save Data**. Note that it is not possible to save data while measurements are underway. Below is shown an extract of data produced via an IV-Sweep mode measurement. 

### IV-Sweep Operation
![QKeithleySweep](https://github.com/mwchalmers/QKeithleyControl/blob/master/doc/img/QKeithelySweep.png)

IV-characterization mode may be used to charachterize both two terminal (Resistances, Diodes, PV devices) and three terminal devices (FET, BJT). For two terminal devices, only one Keithley sourcemeter is required whereas for three terminal devices two Keithleys are required. In two terminal operation, a range of voltages(currents) is applied and the corresponding current(voltage) is measured for each bias point respectively. In basic two terminal operation, one only needs to specify a **start value**, **stop value** and the **number of points** in the controller. 

To measure a three terminal device such as a field effect transistor, one would like to perform repeated two terminal **IV-sweeps** while varying the voltage of the gate of the device via a **V-step**. This behaviour of **IV-sweep** and **V-step** can be configured independently via the **Configure Parameters** dropdown menu. By default, the three terminal **V-step** behaviour is disabled thus providing two terminal operation. To enable **V-step** simply toggle the **V-step (ON/OFF)** button. 

In order to perform a three terminal measurement, it is important that one first initializes two Keithley sourcemeters in the **Hardware Configuration**. These devices will then appear in the **Select Device**´dropdown in the IV-characterization application. Take note of the GPIB addresses of your IV-sweep and V-step sourcemeters when you are initializing your insturments. Note that the application will allow for the selection of the same device for the IV-sweep and V-step parameters. However, in this case, a warning message will be displayed indicating that the same sourcemeter has been selected for sweep and step operation and hardware operation will default to multiple identical sweeps.

### IV-Hysteresis Measurements 
The QKeithleySweep application has a **Hysteresis Mode** selector embedded into the **IV-sweep** controller allowing one to configure a variety of sweep conditions. Hysteresis measurements can be useful to characterize electronic devices that are unstable due to electronic trapping effects. The application summarizes the hysteresis modes available in QKeithleySweep. Note that the number of points in hysteresis modes is approximately `2n`.

Hysteresis Mode    | Bias Operation               |  nPoints  
------------       | -------------                | -------------
`None`             | `start - stop`               | `n`
`Reverse-sweep`    | `start - stop - start`       | `2*n - 1`
`Zero-centered`    | `0V - start - 0V -stop - 0V` | `2*n + 2`

### Bias step for transistor charachterization

QKeithleyControl offers a bias step mode which is useful for characterizing active devices such as field effect transistors (FETs) and bipolar junction transistors (BJTs). During a typical FET transistor measurement (output charachteristic), a varying voltage bias is applied between the soure-drain terminals of the FET and drain current is measured for a series of gate voltages *(voltage sweep, voltage step)*. In the case of a BJT, varying voltage bias is applied between the emitter-collector terminals and collector current is measured for varying base currents *(voltage sweep, current step)*. When operating in bias step mode, two independent Keithleys should be initialized in the Hardware Configuration setup for the sweep bias supply and step bias supply respectively. To configure a bias step measurement, select the **IV-step** option in the **configure parameters** menu and select the step source mode (voltage/current) and desired step parameters. Note that the QKeithleyControl will not perform the bias step loop unless the **Step Bias** button is in the ON state.

![QKeithleyBiasStep](https://github.com/mesoic/QKeithleyControl/blob/master/doc/img/QKeithleyBiasStep.png)

### Measuring Unstable Devices

Keithley sourcemeters can only supply starcase sweeps in which the voltage(current) is stepped from value to value in a discrete fashion. In the case of unstable devices, a sudden change in voltage may generate some transient behaviour in the current. However, IV-characterization mode only measures once for each applied bias, leaving integration of unstable currents and voltages up to the hardware itself. In all cases, the software will measure the current as soon as possible (i.e. before applying the measurement dealy cycle) such that the measuremnt settle time is determined by the hardware integration time. To investivate slow transients when quickly changing the bias, it is advised to use IV-bias mode with a short hardware integration time.

# PV-Characterization Mode


### Voc and MPP tracking modes

![QKeithleySolar](https://github.com/mesoic/QKeithleyControl/blob/master/doc/img/QKeithleySolar.png)


# Data Format 
QKeithleyControl is built upon the [QVisaFramework](https://github.com/mesoic/PyQtVisa). This allows for a unified method of handling data for all application modes. The file below shows an example measurement consisting of two IV-sweeps. The data format is *tab-deliminated* and is designed to be easy to manipulate in commercial software. Data header lines are always preceeded by the `*!` prefix. Measurement header lines will always take the following form `#! <type> <hash>`. The type wiil injected by the calling application (e.g. QKeithleyBias, QKeithleySweep, etc.), and the hash value provides for a cryptographically unique stamp which can be used to identify the data in user built postprocessing applications. 

```
*! QVisaDatafile v1.1
*! Diode Resistor(100Ohm) Series Circuit 
#! sweep c6bd7f6
t		V		I		P		
0.3358933925628662	-1.0	-2.730513e-09	2.730513e-09	
0.664708137512207	-0.97	-2.702644e-09	2.62156468e-09	
0.9892799854278564	-0.94	-2.690437e-09	2.52901078e-09	
1.315497875213623	-0.91	-2.672253e-09	2.43175023e-09	
1.627976894378662	-0.88	-2.657855e-09	2.3389123999999997e-09	 
1.9469718933105469	-0.85	-2.637861e-09	2.24218185e-09	
2.2590084075927734	-0.82	-2.619003e-09	2.14758246e-09	
2.578735589981079	-0.79	-2.606122e-09	2.05883638e-09	
2.889404535293579	-0.76	-2.585623e-09	1.9650734800000003e-09	
3.2051875591278076	-0.73	-2.57089e-09	1.8767497e-09	

#! sweep 80ae4de
t		V		I		P		
0.3355216979980469	-1.0	-2.759639e-09	2.759639e-09	
0.6530659198760986	-0.97	-2.746253e-09	2.66386541e-09	
0.9681046009063721	-0.94	-2.716027e-09	2.55306538e-09	
1.2886137962341309	-0.91	-2.69313e-09	2.4507483000000003e-09	
1.600466012954712	-0.88	-2.674778e-09	2.35380464e-09	
1.9178540706634521	-0.85	-2.655414e-09	2.2571019e-09	
2.231292963027954	-0.82	-2.6443e-09	2.168326e-09	
2.546135902404785	-0.79	-2.619634e-09	2.06951086e-09	
2.8595333099365234	-0.76	-2.605027e-09	1.97982052e-09	
3.1762137413024902	-0.73	-2.594043e-09	1.89365138999999

```

# Installation

Since QKeithleyControl is written in [python](https://www.python.org/downloads/), be sure to install [python](https://www.python.org/downloads/) before continuing. To get QKeithleyControl, simply clone this [repository](https://github.com/mesoic/QKeithleyControl). Alternatively you can download `.zip` file. Assuming you have all dependencies installed properly you can run QKeithleyControl directly out of the source directory. 

```
cd QKeithleyControl/
python QKeithleyControl.py
```
It may be desired to create a softlink shortcut to the program contol. To do this in Windows, navigate to your `QKeithleyControl` directory, left click on `QKeithleyControl.py` and create your shortcut. In Linux, execute the following commands with your specific source and destination paths.
```
ln -s <src_path>/QKeithleyControl/QKeithleyControl.py <dest_path>/QKeithleyControl.py
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
5. [PyQtVisa](https://github.com/mesoic/PyQtVisa) Qt Framework for building pyVisa applications.

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
pip install PyQtVisa
```
