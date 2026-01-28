"""
HTML Report Builder
"""

import json
from pathlib import Path
from datetime import datetime
import pandas as pd

from reporting.charts import ChartGenerator
from reporting.templates import HTML_TEMPLATE


class ReportBuilder:
    """Generate comprehensive HTML report"""
    
    def __init__(self, results, metrics, config):
        self.results = results
        self.metrics = metrics
        self.config = config
        self.output_dir = Path(config.get('output_settings', {}).get('output_dir', 'output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build(self):
        """Build complete HTML report"""
        
        print("\n5️⃣  Generating HTML report...")
        
        # Generate charts
        chart_gen = ChartGenerator(self.results, self.metrics, self.output_dir)
        charts = chart_gen.generate_all()
        
        # Export data
        self._export_data()
        
        # Save metrics as JSON
        self._save_metrics_json()
        
        # Build HTML
        html_path = self._build_html(charts)
        
        return html_path
    
    def _export_data(self):
        """Export equity curves and trades to CSV"""
        
        # Daily equity curve
        daily_path = self.output_dir / 'equity_curve_daily.csv'
        self.results['equity_curve'].to_csv(daily_path, index=False)
        print(f"      ✅ Saved daily equity: {daily_path}")
        
        # M1 equity curve (if available)
        if 'm1_equity' in self.results:
            m1_path = self.output_dir / 'equity_curve_m1.csv'
            self.results['m1_equity'].to_csv(m1_path, index=False)
            print(f"      ✅ Saved M1 equity: {m1_path}")
        
        # Combined trades
        trades_path = self.output_dir / 'trades_combined.csv'
        self.results['trades'].to_csv(trades_path, index=False)
        print(f"      ✅ Saved trades: {trades_path}")
    
    def _save_metrics_json(self):
        """Save metrics to JSON file"""
        
        # Convert metrics to JSON-serializable format
        metrics_json = self._serialize_metrics(self.metrics)
        
        json_path = self.output_dir / 'metrics.json'
        with open(json_path, 'w') as f:
            json.dump(metrics_json, f, indent=2)
        
        print(f"      ✅ Saved metrics: {json_path}")
    
    def _serialize_metrics(self, obj):
        """Convert metrics to JSON-serializable format"""
        
        if isinstance(obj, dict):
            return {k: self._serialize_metrics(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_metrics(item) for item in obj]
        elif isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        elif isinstance(obj, (pd.Series, pd.DataFrame)):
            return obj.to_dict()
        elif pd.isna(obj):
            return None
        else:
            return obj
    
    def _build_html(self, charts):
        """Build HTML report from template"""
        
        # Format metrics for display
        formatted_metrics = self._format_metrics()
        
        # Build algo attribution table
        algo_table = self._build_algo_table()
        
        # Build config summary
        config_summary = self._build_config_summary()
        
        # Replace template variables
        html = HTML_TEMPLATE
        html = html.replace('{{REPORT_TITLE}}', 'Portfolio Simulation Report')
        html = html.replace('{{GENERATION_TIME}}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        html = html.replace('{{CONFIG_SUMMARY}}', config_summary)
        html = html.replace('{{METRICS_SUMMARY}}', formatted_metrics)
        html = html.replace('{{EQUITY_CHART}}', charts['equity'])
        html = html.replace('{{DRAWDOWN_CHART}}', charts['drawdown'])
        html = html.replace('{{MONTHLY_RETURNS}}', charts['monthly_returns'])
        html = html.replace('{{TRADE_DISTRIBUTION}}', charts['trade_distribution'])
        html = html.replace('{{ALGO_ATTRIBUTION}}', charts['algo_attribution'])
        html = html.replace('{{ALGO_TABLE}}', algo_table)
        
        # Save HTML
        html_path = self.output_dir / 'report.html'
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"      ✅ Report saved: {html_path}")
        
        return html_path
    
    def _format_metrics(self):
        """Format metrics for HTML display"""
        
        m = self.metrics
        
        html = f"""
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Portfolio Performance</h3>
                <div class="metric-row">
                    <span>Starting Balance:</span>
                    <span>${m['starting_balance']:,.2f}</span>
                </div>
                <div class="metric-row">
                    <span>Ending Balance:</span>
                    <span>${m['ending_balance']:,.2f}</span>
                </div>
                <div class="metric-row">
                    <span>Total Return:</span>
                    <span class="{'positive' if m['total_return_pct'] > 0 else 'negative'}">{m['total_return_pct']:.2f}%</span>
                </div>
                <div class="metric-row">
                    <span>CAGR:</span>
                    <span class="{'positive' if m['cagr'] > 0 else 'negative'}">{m['cagr']:.2f}%</span>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>Risk Metrics</h3>
                <div class="metric-row">
                    <span>Max Drawdown:</span>
                    <span class="negative">{m['max_drawdown_pct']:.2f}%</span>
                </div>
                <div class="metric-row">
                    <span>Sharpe Ratio:</span>
                    <span>{m['sharpe_ratio']:.2f}</span>
                </div>
                <div class="metric-row">
                    <span>Sortino Ratio:</span>
                    <span>{m['sortino_ratio']:.2f}</span>
                </div>
                <div class="metric-row">
                    <span>Calmar Ratio:</span>
                    <span>{m['calmar_ratio']:.2f}</span>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>Trade Statistics</h3>
                <div class="metric-row">
                    <span>Total Trades:</span>
                    <span>{m['total_trades']}</span>
                </div>
                <div class="metric-row">
                    <span>Win Rate:</span>
                    <span class="{'positive' if m['win_rate'] > 50 else 'negative'}">{m['win_rate']:.2f}%</span>
                </div>
                <div class="metric-row">
                    <span>Profit Factor:</span>
                    <span>{m['profit_factor']:.2f}</span>
                </div>
                <div class="metric-row">
                    <span>Avg Win / Avg Loss:</span>
                    <span>{m['avg_win']:.2f} / {abs(m['avg_loss']):.2f}</span>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>Time Period</h3>
                <div class="metric-row">
                    <span>Start Date:</span>
                    <span>{m['start_date']}</span>
                </div>
                <div class="metric-row">
                    <span>End Date:</span>
                    <span>{m['end_date']}</span>
                </div>
                <div class="metric-row">
                    <span>Duration:</span>
                    <span>{m['duration_days']} days</span>
                </div>
                <div class="metric-row">
                    <span>Algorithms:</span>
                    <span>{m['num_algos']}</span>
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _build_algo_table(self):
        """Build algorithm attribution table"""
        
        if 'algo_attribution' not in self.metrics:
            return "<p>No algorithm attribution data available.</p>"
        
        attr = self.metrics['algo_attribution']
        
        html = """
        <table class="algo-table">
            <thead>
                <tr>
                    <th>Algorithm</th>
                    <th>Trades</th>
                    <th>Win Rate</th>
                    <th>Total P&L</th>
                    <th>Avg P&L</th>
                    <th>Max Win</th>
                    <th>Max Loss</th>
                    <th>Contribution</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for algo_name, stats in attr.items():
            pnl_class = 'positive' if stats['total_pnl'] > 0 else 'negative'
            
            html += f"""
                <tr>
                    <td><strong>{algo_name}</strong></td>
                    <td>{stats['num_trades']}</td>
                    <td>{stats['win_rate']:.1f}%</td>
                    <td class="{pnl_class}">${stats['total_pnl']:,.2f}</td>
                    <td>${stats['avg_pnl']:,.2f}</td>
                    <td class="positive">${stats['max_win']:,.2f}</td>
                    <td class="negative">${stats['max_loss']:,.2f}</td>
                    <td>{stats['contribution_pct']:.1f}%</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def _build_config_summary(self):
        """Build configuration summary"""
        
        html = f"""
        <div class="config-summary">
            <p><strong>Portfolio Balance:</strong> ${self.config['portfolio_balance']:,.2f}</p>
            <p><strong>Date Range:</strong> {self.config['date_start']} to {self.config['date_end']}</p>
            <p><strong>Algorithms:</strong> {len(self.config['algo_configs'])}</p>
        </div>
        """
        
        return html
