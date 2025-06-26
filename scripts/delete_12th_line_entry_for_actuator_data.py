import csv
from pathlib import Path

# Path to the data directory
data_dir = Path(__file__).resolve().parent.parent / 'data'

# Get all .csv files
csv_files = list(data_dir.glob('*_data.csv'))

for file_path in csv_files:
    print(f"Processing {file_path.name}...")

    cleaned_rows = []

    with file_path.open('r', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            # Defensive: only process rows with at least 5 fields
            if len(row) >= 5 and row[3] == 'Actuator' and len(row) == 12:
                # Remove the last field
                row = row[:-1]
            cleaned_rows.append(row)

    # Overwrite the file with cleaned data
    with file_path.open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(cleaned_rows)

    print(f"✔ Cleaned and saved: {file_path.name}")