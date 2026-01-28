"""
Default settings and instrument specifications
"""

# Instrument specifications
INSTRUMENT_SPECS = {
    'DE40': {
        'contract_size': 1,
        'point_value': 1,
        'currency': 'EUR',
        'type': 'index'
    },
    'XAUUSD': {
        'contract_size': 100,
        'point_value': 1,
        'currency': 'USD',
        'type': 'commodity'
    },
    'EURUSD': {
        'contract_size': 100000,
        'point_value': 0.0001,
        'currency': 'USD',
        'type': 'forex'
    },
    'GBPUSD': {
        'contract_size': 100000,
        'point_value': 0.0001,
        'currency': 'USD',
        'type': 'forex'
    },
}

# Default FX conversion rates (will be updated from M1 data if available)
DEFAULT_FX_RATES = {
    'EURUSD': 1.10,
    'GBPUSD': 1.27,
    'USDJPY': 110.0,
}

# Simulation defaults
DEFAULT_SETTINGS = {
    'starting_balance': 100000,
    'date_start': '2018-01-01',
    'date_end': '2025-12-31',
    'use_m1_for_equity': True,
    'conservative_dd_mode': False,
    'mae_mfe_tolerance': 0.05,
    'output_dir': 'output',
    'm1_data_folder': './data/m1_data',      # ← NEW
    'backtests_folder': './data/backtests',  # ← NEW
}

# Chart styling
CHART_STYLE = {
    'figure_width': 1200,
    'figure_height': 600,
    'color_positive': '#2ecc71',
    'color_negative': '#e74c3c',
    'color_equity': '#3498db',
    'color_drawdown': '#e67e22',
    'font_family': 'Arial, sans-serif',
}
