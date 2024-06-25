#!/usr/bin/env python

import uhd
import numpy as np

# Parameters
samp_rate = 20e6  # Sample rate in sps
center_freq = 1702.5e6  # Center frequency in Hz
gain = 20  # Gain in dB
capture_duration = 0.160e-3  # Capture duration in seconds (0.160ms)

# Calculate the number of samples to capture for 0.160ms
num_samps = int(samp_rate * capture_duration)

# Create USRP object
usrp = uhd.usrp.MultiUSRP()

# Set sample rate and frequency
usrp.set_rx_rate(samp_rate)
usrp.set_rx_freq(uhd.libpyuhd.types.tune_request(center_freq))
usrp.set_rx_gain(gain)

# Print the current configuration settings
print(f"Actual Sample Rate: {usrp.get_rx_rate() / 1e6} Msps")
print(f"Actual Center Frequency: {usrp.get_rx_freq() / 1e6} MHz")
print(f"Actual RX Gain: {usrp.get_rx_gain()} dB")

# Set up the stream and receive buffer
st_args = uhd.usrp.StreamArgs("fc32", "sc16")
st_args.channels = [0]
metadata = uhd.types.RXMetadata()
streamer = usrp.get_rx_stream(st_args)
recv_buffer = np.zeros((1, num_samps), dtype=np.complex64)


# Function to update the plot
def update(frame):
    # Start streaming
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)

    # Receive samples
    samples = np.zeros(num_samps, dtype=np.complex64)
    for i in range(num_samps // recv_buffer.shape[1]):
        streamer.recv(recv_buffer, metadata)
        samples[i * recv_buffer.shape[1]:(i + 1) * recv_buffer.shape[1]] = recv_buffer[0]

    # Stop streaming
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
    streamer.issue_stream_cmd(stream_cmd)

    # Perform FFT and update plot
    fft_result = np.fft.fftshift(np.fft.fft(samples))
    freq_axis = np.fft.fftshift(np.fft.fftfreq(num_samps, 1 / samp_rate))


