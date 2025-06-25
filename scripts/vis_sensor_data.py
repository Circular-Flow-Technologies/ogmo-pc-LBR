import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from src.utils import get_file_path
from pathlib import Path

# Path to the data directory
data_dir = Path(__file__).resolve().parent.parent / 'data'

# Get all .csv files
csv_files = list(data_dir.glob('*_data.csv'))

print(csv_files)
