import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from src.utils import get_file_path

# file path
folder = "data"
file_name = "2025-04-14_NH-25-001_measurement_data.csv"
csv_file = get_file_path(folder, file_name)
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Load data
def load_data(file_path, io_type):
    df = pd.read_csv(file_path, delimiter=',', names=['timestamp', 'runtime', 'machine_id', 'io_type', 'device_type', 'name', 'address', 'state', 'value'], header=0)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format=DATE_FORMAT)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    df = filter_data(df, 'io_type', io_type)

    device_types = df['device_type'].unique()

    print("\n Listed device types:")
    print(device_types)

    return df


# Filter data
def filter_data(df, id_type, id=None):
    if id:
        df = df[df[id_type] == id]
    return df

# Plot data
def plot_data(df, device_type):
    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['value'], label=f'{device_type}')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    filename = str(csv_file).replace('_measurement_data.csv', device_type+".png")
    plt.savefig(filename, dpi=300)
    plt.show()

# Main function
sel_io_type = input("\nEnter 'Sensor' or 'Actuator' depending on which IO-type you want to plot: ")
df = load_data(csv_file, sel_io_type)

# Input filters
sel_device_types = input("\nEnter device type (or leave blank to include all): ").strip() or None
filtered_df = filter_data(df, 'device_type', sel_device_types)
    
if filtered_df.empty:
    print("No data found for the specified filters.")
else:
    plot_data(filtered_df, sel_device_types or 'All')
