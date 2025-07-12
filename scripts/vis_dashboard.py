import numpy as np
import re
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

# Path to the data directory
data_dir = Path(__file__).resolve().parent.parent / 'data'

# Get all .csv files
csv_files = list(data_dir.glob('*_data.csv'))

# Extract dates from file names and build a mapping
def extract_date_from_filename(path):
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return datetime.strptime(match.group(1), "%Y-%m-%d") if match else None

file_date_map = {extract_date_from_filename(f): f for f in csv_files}

# Prompt the user for date input
date_input = input("Enter date or range (e.g., '2025-06-23' or '2025-06-23 to 2025-06-25'): ").strip()

# Parse input
if "to" in date_input:
    start_str, end_str = map(str.strip, date_input.split("to"))
    start_date = datetime.strptime(start_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_str, "%Y-%m-%d")
    selected_files = [f for date, f in file_date_map.items() if start_date <= date <= end_date]
else:
    single_date = datetime.strptime(date_input, "%Y-%m-%d")
    selected_files = [f for date, f in file_date_map.items() if date == single_date]

if not selected_files:
    print("No files found for the given date(s).")
    exit()

print(f"Selected files:\n{[str(f) for f in selected_files]}")

# set data filter
def filter_data(df, tag_type_A=None, tag_name_A=None, tag_type_B=None, tag_name_B=None):
    if tag_name_A:
        df = df[df[tag_type_A] == tag_name_A]

    if tag_name_B:
        df = df[df[tag_type_B] == tag_name_B]

    return df 

# Load and concatenate data
DF = []

for file in selected_files:
    df = pd.read_csv(file, delimiter=',', header=0)
    df.columns = ['timestamp', 'runtime', 'machine_id', 'io_type', 'device_type',
                  'name', 'address', 'state', 'value', 'value_aux1', 'value_aux2']
    
    DF.append(df)

# Concatenate all selected sensor data
DF = pd.concat(DF, ignore_index=True)
DF["timestamp"]  = pd.to_datetime(DF["timestamp"]) # for nicer plotting results
DF["value"]      = pd.to_numeric(DF['value'], errors='coerce')
DF["value_aux1"] = pd.to_numeric(DF['value_aux1'], errors='coerce')

# Filter data frame - Sensor data
EVENT = filter_data(DF, 'io_type', 'Event').sort_values(by='timestamp')
CPU   = filter_data(DF, 'io_type', 'CPU', 'name', 'CPU-Temp').sort_values(by='timestamp')
B0001 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0001').sort_values(by='timestamp')
B0101 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0101').sort_values(by='timestamp')
B0111 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0111').sort_values(by='timestamp')
B0102 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0102').sort_values(by='timestamp')
B0103 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0103').sort_values(by='timestamp')
B0201 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0201').sort_values(by='timestamp')
B0202 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0202').sort_values(by='timestamp')
B0203 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0203').sort_values(by='timestamp')
B0301 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0301').sort_values(by='timestamp')
B0303 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0303').sort_values(by='timestamp')

# Filter data frame - Actuator data
M0101 = filter_data(DF, 'io_type', 'Actuator', 'name', 'M0101').sort_values(by='timestamp')
M0102 = filter_data(DF, 'io_type', 'Actuator', 'name', 'M0102').sort_values(by='timestamp')
M0111 = filter_data(DF, 'io_type', 'Actuator', 'name', 'M0111').sort_values(by='timestamp')
M0112 = filter_data(DF, 'io_type', 'Actuator', 'name', 'M0112').sort_values(by='timestamp')
M0201 = filter_data(DF, 'io_type', 'Actuator', 'name', 'M0201').sort_values(by='timestamp')
M0202 = filter_data(DF, 'io_type', 'Actuator', 'name', 'M0202').sort_values(by='timestamp')
M0203 = filter_data(DF, 'io_type', 'Actuator', 'name', 'M0203').sort_values(by='timestamp')
M0204 = filter_data(DF, 'io_type', 'Actuator', 'name', 'M0204').sort_values(by='timestamp')
M0301 = filter_data(DF, 'io_type', 'Actuator', 'name', 'M0301').sort_values(by='timestamp')


#---------------------------
# CALCULATIONS
#---------------------------

# consider only larger than detection threshold
detect_threshold = .1
NZ_EVENT = EVENT[EVENT["value_aux1"] > detect_threshold]

