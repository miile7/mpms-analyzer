# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 10:11:41 2017

@author: Maximilian Seidler
"""

import scipy.optimize
import numpy as np

def dipolfunction(x, A = -1, B = 0, C = 0, D = 0, radius = 8, space = 8):
    """Create a dipol function f(x) = dipulfunction(x). The parameters A, B, C and
    D are fitting parameters: A describes the amplitude of the function, B is a
    linear function added to the dipolfunction. In this program this is caused by
    the linear SQID drive. The C is a constant offset in the y axis, D is a x
    offset of the peak centre
    Parameters
    ----------
        x : float
            The x axis values
        A : float
            The amplitude of the dipol funciton
        B : float
            The linear part in the dipol function
        C : float
            The constant y offset in the dipol function
        D : float
            The constant x offset in the dipol function
    Returns
    -------
        float
            The y value for the given x value with the parameters A, B, C and D
    """
    
#    radius = 8.3654 # Spulenradius
#    space  = 7.960  # Spulenabstand  
    posint = 1.0 * (x - D) #30.8, relative Position bezogen auf das Peakzentrum  
    
    x1 = singleturn(radius, space, posint ) # der Uebersichtlichkeit halber in separater funktion 'singleturn' ermittelt
    x2 = singleturn(radius,-space, posint )
    x3 = singleturn(radius,     0, posint )
    
    return A * ( (-x1-x2+2*x3)) + B* posint + C # fuer Dipol ermittelter, theoretischer Spannungsverlauf   

def singleturn(cradius, cspace, z):
    return cradius**2.0 /pow(cradius*cradius + (z-cspace)**2.0,1.5)

def datapointFit(xdata, ydata, squid_range = 1):
    result, errors = scipy.optimize.curve_fit(dipolfunction, xdata, ydata, bounds=([-15, -1, -0.5, 29.5, 8, 7.5], [15, 1, 0.5, 31.5, 8.5, 8.5]))
    
    # calculate magnetization and error
    magnetization = -0.00285897 * 14.7029 * result[0] * squid_range
    magnetization_error = -0.00285897 * 14.7029 * errors[0][0] * squid_range
    
    # parse the results, the errors are in the diagonal of the reutrned array
    return (magnetization, magnetization_error, result, np.diag(result))

    
if __name__ == "__main__":
#    import matplotlib.pyplot as plt
    import os
#    import sys
    
    import DataHandling.DataContainer
    import my_utilities
    
    maxlen = 0
    def loadFile(max_len, filename):
        global maxlen
        
        print("Loading file '{}': ".format(os.path.basename(filename)))
#        print("0%".ljust(7))
        maxlen = max_len
    
    def loadFileProgress(progress):
#        sys.stdout.write('\r')
#        sys.stdout.flush()
#        print((str(round(progress/maxlen*100)) + "%").ljust(7))
        pass
    
    def loadingEnd(success):
        global maxlen
#        sys.stdout.write('\r')
#        sys.stdout.flush()
#        print("100%".ljust(7))
        if success:
            print("\tSucessfully loaded {} lines".format(maxlen))
        else:
            print("\tLoading failed")
    
    root = os.path.abspath("\\\\cfs-student.student.uni-augsburg.de\\seidlema\\Bachlorarbeit\\Auswertungsdaten\\")
    
    print("Analyzing data files of " + str(root))
    
    coils_radius = []
    coils_distance = []
    
    file_count = 0
    datapoint_count = 0
    
    for file in os.scandir(root):
        file = str(file.path)
        filename, file_extension = os.path.splitext(file)
        
        if file.endswith(".rw.dat"):
            file_count += 1
            datacontainer = DataHandling.DataContainer.DataContainer(file)
            datacontainer.loadingStart.connect(lambda length, mode, file: loadFile(length, file))
            datacontainer.loadingProgress.connect(lambda progress, mode, file: loadFileProgress(progress))
            datacontainer.loadingEnd.connect(lambda success, mode, file: loadingEnd(success))
            datacontainer.readFileData()
            
            print("\tFitting {} datapoints (fitting free center fit over position)".format(len(datacontainer.datapoints)))
            y_fits = []
            
            current_file_coils_radius = []
            current_file_coils_distance = []
            
            for datapoint in datacontainer.datapoints:
                datapoint_count += 1
                xdata, ydata = datapoint.getPlotData("raw_position", "free_c_fit")
                squid_range = int(datapoint.getEnvironmentVariableAvg("squid range")[0])
                
                magnetization, mag_error, fitparameters, fiterrors = datapointFit(xdata, ydata, squid_range)

                current_file_coils_radius.append(fitparameters[4])                
                current_file_coils_distance.append(fitparameters[5])                
                
                y_fits.append([dipolfunction(x, fitparameters[0], fitparameters[1], fitparameters[2], fitparameters[3], fitparameters[4], fitparameters[5]) for x in xdata])
#                print("Amplitude: " + str(fitparameters[0]) + " \u00B1 " + str(fiterrors[0][0]) + ", Magnetization: " + str(magnetization) + " \u00B1 " + str(mag_error))
#                print("Coil radius: " + str(coils_radius[-1]) + ", Coils distance: " + str(coils_distance[-1]))
            
            line2 = "   coil radius: {: 0.8}   |   coils distance: {: 0.8}".format(
                    my_utilities.mean_std(current_file_coils_radius)[0], 
                    my_utilities.mean_std(current_file_coils_distance)[0])
            line1 = ("{:*^" + str(len(line2)) + "}").format("mean values for this file")
            print(line1 + "\n" + line2 + "\n" + len(line2) * "*" + "\n")
            
            coils_radius += current_file_coils_radius
            coils_distance += current_file_coils_distance
            
#            plt.plot(xdata, ydata, label="SQUID Spannung")
#            for index, yfit in enumerate(y_fits):
#               plt.plot(xdata, yfit, label="Fit {}".format(index))
#            plt.ylabel("SQUID Spannung")
#            plt.xlabel("Ort")
#            plt.legend()
    
    coils_radius = my_utilities.mean_std(coils_radius)
    coils_distance = my_utilities.mean_std(coils_distance)
    
    print(("\n\nTested {} files with a total of {} datapoints:\n   coil radius:   " + 
          "{: 0.8} \u00B1 {:0.8}\n   coil distance: {: 0.8} \u00B1 {:0.8}").format(file_count, datapoint_count, 
           coils_radius[0], coils_radius[1], coils_distance[0], coils_distance[1]))
    
#    plt.savefig("oij.pdf")