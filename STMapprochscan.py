"""
   STM Python
   Author:  Pawel
   Revision:  2024-02-20

   Requires:
       Python 2.7, 3
"""
import RPi.GPIO as GPIO
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
SAMPLING_RATE_AP = 8388608
SAMPLING_RATE = 128
TRIANGLE_FREQ = 0.5
SAWTOOTH_FREQ = 0.001953125
VOLTAGE_TRI = 0.05 # 50 mV
VOLTAGE_SAW = 0.1  # 100 mV
OFFSET_TRI = 0.05
OFFSET_SAW = 0

in1 = 17
in2 = 18
in3 = 27
in4 = 22

# careful lowering this, at some point you run into the mechanical limitation of how quick your motor can move
step_sleep = 0.002
step_count = 4096*3  # 5.625*(1/64) per step, 4096 steps is 360 deg
direction = True  # True for clockwise, False for counter-clockwise

# defining stepper motor sequence (found in documentation http://www.4tronix.co.uk/arduino/Stepper-Motors.php)
step_sequence = [[1,0,0,1], [1,0,0,0], [1,1,0,0], [0,1,0,0], [0,1,1,0], [0,0,1,0], [0,0,1,1], [0,0,0,1]]

# setting up
GPIO.setmode(GPIO.BCM)
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(in3, GPIO.OUT)
GPIO.setup(in4, GPIO.OUT)

# initializing
GPIO.output(in1, GPIO.LOW)
GPIO.output(in2, GPIO.LOW)
GPIO.output(in3, GPIO.LOW)
GPIO.output(in4, GPIO.LOW)

motor_pins = [in1, in2, in3, in4]
motor_step_counter = 0

# Open device
version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("Version: " + str(version.value))

cdevices = c_int()
dwf.FDwfEnum(c_int(0), byref(cdevices))
print("Number of Devices: " + str(cdevices.value))

if cdevices.value == 0:
    print("no device detected")
    quit()

# Prevent temperature drift
dwf.FDwfParamSet(DwfParamOnClose, c_int(0))  # 0 = run, 1 = stop, 2 = shutdown

print("Opening first device")
hdwf = c_int()
dwf.FDwfDeviceOpen(c_int(0), byref(hdwf))

if hdwf.value == hdwfNone.value:
    print("failed to open device")
    quit()

# Piezo tip approach

# set up analog IO channel nodes
IsEnabled = c_bool()
# enable positive supply
dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(0), c_int(0), c_double(True)) 
# set voltage to 600 mV
dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(0), c_int(1), c_double(0.6))

# Set up the analog input channel
dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(1.0))  # Set the voltage range to 1V

# in case of over-current condition the supplies are disabled
dwf.FDwfAnalogIOEnableStatus(hdwf, byref(IsEnabled))
if not IsEnabled:
    #re-enable supplies
    print("Power supplies stopped. Restarting...")
    dwf.FDwfAnalogIOEnableSet(hdwf, c_int(False)) 
    dwf.FDwfAnalogIOEnableSet(hdwf, c_int(True))

# Set up the sample rate and buffer size
dwf.FDwfAnalogInFrequencySet(hdwf, c_double(SAMPLING_RATE_AP))  # Set the sample rate to 8388608 samples per second
dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(BUFFER_SIZE))  # Set the buffer size to 8192 samples

# Motor tip approach

# Start the acquisition
print("Starting acquisition...")
dwf.FDwfAnalogInConfigure(hdwf, c_int(1), c_int(1))

# the meat
try:
    i = 0
    avg_voltage = 0.0

    while avg_voltage < 0.01:  # 10 mV
        for pin in range(0, len(motor_pins)):
            GPIO.output(motor_pins[pin], step_sequence[motor_step_counter][pin])

        if direction == True:
            motor_step_counter = (motor_step_counter - 1) % 8
        elif direction == False:
            motor_step_counter = (motor_step_counter + 1) % 8
        else:
            # defensive programming
            print("uh oh... direction should *always* be either True or False")
            cleanup()
            exit(1)

        time.sleep(step_sleep)
        i += 1

        if i % 1 == 0:  # read average voltage every step
            # Wait for the acquisition to complete
            while True:
                sts = c_byte()
                dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
                if sts.value == DwfStateDone.value:
                    break
                time.sleep(0.5)

            # Read the acquired data
            data = np.zeros(BUFFER_SIZE, dtype=np.float64)
            dwf.FDwfAnalogInStatusData(hdwf, c_int(0), data.ctypes.data_as(POINTER(c_double)), c_int(BUFFER_SIZE))
            avg_voltage = np.average(data)
            #print("Average Voltage: " + str(avg_voltage))


    # disable positive supply
    dwf.FDwfAnalogIOChannelNodeSet(hdwf, c_int(0), c_int(0), c_double(True)) 

# End of tip approach

except KeyboardInterrupt:
    cleanup()
    exit(1)

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

# Motor tip retraction

direction = False

try:
    for i in range(i):
        for pin in range(0, len(motor_pins)):
            GPIO.output( motor_pins[pin], step_sequence[motor_step_counter][pin])
        if direction==False:
            motor_step_counter = (motor_step_counter + 1) % 8
        else: # defensive programming
            print("uh oh... direction should *always* be either True or False")
            cleanup()
            exit(1)
        time.sleep(step_sleep)

except KeyboardInterrupt:
    cleanup()
    exit(1)

# End of motor tip retraction

# Make into numpy array and reshape to (128,128)
a = np.array(rg).reshape((128,128))

# Reverse alternate rows
for r in range(1,128,2):
   a[r] = a[r][::-1]

#Generate image
plt.imsave('/home/pi/mystm_pic.tiff', a, cmap='gray') # file location

plt.imshow(a, cmap='afmhot')

plt.show()