import xarray as xr
import numpy as np

# Define the data fields
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

# Prepare the data: only 'equity' has a value, the rest are empty arrays
# We'll use float arrays for all except 'stocks_in_positions', which could be string/object
# For simplicity, all arrays will be float, and 'stocks_in_positions' will be an empty string array

data = {
    'equity': (['records'], np.array([1000.0])),
    'open_positions': (['records'], np.array([np.nan])),
    'amount_invested': (['records'], np.array([np.nan])),
    'stop_price': (['records'], np.array([np.nan])),
    'value_at_entry': (['records'], np.array([np.nan])),
    'stocks_in_positions': (['records'], np.array([""], dtype=str)),
    'stock_price_at_entry': (['records'], np.array([np.nan])),
    'stock_price_at_close': (['records'], np.array([np.nan])),
    'net_gain_loss_amount': (['records'], np.array([np.nan])),
    'net_gain_loss_percent': (['records'], np.array([np.nan])),
    'target_price': (['records'], np.array([np.nan])),
}

# Create the xarray Dataset
# Note: NetCDF does not support zero-length dimensions, so we use length 0 for empty arrays, 1 for equity
# The 'records' dimension will be length 1 for equity, 0 for others

ds = xr.Dataset(data)

# Save to NetCDF file
output_file = 'equity_data.nc'
ds.to_netcdf(output_file)

print(f"NetCDF file '{output_file}' created with specified fields.")