# Step 2: Keep only rows where the value differs from the previous row
NZ_EVENT = NZ_EVENT[NZ_EVENT["value_aux1"] != NZ_EVENT["value_aux1"].shift()]

# extract number of events over considered period and average inflow volume
num_events = len(NZ_EVENT)
avg_value = NZ_EVENT["value_aux1"].mean()


#---------------------------
# PLOTTING
#---------------------------
plt.close('all')

# SENSORS
fig = plt.figure(1, figsize=[16, 20])

# liquid level collection tube
ax1 = fig.add_subplot(711)
ax1.plot(B0111["timestamp"], B0111["value"]*1000, c='black')
ax1.text(0.95, 0.95, f'N={num_events}\nAvg={avg_value:.1f}',
        transform=ax1.transAxes, fontsize=10,
        verticalalignment='top', horizontalalignment='right',
        bbox=dict(facecolor='white', alpha=0.5))
ax1.set_title("liquid level collection tube")
ax1.set_ylim(0, 700)
ax1.set_ylabel("V [ml]")
ax1.tick_params(axis='x', labelbottom=False)
ax1.legend()

# # events
# ax2 = fig.add_subplot(712, sharex=ax1)
# ax2.scatter(NZ_EVENT["timestamp"], NZ_EVENT["value_aux1"]*1000, c='black', s=10)
# ax2.text(0.95, 0.95, f'N={num_events}\nAvg={avg_value:.1f}',
#         transform=ax2.transAxes, fontsize=10,
#         verticalalignment='top', horizontalalignment='right',
#         bbox=dict(facecolor='white', alpha=0.5))
# ax2.set_title("Inflow events")
# ax2.set_ylim(0, 700)
# ax2.set_xlim(B0001["timestamp"].min(), B0001["timestamp"].max())
# ax2.set_ylabel("V [ml]")
# ax2.tick_params(axis='x', labelbottom=False)

# liquid level
ax3 = fig.add_subplot(712)
low_lim_S, up_lim_S = 15, 40.3 
low_lim_E = 12
lw = 1.0
S_ax, = ax3.plot(B0101["timestamp"], B0101["value"], label="Stabilizor")
S_color = S_ax.get_color()
ax3.plot(B0101["timestamp"], low_lim_S*np.ones_like(B0101["value"]), '--', color = S_color, label="Stab. lower limit", linewidth=lw)
ax3.plot(B0101["timestamp"],  up_lim_S*np.ones_like(B0101["value"]), '-.', color = S_color, label="Stab. upper limit", linewidth=lw)
E_ax, = ax3.plot(B0201["timestamp"], B0201["value"], label="Evaporator")
E_color = E_ax.get_color()
ax3.plot(B0201["timestamp"], low_lim_E*np.ones_like(B0101["value"]), '--', color = E_color, label="Evap. lower limit", linewidth=lw)
ax3.set_title("Liquid level")
ax3.set_ylim(0, 50)
ax3.set_ylabel("V [l]")
ax3.tick_params(axis='x', labelbottom=False)
ax3.legend()

# ph
ax4 = fig.add_subplot(713)
ax4.plot(B0102["timestamp"], B0102["value"], label="Stabilizor")
ax4.plot(B0202["timestamp"], B0202["value"], label="Evaporator")
ax4.plot(B0202["timestamp"], 11.5*np.ones_like(B0202["value"]), 'k--', label="ph = 11.5", linewidth=lw)
ax4.set_title("pH")
ax4.set_ylim(0, 14)
ax4.set_ylabel("pH")
ax4.tick_params(axis='x', labelbottom=False)
ax4.legend()

# temperature (liquid)
ax5 = fig.add_subplot(714)
ax5.plot(B0103["timestamp"], B0103["value"], label="Stabilizor")
ax5.plot(B0203["timestamp"], B0203["value"], label="Evaporator")
ax5.set_title("Temperature (liquid)")
ax5.set_ylim(20, 40)
ax5.set_ylabel("T [°C]")
ax5.tick_params(axis='x', labelbottom=False)
ax5.legend()

# # rel. humidity (process air)
# ax = fig.add_subplot(815)
# ax.plot(B0301["timestamp"], B0301["value"], label="upstream dehum.")
# ax.plot(B0303["timestamp"], B0303["value"], label="downstream dehum.")
# ax.set_title("rel. humidity (process air)")
# ax.set_ylim(0, 100)
# ax.set_ylabel("RH [%]")
# ax.tick_params(axis='x', labelbottom=False)
# ax.legend()

