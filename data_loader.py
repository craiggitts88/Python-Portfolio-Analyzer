"""
Data loading and normalization
"""

import pandas as pd
from pathlib import Path
from utils.validators import validate_data
from utils.helpers import parse_datetime


class DataLoader:
    """Load M1 data and backtest files"""
    
    def __init__(self, config):
        self.config = config
        # Support both old 'data_folder' and new separate folders
        self.m1_folder = Path(config.get('m1_data_folder', config.get('data_folder', './data/m1_data')))
        self.bt_folder = Path(config.get('backtests_folder', config.get('data_folder', './data/backtests')))
    
    def load_all(self):
        """Load all M1 and backtest data"""
        
        m1_data = self.load_m1_data()
        backtest_data = self.load_backtest_data()
        
        return m1_data, backtest_data
    
    def load_m1_data(self):
        """Load all M1 data files"""
        
        m1_data = {}
        
        for symbol, filename in self.config.get('m1_data_files', {}).items():
            filepath = self.m1_folder / filename
            
            if not filepath.exists():
                print(f"⚠️  Warning: M1 file not found: {filepath}")
                continue
            
            print(f"   Loading M1 data: {symbol}...")
            
            try:
                # Read CSV with tab delimiter and handle quotes
                df = pd.read_csv(
                    filepath,
                    sep='\t',           # Tab-separated
                    quotechar='"',      # Handle quotes
                    skipinitialspace=True
                )
                
                # Normalize column names
                df = self._normalize_m1_columns(df)
                
                # Parse datetime from separate date and time columns
                if 'date' in df.columns and 'time' in df.columns:
                    df['datetime'] = pd.to_datetime(
                        df['date'].astype(str) + ' ' + df['time'].astype(str),
                        format='%Y.%m.%d %H:%M:%S'
                    )
                elif 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                else:
                    raise ValueError(f"Could not find datetime columns. Available columns: {list(df.columns)}")
                
                # Ensure we have OHLC columns
                required_cols = ['open', 'high', 'low', 'close']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    raise ValueError(f"Missing required columns: {missing_cols}. Available: {list(df.columns)}")
                
                # Select required columns
                df = df[['datetime', 'open', 'high', 'low', 'close']].copy()
                
                # Convert OHLC to numeric (in case they're strings)
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Remove any rows with NaN values
                df.dropna(inplace=True)
                
                # Sort by datetime
                df.sort_values('datetime', inplace=True)
                df.reset_index(drop=True, inplace=True)
                
                # Filter by date range
                start_date = pd.to_datetime(self.config['date_start'])
                end_date = pd.to_datetime(self.config['date_end'])
                
                df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
                
                if len(df) == 0:
                    raise ValueError(f"No data in date range {start_date} to {end_date}")
                
                # Validate
                validate_data(df, 'm1')
                
                m1_data[symbol] = df
                
                print(f"      ✅ Loaded {len(df):,} M1 bars for {symbol}")
                print(f"      Date range: {df['datetime'].min()} to {df['datetime'].max()}")
                
            except Exception as e:
                print(f"      ❌ Error loading {symbol}: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        return m1_data
    
    def _normalize_m1_columns(self, df):
        """Normalize M1 column names"""
        
        # Map various column name formats to standard names
        column_mapping = {
            # MetaTrader format
            '<DATE>': 'date',
            '<TIME>': 'time',
            '<OPEN>': 'open',
            '<HIGH>': 'high',
            '<LOW>': 'low',
            '<CLOSE>': 'close',
            '<TICKVOL>': 'tickvol',
            '<VOL>': 'vol',
            '<SPREAD>': 'spread',
            
            # Standard capitalized
            'Date': 'date',
            'Time': 'time',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'DateTime': 'datetime',
            'Datetime': 'datetime',
            
            # All caps
            'DATE': 'date',
            'TIME': 'time',
            'OPEN': 'open',
            'HIGH': 'high',
            'LOW': 'low',
            'CLOSE': 'close',
            'DATETIME': 'datetime',
            
            # Other variations
            'date_time': 'datetime',
            'timestamp': 'datetime',
            'Timestamp': 'datetime',
        }
        
        # Apply mapping
        df.rename(columns=column_mapping, inplace=True)
        
        # Convert all column names to lowercase
        df.columns = df.columns.str.lower().str.strip()
        
        return df
    
    def load_backtest_data(self):
        """Load all backtest Excel files"""
        
        backtest_data = {}
        
        for algo_config in self.config['algo_configs']:
            if not algo_config.get('enabled', True):
                continue
            
            algo_name = algo_config['name']
            filename = algo_config['backtest_file']
            filepath = self.bt_folder / filename
            
            if not filepath.exists():
                print(f"⚠️  Warning: Backtest file not found: {filepath}")
                continue
            
            print(f"   Loading backtest: {algo_name}...")
            
            try:
                # Read Excel file
                df = pd.read_excel(filepath, sheet_name='Tradelist')
                
                # Normalize column names
                df = self._normalize_backtest_columns(df)
                
                # Parse datetimes
                df['open_time'] = df['open_time'].apply(parse_datetime)
                df['close_time'] = df['close_time'].apply(parse_datetime)
                
                # Filter out pending orders (no close time or close price)
                df = df[df['close_time'].notna()].copy()
                df = df[df['close_price'].notna()].copy()
                
                # Filter by date range
                start_date = pd.to_datetime(self.config['date_start'])
                end_date = pd.to_datetime(self.config['date_end'])
                
                df = df[(df['open_time'] >= start_date) & (df['close_time'] <= end_date)]
                
                # Sort by open time
                df.sort_values('open_time', inplace=True)
                df.reset_index(drop=True, inplace=True)
                
                # Add algo name and risk
                df['algo_name'] = algo_name
                df['risk_pct'] = algo_config['risk_per_trade']
                
                # Validate
                validate_data(df, 'backtest')
                
                backtest_data[algo_name] = df
                
                print(f"      ✅ Loaded {len(df)} trades for {algo_name}")
                
            except Exception as e:
                print(f"      ❌ Error loading {algo_name}: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        return backtest_data
    
    def _normalize_backtest_columns(self, df):
        """Normalize backtest column names"""
        
        column_mapping = {
            'Ticket': 'ticket',
            'Symbol': 'symbol',
            'Type': 'type',
            'Open time': 'open_time',
            'Open price': 'open_price',
            'Stop Loss price level': 'sl_price',
            'Take Profit price level': 'tp_price',
            'Size': 'size',
            'Close time': 'close_time',
            'Close price': 'close_price',
            'Profit/Loss': 'pnl',
            'Balance': 'balance',
            'Sample type': 'sample_type',
            'Close type': 'close_type',
            'MAE ($)': 'mae',
            'MFE ($)': 'mfe',
            'Time in trade': 'time_in_trade',
            'Comment': 'comment',
            'Commission': 'commission',
            'Swap': 'swap',
        }
        
        df.rename(columns=column_mapping, inplace=True)
        
        # Ensure required columns exist with default values if missing
        if 'sl_price' not in df.columns:
            df['sl_price'] = 0
        
        if 'tp_price' not in df.columns:
            df['tp_price'] = 0
        
        if 'mae' not in df.columns:
            df['mae'] = pd.NA
        
        if 'mfe' not in df.columns:
            df['mfe'] = pd.NA
        
        if 'commission' not in df.columns:
            df['commission'] = 0
        
        if 'swap' not in df.columns:
            df['swap'] = 0
        
        return df
