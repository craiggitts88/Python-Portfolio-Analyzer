"""
Configuration and data validation
"""

import pandas as pd
from pathlib import Path


def validate_config(config):
    """Validate configuration dictionary"""
    
    # Required fields (support both old and new folder structure)
    required_fields = [
        'portfolio_balance',
        'date_start',
        'date_end',
        'algo_configs',
    ]
    
    # Check for either old 'data_folder' or new separate folders
    has_old_structure = 'data_folder' in config
    has_new_structure = 'm1_data_folder' in config and 'backtests_folder' in config
    
    if not has_old_structure and not has_new_structure:
        raise ValueError("Missing data folder configuration. Need either 'data_folder' or both 'm1_data_folder' and 'backtests_folder'")
    
    # Validate required fields
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate portfolio balance
    if config['portfolio_balance'] <= 0:
        raise ValueError("Portfolio balance must be positive")
    
    # Validate date format
    try:
        pd.to_datetime(config['date_start'])
        pd.to_datetime(config['date_end'])
    except:
        raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    # Validate date range
    if pd.to_datetime(config['date_start']) >= pd.to_datetime(config['date_end']):
        raise ValueError("Start date must be before end date")
    
    # Validate algo configs
    if not config['algo_configs']:
        raise ValueError("No algorithms configured")
    
    for algo in config['algo_configs']:
        if 'name' not in algo:
            raise ValueError("Algorithm missing 'name' field")
        if 'backtest_file' not in algo:
            raise ValueError(f"Algorithm '{algo['name']}' missing 'backtest_file' field")
        if 'risk_per_trade' not in algo:
            raise ValueError(f"Algorithm '{algo['name']}' missing 'risk_per_trade' field")
        if algo['risk_per_trade'] <= 0:
            raise ValueError(f"Algorithm '{algo['name']}' has invalid risk_per_trade: {algo['risk_per_trade']}")
    
    # Validate folders exist
    if has_new_structure:
        m1_folder = Path(config['m1_data_folder'])
        bt_folder = Path(config['backtests_folder'])
        
        if not m1_folder.exists():
            raise ValueError(f"M1 data folder does not exist: {m1_folder}")
        
        if not bt_folder.exists():
            raise ValueError(f"Backtests folder does not exist: {bt_folder}")
    
    elif has_old_structure:
        data_folder = Path(config['data_folder'])
        if not data_folder.exists():
            raise ValueError(f"Data folder does not exist: {data_folder}")
    
    return True


def validate_data(df, data_type):
    """Validate loaded data"""
    
    if df is None or len(df) == 0:
        raise ValueError(f"Empty {data_type} data")
    
    if data_type == 'm1':
        required_columns = ['datetime', 'open', 'high', 'low', 'close']
        
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"M1 data missing required column: {col}")
        
        # Check for NaN values
        if df[required_columns].isnull().any().any():
            raise ValueError("M1 data contains NaN values")
        
        # Check for valid OHLC relationship
        if not (df['high'] >= df['low']).all():
            raise ValueError("M1 data: High must be >= Low")
        
        if not ((df['high'] >= df['open']) & (df['high'] >= df['close'])).all():
            raise ValueError("M1 data: High must be >= Open and Close")
        
        if not ((df['low'] <= df['open']) & (df['low'] <= df['close'])).all():
            raise ValueError("M1 data: Low must be <= Open and Close")
    
    elif data_type == 'backtest':
        required_columns = ['ticket', 'symbol', 'type', 'open_time', 'close_time', 
                          'open_price', 'close_price', 'size', 'pnl']
        
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Backtest data missing required column: {col}")
        
        # Check for NaN in critical columns
        critical_columns = ['open_time', 'close_time', 'open_price', 'close_price']
        if df[critical_columns].isnull().any().any():
            raise ValueError("Backtest data contains NaN values in critical columns")
        
        # Check trade types
        valid_types = ['buy', 'sell', 'Buy', 'Sell', 'BUY', 'SELL']
        if not df['type'].isin(valid_types).all():
            invalid_types = df[~df['type'].isin(valid_types)]['type'].unique()
            raise ValueError(f"Backtest data contains invalid trade types: {invalid_types}")
        
        # Check time order
        if not (df['close_time'] >= df['open_time']).all():
            raise ValueError("Backtest data: Close time must be >= Open time")
    
    else:
        raise ValueError(f"Unknown data type: {data_type}")
    
    return True


def validate_m1_coverage(m1_data, backtest_data):
    """Validate that M1 data covers all backtest trades"""
    
    issues = []
    
    for algo_name, trades_df in backtest_data.items():
        for idx, trade in trades_df.iterrows():
            symbol = trade['symbol']
            
            # Check if M1 data exists for this symbol
            if symbol not in m1_data:
                issues.append(f"No M1 data for symbol: {symbol} (algo: {algo_name})")
                continue
            
            m1_df = m1_data[symbol]
            
            # Check if trade times are within M1 data range
            m1_start = m1_df['datetime'].min()
            m1_end = m1_df['datetime'].max()
            
            if trade['open_time'] < m1_start:
                issues.append(f"Trade {trade['ticket']} opens before M1 data starts ({symbol})")
            
            if trade['close_time'] > m1_end:
                issues.append(f"Trade {trade['ticket']} closes after M1 data ends ({symbol})")
    
    if issues:
        print("\n⚠️  M1 Coverage Warnings:")
        for issue in issues[:10]:  # Show first 10
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more issues")
        print()
    
    return len(issues) == 0