# # temperature (process air)
# ax = fig.add_subplot(816)
# ax.plot(B0301["timestamp"], B0301["value_aux1"], color=[0.5, 0.2, 0.5], label="upstream dehum.")
# ax.plot(B0303["timestamp"], B0303["value_aux1"], color=[0.2, 0.2, 0.5], label="downstream dehum.")
# ax.set_title("rel. humidity (process air)")
# ax.set_ylim(15, 40)
# ax.set_ylabel("T [°C]")
# ax.tick_params(axis='x', labelbottom=False)
# ax.legend()

# system current draw()
ax6 = fig.add_subplot(715)
ax6.plot(B0001["timestamp"], B0001["value"], color=[0.5, 0.5, 0.5])
ax6.set_title("System current draw")
ax6.set_ylim(0, 5)
ax6.set_ylabel("I [A]")
ax6.tick_params(axis='x', labelbottom=False)

# CPU-Temp
ax7 = fig.add_subplot(716)
ax7.plot(CPU["timestamp"], CPU["value"], 'k')
ax7.set_title("CPU-temperature")
ax7.set_ylim(0, 80)
ax7.set_ylabel("T [°C]")
ax7.set_xlabel("time")


plt.xticks(rotation=45)
plt.tight_layout()

# Path to the data directory
figure_dir = Path(__file__).resolve().parent.parent / 'figures'
filename = date_input + '_sensors_dashboard.png'
file_path = figure_dir / filename
plt.savefig(file_path, dpi=300)


# ACTUATORS
fig = plt.figure(2, figsize=[16, 16])

# events
ax = fig.add_subplot(911)
ax.plot(M0101["timestamp"], M0101["state"])
ax.set_title("Stabilizer stirrer (M0101)")
ax.set_ylim(0, 1)
ax.tick_params(axis='x', labelbottom=False)

ax = fig.add_subplot(912)
ax.plot(M0102["timestamp"], M0102["state"])
ax.set_title("Evaporator feed pump (M0102)")
ax.set_ylim(0, 1)
ax.tick_params(axis='x', labelbottom=False)

ax = fig.add_subplot(913)
ax.plot(M0111["timestamp"], M0111["state"])
ax.set_title("Collection tube drain pump (M0111)")
ax.set_ylim(0, 1)
ax.tick_params(axis='x', labelbottom=False)

ax = fig.add_subplot(914)
ax.plot(M0112["timestamp"], M0112["state"])
ax.set_title("Collection tube flush pump (M0112)")
ax.set_ylim(0, 1)
ax.tick_params(axis='x', labelbottom=False)

ax = fig.add_subplot(915)
ax.plot(M0201["timestamp"], M0201["state"])
ax.set_title("Evaporator disc motor (M0201)")
ax.set_ylim(0, 1)
ax.tick_params(axis='x', labelbottom=False)

ax = fig.add_subplot(916)
ax.plot(M0202["timestamp"], M0202["state"])
ax.set_title("Evaporator screw motor (M0202)")
ax.set_ylim(0, 1)
ax.tick_params(axis='x', labelbottom=False)

ax = fig.add_subplot(917)
ax.plot(M0203["timestamp"], M0203["state"])
ax.set_title("Concentrate sludge pump (M0203)")
ax.set_ylim(0, 1)
ax.tick_params(axis='x', labelbottom=False)

ax = fig.add_subplot(918)
ax.plot(M0204["timestamp"], M0204["state"])
ax.set_title("Evaporator fans (M0401)")
ax.set_ylim(0, 1)
ax.tick_params(axis='x', labelbottom=False)

ax = fig.add_subplot(919)
ax.plot(M0301["timestamp"], M0301["state"])
ax.set_title("Dehumidifier compressor (M0301)")
ax.set_ylim(0, 1)
ax.set_xlabel("time")

plt.xticks(rotation=45)
plt.tight_layout()

# Path to the data directory
figure_dir = Path(__file__).resolve().parent.parent / 'figures'
filename = date_input + '_actuators_dashboard.png'
file_path = figure_dir / filename
plt.savefig(file_path, dpi=300)


plt.show()


