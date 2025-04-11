import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from src.utils import get_file_path

# file path
folder = "data"
file_name = "2025-04-11_NH-25-001_measurement_data.csv"
csv_file = get_file_path(folder, file_name)
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Load data
def load_data(file_path):
    df = pd.read_csv(file_path, delimiter=',', names=['timestamp', 'runtime', 'machine_id', 'sensor_name', 'sensor_type', 'sensor_state', 'sensor_value'], header=0)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format=DATE_FORMAT)
    df['sensor_value'] = pd.to_numeric(df['sensor_value'], errors='coerce')

    sensor_types = df['sensor_type'].unique()

    print("\n Listed sensor types:")
    print(sensor_types)

    return df

# Filter data
def filter_data(df, id_type, id=None):
    if id:
        df = df[df[id_type] == id]
    return df

# Plot data
def plot_data(df, sensor_type):
    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['sensor_value'], label=f'{sensor_type}')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    filename = str(csv_file).replace('_measurement_data.csv', sensor_type+".png")
    plt.savefig(filename, dpi=300)
    plt.show()

# Main function
df = load_data(csv_file)

# Input filters
sel_sensor_types = input("\nEnter sensor type (or leave blank to include all): ").strip() or None
filtered_df = filter_data(df, 'sensor_type', sel_sensor_types)
    
if filtered_df.empty:
    print("No data found for the specified filters.")
else:
    plot_data(filtered_df, sel_sensor_types or 'All')
