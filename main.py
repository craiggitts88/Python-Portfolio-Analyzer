#!/usr/bin/env python3
"""
Portfolio Simulator - Main Entry Point
Interactive prompts with config file persistence
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import DEFAULT_SETTINGS
from core.data_loader import DataLoader
from core.portfolio_engine import PortfolioEngine
from analytics.metrics import MetricsCalculator
from reporting.report_builder import ReportBuilder
from utils.validators import validate_config


def load_or_create_config():
    """Load existing config or create new one via interactive prompts"""
    config_path = Path('config/user_config.json')
    
    # Check if config exists
    if config_path.exists():
        print("\n" + "="*60)
        print("📁 Found existing configuration file")
        print("="*60)
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"\n📊 Portfolio Balance: ${config['portfolio_balance']:,.2f}")
        print(f"📅 Date Range: {config['date_start']} to {config['date_end']}")
        print(f"📂 M1 Data Folder: {config.get('m1_data_folder', config.get('data_folder', 'N/A'))}")
        print(f"📂 Backtests Folder: {config.get('backtests_folder', config.get('data_folder', 'N/A'))}")
        print(f"\n🤖 Algorithms Configured: {len(config['algo_configs'])}")
        for algo in config['algo_configs']:
            status = "✅ Enabled" if algo['enabled'] else "❌ Disabled"
            print(f"   - {algo['name']}: {algo['risk_per_trade']}% risk {status}")
        
        use_existing = input("\n❓ Use this configuration? (y/n): ").strip().lower()
        
        if use_existing == 'y':
            return config
        else:
            print("\n🔄 Creating new configuration...\n")
    
    # Create new config via prompts
    return create_config_interactive()


def create_config_interactive():
    """Interactive prompts to create configuration"""
    print("\n" + "="*60)
    print("🚀 PORTFOLIO SIMULATOR - CONFIGURATION WIZARD")
    print("="*60)
    
    config = {}
    
    # Portfolio settings
    print("\n📊 PORTFOLIO SETTINGS")
    print("-" * 60)
    
    default_balance = DEFAULT_SETTINGS['starting_balance']
    balance_input = input(f"Starting Portfolio Balance (default: ${default_balance:,}): ").strip()
    config['portfolio_balance'] = float(balance_input) if balance_input else default_balance
    
    default_start = DEFAULT_SETTINGS['date_start']
    start_input = input(f"Start Date (YYYY-MM-DD, default: {default_start}): ").strip()
    config['date_start'] = start_input if start_input else default_start
    
    default_end = DEFAULT_SETTINGS['date_end']
    end_input = input(f"End Date (YYYY-MM-DD, default: {default_end}): ").strip()
    config['date_end'] = end_input if end_input else default_end
    
    # Data folders
    print("\n📂 DATA LOCATION")
    print("-" * 60)
    
    default_m1_folder = DEFAULT_SETTINGS['m1_data_folder']
    m1_folder_input = input(f"M1 data folder (default: {default_m1_folder}): ").strip()
    config['m1_data_folder'] = m1_folder_input if m1_folder_input else default_m1_folder
    
    default_bt_folder = DEFAULT_SETTINGS['backtests_folder']
    bt_folder_input = input(f"Backtests folder (default: {default_bt_folder}): ").strip()
    config['backtests_folder'] = bt_folder_input if bt_folder_input else default_bt_folder
    
    # Create folders if they don't exist
    m1_path = Path(config['m1_data_folder'])
    bt_path = Path(config['backtests_folder'])
    
    if not m1_path.exists():
        print(f"⚠️  Creating M1 data folder: {m1_path}")
        m1_path.mkdir(parents=True, exist_ok=True)
    
    if not bt_path.exists():
        print(f"⚠️  Creating backtests folder: {bt_path}")
        bt_path.mkdir(parents=True, exist_ok=True)
    
    # Scan for M1 data files
    print(f"\n🔍 Scanning for M1 data files in: {m1_path}")
    m1_files = list(m1_path.glob("*_M1_*.csv"))
    
    if not m1_files:
        print(f"❌ No M1 data files found in: {m1_path}")
        print("   Expected format: SYMBOL_M1_YYYYMMDDHHMMSS_YYYYMMDDHHMMSS.csv")
        print("\n   Please add M1 CSV files to the folder and run again.")
        sys.exit(1)
    
    config['m1_data_files'] = {}
    print(f"\n✅ Found {len(m1_files)} M1 data file(s):")
    for m1_file in m1_files:
        # Extract symbol from filename (e.g., DE40_M1_... -> DE40)
        symbol = m1_file.stem.split('_M1_')[0]
        config['m1_data_files'][symbol] = m1_file.name
        print(f"   - {symbol}: {m1_file.name}")
    
    # Scan for backtest files
    print(f"\n🔍 Scanning for backtest files in: {bt_path}")
    backtest_files = list(bt_path.glob("*.xlsx")) + list(bt_path.glob("*.xls"))
    
    if not backtest_files:
        print(f"❌ No backtest Excel files found in: {bt_path}")
        print("\n   Please add backtest Excel files to the folder and run again.")
        sys.exit(1)
    
    print(f"\n✅ Found {len(backtest_files)} backtest file(s):")
    for i, bt_file in enumerate(backtest_files, 1):
        print(f"   {i}. {bt_file.name}")
    
    # Configure each algo
    print("\n🤖 ALGORITHM CONFIGURATION")
    print("-" * 60)
    
    config['algo_configs'] = []
    
    for i, bt_file in enumerate(backtest_files, 1):
        print(f"\n📈 Algorithm {i}/{len(backtest_files)}: {bt_file.stem}")
        
        enable = input(f"   Enable this algo? (y/n, default: y): ").strip().lower()
        if enable == 'n':
            continue
        
        risk_input = input(f"   Risk % per trade (e.g., 0.314 for 0.314%): ").strip()
        
        if not risk_input:
            print("   ⚠️  Skipping - no risk specified")
            continue
        
        try:
            risk_pct = float(risk_input)
        except ValueError:
            print("   ❌ Invalid risk percentage, skipping")
            continue
        
        config['algo_configs'].append({
            'name': bt_file.stem,
            'backtest_file': bt_file.name,
            'risk_per_trade': risk_pct,
            'enabled': True
        })
        
        print(f"   ✅ Added: {risk_pct}% risk per trade")
    
    if not config['algo_configs']:
        print("\n❌ No algorithms configured! Exiting.")
        sys.exit(1)
    
    # Output settings
    print("\n⚙️  OUTPUT SETTINGS")
    print("-" * 60)
    
    gen_m1 = input("Generate M1 equity curve CSV? (y/n, default: n): ").strip().lower()
    conservative = input("Use conservative DD mode? (y/n, default: n): ").strip().lower()
    
    config['output_settings'] = {
        'generate_m1_equity': gen_m1 == 'y',
        'conservative_dd': conservative == 'y',
        'output_dir': 'output'
    }
    
    # Save config
    print("\n💾 Saving configuration...")
    config_path = Path('config/user_config.json')
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuration saved to: {config_path}")
    
    return config


def run_simulation(config):
    """Run the portfolio simulation"""
    print("\n" + "="*60)
    print("🚀 STARTING PORTFOLIO SIMULATION")
    print("="*60)
    
    try:
        # Validate configuration
        print("\n1️⃣  Validating configuration...")
        validate_config(config)
        print("   ✅ Configuration valid")
        
        # Load data
        print("\n2️⃣  Loading data...")
        loader = DataLoader(config)
        m1_data, backtest_data = loader.load_all()
        print(f"   ✅ Loaded {len(m1_data)} M1 datasets")
        print(f"   ✅ Loaded {len(backtest_data)} backtest datasets")
        
        # Run simulation
        print("\n3️⃣  Running portfolio simulation...")
        engine = PortfolioEngine(config, m1_data, backtest_data)
        results = engine.run()
        print(f"   ✅ Simulated {results['total_trades']} trades")
        print(f"   ✅ Generated {len(results['equity_curve'])} equity points")
        
        # Calculate metrics
        print("\n4️⃣  Calculating performance metrics...")
        calculator = MetricsCalculator(results, config)
        metrics = calculator.calculate_all()
        print(f"   ✅ Total Return: {metrics['total_return']:.2f}%")
        print(f"   ✅ CAGR: {metrics['cagr']:.2f}%")
        print(f"   ✅ Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"   ✅ Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        
        # Generate report
        print("\n5️⃣  Generating HTML report...")
        reporter = ReportBuilder(results, metrics, config)
        report_path = reporter.build()
        print(f"   ✅ Report saved to: {report_path}")
        
        print("\n" + "="*60)
        print("✅ SIMULATION COMPLETE!")
        print("="*60)
        print(f"\n📊 View your report: {report_path}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("💼 MULTI-ALGO PORTFOLIO SIMULATOR")
    print("   Accurate path-based drawdown calculation")
    print("="*60)
    
    # Load or create config
    config = load_or_create_config()
    
    # Confirm before running
    print("\n" + "="*60)
    print("📋 CONFIGURATION SUMMARY")
    print("="*60)
    print(f"💰 Starting Balance: ${config['portfolio_balance']:,.2f}")
    print(f"📅 Period: {config['date_start']} to {config['date_end']}")
    print(f"🤖 Active Algos: {len([a for a in config['algo_configs'] if a['enabled']])}")
    print(f"📊 Total Risk: {sum(a['risk_per_trade'] for a in config['algo_configs'] if a['enabled']):.3f}% per concurrent trade")
    
    proceed = input("\n▶️  Proceed with simulation? (y/n): ").strip().lower()
    
    if proceed != 'y':
        print("\n❌ Simulation cancelled")
        sys.exit(0)
    
    # Run simulation
    run_simulation(config)


if __name__ == "__main__":
    main()
