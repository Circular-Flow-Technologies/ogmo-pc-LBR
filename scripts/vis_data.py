import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
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
def filter_data(df, tag_type, tag_name=None):
    if id:
        df = df[df[tag_type] == tag_name]
    return df 

example_df = pd.read_csv(selected_files[0], delimiter=',', header=0)
example_df.columns = ['timestamp', 'runtime', 'machine_id', 'io_type', 'device_type',
                      'name', 'address', 'state', 'value', 'value_aux1', 'value_aux2']

io_types = example_df['io_type'].unique()
io_type = input(f"Select an io-type from this list {io_types}: ").strip()
example_df = filter_data(example_df, 'io_type', io_type)

device_names = example_df['name'].unique()
device_name = input(f"Select an io-type from this list {device_names}: ").strip()
example_df = filter_data(example_df, 'name', device_name)

# Load and concatenate data
DF = []

for file in selected_files:
    df = pd.read_csv(file, delimiter=',', header=0)
    df.columns = ['timestamp', 'runtime', 'machine_id', 'io_type', 'device_type',
                  'name', 'address', 'state', 'value', 'value_aux1', 'value_aux2']
    
    df = filter_data(df, 'io_type', io_type)
    df = filter_data(df, 'name', device_name)
    
    DF.append(df)

# Concatenate all selected sensor data
df = pd.concat(DF, ignore_index=True)

# for nicer plotting results
df["timestamp"]  = pd.to_datetime(df["timestamp"]) 
df["value"]      = pd.to_numeric(df['value'], errors='coerce')
df["value_aux1"] = pd.to_numeric(df['value_aux1'], errors='coerce')
df               = df.sort_values(by='timestamp')

###############
# CALCULATION #
###############

# linear fit to sample point for selected period

# --- Define time window ---
# Pick a specific start day (e.g. July 10, 2025 at 12:00)
start_time = pd.Timestamp('2025-07-06 00:00:00')
end_time   = pd.Timestamp('2025-07-06 18:00:00')

# Filter the DataFrame for the desired time window
df_window = df[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]

# linear regression
x = df_window['timestamp'].astype(np.int64) / 1e9  # Convert nanoseconds to seconds
y = df_window['value']
slope, intercept, r_value, p_value, std_err = linregress(x, y)

# plotting
plt.close('all')
default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
slope_text = f"Slope: {slope*3600000:.4f} [ml/h]"
lw = 0.7

fig = plt.figure(1)

ax = fig.add_subplot(111)

ax.plot(df_window["timestamp"], y, c=[0.5, 0.5, 0.5], linewidth=lw, label='Sensor '+device_name)
# ax.plot(df_window["timestamp"], intercept + slope * x, c='black', label='Linear fit')
# ax.text(df_window['timestamp'].iloc[0], 0.8*y.max(), slope_text, color='black', fontsize=12)

ax.set_title(device_name)
ax.set_xlabel("time")
ax.set_ylabel("I [A]")

plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()

# Path to the data directory
figure_dir = Path(__file__).resolve().parent.parent / 'figures'
filename = date_input + '_' + io_type + '_' + device_name + '.png'
file_path = figure_dir / filename
plt.savefig(file_path, dpi=300)

plt.show()


