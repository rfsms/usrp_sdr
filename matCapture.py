#!/usr/bin/env python

import uhd
import json
import numpy as np
import scipy.io
from datetime import datetime, timezone
import time
import random

# Load configuration from config.json
config_path = 'Tools/config.json'
with open(config_path, 'r') as f:
    config = json.load(f)

# # Function to calculate the size of complex, I and Q samples
# def sample_size_check():
#     complex_sample_size = np.dtype(np.complex64).itemsize
#     float_sample_size = np.dtype(np.float32).itemsize
#     return complex_sample_size, float_sample_size

# Parameters
args = f"addr={config['sdrIP']}"
samp_rate = config['srat']
freq = config['cf_MHz']
capture_duration = config['measTime']
pause_duration = 5

satellite_name = "NOAA19"

# Print the configuration values to ensure they are as expected
print(f"SDR IP: {config['sdrIP']}")
print(f"Sample Rate: {samp_rate / 1e6} Msps")
print(f"Center Frequency: {freq / 1e6} MHz")
print(f"Capture Duration: {capture_duration * 1000} ms")
print(f"Pause Duration: {pause_duration} seconds")

# Create USRP object
usrp = uhd.usrp.MultiUSRP(args)

# Set sample rate and frequency
usrp.set_rx_rate(samp_rate) 
usrp.set_rx_freq(freq) 
usrp.set_rx_gain(20)  # Adjust as neccesary

# Create a receive streamer
stream_args = uhd.usrp.StreamArgs("fc32", "fc32")

# Allocate buffer for samples
buffer_size = int(samp_rate * capture_duration)
buffer = np.zeros((buffer_size,), dtype=np.complex64)

# Function to capture data
def capture_data(file_name):
    try:
        rx_streamer = usrp.get_rx_stream(stream_args)

        # Issue stream command to start continuous streaming
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
        rx_streamer.issue_stream_cmd(stream_cmd)

        # Receive samples
        metadata = uhd.types.RXMetadata()
        num_samps = rx_streamer.recv(buffer, metadata, timeout=5.0)

        # Stop streaming
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        rx_streamer.issue_stream_cmd(stream_cmd)

        if num_samps > 0:
            # Separate I and Q data, convert to double precision, and save it to .mat format
            #Investagate keeping this as single (32bit) so we can keep the filesize smaller on server
            # I_Data = np.real(buffer[:num_samps]).reshape(1, -1)  # will be a 32bit float for 4 bytes
            # Q_Data = np.imag(buffer[:num_samps]).reshape(1, -1)  # will be another 32bit float for 4 bytes
            I_Data = np.real(buffer[:num_samps]).reshape(1, -1).astype(np.float64)
            Q_Data = np.imag(buffer[:num_samps]).reshape(1, -1).astype(np.float64)
            scipy.io.savemat(file_name, {'I_Data': I_Data, 'Q_Data': Q_Data})
                             
            ''' Iteration of a sample .mat file with keys
                dict_keys(['__header__', '__version__', '__globals__', 'I_Data', 'Q_Data'])
                Key: I_Data
                Type: <class 'numpy.ndarray'>
                Shape: (1, 3000001)
                Content: [[ 3.41609921e-05 -4.50716179e-05  5.74606429e-06 ... -3.84385094e-05
                -2.49702480e-05  6.21176150e-05]]

                Key: Q_Data
                Type: <class 'numpy.ndarray'>
                Shape: (1, 3000001)
                Content: [[-2.64930040e-05 -1.00728612e-05 -9.18089063e-06 ... -4.86394993e-06
                -3.64180232e-06 -5.52036145e-05]]
            '''

            print(f"Saved {num_samps} samples to {file_name}")
        else:
            print("No samples received or receive timeout.")
    except Exception as e:
        print(f"Error during capture: {e}")

# Perform 3 captures with a pause of 5 seconds between each
for i in range(3):
    az = random.randrange(0,360)
    el = random.randrange(0,180)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_UTC')
    file_name = f"{timestamp}_{satellite_name}_AZ_{az}_EL_{el}.mat"
    print(f"Starting capture {i + 1}")
    capture_data(file_name)
    if i < 2:  # lol...dont pause after the last capture
        print(f"Pausing for {pause_duration} seconds")
        time.sleep(pause_duration)

# # Load the saved .mat files to verify their content
# for i in range(3):
#     timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_UTC')
#     file_name = f"{timestamp}_{satellite_name}_AZ_{az}_EL_{el}.mat"
#     mat_data = scipy.io.loadmat(file_name)
#     print(f"Content of {file_name}:")
#     print(mat_data.keys())

#     # Iterate through the items to inspect their format and content
#     for key in mat_data:
#         if not key.startswith('__'):  # Skip the metadata
#             print(f"Key: {key}")
#             print(f"Type: {type(mat_data[key])}")
#             print(f"Shape: {mat_data[key].shape}")
#             print(f"Content: {mat_data[key]}\n")