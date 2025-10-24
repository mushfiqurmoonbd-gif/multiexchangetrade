import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass

@dataclass
class BacktestMetrics:
    """Comprehensive backtesting metrics"""
    # Basic metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # P&L metrics
    total_profit: float
    total_loss: float
    net_profit: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    
    # Return metrics
    total_return: float
    annualized_return: float
    avg_trade_return: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_duration: int
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional Value at Risk 95%
    
    # Time metrics
    avg_trade_duration: float
    avg_winning_trade_duration: float
    avg_losing_trade_duration: float
    
    # Consistency metrics
    consecutive_wins: int
    consecutive_losses: int
    recovery_factor: float
    expectancy: float
    
    # Monthly metrics
    monthly_returns: List[float]
    best_month: float
    worst_month: float
    positive_months: int
    negative_months: int

class ComprehensiveMetricsCalculator:
    """
    Comprehensive backtesting metrics calculator with detailed reporting
    """
    
    def __init__(self):
        self.metrics_history = []
    
    def calculate_comprehensive_metrics(self, 
                                      equity_curve: pd.Series,
                                      trades: List[Dict],
                                      initial_capital: float,
                                      risk_free_rate: float = 0.02) -> BacktestMetrics:
        """
        Calculate comprehensive backtesting metrics
        
        Args:
            equity_curve: Equity curve over time
            trades: List of trade dictionaries
            initial_capital: Initial capital
            risk_free_rate: Risk-free rate for Sharpe ratio
            
        Returns:
            BacktestMetrics: Comprehensive metrics object
        """
        # Basic trade metrics
        closed_trades = [t for t in trades if 'pnl' in t and t.get('status') == 'closed']
        
        if not closed_trades:
            return self._create_empty_metrics()
        
        # Separate winning and losing trades
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] < 0]
        
        # Basic counts
        total_trades = len(closed_trades)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)
        win_rate = winning_count / total_trades if total_trades > 0 else 0
        
        # P&L calculations
        total_profit = sum(t['pnl'] for t in winning_trades)
        total_loss = abs(sum(t['pnl'] for t in losing_trades))
        net_profit = total_profit - total_loss
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Average calculations
        avg_win = total_profit / winning_count if winning_count > 0 else 0
        avg_loss = total_loss / losing_count if losing_count > 0 else 0
        
        # Largest trades
        largest_win = max((t['pnl'] for t in winning_trades), default=0)
        largest_loss = min((t['pnl'] for t in losing_trades), default=0)
        
        # Return calculations
        final_capital = equity_curve.iloc[-1] if len(equity_curve) > 0 else initial_capital
        total_return = (final_capital - initial_capital) / initial_capital
        
        # Calculate trading days
        trading_days = len(equity_curve)
        years = trading_days / 252  # Assuming 252 trading days per year
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        avg_trade_return = net_profit / total_trades if total_trades > 0 else 0
        
        # Risk metrics
        returns = equity_curve.pct_change().dropna()
        
        # Drawdown calculations
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        max_drawdown = drawdown.min()
        
        # Max drawdown duration
        max_dd_duration = self._calculate_max_drawdown_duration(drawdown)
        
        # Risk-adjusted returns
        sharpe_ratio = self._calculate_sharpe_ratio(returns, risk_free_rate)
        sortino_ratio = self._calculate_sortino_ratio(returns, risk_free_rate)
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Value at Risk calculations
        var_95, cvar_95 = self._calculate_var_cvar(returns, 0.95)
        
        # Trade duration metrics
        duration_metrics = self._calculate_duration_metrics(closed_trades)
        
        # Consistency metrics
        consecutive_wins, consecutive_losses = self._calculate_consecutive_trades(closed_trades)
        recovery_factor = net_profit / abs(max_drawdown) if max_drawdown != 0 else 0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        # Monthly metrics
        monthly_metrics = self._calculate_monthly_metrics(equity_curve, initial_capital)
        
        return BacktestMetrics(
            # Basic metrics
            total_trades=total_trades,
            winning_trades=winning_count,
            losing_trades=losing_count,
            win_rate=win_rate,
            
            # P&L metrics
            total_profit=total_profit,
            total_loss=total_loss,
            net_profit=net_profit,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            
            # Return metrics
            total_return=total_return,
            annualized_return=annualized_return,
            avg_trade_return=avg_trade_return,
            
            # Risk metrics
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            var_95=var_95,
            cvar_95=cvar_95,
            
            # Time metrics
            avg_trade_duration=duration_metrics['avg_duration'],
            avg_winning_trade_duration=duration_metrics['avg_winning_duration'],
            avg_losing_trade_duration=duration_metrics['avg_losing_duration'],
            
            # Consistency metrics
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses,
            recovery_factor=recovery_factor,
            expectancy=expectancy,
            
            # Monthly metrics
            monthly_returns=monthly_metrics['monthly_returns'],
            best_month=monthly_metrics['best_month'],
            worst_month=monthly_metrics['worst_month'],
            positive_months=monthly_metrics['positive_months'],
            negative_months=monthly_metrics['negative_months']
        )
    
    def _create_empty_metrics(self) -> BacktestMetrics:
        """Create empty metrics for cases with no trades"""
        return BacktestMetrics(
            total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
            total_profit=0.0, total_loss=0.0, net_profit=0.0, profit_factor=0.0,
            avg_win=0.0, avg_loss=0.0, largest_win=0.0, largest_loss=0.0,
            total_return=0.0, annualized_return=0.0, avg_trade_return=0.0,
            max_drawdown=0.0, max_drawdown_duration=0, sharpe_ratio=0.0,
            sortino_ratio=0.0, calmar_ratio=0.0, var_95=0.0, cvar_95=0.0,
            avg_trade_duration=0.0, avg_winning_trade_duration=0.0, avg_losing_trade_duration=0.0,
            consecutive_wins=0, consecutive_losses=0, recovery_factor=0.0, expectancy=0.0,
            monthly_returns=[], best_month=0.0, worst_month=0.0, positive_months=0, negative_months=0
        )
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        if returns.std() == 0:
            return 0.0
        return (excess_returns.mean() / returns.std()) * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float) -> float:
        """Calculate Sortino ratio"""
        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = returns[returns < 0]
        if downside_returns.std() == 0:
            return 0.0
        return (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)
    
    def _calculate_var_cvar(self, returns: pd.Series, confidence_level: float) -> Tuple[float, float]:
        """Calculate Value at Risk and Conditional Value at Risk"""
        var = np.percentile(returns, (1 - confidence_level) * 100)
        cvar = returns[returns <= var].mean()
        return var, cvar
    
    def _calculate_max_drawdown_duration(self, drawdown: pd.Series) -> int:
        """Calculate maximum drawdown duration in periods"""
        in_drawdown = drawdown < 0
        drawdown_periods = []
        current_period = 0
        
        for is_dd in in_drawdown:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0
        
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        return max(drawdown_periods) if drawdown_periods else 0
    
    def _calculate_duration_metrics(self, trades: List[Dict]) -> Dict[str, float]:
        """Calculate trade duration metrics"""
        durations = []
        winning_durations = []
        losing_durations = []
        
        for trade in trades:
            if 'entry_time' in trade and 'exit_time' in trade:
                duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600  # Hours
                durations.append(duration)
                
                if trade['pnl'] > 0:
                    winning_durations.append(duration)
                else:
                    losing_durations.append(duration)
        
        return {
            'avg_duration': np.mean(durations) if durations else 0.0,
            'avg_winning_duration': np.mean(winning_durations) if winning_durations else 0.0,
            'avg_losing_duration': np.mean(losing_durations) if losing_durations else 0.0
        }
    
    def _calculate_consecutive_trades(self, trades: List[Dict]) -> Tuple[int, int]:
        """Calculate maximum consecutive wins and losses"""
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in trades:
            if trade['pnl'] > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
        
        return max_consecutive_wins, max_consecutive_losses
    
    def _calculate_monthly_metrics(self, equity_curve: pd.Series, initial_capital: float) -> Dict[str, Any]:
        """Calculate monthly return metrics"""
        if len(equity_curve) == 0:
            return {
                'monthly_returns': [],
                'best_month': 0.0,
                'worst_month': 0.0,
                'positive_months': 0,
                'negative_months': 0
            }
        
        # Resample to monthly data
        monthly_equity = equity_curve.resample('M').last()
        monthly_returns = monthly_equity.pct_change().dropna()
        
        if len(monthly_returns) == 0:
            return {
                'monthly_returns': [],
                'best_month': 0.0,
                'worst_month': 0.0,
                'positive_months': 0,
                'negative_months': 0
            }
        
        positive_months = (monthly_returns > 0).sum()
        negative_months = (monthly_returns < 0).sum()
        
        return {
            'monthly_returns': monthly_returns.tolist(),
            'best_month': monthly_returns.max(),
            'worst_month': monthly_returns.min(),
            'positive_months': positive_months,
            'negative_months': negative_months
        }
    
    def generate_comprehensive_report(self, metrics: BacktestMetrics) -> str:
        """
        Generate comprehensive backtesting report
        
        Args:
            metrics: BacktestMetrics object
            
        Returns:
            str: Formatted report
        """
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                           COMPREHENSIVE BACKTEST REPORT                        ║
╚══════════════════════════════════════════════════════════════════════════════════╝

