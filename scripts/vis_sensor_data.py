import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Load the .npy file
# Replace 'sensor_data.npy' with the actual filename
file_path = 'data/2025-02-20_FuMu-RM_sensor_data.npy'
data = np.load(file_path, allow_pickle=True)

# Extract time and sensor columns based on the header
header = [
    'Timestamp', 'Runtime', 'B0101', 'B0201', 'B0102', 'B0202', 'B0103', 'B0203',
    'B0401', 'B0402', 'B0403', 'B0404', 'B0104', 'B0204'
]

# Map header names to indices for easy reference
header_indices = {name: idx for idx, name in enumerate(header)}

# Extract columns
timestamps_ = data[:, header_indices['Timestamp']]
timestamps = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamps_]

runtime    = data[:, header_indices['Runtime']].astype(np.float16)

B0101 = data[:, header_indices['B0101']].astype(np.float16) # temperature
B0201 = data[:, header_indices['B0201']].astype(np.float16) # temperature
B0102 = data[:, header_indices['B0102']].astype(np.float16) # pH
B0202 = data[:, header_indices['B0202']].astype(np.float16) # pH
B0103 = data[:, header_indices['B0103']].astype(np.float32) # EC
B0203 = data[:, header_indices['B0203']].astype(np.float32) # EC
B0401 = data[:, header_indices['B0401']].astype(np.float16) # rel. Humidity (downstream evap)
B0402 = data[:, header_indices['B0402']].astype(np.float16) # rel. Humidity (upstream evap)
B0403 = data[:, header_indices['B0403']].astype(np.float16) # temperature (downstream evap)
B0404 = data[:, header_indices['B0404']].astype(np.float16) # temperature (upstream evap)
B0104 = data[:, header_indices['B0104']].astype(np.float16) # level stabilizer tank
B0204 = data[:, header_indices['B0204']].astype(np.float16) # level evaporator dummy tank

# Plots
# ---------------------
plt.close('all')

# temperature sensors
fig = plt.figure(1)

ax = fig.add_subplot(111)
ax.plot(timestamps, B0101, label='B0101')
ax.plot(timestamps, B0201, label='B0201')
ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Auto adjust ticks
#ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Show time only
ax.set_xlabel('time [h]')
ax.set_ylabel('temp [°C]')
ax.set_title('Temperature')
plt.legend()
plt.xticks(rotation=45)
plt.grid()

# pH sensors
fig = plt.figure(2)

ax = fig.add_subplot(111)
ax.plot(timestamps, B0102, label='B0102')
ax.plot(timestamps, B0202, label='B0202')
ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Auto adjust ticks
#ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Show time only
ax.set_xlabel('time [h]')
ax.set_ylabel('pH')
ax.set_title('pH')
plt.legend()
plt.xticks(rotation=45)
plt.grid()

file_name = file_path.replace('data/', '').replace('.npy', '_pH.png')
plt.savefig(f"figures/{file_name}", dpi=300)

# EC sensors
fig = plt.figure(3)

ax = fig.add_subplot(111)
ax.plot(timestamps, B0103, label='B0103')
ax.plot(timestamps, B0203, label='B0203')
ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Auto adjust ticks
#ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Show time only
ax.set_xlabel('time [h]')
ax.set_ylabel('EC [mS]')
ax.set_title('EC')
plt.legend()
plt.xticks(rotation=45)
plt.grid()

file_name = file_path.replace('data/', '').replace('.npy', '_EC.png')
plt.savefig(f"figures/{file_name}", dpi=300)


# humidity sensors
fig = plt.figure(4)

# Subplot 211: B0401 and B0402 vs. Time (Relative Humidity)
ax = fig.add_subplot(211)
ax.plot(timestamps, B0401, label='B0401', color='blue')
ax.plot(timestamps, B0402, label='B0402', color='green')
ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Auto adjust ticks
#ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Show time only
ax.set_xlabel('time [h]')
ax.set_ylabel('rel. hum. [%]')
ax.set_title('Relative Humidity')
plt.legend()
plt.xticks(rotation=45)
plt.grid(True)


# Subplot 212: B0403 and B0404 vs. Time (Relative Humidity)
ax = fig.add_subplot(212)
ax.plot(timestamps, B0403, label='B0403', color='blue')
ax.plot(timestamps, B0404, label='B0404', color='green')
ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Auto adjust ticks
#ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Show time only
ax.set_xlabel('time [h]')
ax.set_ylabel('temp. [°C]')
ax.set_title('Temperature')
plt.legend()
plt.xticks(rotation=45)
plt.grid(True)


# level sensors
fig = plt.figure(5)

ax = fig.add_subplot(111)
ax.plot(timestamps, B0104, label='B0104')
ax.plot(timestamps, B0204, label='B0204')
ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Auto adjust ticks
#ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Show time only
ax.set_xlabel('time [h]')
ax.set_ylabel('liquid level [L]')
ax.set_title('Liquid Level')
plt.legend()
plt.xticks(rotation=45)
plt.grid()

file_name = file_path.replace('data/', '').replace('.npy', '_liquid_level.png')
plt.savefig(f"figures/{file_name}", dpi=300)


# Adjust layout and show plots
plt.tight_layout()
plt.show()
