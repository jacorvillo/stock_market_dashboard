import pandas as pd
import numpy as np

# Read the existing CSV
df = pd.read_csv('equity_data.csv')

# Add the new fields if they don't exist
if 'side' not in df.columns:
    df['side'] = 'buy'
if 'stop_hit' not in df.columns:
    df['stop_hit'] = False
if 'stop_hit_price' not in df.columns:
    df['stop_hit_price'] = np.nan

# Save the updated CSV
df.to_csv('equity_data.csv', index=False)
print("CSV file updated with new fields: side, stop_hit, and stop_hit_price") 