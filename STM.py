"""
   STM Python
   Author:  Pawel
   Revision:  2023-07-10

   Requires:
       Python 2.7, 3
"""

from ctypes import *
import time
from dwfconstants import *
import sys
import matplotlib.pyplot as plt
import numpy as np

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

# Constants
BUFFER_SIZE = 8192
SAMPLING_RATE = 128
TRIANGLE_FREQ = 0.5
SAWTOOTH_FREQ = 0.001953125
VOLTAGE_TRI = 0.05 # 50 mV
VOLTAGE_SAW = 0.1  # 100 mV
OFFSET_TRI = 0.05
OFFSET_SAW = 0

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("Version: "+str(version.value))

cdevices = c_int()
dwf.FDwfEnum(c_int(0), byref(cdevices))
print("Number of Devices: "+str(cdevices.value))

if cdevices.value == 0:
    print("no device detected")
    quit()

# Prevent temperature drift
dwf.FDwfParamSet(DwfParamOnClose, c_int(0)) # 0 = run, 1 = stop, 2 = shutdown

print("Opening first device")
hdwf = c_int()
dwf.FDwfDeviceOpen(c_int(0), byref(hdwf))

if hdwf.value == hdwfNone.value:
    print("failed to open device")
    quit()

print("Configure and start first and second analog out channel")
# Triangle waveform
dwf.FDwfAnalogOutEnableSet(hdwf, c_int(0), c_int(1))
dwf.FDwfAnalogOutFunctionSet(hdwf, c_int(0), c_int(3)) # 3 = Triange waveform
dwf.FDwfAnalogOutFrequencySet(hdwf, c_int(0), c_double(TRIANGLE_FREQ))
dwf.FDwfAnalogOutAmplitudeSet(hdwf, c_int(0), c_double(VOLTAGE_TRI)) # Set voltage amplitude
dwf.FDwfAnalogOutOffsetSet(hdwf, c_int(0), c_double(OFFSET_TRI)) # Set voltage offset

# Sawtooth waveform
dwf.FDwfAnalogOutEnableSet(hdwf, c_int(1), c_int(1))
dwf.FDwfAnalogOutFunctionSet(hdwf, c_int(1), c_int(4)) # 4 = Sawtooth waveform
dwf.FDwfAnalogOutFrequencySet(hdwf, c_int(1), c_double(SAWTOOTH_FREQ))
dwf.FDwfAnalogOutAmplitudeSet(hdwf, c_int(1), c_double(VOLTAGE_SAW)) # Set voltage amplitude
dwf.FDwfAnalogOutOffsetSet(hdwf, c_int(1), c_double(OFFSET_SAW)) # Set voltage offset

# Set phase
dwf.FDwfAnalogOutPhaseSet(hdwf, c_int(1), AnalogOutNodeCarrier, c_double(95.0))

# Start the waveform generation
dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_int(1))
dwf.FDwfAnalogOutConfigure(hdwf, c_int(1), c_int(1))


# Set up the analog input channel
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(1.0))  # Set the voltage range to 5V

# Set up the sample rate and buffer size
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(SAMPLING_RATE))  # Set the sample rate to 128 samples per second
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(BUFFER_SIZE))  # Set the buffer size to 8192 samples

# Start the first acquisition
print("Starting acquisition...")
dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(1))

# Wait for the first acquisition to complete
while True:
    sts = c_byte()
    dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
    if sts.value == DwfStateDone.value:
        break
    time.sleep(0.5)

# Read the first set of acquired data
data_1 = np.zeros(8192, dtype=np.float64)
dwf.FDwfAnalogInStatusData(hdwf, c_int(0), data_1.ctypes.data_as(POINTER(c_double)), c_int(BUFFER_SIZE))

# Start the second acquisition
dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(1))

# Wait for the second acquisition to complete
while True:
    sts = c_byte()
    dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
    if sts.value == DwfStateDone.value:
        break
    time.sleep(0.5)

# Read the second set of acquired data
data_2 = np.zeros(8192, dtype=np.float64)
dwf.FDwfAnalogInStatusData(hdwf, c_int(0), data_2.ctypes.data_as(POINTER(c_double)), c_int(BUFFER_SIZE))

# Concatenate the acquired data
rg = np.concatenate((data_1, data_2))

dwf.FDwfAnalogOutReset(hdwf)
dwf.FDwfDeviceCloseAll()

# Make into numpy array and reshape to (128,128)
a = np.array(rg).reshape((128,128))

# Reverse alternate rows
for r in range(1,128,2):
   a[r] = a[r][::-1]


#Generate image
plt.imsave('/home/rpi/mystm_pic.tiff', a, cmap='afmhot') # file location

plt.imshow(a, cmap='afmhot')

plt.show()
