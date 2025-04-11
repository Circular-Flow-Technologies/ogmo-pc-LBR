import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from src.utils import get_file_path

# file path
folder = "data"
file_name = ""
file_path = get_file_path(folder, file_name)
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

# Load data
def load_data(file_path):
    df = pd.read_csv(file_path, delimiter=';', names=['timestamp', 'machine_id', 'source_id', 'signal_id', 'value'], header=0)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format=DATE_FORMAT)
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    machines = df['machine_id'].unique()
    signals  = df['signal_id'].unique()
    sources  = df['source_id'].unique()

    print("\n Listed machines:")
    print(machines)
    print("\n Listed signals:")
    print(signals)
    print("\n Listed sources:")
    print(sources)

    return df

# Filter data
def filter_data(df, id_type, id=None):
    if id:
        df = df[df[id_type] == id]
    return df

# Plot data
def plot_data(df, machine_id, source_id, signal_id):
    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['value'], label=f'{machine_id} - {source_id} - {signal_id}')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title(f'{signal_id} over Time')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    filename = CSV_FILE.replace('measurements.csv', source_id+"_"+signal_id+".png")
    plt.savefig(filename, dpi=300)

# Main function
def main():
    df = load_data(CSV_FILE)
    
    # Input filters
    sel_machine_id = input("\nEnter machine_id (or leave blank to include all): ").strip() or None
    filtered_df = filter_data(df, 'machine_id', sel_machine_id)
    leftover_signals = filtered_df['signal_id'].unique()
    print("Left-over signals:")
    print(leftover_signals)

    sel_signal_id = input("\nEnter signal_id (or leave blank to include all): ").strip() or None
    filtered_df = filter_data(filtered_df, 'signal_id', sel_signal_id)
    leftover_sources = filtered_df['source_id'].unique()
    print("Left-over sources:")
    print(leftover_sources)

    sel_source_id = input("\nEnter source_id (or leave blank to include all): ").strip() or None
    
    # Filtered data
    filtered_df = filter_data(filtered_df, 'source_id', sel_source_id)
    
    if filtered_df.empty:
        print("No data found for the specified filters.")
    else:
        plot_data(filtered_df, sel_machine_id or 'All', sel_source_id or 'All', sel_signal_id or 'All')

if __name__ == '__main__':
    main()
