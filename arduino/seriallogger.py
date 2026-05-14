import serial
import csv
import time

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Serial settings
PORT = 'COM3'
BAUD = 9600

# Output CSV file
OUTPUT_FILE = 'temperature_data.csv'

# Open serial connection
ser = serial.Serial(PORT, BAUD)

# Wait for Arduino reset
time.sleep(2)

# Store collected data
times = []
temps = []

# Save incoming serial data
with open(OUTPUT_FILE, 'w', newline='') as file:

  writer = csv.writer(file)

  while True:

    try:
      line = ser.readline().decode().strip()

      print(line)

      row = line.split(',')

      # Skip invalid rows
      if len(row) != 2:
        continue

      # Save CSV header
      if row[0] == "Time":
        writer.writerow(row)
        continue

      t = float(row[0])
      temp = float(row[1])

      times.append(t)
      temps.append(temp)

      writer.writerow([t, temp])

    # Stop recording manually
    except KeyboardInterrupt:
      break

    # Ignore bad serial data
    except:
      continue

# Close serial port
ser.close()

# Convert lists to arrays
time_data = np.array(times)
temp_data = np.array(temps)

# Calculate sample spacing
dt = time_data[1] - time_data[0]
fs = 1 / dt

# Remove average temperature
temp_detrended = temp_data - np.mean(temp_data)

# Perform FFT analysis
N = len(temp_data)

fft_vals = np.fft.fft(temp_detrended)
fft_freq = np.fft.fftfreq(N, d=dt)

# Keep positive frequencies
positive = fft_freq >= 0

freqs = fft_freq[positive]
magnitude = np.abs(fft_vals[positive]) / N

# Save FFT results
freq_df = pd.DataFrame({
  "Frequency": freqs,
  "Magnitude": magnitude
})

freq_df.to_csv("frequency_data.csv", index=False)

# Apply moving average filter
window = 5

smoothed = np.convolve(temp_data, np.ones(window) / window, mode='same')

# Calculate temperature change rate
temp_rate = np.diff(temp_data) / dt
rate_time = time_data[:-1]

# Plot temperature vs time
plt.figure(figsize=(10, 5))

plt.plot(time_data, temp_data)

plt.title("Temperature vs Time")
plt.xlabel("Time (s)")
plt.ylabel("Temperature (°C)")
plt.grid(True)

# Plot FFT magnitude
plt.figure(figsize=(10, 5))

plt.plot(freqs, magnitude)

plt.title("Magnitude vs Frequency")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")
plt.grid(True)

# Plot smoothed signal
plt.figure(figsize=(10, 5))

plt.plot(time_data, temp_data, label='Original')
plt.plot(time_data, smoothed, label='Smoothed')

plt.title("Smoothed Temperature Signal")
plt.xlabel("Time (s)")
plt.ylabel("Temperature (°C)")

plt.legend()
plt.grid(True)

# Plot temperature histogram
plt.figure(figsize=(8, 5))

plt.hist(temp_data, bins=15)

plt.title("Histogram of Temperature Readings")
plt.xlabel("Temperature (°C)")
plt.ylabel("Count")

# Plot temperature change rate
plt.figure(figsize=(10, 5))

plt.plot(rate_time, temp_rate)

plt.title("Temperature Change Rate vs Time")
plt.xlabel("Time (s)")
plt.ylabel("dT/dt (°C/s)")
plt.grid(True)

# Display all plots
plt.show()