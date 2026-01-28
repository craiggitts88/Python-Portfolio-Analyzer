"""
Position sizing based on risk percentage
"""

from utils.helpers import calculate_risk_amount


class PositionSizer:
    """Calculate position sizes based on risk management rules"""
    
    def __init__(self, pricing_engine):
        self.pricing_engine = pricing_engine
    
    def calculate_size(self, equity, risk_pct, symbol, entry_price, sl_price, timestamp):
        """
        Calculate position size in lots
        
        Args:
            equity: Current portfolio equity
            risk_pct: Risk percentage per trade
            symbol: Instrument symbol
            entry_price: Entry price
            sl_price: Stop loss price
            timestamp: Timestamp for FX conversion
        
        Returns:
            Position size in lots
        """
        
        # Get instrument specs
        specs = self.pricing_engine.get_instrument_specs(symbol)
        
        contract_size = specs['contract_size']
        point_value = specs['point_value']
        currency = specs['currency']
        
        # Get FX rate if needed
        if currency != 'USD':
            fx_pair = f"{currency}USD"
            fx_rate = self.pricing_engine.get_fx_rate(fx_pair, timestamp)
        else:
            fx_rate = 1.0
        
        # Calculate position size
        lot_size = calculate_risk_amount(
            equity=equity,
            risk_pct=risk_pct,
            entry_price=entry_price,
            sl_price=sl_price,
            contract_size=contract_size,
            point_value=point_value
        )
        
        return lot_size
    
    def calculate_pnl(self, trade_type, symbol, entry_price, exit_price, size, timestamp):
        """
        Calculate P&L for a trade
        
        Args:
            trade_type: 'Buy' or 'Sell'
            symbol: Instrument symbol
            entry_price: Entry price
            exit_price: Exit price
            size: Position size in lots
            timestamp: Timestamp for FX conversion
        
        Returns:
            P&L in USD
        """
        
        # Get instrument specs
        specs = self.pricing_engine.get_instrument_specs(symbol)
        
        contract_size = specs['contract_size']
        point_value = specs['point_value']
        currency = specs['currency']
        
        # Calculate price difference
        if trade_type.lower() in ['buy', 'buystop']:
            price_diff = exit_price - entry_price
        else:  # Sell
            price_diff = entry_price - exit_price
        
        # Calculate P&L in instrument currency
        pnl = price_diff * size * contract_size * point_value
        
        # Convert to USD if needed
        if currency != 'USD':
            pnl = self.pricing_engine.convert_to_usd(pnl, currency, timestamp)
        
        return pnl