📊 BASIC METRICS
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Total Trades:           {metrics.total_trades:>8}                                    │
│ Winning Trades:         {metrics.winning_trades:>8}                                    │
│ Losing Trades:          {metrics.losing_trades:>8}                                    │
│ Win Rate:               {metrics.win_rate:>8.2%}                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

💰 P&L METRICS
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Total Profit:           ${metrics.total_profit:>8,.2f}                                    │
│ Total Loss:             ${metrics.total_loss:>8,.2f}                                    │
│ Net Profit:             ${metrics.net_profit:>8,.2f}                                    │
│ Profit Factor:           {metrics.profit_factor:>8.2f}                                    │
│ Average Win:            ${metrics.avg_win:>8,.2f}                                    │
│ Average Loss:            ${metrics.avg_loss:>8,.2f}                                    │
│ Largest Win:             ${metrics.largest_win:>8,.2f}                                    │
│ Largest Loss:            ${metrics.largest_loss:>8,.2f}                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

📈 RETURN METRICS
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Total Return:           {metrics.total_return:>8.2%}                                    │
│ Annualized Return:      {metrics.annualized_return:>8.2%}                                    │
│ Average Trade Return:   ${metrics.avg_trade_return:>8,.2f}                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

⚠️  RISK METRICS
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Max Drawdown:           {metrics.max_drawdown:>8.2%}                                    │
│ Max DD Duration:        {metrics.max_drawdown_duration:>8} periods                              │
│ Sharpe Ratio:           {metrics.sharpe_ratio:>8.2f}                                    │
│ Sortino Ratio:          {metrics.sortino_ratio:>8.2f}                                    │
│ Calmar Ratio:           {metrics.calmar_ratio:>8.2f}                                    │
│ VaR (95%):              {metrics.var_95:>8.2%}                                    │
│ CVaR (95%):             {metrics.cvar_95:>8.2%}                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

