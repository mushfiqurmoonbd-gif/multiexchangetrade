import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum

class StopLossType(Enum):
    """Stop loss calculation types"""
    PERCENTAGE = "percentage"
    ATR = "atr"  # Average True Range
    SUPPORT_RESISTANCE = "support_resistance"
    VOLATILITY = "volatility"

class ConfigurableRiskManager:
    """
    Enhanced risk management with configurable stop-loss percentages
    and multiple stop-loss calculation methods
    """
    
    def __init__(self, 
                 initial_capital: float = 10000.0,
                 risk_per_trade: float = 0.02,
                 daily_loss_limit: float = 0.05,
                 max_positions: int = 5,
                 default_stop_loss_pct: float = 0.02,
                 default_stop_loss_type: StopLossType = StopLossType.PERCENTAGE):
        """
        Initialize configurable risk manager
        
        Args:
            initial_capital: Starting capital
            risk_per_trade: Risk per trade as percentage of capital
            daily_loss_limit: Maximum daily loss as percentage of capital
            max_positions: Maximum number of concurrent positions
            default_stop_loss_pct: Default stop loss percentage
            default_stop_loss_type: Default stop loss calculation type
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.daily_loss_limit = daily_loss_limit
        self.max_positions = max_positions
        self.default_stop_loss_pct = default_stop_loss_pct
        self.default_stop_loss_type = default_stop_loss_type
        
        # Daily tracking
        self.daily_start_capital = initial_capital
        self.daily_trades = []
        self.daily_pnl = 0.0
        
        # Position tracking
        self.positions: List[Dict] = []
        self.closed_trades: List[Dict] = []
        
        # Stop loss configurations
        self.stop_loss_configs = {
            StopLossType.PERCENTAGE: {
                'min_pct': 0.005,  # 0.5%
                'max_pct': 0.10,   # 10%
                'default_pct': 0.02  # 2%
            },
            StopLossType.ATR: {
                'min_multiplier': 0.5,
                'max_multiplier': 5.0,
                'default_multiplier': 2.0,
                'lookback_period': 14
            },
            StopLossType.SUPPORT_RESISTANCE: {
                'min_distance_pct': 0.01,  # 1%
                'max_distance_pct': 0.05,  # 5%
                'default_distance_pct': 0.02,  # 2%
                'lookback_period': 20
            },
            StopLossType.VOLATILITY: {
                'min_multiplier': 1.0,
                'max_multiplier': 3.0,
                'default_multiplier': 2.0,
                'lookback_period': 20
            }
        }
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR)
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period
            
        Returns:
            pd.Series: ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR using exponential moving average
        atr = true_range.ewm(span=period, adjust=False).mean()
        
        return atr
    
    def find_support_resistance(self, df: pd.DataFrame, 
                              lookback: int = 20) -> Tuple[pd.Series, pd.Series]:
        """
        Find support and resistance levels
        
        Args:
            df: DataFrame with OHLC data
            lookback: Lookback period for finding levels
            
        Returns:
            Tuple[pd.Series, pd.Series]: Support and resistance levels
        """
        high = df['high']
        low = df['low']
        
        # Find local highs and lows
        resistance = high.rolling(window=lookback, center=True).max()
        support = low.rolling(window=lookback, center=True).min()
        
        return support, resistance
    
    def calculate_volatility_stop(self, df: pd.DataFrame, 
                                 multiplier: float = 2.0,
                                 lookback: int = 20) -> pd.Series:
        """
        Calculate volatility-based stop loss
        
        Args:
            df: DataFrame with price data
            multiplier: Volatility multiplier
            lookback: Lookback period
            
        Returns:
            pd.Series: Volatility-based stop distances
        """
        returns = df['close'].pct_change()
        volatility = returns.rolling(window=lookback).std()
        
        # Convert volatility to price-based stop distance
        stop_distance = df['close'] * volatility * multiplier
        
        return stop_distance
    
    def calculate_stop_loss_price(self, 
                                entry_price: float,
                                side: str,
                                df: pd.DataFrame,
                                stop_loss_type: StopLossType = None,
                                stop_loss_value: float = None,
                                current_index: int = -1) -> float:
        """
        Calculate stop loss price using various methods
        
        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            df: DataFrame with OHLC data
            stop_loss_type: Stop loss calculation type
            stop_loss_value: Custom stop loss value
            current_index: Current data index
            
        Returns:
            float: Calculated stop loss price
        """
        if stop_loss_type is None:
            stop_loss_type = self.default_stop_loss_type
        
        if stop_loss_value is None:
            config = self.stop_loss_configs[stop_loss_type]
            stop_loss_value = config.get('default_pct', config.get('default_multiplier', 0.02))
        
        # Get recent data for calculations
        recent_df = df.iloc[max(0, current_index-50):current_index+1] if current_index >= 0 else df.tail(50)
        
        if stop_loss_type == StopLossType.PERCENTAGE:
            # Simple percentage-based stop loss
            if side == 'buy':
                stop_price = entry_price * (1 - stop_loss_value)
            else:  # sell
                stop_price = entry_price * (1 + stop_loss_value)
        
        elif stop_loss_type == StopLossType.ATR:
            # ATR-based stop loss
            config = self.stop_loss_configs[StopLossType.ATR]
            period = config['lookback_period']
            atr = self.calculate_atr(recent_df, period)
            current_atr = atr.iloc[-1] if len(atr) > 0 else entry_price * 0.02
            
            if side == 'buy':
                stop_price = entry_price - (current_atr * stop_loss_value)
            else:  # sell
                stop_price = entry_price + (current_atr * stop_loss_value)
        
        elif stop_loss_type == StopLossType.SUPPORT_RESISTANCE:
            # Support/resistance based stop loss
            config = self.stop_loss_configs[StopLossType.SUPPORT_RESISTANCE]
            lookback = config['lookback_period']
            support, resistance = self.find_support_resistance(recent_df, lookback)
            
            if side == 'buy':
                # For buy orders, use support level with buffer
                current_support = support.iloc[-1] if len(support) > 0 else entry_price * 0.98
                stop_price = current_support * (1 - stop_loss_value)
            else:  # sell
                # For sell orders, use resistance level with buffer
                current_resistance = resistance.iloc[-1] if len(resistance) > 0 else entry_price * 1.02
                stop_price = current_resistance * (1 + stop_loss_value)
        
        elif stop_loss_type == StopLossType.VOLATILITY:
            # Volatility-based stop loss
            config = self.stop_loss_configs[StopLossType.VOLATILITY]
            lookback = config['lookback_period']
            vol_stop = self.calculate_volatility_stop(recent_df, stop_loss_value, lookback)
            current_vol_stop = vol_stop.iloc[-1] if len(vol_stop) > 0 else entry_price * 0.02
            
            if side == 'buy':
                stop_price = entry_price - current_vol_stop
            else:  # sell
                stop_price = entry_price + current_vol_stop
        
        else:
            # Fallback to percentage
            if side == 'buy':
                stop_price = entry_price * (1 - stop_loss_value)
            else:  # sell
                stop_price = entry_price * (1 + stop_loss_value)
        
        # Ensure stop price is reasonable
        if side == 'buy':
            stop_price = max(stop_price, entry_price * 0.5)  # Don't go below 50% of entry
        else:
            stop_price = min(stop_price, entry_price * 1.5)  # Don't go above 150% of entry
        
        return stop_price
    
    def validate_stop_loss_config(self, 
                                 stop_loss_type: StopLossType,
                                 stop_loss_value: float) -> Tuple[bool, str]:
        """
        Validate stop loss configuration
        
        Args:
            stop_loss_type: Stop loss type
            stop_loss_value: Stop loss value
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        config = self.stop_loss_configs.get(stop_loss_type)
        if not config:
            return False, f"Unknown stop loss type: {stop_loss_type}"
        
        if stop_loss_type == StopLossType.PERCENTAGE:
            min_val = config['min_pct']
            max_val = config['max_pct']
            if not (min_val <= stop_loss_value <= max_val):
                return False, f"Stop loss percentage must be between {min_val*100:.1f}% and {max_val*100:.1f}%"
        
        elif stop_loss_type in [StopLossType.ATR, StopLossType.VOLATILITY]:
            min_val = config['min_multiplier']
            max_val = config['max_multiplier']
            if not (min_val <= stop_loss_value <= max_val):
                return False, f"Stop loss multiplier must be between {min_val} and {max_val}"
        
        elif stop_loss_type == StopLossType.SUPPORT_RESISTANCE:
            min_val = config['min_distance_pct']
            max_val = config['max_distance_pct']
            if not (min_val <= stop_loss_value <= max_val):
                return False, f"Stop loss distance must be between {min_val*100:.1f}% and {max_val*100:.1f}%"
        
        return True, ""
    
    def create_position_with_configurable_stop(self,
                                              symbol: str,
                                              side: str,
                                              entry_price: float,
                                              df: pd.DataFrame,
                                              stop_loss_type: StopLossType = None,
                                              stop_loss_value: float = None,
                                              tp1_multiplier: float = 1.5,
                                              tp2_multiplier: float = 2.0,
                                              runner_multiplier: float = 3.0,
                                              custom_risk: Optional[float] = None,
                                              current_index: int = -1) -> Optional[Dict]:
        """
        Create position with configurable stop loss
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            entry_price: Entry price
            df: DataFrame with OHLC data
            stop_loss_type: Stop loss calculation type
            stop_loss_value: Custom stop loss value
            tp1_multiplier: TP1 multiplier
            tp2_multiplier: TP2 multiplier
            runner_multiplier: Runner multiplier
            custom_risk: Custom risk amount
            current_index: Current data index
            
        Returns:
            Dict: Position details or None if position cannot be opened
        """
        # Validate stop loss configuration
        if stop_loss_type is None:
            stop_loss_type = self.default_stop_loss_type
        if stop_loss_value is None:
            config = self.stop_loss_configs[stop_loss_type]
            stop_loss_value = config.get('default_pct', config.get('default_multiplier', 0.02))
        
        is_valid, error_msg = self.validate_stop_loss_config(stop_loss_type, stop_loss_value)
        if not is_valid:
            print(f"Invalid stop loss configuration: {error_msg}")
            return None
        
        # Calculate stop loss price
        stop_loss_price = self.calculate_stop_loss_price(
            entry_price, side, df, stop_loss_type, stop_loss_value, current_index
        )
        
        # Calculate position size
        risk_amount = custom_risk if custom_risk else self.current_capital * self.risk_per_trade
        risk_per_share = abs(entry_price - stop_loss_price)
        
        if risk_per_share <= 0:
            return None
        
        quantity = risk_amount / risk_per_share
        position_value = quantity * entry_price
        
        # Ensure we don't exceed available capital
        max_position_value = self.current_capital * 0.9
        if position_value > max_position_value:
            quantity = max_position_value / entry_price
            position_value = quantity * entry_price
            risk_amount = quantity * risk_per_share
        
        # Create TP1/TP2/Runner system
        risk_distance = abs(entry_price - stop_loss_price)
        tp1_price = entry_price + (risk_distance * tp1_multiplier) if side == 'buy' else entry_price - (risk_distance * tp1_multiplier)
        tp2_price = entry_price + (risk_distance * tp2_multiplier) if side == 'buy' else entry_price - (risk_distance * tp2_multiplier)
        runner_price = entry_price + (risk_distance * runner_multiplier) if side == 'buy' else entry_price - (risk_distance * runner_multiplier)
        
        # Create position
        position = {
            'id': len(self.positions) + 1,
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'quantity': quantity,
            'position_value': position_value,
            'stop_loss_price': stop_loss_price,
            'stop_loss_type': stop_loss_type.value,
            'stop_loss_value': stop_loss_value,
            'tp1_price': tp1_price,
            'tp2_price': tp2_price,
            'runner_price': runner_price,
            'risk_amount': risk_amount,
            'entry_time': datetime.now(),
            'status': 'open',
            'tp1_hit': False,
            'tp2_hit': False,
            'runner_active': False
        }
        
        self.positions.append(position)
        return position
    
    def get_stop_loss_summary(self) -> Dict[str, any]:
        """
        Get stop loss configuration summary
        
        Returns:
            Dict: Stop loss summary
        """
        return {
            'default_stop_loss_type': self.default_stop_loss_type.value,
            'default_stop_loss_pct': self.default_stop_loss_pct,
            'available_types': [t.value for t in StopLossType],
            'configurations': {
                t.value: self.stop_loss_configs[t] for t in StopLossType
            },
            'active_positions': len(self.positions),
            'positions_with_stops': [
                {
                    'id': p['id'],
                    'symbol': p['symbol'],
                    'stop_loss_type': p['stop_loss_type'],
                    'stop_loss_value': p['stop_loss_value'],
                    'stop_loss_price': p['stop_loss_price']
                } for p in self.positions
            ]
        }
