"""
Per-algorithm attribution analysis
"""

import pandas as pd
import numpy as np
from utils.helpers import calculate_drawdown_series


class AttributionAnalyzer:
    """Analyze contribution of each algorithm to portfolio performance"""
    
    def __init__(self, results, config):
        self.results = results
        self.config = config
        self.trades = results['trades']
    
    def analyze(self):
        """Perform attribution analysis"""
        
        if len(self.trades) == 0:
            return {}
        
        attribution = {}
        
        # Group trades by algorithm
        for algo_name in self.trades['algo_name'].unique():
            algo_trades = self.trades[self.trades['algo_name'] == algo_name]
            
            attribution[algo_name] = self._calculate_algo_metrics(algo_trades)
        
        return attribution
    
    def _calculate_algo_metrics(self, trades):
        """Calculate metrics for a single algorithm"""
        
        total_pnl = trades['pnl'].sum()
        
        winning_trades = trades[trades['pnl'] > 0]
        losing_trades = trades[trades['pnl'] < 0]
        
        num_trades = len(trades)
        num_wins = len(winning_trades)
        num_losses = len(losing_trades)
        
        win_rate = (num_wins / num_trades * 100) if num_trades > 0 else 0
        
        avg_win = winning_trades['pnl'].mean() if num_wins > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if num_losses > 0 else 0
        
        gross_profit = winning_trades['pnl'].sum() if num_wins > 0 else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if num_losses > 0 else 0
        
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        return {
            'total_trades': num_trades,
            'total_pnl': total_pnl,
            'winning_trades': num_wins,
            'losing_trades': num_losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'profit_factor': profit_factor,
            'expectancy': trades['pnl'].mean(),
        }
