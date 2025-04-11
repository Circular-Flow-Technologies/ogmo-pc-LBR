import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from src.utils import get_file_path

# Load the .npy file
folder = "data"
file_name = "2025-04-10_sensor_data_NH-25-001.npy"
file_path = get_file_path(folder, file_name)
data = np.load(file_path, allow_pickle=True)

# Extract time and sensor columns based on the header
header = [
    'Timestamp', 'Runtime', 'B0001', 'B0101', 'B0111', 'B0102', 'B0201', 'B0202', 'B0203', 'B0401'
]

# Map header names to indices for easy reference
header_indices = {name: idx for idx, name in enumerate(header)}

# Extract columns
timestamps_ = data[:, header_indices['Timestamp']]
timestamps = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamps_]

runtime    = data[:, header_indices['Runtime']].astype(np.float16)

B0001 = data[:, header_indices['B0001']].astype(np.float16) # current sensor
B0101 = data[:, header_indices['B0101']].astype(np.float16) # level stabilizer tank
B0111 = data[:, header_indices['B0111']].astype(np.float16) # level collector tube
B0201 = data[:, header_indices['B0201']].astype(np.float16) # level evaporator
B0102 = data[:, header_indices['B0102']].astype(np.float16) # pH
B0202 = data[:, header_indices['B0202']].astype(np.float16) # pH
# B0103 = data[:, header_indices['B0103']].astype(np.float32) # temperature
B0203 = data[:, header_indices['B0203']].astype(np.float32) # temperature
# B0301 = data[:, header_indices['B0301']].astype(np.float16) # rel. Humidity (downstream evap)
# B0302 = data[:, header_indices['B0302']].astype(np.float16) # temperature (downstream evap)
# B0303 = data[:, header_indices['B0303']].astype(np.float16) # rel. Humidity (upstream evap)
# B0304 = data[:, header_indices['B0304']].astype(np.float16) # temperature (upstream evap)
B0401 = data[:, header_indices['B0401']].astype(np.float16) # level switch stabilizer tank

# Plots
# ---------------------
plt.close('all')

# level sensors
fig = plt.figure(1)

ax = fig.add_subplot(111)
ax.plot(timestamps, B0101, label='B0101')
ax.plot(timestamps, B0201, label='B0201')
ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Auto adjust ticks
#ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Show time only
ax.set_xlabel('time [h]')
ax.set_ylabel('volume [L]')
ax.set_title('Level')
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

# file_name = file_path.replace('data/', '').replace('.npy', '_pH.png')
# plt.savefig(f"figures/{file_name}", dpi=300)

# temperature sensors
fig = plt.figure(3)

ax = fig.add_subplot(111)
# ax.plot(timestamps, B0103, label='B0103')
ax.plot(timestamps, B0203, label='B0203')
ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # Auto adjust ticks
#ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))  # Show time only
ax.set_xlabel('time [h]')
ax.set_ylabel('temperature [°C]')
ax.set_title('Temperature')
plt.legend()
plt.xticks(rotation=45)
plt.grid()

# file_name = file_path.replace('data/', '').replace('.npy', '_T.png')
# plt.savefig(f"figures/{file_name}", dpi=300)


# Adjust layout and show plots
plt.tight_layout()
plt.show()
