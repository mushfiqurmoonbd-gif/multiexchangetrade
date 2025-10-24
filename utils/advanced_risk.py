import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class AdvancedRiskManager:
    """
    Advanced risk management system with:
    - TP1/TP2/Runner system
    - Daily breaker
    - Configurable stop-loss percentages
    - Position sizing
    """
    
    def __init__(self, 
                 initial_capital: float = 10000.0,
                 risk_per_trade: float = 0.02,
                 daily_loss_limit: float = 0.05,
                 max_positions: int = 5):
        """
        Initialize advanced risk manager
        
        Args:
            initial_capital: Starting capital
            risk_per_trade: Risk per trade as percentage of capital
            daily_loss_limit: Maximum daily loss as percentage of capital
            max_positions: Maximum number of concurrent positions
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.daily_loss_limit = daily_loss_limit
        self.max_positions = max_positions
        
        # Daily tracking
        self.daily_start_capital = initial_capital
        self.daily_trades = []
        self.daily_pnl = 0.0
        
        # Position tracking
        self.positions: List[Dict] = []
        self.closed_trades: List[Dict] = []
        
    def reset_daily_tracking(self):
        """Reset daily tracking variables"""
        self.daily_start_capital = self.current_capital
        self.daily_trades = []
        self.daily_pnl = 0.0
    
    def is_daily_breaker_triggered(self) -> bool:
        """
        Check if daily loss limit has been exceeded
        
        Returns:
            bool: True if daily breaker is triggered
        """
        daily_loss_pct = abs(self.daily_pnl) / self.daily_start_capital
        return daily_loss_pct >= self.daily_loss_limit
    
    def calculate_position_size(self, 
                              entry_price: float,
                              stop_loss_price: float,
                              risk_amount: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate position size based on risk management rules
        
        Args:
            entry_price: Entry price for the position
            stop_loss_price: Stop loss price
            risk_amount: Custom risk amount (optional)
            
        Returns:
            Dict containing position size and risk details
        """
        if risk_amount is None:
            risk_amount = self.current_capital * self.risk_per_trade
        
        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)
        
        if risk_per_share <= 0:
            return {
                'quantity': 0.0,
                'risk_amount': 0.0,
                'risk_per_share': 0.0,
                'position_value': 0.0
            }
        
        # Calculate quantity based on risk
        quantity = risk_amount / risk_per_share
        
        # Calculate position value
        position_value = quantity * entry_price
        
        # Ensure we don't exceed available capital
        max_position_value = self.current_capital * 0.9  # Use max 90% of capital
        if position_value > max_position_value:
            quantity = max_position_value / entry_price
            position_value = quantity * entry_price
            risk_amount = quantity * risk_per_share
        
        return {
            'quantity': quantity,
            'risk_amount': risk_amount,
            'risk_per_share': risk_per_share,
            'position_value': position_value
        }
    
    def create_tp1_tp2_runner_system(self,
                                   entry_price: float,
                                   stop_loss_price: float,
                                   tp1_multiplier: float = 1.5,
                                   tp2_multiplier: float = 2.0,
                                   runner_multiplier: float = 3.0) -> Dict[str, float]:
        """
        Create TP1/TP2/Runner system
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            tp1_multiplier: TP1 multiplier (default: 1.5x risk)
            tp2_multiplier: TP2 multiplier (default: 2.0x risk)
            runner_multiplier: Runner multiplier (default: 3.0x risk)
            
        Returns:
            Dict containing TP1, TP2, Runner prices
        """
        risk_amount = abs(entry_price - stop_loss_price)
        
        tp1_price = entry_price + (risk_amount * tp1_multiplier)
        tp2_price = entry_price + (risk_amount * tp2_multiplier)
        runner_price = entry_price + (risk_amount * runner_multiplier)
        
        return {
            'tp1_price': tp1_price,
            'tp2_price': tp2_price,
            'runner_price': runner_price,
            'risk_amount': risk_amount
        }
    
    def open_position(self,
                     symbol: str,
                     side: str,
                     entry_price: float,
                     stop_loss_price: float,
                     tp1_multiplier: float = 1.5,
                     tp2_multiplier: float = 2.0,
                     runner_multiplier: float = 3.0,
                     custom_risk: Optional[float] = None) -> Optional[Dict]:
        """
        Open a new position with advanced risk management
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            entry_price: Entry price
            stop_loss_price: Stop loss price
            tp1_multiplier: TP1 multiplier
            tp2_multiplier: TP2 multiplier
            runner_multiplier: Runner multiplier
            custom_risk: Custom risk amount
            
        Returns:
            Dict: Position details or None if position cannot be opened
        """
        # Check daily breaker
        if self.is_daily_breaker_triggered():
            return None
        
        # Check max positions
        if len(self.positions) >= self.max_positions:
            return None
        
        # Calculate position size
        position_size = self.calculate_position_size(entry_price, stop_loss_price, custom_risk)
        
        if position_size['quantity'] <= 0:
            return None
        
        # Create TP1/TP2/Runner system
        tp_system = self.create_tp1_tp2_runner_system(
            entry_price, stop_loss_price, tp1_multiplier, tp2_multiplier, runner_multiplier
        )
        
        # Create position
        position = {
            'id': len(self.positions) + 1,
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'quantity': position_size['quantity'],
            'position_value': position_size['position_value'],
            'stop_loss_price': stop_loss_price,
            'tp1_price': tp_system['tp1_price'],
            'tp2_price': tp_system['tp2_price'],
            'runner_price': tp_system['runner_price'],
            'risk_amount': position_size['risk_amount'],
            'entry_time': datetime.now(),
            'status': 'open',
            'tp1_hit': False,
            'tp2_hit': False,
            'runner_active': False
        }
        
        self.positions.append(position)
        return position
    
    def update_position(self, position_id: int, current_price: float) -> Dict[str, any]:
        """
        Update position based on current price
        
        Args:
            position_id: Position ID
            current_price: Current market price
            
        Returns:
            Dict: Update results
        """
        position = next((p for p in self.positions if p['id'] == position_id), None)
        if not position:
            return {'status': 'error', 'message': 'Position not found'}
        
        side = position['side']
        entry_price = position['entry_price']
        
        # Calculate current P&L
        if side == 'buy':
            pnl = (current_price - entry_price) * position['quantity']
        else:  # sell
            pnl = (entry_price - current_price) * position['quantity']
        
        # Check stop loss
        if side == 'buy' and current_price <= position['stop_loss_price']:
            return self.close_position(position_id, current_price, 'stop_loss')
        elif side == 'sell' and current_price >= position['stop_loss_price']:
            return self.close_position(position_id, current_price, 'stop_loss')
        
        # Check TP1
        if not position['tp1_hit']:
            if side == 'buy' and current_price >= position['tp1_price']:
                position['tp1_hit'] = True
                # Close 50% of position at TP1
                return self.partial_close_position(position_id, current_price, 0.5, 'tp1')
            elif side == 'sell' and current_price <= position['tp1_price']:
                position['tp1_hit'] = True
                return self.partial_close_position(position_id, current_price, 0.5, 'tp1')
        
        # Check TP2
        if position['tp1_hit'] and not position['tp2_hit']:
            if side == 'buy' and current_price >= position['tp2_price']:
                position['tp2_hit'] = True
                # Close 30% of remaining position at TP2
                return self.partial_close_position(position_id, current_price, 0.3, 'tp2')
            elif side == 'sell' and current_price <= position['tp2_price']:
                position['tp2_hit'] = True
                return self.partial_close_position(position_id, current_price, 0.3, 'tp2')
        
        # Check Runner
        if position['tp2_hit'] and not position['runner_active']:
            if side == 'buy' and current_price >= position['runner_price']:
                position['runner_active'] = True
                # Move stop loss to breakeven for runner
                position['stop_loss_price'] = entry_price
                return {'status': 'runner_activated', 'message': 'Runner activated, stop moved to breakeven'}
            elif side == 'sell' and current_price <= position['runner_price']:
                position['runner_active'] = True
                position['stop_loss_price'] = entry_price
                return {'status': 'runner_activated', 'message': 'Runner activated, stop moved to breakeven'}
        
        return {
            'status': 'updated',
            'pnl': pnl,
            'current_price': current_price,
            'position': position
        }
    
    def partial_close_position(self, position_id: int, price: float, 
                             close_percentage: float, reason: str) -> Dict[str, any]:
        """
        Partially close a position
        
        Args:
            position_id: Position ID
            price: Close price
            close_percentage: Percentage of position to close (0.0 to 1.0)
            reason: Reason for closing
            
        Returns:
            Dict: Close results
        """
        position = next((p for p in self.positions if p['id'] == position_id), None)
        if not position:
            return {'status': 'error', 'message': 'Position not found'}
        
        # Calculate quantities
        close_quantity = position['quantity'] * close_percentage
        remaining_quantity = position['quantity'] - close_quantity
        
        # Calculate P&L
        side = position['side']
        entry_price = position['entry_price']
        
        if side == 'buy':
            pnl = (price - entry_price) * close_quantity
        else:  # sell
            pnl = (entry_price - price) * close_quantity
        
        # Update position
        position['quantity'] = remaining_quantity
        position['position_value'] = remaining_quantity * price
        
        # Update daily tracking
        self.daily_pnl += pnl
        self.current_capital += pnl
        
        # Record trade
        trade = {
            'position_id': position_id,
            'symbol': position['symbol'],
            'side': side,
            'entry_price': entry_price,
            'exit_price': price,
            'quantity': close_quantity,
            'pnl': pnl,
            'reason': reason,
            'timestamp': datetime.now()
        }
        
        self.daily_trades.append(trade)
        self.closed_trades.append(trade)
        
        # If position fully closed, remove from active positions
        if remaining_quantity <= 0.001:  # Account for floating point precision
            self.positions.remove(position)
            return {
                'status': 'fully_closed',
                'pnl': pnl,
                'trade': trade,
                'message': f'Position fully closed: {reason}'
            }
        
        return {
            'status': 'partially_closed',
            'pnl': pnl,
            'trade': trade,
            'remaining_quantity': remaining_quantity,
            'message': f'Position partially closed: {reason}'
        }
    
    def close_position(self, position_id: int, price: float, reason: str) -> Dict[str, any]:
        """
        Fully close a position
        
        Args:
            position_id: Position ID
            price: Close price
            reason: Reason for closing
            
        Returns:
            Dict: Close results
        """
        return self.partial_close_position(position_id, price, 1.0, reason)
    
    def get_portfolio_summary(self) -> Dict[str, any]:
        """
        Get portfolio summary
        
        Returns:
            Dict: Portfolio summary
        """
        total_pnl = sum(trade['pnl'] for trade in self.daily_trades)
        
        return {
            'current_capital': self.current_capital,
            'daily_pnl': self.daily_pnl,
            'daily_pnl_pct': (self.daily_pnl / self.daily_start_capital) * 100,
            'total_pnl': total_pnl,
            'total_pnl_pct': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
            'active_positions': len(self.positions),
            'max_positions': self.max_positions,
            'daily_breaker_triggered': self.is_daily_breaker_triggered(),
            'daily_trades_count': len(self.daily_trades),
            'positions': self.positions
        }
