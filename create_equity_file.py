import pandas as pd
import numpy as np

fields = [
    'equity',
    'open_positions',
    'amount_invested',
    'stop_price',
    'value_at_entry',
    'stocks_in_positions',
    'stock_price_at_entry',
    'stock_price_at_close',
    'net_gain_loss_amount',
    'net_gain_loss_percent',
    'target_price',
]

# Create initial row: equity=1000, rest empty/NaN
row = {f: np.nan for f in fields}
row['equity'] = 1000.0

df = pd.DataFrame([row])
output_file = 'equity_data.csv'
df.to_csv(output_file, index=False)
print(f"CSV file '{output_file}' created with specified fields.")

