import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from src.utils import get_file_path
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

df["timestamp"] = pd.to_datetime(df["timestamp"]) # for nicer plotting results

# plotting
plt.close('all')

fig = plt.figure(1)

ax = fig.add_subplot(111)

ax.plot(df["timestamp"], df["device_type"], 'k')

ax.set_title(device_name)
ax.set_xlabel("time")
ax.set_ylabel("(tbd)")

plt.xticks(rotation=45)
plt.tight_layout()

# Path to the data directory
figure_dir = Path(__file__).resolve().parent.parent / 'figures'
filename = date_input + '_' + io_type + '_' + device_name + '.png'
file_path = figure_dir / filename
plt.savefig(file_path, dpi=300)

plt.show()


