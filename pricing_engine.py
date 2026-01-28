"""
Pricing engine for M1 data lookups and FX conversion
"""

import pandas as pd
import numpy as np
from config.settings import INSTRUMENT_SPECS, DEFAULT_FX_RATES


class PricingEngine:
    """Handle price lookups and conversions"""
    
    def __init__(self, m1_data, config):
        self.m1_data = m1_data
        self.config = config
        
        # Create datetime indices for fast lookup
        self.m1_indices = {}
        for symbol, df in m1_data.items():
            self.m1_indices[symbol] = df.set_index('datetime')
    
    def get_price_at_time(self, symbol, timestamp, price_type='close'):
        """
        Get price at specific timestamp
        
        Args:
            symbol: Instrument symbol
            timestamp: Timestamp to get price for
            price_type: 'open', 'high', 'low', 'close'
        
        Returns:
            Price (float)
        """
        
        if symbol not in self.m1_indices:
            raise ValueError(f"No M1 data for symbol: {symbol}")
        
        df = self.m1_indices[symbol]
        
        # Find nearest timestamp (forward fill)
        try:
            # Use asof to get last available price at or before timestamp
            price = df[price_type].asof(timestamp)
            
            if pd.isna(price):
                # If no price before timestamp, get first available
                price = df[price_type].iloc[0]
            
            return price
            
        except Exception as e:
            raise ValueError(f"Could not get price for {symbol} at {timestamp}: {e}")
    
    def get_bar_at_time(self, symbol, timestamp):
        """
        Get full OHLC bar at specific timestamp
        
        Returns:
            Dict with open, high, low, close
        """
        
        if symbol not in self.m1_indices:
            raise ValueError(f"No M1 data for symbol: {symbol}")
        
        df = self.m1_indices[symbol]
        
        try:
            # Get bar at or before timestamp
            bar_data = df.asof(timestamp)
            
            if bar_data.isnull().all():
                # If no bar before timestamp, get first available
                bar_data = df.iloc[0]
            
            return {
                'open': bar_data['open'],
                'high': bar_data['high'],
                'low': bar_data['low'],
                'close': bar_data['close'],
            }
            
        except Exception as e:
            raise ValueError(f"Could not get bar for {symbol} at {timestamp}: {e}")
    
    def get_fx_rate(self, currency_pair, timestamp):
        """
        Get FX conversion rate at specific timestamp
        
        Args:
            currency_pair: e.g., 'EURUSD'
            timestamp: Timestamp to get rate for
        
        Returns:
            FX rate (float)
        """
        
        if currency_pair in self.m1_data:
            return self.get_price_at_time(currency_pair, timestamp, 'close')
        else:
            # Return default rate
            return DEFAULT_FX_RATES.get(currency_pair, 1.0)
    
    def convert_to_usd(self, amount, currency, timestamp):
        """
        Convert amount from currency to USD
        
        Args:
            amount: Amount to convert
            currency: Source currency (EUR, GBP, etc.)
            timestamp: Timestamp for FX rate
        
        Returns:
            Amount in USD
        """
        
        if currency == 'USD':
            return amount
        
        # Get appropriate FX pair
        fx_pair = f"{currency}USD"
        
        fx_rate = self.get_fx_rate(fx_pair, timestamp)
        
        return amount * fx_rate
    
    def get_instrument_specs(self, symbol):
        """Get instrument specifications"""
        
        if symbol in INSTRUMENT_SPECS:
            return INSTRUMENT_SPECS[symbol]
        else:
            # Default specs
            return {
                'contract_size': 1,
                'point_value': 1,
                'currency': 'USD',
                'type': 'unknown'
            }
