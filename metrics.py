"""
Performance metrics calculations
"""

import pandas as pd
import numpy as np
from scipy import stats
from utils.helpers import calculate_drawdown_series, find_drawdown_periods


class MetricsCalculator:
    """Calculate comprehensive performance metrics"""
    
    def __init__(self, results, config):
        self.results = results
        self.config = config
        self.equity_curve = results['equity_curve']
        self.trades = results['trades']
        self.starting_balance = results['starting_balance']
        self.final_equity = results['final_equity']
    
    def calculate_all(self):
        """Calculate all performance metrics"""
        
        metrics = {}
        
        # Basic metrics
        metrics.update(self._calculate_basic_metrics())
        
        # Returns metrics
        metrics.update(self._calculate_returns_metrics())
        
        # Risk metrics
        metrics.update(self._calculate_risk_metrics())
        
        # Trade metrics
        metrics.update(self._calculate_trade_metrics())
        
        # Drawdown metrics
        metrics.update(self._calculate_drawdown_metrics())
        
        # Risk-adjusted metrics
        metrics.update(self._calculate_risk_adjusted_metrics())
        
        return metrics
    
    def _calculate_basic_metrics(self):
        """Calculate basic performance metrics"""
        
        total_return = ((self.final_equity - self.starting_balance) / self.starting_balance) * 100
        
        # Calculate CAGR
        start_date = self.equity_curve['datetime'].min()
        end_date = self.equity_curve['datetime'].max()
        years = (end_date - start_date).days / 365.25
        
        if years > 0:
            cagr = (((self.final_equity / self.starting_balance) ** (1 / years)) - 1) * 100
        else:
            cagr = 0
        
        return {
            'starting_balance': self.starting_balance,
            'final_equity': self.final_equity,
            'total_return': total_return,
            'total_return_pct': total_return,
            'cagr': cagr,
            'years': years,
            'start_date': start_date,
            'end_date': end_date,
        }
    
    def _calculate_returns_metrics(self):
        """Calculate returns-based metrics"""
        
        # Resample to daily
        daily_equity = self.equity_curve.copy()
        daily_equity['date'] = daily_equity['datetime'].dt.date
        daily_equity = daily_equity.groupby('date')['equity'].last().reset_index()
        
        # Calculate daily returns
        daily_equity['returns'] = daily_equity['equity'].pct_change()
        daily_returns = daily_equity['returns'].dropna()
        
        # Calculate monthly returns
        monthly_equity = self.equity_curve.copy()
        monthly_equity.set_index('datetime', inplace=True)
        monthly_equity = monthly_equity['equity'].resample('M').last()
        monthly_returns = monthly_equity.pct_change().dropna()
        
        return {
            'avg_daily_return': daily_returns.mean() * 100,
            'avg_monthly_return': monthly_returns.mean() * 100,
            'std_daily_return': daily_returns.std() * 100,
            'std_monthly_return': monthly_returns.std() * 100,
            'best_day': daily_returns.max() * 100,
            'worst_day': daily_returns.min() * 100,
            'best_month': monthly_returns.max() * 100,
            'worst_month': monthly_returns.min() * 100,
            'positive_days': (daily_returns > 0).sum(),
            'negative_days': (daily_returns < 0).sum(),
            'positive_months': (monthly_returns > 0).sum(),
            'negative_months': (monthly_returns < 0).sum(),
        }
    
    def _calculate_risk_metrics(self):
        """Calculate risk metrics"""
        
        # Resample to daily
        daily_equity = self.equity_curve.copy()
        daily_equity['date'] = daily_equity['datetime'].dt.date
        daily_equity = daily_equity.groupby('date')['equity'].last().reset_index()
        
        # Calculate drawdown series
        dd_series = calculate_drawdown_series(daily_equity['equity'])
        
        max_dd = dd_series.min()
        
        # Find drawdown periods
        dd_periods = find_drawdown_periods(dd_series)
        
        if dd_periods:
            longest_dd = max(dd_periods, key=lambda x: x['duration'])
            avg_dd_duration = np.mean([p['duration'] for p in dd_periods])
        else:
            longest_dd = {'duration': 0}
            avg_dd_duration = 0
        
        # Calculate daily returns for volatility
        daily_equity['returns'] = daily_equity['equity'].pct_change()
        daily_returns = daily_equity['returns'].dropna()
        
        annual_volatility = daily_returns.std() * np.sqrt(252) * 100
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd,
            'longest_dd_days': longest_dd['duration'],
            'avg_dd_duration': avg_dd_duration,
            'num_dd_periods': len(dd_periods),
            'annual_volatility': annual_volatility,
        }
    
    def _calculate_trade_metrics(self):
        """Calculate trade-based metrics"""
        
        if len(self.trades) == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'profit_factor': 0,
                'expectancy': 0,
            }
        
        trades = self.trades.copy()
        
        winning_trades = trades[trades['pnl'] > 0]
        losing_trades = trades[trades['pnl'] < 0]
        
        total_trades = len(trades)
        num_wins = len(winning_trades)
        num_losses = len(losing_trades)
        
        win_rate = (num_wins / total_trades * 100) if total_trades > 0 else 0
        
        avg_win = winning_trades['pnl'].mean() if num_wins > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if num_losses > 0 else 0
        
        largest_win = winning_trades['pnl'].max() if num_wins > 0 else 0
        largest_loss = losing_trades['pnl'].min() if num_losses > 0 else 0
        
        gross_profit = winning_trades['pnl'].sum() if num_wins > 0 else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if num_losses > 0 else 0
        
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        expectancy = trades['pnl'].mean()
        
        return {
            'total_trades': total_trades,
            'winning_trades': num_wins,
            'losing_trades': num_losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'avg_trade': trades['pnl'].mean(),
            'median_trade': trades['pnl'].median(),
        }
    
    def _calculate_drawdown_metrics(self):
        """Calculate detailed drawdown metrics"""
        
        # Resample to daily
        daily_equity = self.equity_curve.copy()
        daily_equity['date'] = daily_equity['datetime'].dt.date
        daily_equity = daily_equity.groupby('date')['equity'].last().reset_index()
        
        # Calculate drawdown series
        dd_series = calculate_drawdown_series(daily_equity['equity'])
        
        # Find all drawdown periods
        dd_periods = find_drawdown_periods(dd_series)
        
        if not dd_periods:
            return {
                'max_dd_duration': 0,
                'avg_dd_depth': 0,
                'recovery_factor': 0,
            }
        
        max_dd_duration = max(p['duration'] for p in dd_periods)
        avg_dd_depth = np.mean([abs(p['max_dd']) for p in dd_periods])
        
        # Recovery factor = Net Profit / Max DD
        net_profit = self.final_equity - self.starting_balance
        max_dd_dollars = abs(dd_series.min() / 100 * self.starting_balance)
        
        recovery_factor = (net_profit / max_dd_dollars) if max_dd_dollars > 0 else 0
        
        return {
            'max_dd_duration': max_dd_duration,
            'avg_dd_depth': avg_dd_depth,
            'recovery_factor': recovery_factor,
        }
    
    def _calculate_risk_adjusted_metrics(self):
        """Calculate risk-adjusted performance metrics"""
        
        # Resample to daily
        daily_equity = self.equity_curve.copy()
        daily_equity['date'] = daily_equity['datetime'].dt.date
        daily_equity = daily_equity.groupby('date')['equity'].last().reset_index()
        
        # Calculate daily returns
        daily_equity['returns'] = daily_equity['equity'].pct_change()
        daily_returns = daily_equity['returns'].dropna()
        
        if len(daily_returns) == 0:
            return {
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0,
            }
        
        # Sharpe Ratio (assuming 0% risk-free rate)
        avg_return = daily_returns.mean()
        std_return = daily_returns.std()
        
        sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std()
        
        sortino_ratio = (avg_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0
        
        # Calmar Ratio (CAGR / Max DD)
        start_date = daily_equity['date'].min()
        end_date = daily_equity['date'].max()
        years = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365.25
        
        if years > 0:
            cagr = (((self.final_equity / self.starting_balance) ** (1 / years)) - 1) * 100
        else:
            cagr = 0
        
        dd_series = calculate_drawdown_series(daily_equity['equity'])
        max_dd = abs(dd_series.min())
        
        calmar_ratio = (cagr / max_dd) if max_dd > 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
        }
