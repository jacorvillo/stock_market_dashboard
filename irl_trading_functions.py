import numpy as np
import xarray as xr

def open_position(ds, stock, amount, price_at_entry, stop_price):
    """
    Open a new position: deduct amount from equity, add new row to all fields.
    """
    # Calculate new equity
    last_equity = float(ds['equity'].values[-1])
    new_equity = last_equity - amount

    # Append new values to each field
    ds = ds.copy()
    ds['equity'] = xr.concat([ds['equity'], xr.DataArray([new_equity], dims=['records'])], dim='records')
    ds['open_positions'] = xr.concat([ds['open_positions'], xr.DataArray([1.0], dims=['records'])], dim='records')
    ds['amount_invested'] = xr.concat([ds['amount_invested'], xr.DataArray([amount], dims=['records'])], dim='records')
    ds['stop_price'] = xr.concat([ds['stop_price'], xr.DataArray([stop_price], dims=['records'])], dim='records')
    ds['value_at_entry'] = xr.concat([ds['value_at_entry'], xr.DataArray([amount], dims=['records'])], dim='records')
    ds['stocks_in_positions'] = xr.concat([ds['stocks_in_positions'], xr.DataArray([stock], dims=['records'])], dim='records')
    ds['stock_price_at_entry'] = xr.concat([ds['stock_price_at_entry'], xr.DataArray([price_at_entry], dims=['records'])], dim='records')
    ds['stock_price_at_close'] = xr.concat([ds['stock_price_at_close'], xr.DataArray([np.nan], dims=['records'])], dim='records')
    ds['net_gain_loss_amount'] = xr.concat([ds['net_gain_loss_amount'], xr.DataArray([np.nan], dims=['records'])], dim='records')
    ds['net_gain_loss_percent'] = xr.concat([ds['net_gain_loss_percent'], xr.DataArray([np.nan], dims=['records'])], dim='records')
    return ds

def close_position(ds, stock, price_at_close):
    """
    Close an open position for a stock: update fields, add new equity.
    """
    # Find the last open position for this stock
    mask = (ds['stocks_in_positions'].values == stock) & np.isnan(ds['stock_price_at_close'].values)
    if not np.any(mask):
        raise ValueError(f"No open position found for stock {stock}")
    idx = np.where(mask)[0][-1]  # last open position

    amount_invested = float(ds['amount_invested'].values[idx])
    price_at_entry = float(ds['stock_price_at_entry'].values[idx])
    shares = amount_invested / price_at_entry if price_at_entry != 0 else 0
    value_at_close = shares * price_at_close
    gain_loss = value_at_close - amount_invested
    gain_loss_percent = (gain_loss / amount_invested) * 100 if amount_invested != 0 else 0

    # Update the closed position fields
    ds = ds.copy()
    ds['stock_price_at_close'].values[idx] = price_at_close
    ds['net_gain_loss_amount'].values[idx] = gain_loss
    ds['net_gain_loss_percent'].values[idx] = gain_loss_percent
    ds['open_positions'].values[idx] = 0.0  # Mark as closed

    # Update equity
    last_equity = float(ds['equity'].values[-1])
    new_equity = last_equity + value_at_close
    ds['equity'] = xr.concat([ds['equity'], xr.DataArray([new_equity], dims=['records'])], dim='records')
    # For other fields, append np.nan or "" as placeholders for this new record
    for field in ['open_positions', 'amount_invested', 'stop_price', 'value_at_entry',
                  'stocks_in_positions', 'stock_price_at_entry', 'stock_price_at_close',
                  'net_gain_loss_amount', 'net_gain_loss_percent']:
        dtype = str if field == 'stocks_in_positions' else float
        value = "" if field == 'stocks_in_positions' else np.nan
        ds[field] = xr.concat([ds[field], xr.DataArray([value], dims=['records'])], dim='records')
    return ds 