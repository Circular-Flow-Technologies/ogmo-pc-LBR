import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import re

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
DF["timestamp"] = pd.to_datetime(DF["timestamp"]) # for nicer plotting results

# Filter data frame
EVENT = filter_data(DF, 'io_type', 'Event')
CPU   = filter_data(DF, 'io_type', 'CPU', 'name', 'CPU-Temp')
B0101 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0101')
B0102 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0102')
B0103 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0103')
B0201 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0201')
B0202 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0202')
B0203 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0203')
B0301 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0301')
B0303 = filter_data(DF, 'io_type', 'Sensor', 'name', 'B0303')



#---------------------------
# PLOTTING
#---------------------------
plt.close('all')

# SENSORS
fig = plt.figure(1, figsize=[8, 20])

# events
ax = fig.add_subplot(711)
ax.scatter(EVENT["timestamp"], EVENT["value"]*1000)
ax.set_title("Inflow events")
ax.set_ylim(0, 500)
ax.set_yticks(np.linspace(0, 500, 10))
ax.set_ylabel("V [ml]")

# liquid level
ax = fig.add_subplot(712)
ax.plot(B0101["timestamp"], B0101["value"], label="Stabilizor")
ax.plot(B0201["timestamp"], B0201["value"], label="Evaporator")
ax.set_title("Liquid level")
ax.set_ylim(0, 50)
ax.set_yticks(np.linspace(0, 50, 10))
ax.set_ylabel("V [l]")
ax.legend()

# ph
ax = fig.add_subplot(713)
ax.plot(B0102["timestamp"], B0102["value"], label="Stabilizor")
ax.plot(B0202["timestamp"], B0202["value"], label="Evaporator")
ax.set_title("pH")
ax.set_ylim(0, 14)
ax.set_ylabel("pH")
ax.legend()

# temperature (liquid)
ax = fig.add_subplot(714)
ax.plot(B0103["timestamp"], B0103["value"], label="Stabilizor")
ax.plot(B0203["timestamp"], B0203["value"], label="Evaporator")
ax.set_title("Temperature (liquid)")
ax.set_ylim(15, 30)
ax.set_ylabel("T [°C]")
ax.legend()

# rel. humidity (process air)
ax = fig.add_subplot(715)
ax.plot(B0301["timestamp"], B0301["value"], label="upstream dehum.")
ax.plot(B0303["timestamp"], B0303["value"], label="downstream dehum.")
ax.set_title("rel. humidity (process air)")
ax.set_ylim(0, 100)
ax.set_ylabel("RH [%]")
ax.legend()

# temperature (process air)
ax = fig.add_subplot(716)
ax.plot(B0301["timestamp"], B0301["value_aux1"], label="upstream dehum.")
ax.plot(B0303["timestamp"], B0303["value_aux1"], label="downstream dehum.")
ax.set_title("rel. humidity (process air)")
ax.set_ylim(15, 40)
ax.set_ylabel("T [°C]")
ax.legend()

# CPU-Temp
ax = fig.add_subplot(717)
ax.plot(CPU["timestamp"], CPU["value"], 'k')
ax.set_title("CPU-temperature")
ax.set_ylim(0, 80)
ax.set_ylabel("T [°C]")
ax.set_xlabel("time")


plt.xticks(rotation=45)
plt.tight_layout()

# Path to the data directory
figure_dir = Path(__file__).resolve().parent.parent / 'figures'
filename = date_input + '_sensors_dashboard.png'
file_path = figure_dir / filename
plt.savefig(file_path, dpi=300)

plt.show()


