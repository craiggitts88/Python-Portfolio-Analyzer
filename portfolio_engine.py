"""
Event-driven portfolio simulation engine with M1 equity tracking
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .pricing_engine import PricingEngine
from .position_sizer import PositionSizer


class PortfolioEngine:
    """Main portfolio simulation engine"""
    
    def __init__(self, config, m1_data, backtest_data):
        self.config = config
        self.m1_data = m1_data
        self.backtest_data = backtest_data
        
        # Initialize engines
        self.pricing_engine = PricingEngine(m1_data, config)
        self.position_sizer = PositionSizer(self.pricing_engine)
        
        # Portfolio state
        self.starting_balance = config['portfolio_balance']
        self.cash = self.starting_balance
        self.equity = self.starting_balance
        self.open_positions = {}
        
        # Results tracking
        self.equity_curve = []
        self.trade_log = []
        self.daily_returns = []
        
        # Combine all trades from all algos
        self.all_trades = self._combine_all_trades()
    
    def _combine_all_trades(self):
        """Combine trades from all algorithms"""
        
        all_trades = []
        
        for algo_name, df in self.backtest_data.items():
            for idx, trade in df.iterrows():
                all_trades.append({
                    'algo_name': algo_name,
                    'risk_pct': trade['risk_pct'],
                    'ticket': trade['ticket'],
                    'symbol': trade['symbol'],
                    'type': trade['type'],
                    'open_time': trade['open_time'],
                    'close_time': trade['close_time'],
                    'open_price': trade['open_price'],
                    'close_price': trade['close_price'],
                    'sl_price': trade['sl_price'],
                    'size_original': trade['size'],  # Original backtest size
                    'pnl_original': trade['pnl'],    # Original backtest P&L
                    'mae_original': trade.get('mae', np.nan),
                    'mfe_original': trade.get('mfe', np.nan),
                })
        
        # Sort by open time
        all_trades = sorted(all_trades, key=lambda x: x['open_time'])
        
        return all_trades
    
    def run(self):
        """Run the portfolio simulation"""
        
        print(f"\n   🔄 Processing {len(self.all_trades)} trades...")
        
        # Get date range
        start_date = pd.to_datetime(self.config['date_start'])
        end_date = pd.to_datetime(self.config['date_end'])
        
        # Initialize equity curve with starting balance
        self.equity_curve.append({
            'datetime': start_date,
            'equity': self.starting_balance,
            'cash': self.starting_balance,
            'floating_pnl': 0,
            'open_positions': 0,
        })
        
        # Process each trade
        for i, trade in enumerate(self.all_trades):
            if (i + 1) % 100 == 0:
                print(f"      Processing trade {i+1}/{len(self.all_trades)}...")
            
            self._process_trade(trade)
        
        # Close any remaining open positions at end date
        self._close_all_positions(end_date)
        
        # Convert to DataFrame
        equity_df = pd.DataFrame(self.equity_curve)
        trades_df = pd.DataFrame(self.trade_log)
        
        print(f"\n   ✅ Simulation complete:")
        print(f"      - Total trades: {len(trades_df)}")
        print(f"      - Equity points: {len(equity_df)}")
        print(f"      - Final equity: ${equity_df['equity'].iloc[-1]:,.2f}")
        
        return {
            'equity_curve': equity_df,
            'trades': trades_df,
            'total_trades': len(trades_df),
            'starting_balance': self.starting_balance,
            'final_equity': equity_df['equity'].iloc[-1],
            'config': self.config,
        }
    
    def _process_trade(self, trade):
        """Process a single trade"""
        
        # Calculate position size based on current equity and risk %
        current_equity = self._get_current_equity(trade['open_time'])
        
        position_size = self.position_sizer.calculate_size(
            equity=current_equity,
            risk_pct=trade['risk_pct'],
            symbol=trade['symbol'],
            entry_price=trade['open_price'],
            sl_price=trade['sl_price'],
            timestamp=trade['open_time']
        )
        
        # Open position
        position_id = f"{trade['algo_name']}_{trade['ticket']}"
        
        self.open_positions[position_id] = {
            'algo_name': trade['algo_name'],
            'ticket': trade['ticket'],
            'symbol': trade['symbol'],
            'type': trade['type'],
            'open_time': trade['open_time'],
            'open_price': trade['open_price'],
            'sl_price': trade['sl_price'],
            'size': position_size,
            'size_original': trade['size_original'],
            'entry_equity': current_equity,
        }
        
        # Track equity through the trade using M1 data
        if self.config.get('output_settings', {}).get('generate_m1_equity', False):
            self._track_position_m1(position_id, trade)
        
        # Close position
        exit_equity = self._get_current_equity(trade['close_time'])
        
        pnl = self.position_sizer.calculate_pnl(
            trade_type=trade['type'],
            symbol=trade['symbol'],
            entry_price=trade['open_price'],
            exit_price=trade['close_price'],
            size=position_size,
            timestamp=trade['close_time']
        )
        
        # Update cash
        self.cash += pnl
        
        # Log trade
        self.trade_log.append({
            'algo_name': trade['algo_name'],
            'ticket': trade['ticket'],
            'symbol': trade['symbol'],
            'type': trade['type'],
            'open_time': trade['open_time'],
            'close_time': trade['close_time'],
            'open_price': trade['open_price'],
            'close_price': trade['close_price'],
            'sl_price': trade['sl_price'],
            'size': position_size,
            'size_original': trade['size_original'],
            'pnl': pnl,
            'pnl_original': trade['pnl_original'],
            'entry_equity': current_equity,
            'exit_equity': exit_equity,
            'risk_pct': trade['risk_pct'],
            'mae_original': trade['mae_original'],
            'mfe_original': trade['mfe_original'],
        })
        
        # Remove from open positions
        if position_id in self.open_positions:
            del self.open_positions[position_id]
        
        # Update equity curve at close
        self._update_equity_curve(trade['close_time'])
    
    def _track_position_m1(self, position_id, trade):
        """Track position equity minute-by-minute"""
        
        position = self.open_positions[position_id]
        symbol = position['symbol']
        
        if symbol not in self.m1_data:
            return
        
        # Get M1 data between open and close
        m1_df = self.m1_data[symbol]
        
        mask = (m1_df['datetime'] > trade['open_time']) & (m1_df['datetime'] < trade['close_time'])
        m1_bars = m1_df[mask]
        
        # Track equity at each M1 bar
        for idx, bar in m1_bars.iterrows():
            # Calculate floating P&L using close price
            floating_pnl = self.position_sizer.calculate_pnl(
                trade_type=position['type'],
                symbol=symbol,
                entry_price=position['open_price'],
                exit_price=bar['close'],
                size=position['size'],
                timestamp=bar['datetime']
            )
            
            # Calculate total equity
            equity = self.cash + floating_pnl
            
            # Add other open positions' floating P&L
            for other_id, other_pos in self.open_positions.items():
                if other_id != position_id:
                    other_floating = self._calculate_floating_pnl(other_pos, bar['datetime'])
                    equity += other_floating
            
            self.equity_curve.append({
                'datetime': bar['datetime'],
                'equity': equity,
                'cash': self.cash,
                'floating_pnl': floating_pnl,
                'open_positions': len(self.open_positions),
            })
    
    def _calculate_floating_pnl(self, position, timestamp):
        """Calculate floating P&L for a position at given timestamp"""
        
        try:
            current_price = self.pricing_engine.get_price_at_time(
                position['symbol'],
                timestamp,
                'close'
            )
            
            floating_pnl = self.position_sizer.calculate_pnl(
                trade_type=position['type'],
                symbol=position['symbol'],
                entry_price=position['open_price'],
                exit_price=current_price,
                size=position['size'],
                timestamp=timestamp
            )
            
            return floating_pnl
            
        except:
            return 0
    
    def _get_current_equity(self, timestamp):
        """Get current portfolio equity at given timestamp"""
        
        # Start with cash
        equity = self.cash
        
        # Add floating P&L from all open positions
        for position_id, position in self.open_positions.items():
            floating_pnl = self._calculate_floating_pnl(position, timestamp)
            equity += floating_pnl
        
        return equity
    
    def _update_equity_curve(self, timestamp):
        """Update equity curve at given timestamp"""
        
        equity = self._get_current_equity(timestamp)
        
        # Calculate total floating P&L
        total_floating = sum(
            self._calculate_floating_pnl(pos, timestamp)
            for pos in self.open_positions.values()
        )
        
        self.equity_curve.append({
            'datetime': timestamp,
            'equity': equity,
            'cash': self.cash,
            'floating_pnl': total_floating,
            'open_positions': len(self.open_positions),
        })
    
    def _close_all_positions(self, end_date):
        """Close all remaining open positions at end date"""
        
        for position_id, position in list(self.open_positions.items()):
            # Get closing price
            try:
                close_price = self.pricing_engine.get_price_at_time(
                    position['symbol'],
                    end_date,
                    'close'
                )
                
                pnl = self.position_sizer.calculate_pnl(
                    trade_type=position['type'],
                    symbol=position['symbol'],
                    entry_price=position['open_price'],
                    exit_price=close_price,
                    size=position['size'],
                    timestamp=end_date
                )
                
                self.cash += pnl
                
                # Log forced close
                self.trade_log.append({
                    'algo_name': position['algo_name'],
                    'ticket': position['ticket'],
                    'symbol': position['symbol'],
                    'type': position['type'],
                    'open_time': position['open_time'],
                    'close_time': end_date,
                    'open_price': position['open_price'],
                    'close_price': close_price,
                    'sl_price': position['sl_price'],
                    'size': position['size'],
                    'size_original': position['size_original'],
                    'pnl': pnl,
                    'pnl_original': np.nan,
                    'entry_equity': position['entry_equity'],
                    'exit_equity': self.cash,
                    'risk_pct': np.nan,
                    'mae_original': np.nan,
                    'mfe_original': np.nan,
                })
                
            except Exception as e:
                print(f"      ⚠️  Could not close position {position_id}: {e}")
            
            # Remove position
            del self.open_positions[position_id]
        
        # Final equity update
        self._update_equity_curve(end_date)