⏱️  TIME METRICS
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Avg Trade Duration:     {metrics.avg_trade_duration:>8.1f} hours                              │
│ Avg Winning Duration:   {metrics.avg_winning_trade_duration:>8.1f} hours                              │
│ Avg Losing Duration:    {metrics.avg_losing_trade_duration:>8.1f} hours                              │
└─────────────────────────────────────────────────────────────────────────────────┘

🎯 CONSISTENCY METRICS
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Max Consecutive Wins:   {metrics.consecutive_wins:>8}                                    │
│ Max Consecutive Losses: {metrics.consecutive_losses:>8}                                    │
│ Recovery Factor:        {metrics.recovery_factor:>8.2f}                                    │
│ Expectancy:             ${metrics.expectancy:>8,.2f}                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

📅 MONTHLY METRICS
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Best Month:             {metrics.best_month:>8.2%}                                    │
│ Worst Month:            {metrics.worst_month:>8.2%}                                    │
│ Positive Months:        {metrics.positive_months:>8}                                    │
│ Negative Months:        {metrics.negative_months:>8}                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════════════════════════╗
║                              PERFORMANCE SUMMARY                               ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""
        
        # Add performance summary
        if metrics.sharpe_ratio > 2.0:
            performance = "EXCELLENT"
        elif metrics.sharpe_ratio > 1.5:
            performance = "VERY GOOD"
        elif metrics.sharpe_ratio > 1.0:
            performance = "GOOD"
        elif metrics.sharpe_ratio > 0.5:
            performance = "FAIR"
        else:
            performance = "POOR"
        
        report += f"""
Overall Performance Rating: {performance}
Sharpe Ratio: {metrics.sharpe_ratio:.2f}
Max Drawdown: {metrics.max_drawdown:.2%}
Win Rate: {metrics.win_rate:.2%}
"""
        
        return report
    
    def export_metrics_to_csv(self, metrics: BacktestMetrics, filename: str):
        """Export metrics to CSV file"""
        metrics_dict = {
            'Metric': [
                'Total Trades', 'Winning Trades', 'Losing Trades', 'Win Rate',
                'Total Profit', 'Total Loss', 'Net Profit', 'Profit Factor',
                'Average Win', 'Average Loss', 'Largest Win', 'Largest Loss',
                'Total Return', 'Annualized Return', 'Average Trade Return',
                'Max Drawdown', 'Max DD Duration', 'Sharpe Ratio', 'Sortino Ratio',
                'Calmar Ratio', 'VaR 95%', 'CVaR 95%', 'Recovery Factor', 'Expectancy'
            ],
            'Value': [
                metrics.total_trades, metrics.winning_trades, metrics.losing_trades, metrics.win_rate,
                metrics.total_profit, metrics.total_loss, metrics.net_profit, metrics.profit_factor,
                metrics.avg_win, metrics.avg_loss, metrics.largest_win, metrics.largest_loss,
                metrics.total_return, metrics.annualized_return, metrics.avg_trade_return,
                metrics.max_drawdown, metrics.max_drawdown_duration, metrics.sharpe_ratio, metrics.sortino_ratio,
                metrics.calmar_ratio, metrics.var_95, metrics.cvar_95, metrics.recovery_factor, metrics.expectancy
            ]
        }
        
        df = pd.DataFrame(metrics_dict)
        df.to_csv(filename, index=False)
        print(f"Metrics exported to {filename}")
