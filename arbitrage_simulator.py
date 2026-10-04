import yfinance as yf
import pandas as pd
import numpy as np
import requests

def send_discord_alert(webhook_url, message):
    """Sends simulation alerts and final reports directly to Discord once at the conclusion."""
    try:
        requests.post(webhook_url, json={"content": message}, timeout=5)
    except Exception as e:
        print(f"Discord webhook connection error: {e}")

def run_loosened_gate_arbitrage():
    # Discord Webhook Configuration
    webhook_url = "YOUR_WEBHOOK_DISCORD_LINK_HERE"
    
    initial_capital = 10000.0
    cash = initial_capital
    trade_count = 0
    winning_trades = 0
    losing_trades = 0
    timeout_losses = 0
    trailing_stop_liquidation_count = 0
    total_fees_paid = 0.0
    
    peak_portfolio_value = initial_capital
    max_drawdown_pct = 0.0
    circuit_triggered = False
    
    print("Fetching AAPL intraday data for loosened-gate institutional backtest...")
    prices = []
    try:
        df = yf.download("AAPL", period="7d", interval="1m", progress=False)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if 'Close' in df.columns:
                prices = df['Close'].dropna().tolist()
    except Exception:
        pass

    if len(prices) == 0:
        print("Using fallback price sequence...")
        prices = [
            220.10, 220.15, 220.05, 220.20, 220.35, 220.30, 220.45, 220.40, 220.55, 220.60,
            220.50, 220.65, 220.70, 220.85, 220.80, 220.95, 221.00, 220.90, 221.10, 221.15,
            221.25, 221.30, 221.20, 221.40, 221.50, 221.45, 221.60, 221.70, 221.65, 221.80
        ]

    # Retain 4-step tick density
    tick_prices = []
    for i in range(len(prices) - 1):
        p1 = prices[i]
        p2 = prices[i+1]
        sub_ticks = np.linspace(p1, p2, 4)
        tick_prices.extend(sub_ticks)

    # Calculate rolling 30-tick standard deviation
    series_prices = pd.Series(tick_prices)
    rolling_std = series_prices.rolling(window=30).std().fillna(0.05).tolist()

    print(f"Processing {len(tick_prices)} high-frequency ticks with 1.5x volatility & 1.1x fee cushion gates...")

    i = 0
    while i < len(tick_prices) - 51:
        base_price = tick_prices[i]
        curr_std = rolling_std[i]
        
        # Rule 1: Volatility Gate lowered to 1.5x rolling standard deviation
        dynamic_threshold = max(0.04, 1.5 * curr_std)
        
        feed_a = base_price + np.random.uniform(-0.10, 0.15)
        feed_b = base_price + np.random.uniform(-0.15, 0.10)
        
        discrepancy = feed_a - feed_b
        estimated_fee_hurdle = base_price * 0.0005
        
        # Rule 2: Fee Cushion lowered to 1.1x the estimated transaction fee hurdle
        if abs(discrepancy) >= dynamic_threshold and abs(discrepancy) >= (1.1 * estimated_fee_hurdle) and cash > 100:
            if discrepancy > 0:
                entry_price = feed_b
                is_long_feed_b = True
            else:
                entry_price = feed_a
                is_long_feed_b = False
                
            if trade_count == 0:
                trade_capital = cash * 0.90
            else:
                trade_capital = cash * 0.15
                
            shares = trade_capital / entry_price
            invested_amount = shares * entry_price
            fee = invested_amount * 0.0005
            total_fees_paid += fee
            
            required_exit_price = entry_price + (fee / shares)
            
            exit_found = False
            exit_price = 0.0
            exit_idx = i + 1
            is_trailing_stop = False
            highest_favorable_price = entry_price
            
            # Inventory holding module with 0.5% Trailing Stop-Loss & 50-tick timeout
            for offset in range(1, 51):
                check_idx = i + offset
                if check_idx >= len(tick_prices):
                    break
                future_base = tick_prices[check_idx]
                future_feed_a = future_base + np.random.uniform(-0.10, 0.15)
                future_feed_b = future_base + np.random.uniform(-0.15, 0.10)
                
                current_potential_exit = future_feed_a if is_long_feed_b else future_feed_b
                
                if current_potential_exit > highest_favorable_price:
                    highest_favorable_price = current_potential_exit
                
                # Trailing Stop-Loss trigger (0.5% drop from peak favorable price)
                tsl_threshold = highest_favorable_price * 0.995
                if current_potential_exit <= tsl_threshold and current_potential_exit < required_exit_price:
                    exit_price = current_potential_exit
                    exit_idx = check_idx
                    exit_found = True
                    is_trailing_stop = True
                    break
                
                if current_potential_exit >= required_exit_price:
                    exit_price = current_potential_exit
                    exit_idx = check_idx
                    exit_found = True
                    break
            
            if not exit_found:
                timeout_idx = min(i + 50, len(tick_prices) - 1)
                future_base = tick_prices[timeout_idx]
                future_feed_a = future_base + np.random.uniform(-0.10, 0.15)
                future_feed_b = future_base + np.random.uniform(-0.15, 0.10)
                exit_price = future_feed_a if is_long_feed_b else future_feed_b
                exit_idx = timeout_idx
                losing_trades += 1
                timeout_losses += 1
            elif is_trailing_stop:
                losing_trades += 1
                trailing_stop_liquidation_count += 1
            else:
                winning_trades += 1
                
            gross_profit = shares * (exit_price - entry_price)
            net_trade_profit = gross_profit - fee
            cash += net_trade_profit
            trade_count += 1
            
            if cash > peak_portfolio_value:
                peak_portfolio_value = cash
            
            current_drawdown = (peak_portfolio_value - cash) / peak_portfolio_value
            if current_drawdown > max_drawdown_pct:
                max_drawdown_pct = current_drawdown
                
            if current_drawdown > 0.03:
                circuit_triggered = True
                print("CIRCUIT BREAKER TRIGGERED - Algorithm halted due to 3%+ drawdown.")
                break
                
            i = exit_idx
        else:
            i += 1

    final_portfolio_value = cash
    total_profit = final_portfolio_value - initial_capital
    roi_pct = (total_profit / initial_capital) * 100
    win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0.0

    report = (
        "=== LOOSENED GATE 1.5x INSTITUTIONAL EXECUTION REPORT ===\n"
        f"Initial Capital:          ${initial_capital:,.2f}\n"
        f"Final Portfolio Value:    ${final_portfolio_value:,.2f}\n"
        f"Net Profit:               ${total_profit:+,.2f} ({roi_pct:+.2f}%)\n"
        f"Total Trades Executed:    {trade_count}\n"
        f"Winning Trades:           {winning_trades}\n"
        f"Losing Trades:            {losing_trades}\n"
        f"Latency Timeout Losses:   {timeout_losses}\n"
        f"Trailing Stop Liquidations: {trailing_stop_liquidation_count}\n"
        f"Win Rate:                 {win_rate:.2f}%\n"
        f"Total Transaction Fees:   ${total_fees_paid:,.2f}\n"
        f"Max Peak-to-Trough DD:    {max_drawdown_pct * 100:.2f}%\n"
        f"Circuit Breaker Status:   {'TRIGGERED (HALTED)' if circuit_triggered else 'NORMAL (PASSED)'}"
    )

    print("\n" + report)
    
    # Single webhook invocation at absolute conclusion
    send_discord_alert(webhook_url, f"```\n{report}\n```")

if __name__ == "__main__":
    run_loosened_gate_arbitrage()
