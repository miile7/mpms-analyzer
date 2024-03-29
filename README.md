# MPMSAnalyzer

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quickstart](#quickstart)
4. [Known Bugs](#known-bugs)

## Overview

MPMSAnalyzer is a program to increase information gain from Magnetic Property Measurement 
System (SQUID) DC-Measurements (program written for MPMS 3 by Quantum Design). 

MPMSAnalyzer key features:
- Subtract background data to remove magnetic influence of specimen holders ect.
- Afterwards adjust the dipol fitting curve to support very small specimens
- Exclude single points to avoid integrating bolter points
- Interpolate (background) measurements to save time for background subtraction
- Export to standard formats (csv)

![Screenshot of MPMSAnalyzer](screenshot.jpg)
Screenshot of MPMSAnalyzer: Original data with background subtracted and fit area cutted
so borders do not influence the dipol fit. Every single fit can be inspected. (Used data
is available in the `example_data` directory.)

## Installation

Open the command line (Windows: Type `cmd` in the search) and run 
```
pip install MPMSAnalyzer
```

Now you can start the MPMSAnalyzer by typing

```
python -m MPMSAnalyzer
```

### Shortcut (Windows only)

If you prefer having a clickable program icon, create a shortcut like the following:

1. Create a new junction:  
   <img src="doc/new-junction.jpg" width="300" />
2. Enter `python -m MPMSAnalyzer` into the input field:  
   <img src="doc/new-junction-target.jpg" width="300" />
3. If you like, you can change the icon of the shortcut. To do so
   1. Download the [*MPMSAnalyzer.ico*](doc/MPMSAnalyzer.ico) image from the `doc` directory.
   2. Now select the shortcut on your machine, then
   3. right click on it and open the *Properties*.
   4. In the *Junction* tab click on the *Change icon* button, then
   5. select the *MPMSAnalyzer.ico* image.

### Manual installation

For manual installation [download all the files](https://github.com/miile7/mpms-analyzer/archive/master.zip), 
extract them and execute the `Controller.py` file in the `MPMSAnalyzer` directory to run 
MPMSAnalyzer.

## Quickstart

### Measurement
- **Create new files for each $`M(T)`$/$`M(H)`$ measurement.** Keep the files as short as 
  possible. The MPMSAnalyzer supports files only if they have a $`M(T)`$ **or** a $`M(H)`$ 
  measurement. 
- Use the material in the *sample material* field in the MPMS program. If you have more 
  probes than one use the exact definition of the probe in the *sample comment* field. 
  Otherwise there will be no chance to identify your probe.
  > You can use $`\LaTeX{}`$ code surrounded by `\$`'s in the title, comment, and other 
  > fields.
- If possible: Use the exact same sequence for measuring the background.

### General program use
- Save the edited data right after editing. There may be crashes so do not hope for the 
  best.
- All datapoints are divided in the Up- and the Down-Sweep. This means that all plotted 
  data and all files will have twice the amount of datapoints than in the MPMS program.

### Toolbar
- *Open/Plot/Format*: Open and plot a MPMS file. Select the `*.rw.dat` file. The `*.dat` 
  file has be in the same directory and the same name to be registered automatically. If 
  the file is not found you can select the `*.dat` file manually.
  > Try to use both files always.
  The Open, the Plot and the Format commands are more less the same.
- *Edit*: Define the fit frame. Set the range of the raw position for the voltages to fit.
- *Interpolate*: Interpolate the background for a given measurement. The background of the 
  probe has to be measured seperately. The background has to contain as much values as 
  possible. You can increase the temperature/field steps, the last and first point should 
  be the same like in the probe. Also try to cover all measurement ranges. This means for 
  a $`M(T)`$ measurement with multiple fields record the background for **all** field 
  values.
- *Subtract*: Subtract the background from the probe measurement. Make sure that the 
  background file has the same length (so the same number of datapoints) like the probe 
  measurement. If it does not have the same size use the *Interpolate* button.
  > Try to subtract files as short as possible. The more lines in the file the longer it 
  > takes. Also the MPMS adds empty lines which may cause errors. If the files are shorter 
  > there are less empty lines.
- *Export*: Export the data to a file. This supports `*.csv` files and the MPMS `*.rw.dat`
  and the `*.dat` files. `*.csv` files are recommended.

### Inspect and corect data
- Use double click on a datapoint of a measurement to open the fits. There you can see the 
  recorded data and the fit. The subtracted background data will also be displayed there 
  if you used some.
- Use the `...` button for getting more information about each datapoint.
- Change the fit constants in the `constants.py` if the fit was not successfully.
- Remember to use the Edit Tool for specifying the fit frame.
  > If background has been subtracted, there is the `probe (index)` and the 
  > `probe (position)`. They should be always congruent.

### Exporting
- Use the `*.csv` format for exporting if possible.
- Images of the plots can be created by left click and *Save* in the graph or in the 
  graph window toolbar.

## Known Bugs
- The *Plot* tool opens even if the file has been opened with another tool. 

  *Solution*: Simply close the plot tool.
- If the files are very large or the wrong running variable has been choosen, the *Format* 
  tool crashes. 
  
  *Solution*: Decrease the filesize or use the correct running variable.
- Sometimes the background will be used as the probe right after opening the background 
  file.
  
  *Solution*: Check if the probe and the background files are the correct files. If not 
  select them again.
