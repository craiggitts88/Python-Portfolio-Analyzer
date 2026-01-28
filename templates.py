"""
HTML Report Templates
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{REPORT_TITLE}}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .section {
            margin-bottom: 50px;
        }
        
        .section h2 {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #2E86AB;
            border-bottom: 3px solid #2E86AB;
            padding-bottom: 10px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .metric-card h3 {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #2E86AB;
        }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }
        
        .metric-row:last-child {
            border-bottom: none;
        }
        
        .metric-row span:first-child {
            font-weight: 500;
            color: #555;
        }
        
        .metric-row span:last-child {
            font-weight: 700;
            color: #333;
        }
        
        .positive {
            color: #10b981 !important;
        }
        
        .negative {
            color: #ef4444 !important;
        }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .algo-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .algo-table thead {
            background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
            color: white;
        }
        
        .algo-table th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        
        .algo-table td {
            padding: 12px 15px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .algo-table tbody tr:hover {
            background: #f9fafb;
        }
        
        .algo-table tbody tr:last-child td {
            border-bottom: none;
        }
        
        .config-summary {
            background: #f9fafb;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #2E86AB;
        }
        
        .config-summary p {
            margin-bottom: 10px;
            font-size: 1.05em;
        }
        
        .footer {
            background: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }
        
        @media (max-width: 768px) {
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
            
            .content {
                padding: 20px;
            }
        }
        
        /* Plotly chart responsiveness */
        .plotly-graph-div {
            width: 100% !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{REPORT_TITLE}}</h1>
            <p>Generated: {{GENERATION_TIME}}</p>
        </div>
        
        <div class="content">
            <!-- Configuration Summary -->
            <div class="section">
                <h2>📋 Configuration</h2>
                {{CONFIG_SUMMARY}}
            </div>
            
            <!-- Performance Metrics -->
            <div class="section">
                <h2>📊 Performance Metrics</h2>
                {{METRICS_SUMMARY}}
            </div>
            
            <!-- Equity Curve -->
            <div class="section">
                <h2>📈 Equity Curve</h2>
                <div class="chart-container">
                    {{EQUITY_CHART}}
                </div>
            </div>
            
            <!-- Drawdown -->
            <div class="section">
                <h2>📉 Drawdown Analysis</h2>
                <div class="chart-container">
                    {{DRAWDOWN_CHART}}
                </div>
            </div>
            
            <!-- Monthly Returns -->
            <div class="section">
                <h2>📅 Monthly Returns</h2>
                <div class="chart-container">
                    {{MONTHLY_RETURNS}}
                </div>
            </div>
            
            <!-- Trade Distribution -->
            <div class="section">
                <h2>💰 Trade Distribution</h2>
                <div class="chart-container">
                    {{TRADE_DISTRIBUTION}}
                </div>
            </div>
            
            <!-- Algorithm Attribution -->
            <div class="section">
                <h2>🤖 Algorithm Attribution</h2>
                <div class="chart-container">
                    {{ALGO_ATTRIBUTION}}
                </div>
                {{ALGO_TABLE}}
            </div>
        </div>
        
        <div class="footer">
            <p>Portfolio Simulator v1.0 | Built with Python, Pandas & Plotly</p>
        </div>
    </div>
</body>
</html>
"""
