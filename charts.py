"""
Chart generation using Plotly
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


class ChartGenerator:
    """Generate interactive charts for report"""
    
    def __init__(self, results, metrics, output_dir):
        self.results = results
        self.metrics = metrics
        self.output_dir = output_dir
    
    def generate_all(self):
        """Generate all charts"""
        
        charts = {}
        
        print("      Generating equity curve chart...")
        charts['equity'] = self.generate_equity_curve()
        
        print("      Generating drawdown chart...")
        charts['drawdown'] = self.generate_drawdown_chart()
        
        print("      Generating monthly returns heatmap...")
        charts['monthly_returns'] = self.generate_monthly_returns()
        
        print("      Generating trade distribution...")
        charts['trade_distribution'] = self.generate_trade_distribution()
        
        print("      Generating algo attribution...")
        charts['algo_attribution'] = self.generate_algo_attribution()
        
        return charts
    
    def generate_equity_curve(self):
        """Generate equity curve chart"""
        
        df = self.results['equity_curve']
        
        fig = go.Figure()
        
        # Main equity curve
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['equity'],
            mode='lines',
            name='Portfolio Equity',
            line=dict(color='#2E86AB', width=2),
            hovertemplate='%{x}<br>Equity: $%{y:,.2f}<extra></extra>'
        ))
        
        # Add drawdown shading
        if 'drawdown_pct' in df.columns:
            # Find drawdown periods
            dd_periods = df[df['drawdown_pct'] < -1].copy()
            
            if len(dd_periods) > 0:
                fig.add_trace(go.Scatter(
                    x=dd_periods['datetime'],
                    y=dd_periods['equity'],
                    mode='markers',
                    name='Drawdown > 1%',
                    marker=dict(color='red', size=3, opacity=0.3),
                    showlegend=False,
                    hovertemplate='DD: %{text}%<extra></extra>',
                    text=dd_periods['drawdown_pct'].round(2)
                ))
        
        fig.update_layout(
            title='Portfolio Equity Curve',
            xaxis_title='Date',
            yaxis_title='Equity ($)',
            hovermode='x unified',
            template='plotly_white',
            height=500
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='equity-chart')
    
    def generate_drawdown_chart(self):
        """Generate drawdown chart"""
        
        df = self.results['equity_curve']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['drawdown_pct'],
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            line=dict(color='#A23B72', width=2),
            hovertemplate='%{x}<br>Drawdown: %{y:.2f}%<extra></extra>'
        ))
        
        # Mark max drawdown
        max_dd_idx = df['drawdown_pct'].idxmin()
        max_dd_date = df.loc[max_dd_idx, 'datetime']
        max_dd_val = df.loc[max_dd_idx, 'drawdown_pct']
        
        fig.add_trace(go.Scatter(
            x=[max_dd_date],
            y=[max_dd_val],
            mode='markers',
            name='Max Drawdown',
            marker=dict(color='red', size=10),
            hovertemplate=f'Max DD: {max_dd_val:.2f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title='Portfolio Drawdown',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='drawdown-chart')
    
    def generate_monthly_returns(self):
        """Generate monthly returns heatmap"""
        
        df = self.results['equity_curve'].copy()
        df.set_index('datetime', inplace=True)
        
        # Resample to monthly
        monthly_equity = df['equity'].resample('ME').last()
        monthly_returns = monthly_equity.pct_change() * 100
        
        # Create pivot table for heatmap
        monthly_returns_df = monthly_returns.to_frame('return')
        monthly_returns_df['year'] = monthly_returns_df.index.year
        monthly_returns_df['month'] = monthly_returns_df.index.month
        
        pivot = monthly_returns_df.pivot(index='year', columns='month', values='return')
        
        # Month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=month_names,
            y=pivot.index,
            colorscale='RdYlGn',
            zmid=0,
            text=np.round(pivot.values, 2),
            texttemplate='%{text}%',
            textfont={"size": 10},
            hovertemplate='%{y} %{x}<br>Return: %{z:.2f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title='Monthly Returns (%)',
            xaxis_title='Month',
            yaxis_title='Year',
            template='plotly_white',
            height=400
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='monthly-returns-chart')
    
    def generate_trade_distribution(self):
        """Generate trade P&L distribution"""
        
        trades = self.results['trades']
        
        fig = go.Figure()
        
        # Histogram of P&L
        fig.add_trace(go.Histogram(
            x=trades['pnl'],
            nbinsx=50,
            name='Trade P&L',
            marker=dict(
                color=trades['pnl'],
                colorscale='RdYlGn',
                cmid=0,
                line=dict(color='white', width=1)
            ),
            hovertemplate='P&L: $%{x:.2f}<br>Count: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Trade P&L Distribution',
            xaxis_title='P&L ($)',
            yaxis_title='Number of Trades',
            template='plotly_white',
            height=400,
            showlegend=False
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='trade-dist-chart')
    
    def generate_algo_attribution(self):
        """Generate algorithm attribution chart"""
        
        if 'algo_attribution' not in self.metrics:
            return "<p>No attribution data available.</p>"
        
        attr = self.metrics['algo_attribution']
        
        # Prepare data
        algos = list(attr.keys())
        pnls = [attr[algo]['total_pnl'] for algo in algos]
        colors = ['green' if pnl > 0 else 'red' for pnl in pnls]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=algos,
            y=pnls,
            marker=dict(color=colors),
            text=[f'${pnl:,.0f}' for pnl in pnls],
            textposition='outside',
            hovertemplate='%{x}<br>P&L: $%{y:,.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Algorithm P&L Attribution',
            xaxis_title='Algorithm',
            yaxis_title='Total P&L ($)',
            template='plotly_white',
            height=400,
            showlegend=False
        )
        
        # Rotate x-axis labels if many algos
        if len(algos) > 5:
            fig.update_xaxes(tickangle=-45)
        
        return fig.to_html(include_plotlyjs='cdn', div_id='algo-attribution-chart')
