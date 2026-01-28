"""
Helper utility functions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def parse_datetime(dt_string):
    """Parse datetime string in various formats"""
    
    if pd.isna(dt_string) or dt_string == '':
        return None
    
    # Try common formats
    formats = [
        '%Y.%m.%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d %H:%M:%S',
        '%Y.%m.%d',
        '%Y-%m-%d',
    ]
    
    for fmt in formats:
        try:
            return pd.to_datetime(dt_string, format=fmt)
        except:
            continue
    
    # Fallback to pandas auto-parsing
    try:
        return pd.to_datetime(dt_string)
    except:
        raise ValueError(f"Could not parse datetime: {dt_string}")


def format_currency(value, currency='USD'):
    """Format value as currency"""
    
    if pd.isna(value):
        return 'N/A'
    
    symbol = '$' if currency == 'USD' else '€' if currency == 'EUR' else ''
    
    if abs(value) >= 1_000_000:
        return f"{symbol}{value/1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"{symbol}{value/1_000:.2f}K"
    else:
        return f"{symbol}{value:.2f}"


def format_percentage(value, decimals=2):
    """Format value as percentage"""
    
    if pd.isna(value):
        return 'N/A'
    
    return f"{value:.{decimals}f}%"


def calculate_risk_amount(equity, risk_pct, entry_price, sl_price, contract_size, point_value):
    """
    Calculate position size based on risk percentage
    
    Args:
        equity: Current portfolio equity
        risk_pct: Risk percentage (e.g., 0.314 for 0.314%)
        entry_price: Entry price
        sl_price: Stop loss price
        contract_size: Contract size for instrument
        point_value: Point value for instrument
    
    Returns:
        Position size in lots
    """
    
    # Risk amount in dollars
    risk_amount = equity * (risk_pct / 100)
    
    # Stop distance in points
    stop_distance = abs(entry_price - sl_price)
    
    if stop_distance == 0:
        return 0
    
    # Risk per lot
    risk_per_lot = stop_distance * contract_size * point_value
    
    if risk_per_lot == 0:
        return 0
    
    # Position size in lots
    lot_size = risk_amount / risk_per_lot
    
    return round(lot_size, 1)  # Round to 0.1 lot


def get_fx_rate(currency_pair, m1_data_dict, timestamp):
    """
    Get FX conversion rate at specific timestamp
    
    Args:
        currency_pair: e.g., 'EURUSD'
        m1_data_dict: Dictionary of M1 dataframes
        timestamp: Timestamp to get rate for
    
    Returns:
        FX rate (float)
    """
    
    if currency_pair not in m1_data_dict:
        # Return default rates if M1 data not available
        from config.settings import DEFAULT_FX_RATES
        return DEFAULT_FX_RATES.get(currency_pair, 1.0)
    
    fx_data = m1_data_dict[currency_pair]
    
    # Find closest timestamp
    idx = fx_data['datetime'].searchsorted(timestamp)
    
    if idx >= len(fx_data):
        idx = len(fx_data) - 1
    elif idx > 0 and abs(fx_data.iloc[idx-1]['datetime'] - timestamp) < abs(fx_data.iloc[idx]['datetime'] - timestamp):
        idx = idx - 1
    
    return fx_data.iloc[idx]['close']


def calculate_pnl(trade_type, entry_price, exit_price, size, contract_size, point_value, fx_rate=1.0):
    """
    Calculate P&L for a trade
    
    Args:
        trade_type: 'Buy' or 'Sell'
        entry_price: Entry price
        exit_price: Exit price
        size: Position size in lots
        contract_size: Contract size
        point_value: Point value
        fx_rate: FX conversion rate to USD
    
    Returns:
        P&L in USD
    """
    
    if trade_type.lower() in ['buy', 'buystop']:
        price_diff = exit_price - entry_price
    else:  # Sell
        price_diff = entry_price - exit_price
    
    pnl = price_diff * size * contract_size * point_value * fx_rate
    
    return pnl


def resample_to_daily(equity_curve):
    """
    Resample minute-level equity curve to daily
    
    Args:
        equity_curve: DataFrame with datetime and equity columns
    
    Returns:
        Daily equity DataFrame
    """
    
    df = equity_curve.copy()
    df.set_index('datetime', inplace=True)
    
    # Resample to daily, taking last value of each day
    daily = df.resample('D').last()
    
    # Forward fill any missing days
    daily = daily.fillna(method='ffill')
    
    daily.reset_index(inplace=True)
    
    return daily


def calculate_drawdown_series(equity_series):
    """
    Calculate drawdown series from equity curve
    
    Args:
        equity_series: Pandas Series of equity values
    
    Returns:
        Drawdown series (negative values)
    """
    
    # Calculate running maximum
    running_max = equity_series.expanding().max()
    
    # Calculate drawdown
    drawdown = (equity_series - running_max) / running_max * 100
    
    return drawdown


def find_drawdown_periods(drawdown_series):
    """
    Find all drawdown periods
    
    Args:
        drawdown_series: Series of drawdown values
    
    Returns:
        List of dicts with drawdown period info
    """
    
    periods = []
    in_drawdown = False
    start_idx = None
    
    for idx, dd in enumerate(drawdown_series):
        if dd < 0 and not in_drawdown:
            # Start of drawdown
            in_drawdown = True
            start_idx = idx
        elif dd >= 0 and in_drawdown:
            # End of drawdown
            in_drawdown = False
            
            dd_period = drawdown_series.iloc[start_idx:idx]
            
            periods.append({
                'start_idx': start_idx,
                'end_idx': idx - 1,
                'duration': idx - start_idx,
                'max_dd': dd_period.min(),
                'max_dd_idx': dd_period.idxmin()
            })
    
    # Handle case where still in drawdown at end
    if in_drawdown:
        dd_period = drawdown_series.iloc[start_idx:]
        periods.append({
            'start_idx': start_idx,
            'end_idx': len(drawdown_series) - 1,
            'duration': len(drawdown_series) - start_idx,
            'max_dd': dd_period.min(),
            'max_dd_idx': dd_period.idxmin()
        })
    
    return periods
