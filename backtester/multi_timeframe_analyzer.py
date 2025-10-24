import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class TimeframeType(Enum):
    """Timeframe types for multi-timeframe analysis"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

@dataclass
class TimeframeConfig:
    """Configuration for a specific timeframe"""
    name: str
    period: str  # pandas resample period (e.g., '1H', '4H', '1D')
    timeframe_type: TimeframeType
    weight: float = 1.0  # Weight in multi-timeframe analysis
    enabled: bool = True

@dataclass
class MultiTimeframeSignal:
    """Signal from multi-timeframe analysis"""
    primary_timeframe: str
    signals: Dict[str, bool]  # timeframe -> signal
    weighted_score: float
    confidence: float
    trend_direction: str  # 'bullish', 'bearish', 'neutral'
    strength: str  # 'weak', 'moderate', 'strong'

class MultiTimeframeAnalyzer:
    """
    Multi-timeframe analysis for backtesting
    Analyzes multiple timeframes simultaneously to generate stronger signals
    """
    
    def __init__(self, 
                 primary_timeframe: str = '1H',
                 secondary_timeframes: List[str] = None,
                 signal_weights: Dict[str, float] = None):
        """
        Initialize multi-timeframe analyzer
        
        Args:
            primary_timeframe: Primary timeframe for analysis
            secondary_timeframes: List of secondary timeframes
            signal_weights: Weights for each timeframe
        """
        self.primary_timeframe = primary_timeframe
        
        if secondary_timeframes is None:
            secondary_timeframes = ['15m', '1H', '4H', '1D', '1W']
        
        if signal_weights is None:
            # Default weights: shorter timeframes get lower weights
            signal_weights = {
                '15m': 0.1,
                '30m': 0.15,
                '1H': 0.25,
                '4H': 0.3,
                '1D': 0.4,
                '1W': 0.5
            }
        
        self.timeframes = self._create_timeframe_configs(secondary_timeframes, signal_weights)
        self.signal_history = []
    
    def _create_timeframe_configs(self, 
                                 timeframes: List[str], 
                                 weights: Dict[str, float]) -> List[TimeframeConfig]:
        """Create timeframe configurations"""
        configs = []
        
        for tf in timeframes:
            timeframe_type = self._determine_timeframe_type(tf)
            weight = weights.get(tf, 1.0)
            
            config = TimeframeConfig(
                name=tf,
                period=tf,
                timeframe_type=timeframe_type,
                weight=weight,
                enabled=True
            )
            configs.append(config)
        
        return configs
    
    def _determine_timeframe_type(self, timeframe: str) -> TimeframeType:
        """Determine timeframe type from string"""
        if 'm' in timeframe.lower():
            return TimeframeType.MINUTE
        elif 'h' in timeframe.lower():
            return TimeframeType.HOUR
        elif 'd' in timeframe.lower():
            return TimeframeType.DAY
        elif 'w' in timeframe.lower():
            return TimeframeType.WEEK
        elif 'M' in timeframe or 'month' in timeframe.lower():
            return TimeframeType.MONTH
        else:
            return TimeframeType.HOUR  # Default
    
    def resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resample data to specific timeframe
        
        Args:
            df: Original DataFrame with OHLC data
            timeframe: Target timeframe (e.g., '1H', '4H', '1D')
            
        Returns:
            pd.DataFrame: Resampled data
        """
        if 'timestamp' not in df.columns:
            df = df.reset_index()
            if 'index' in df.columns:
                df = df.rename(columns={'index': 'timestamp'})
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Resample OHLC data
        resampled = df.resample(timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Add technical indicators for resampled data
        resampled = self._add_technical_indicators(resampled)
        
        return resampled.reset_index()
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to resampled data"""
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        return df
    
    def analyze_timeframe_trend(self, df: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """
        Analyze trend for a specific timeframe
        
        Args:
            df: DataFrame with OHLC and technical indicators
            timeframe: Timeframe name
            
        Returns:
            Dict: Analysis results
        """
        if len(df) < 50:  # Need sufficient data
            return {
                'trend': 'neutral',
                'strength': 0.0,
                'signals': {},
                'confidence': 0.0
            }
        
        signals = {}
        signal_scores = []
        
        # Moving Average signals
        if 'sma_20' in df.columns and 'sma_50' in df.columns:
            sma_signal = df['sma_20'].iloc[-1] > df['sma_50'].iloc[-1]
            signals['sma_trend'] = sma_signal
            signal_scores.append(1 if sma_signal else -1)
        
        # MACD signals
        if 'macd' in df.columns and 'macd_signal' in df.columns:
            macd_signal = df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]
            signals['macd_trend'] = macd_signal
            signal_scores.append(1 if macd_signal else -1)
        
        # RSI signals
        if 'rsi' in df.columns:
            rsi_value = df['rsi'].iloc[-1]
            if rsi_value > 70:
                rsi_signal = False  # Overbought
            elif rsi_value < 30:
                rsi_signal = True   # Oversold
            else:
                rsi_signal = None   # Neutral
            signals['rsi_signal'] = rsi_signal
            if rsi_signal is not None:
                signal_scores.append(1 if rsi_signal else -1)
        
        # Bollinger Bands signals
        if all(col in df.columns for col in ['bb_upper', 'bb_lower', 'close']):
            close_price = df['close'].iloc[-1]
            bb_upper = df['bb_upper'].iloc[-1]
            bb_lower = df['bb_lower'].iloc[-1]
            
            if close_price > bb_upper:
                bb_signal = False  # Overbought
            elif close_price < bb_lower:
                bb_signal = True   # Oversold
            else:
                bb_signal = None   # Neutral
            signals['bb_signal'] = bb_signal
            if bb_signal is not None:
                signal_scores.append(1 if bb_signal else -1)
        
        # Volume confirmation
        if 'volume_ratio' in df.columns:
            volume_ratio = df['volume_ratio'].iloc[-1]
            volume_confirmation = volume_ratio > 1.2  # Above average volume
            signals['volume_confirmation'] = volume_confirmation
            if volume_confirmation:
                signal_scores.append(0.5)  # Bonus for volume confirmation
        
        # Calculate overall trend
        if not signal_scores:
            trend = 'neutral'
            strength = 0.0
        else:
            avg_score = np.mean(signal_scores)
            if avg_score > 0.3:
                trend = 'bullish'
                strength = min(abs(avg_score), 1.0)
            elif avg_score < -0.3:
                trend = 'bearish'
                strength = min(abs(avg_score), 1.0)
            else:
                trend = 'neutral'
                strength = abs(avg_score)
        
        # Calculate confidence based on signal agreement
        positive_signals = sum(1 for score in signal_scores if score > 0)
        total_signals = len(signal_scores)
        confidence = positive_signals / total_signals if total_signals > 0 else 0.0
        
        return {
            'trend': trend,
            'strength': strength,
            'signals': signals,
            'confidence': confidence,
            'timeframe': timeframe
        }
    
    def generate_multi_timeframe_signals(self, df: pd.DataFrame) -> MultiTimeframeSignal:
        """
        Generate multi-timeframe signals
        
        Args:
            df: Original DataFrame with OHLC data
            
        Returns:
            MultiTimeframeSignal: Combined multi-timeframe signal
        """
        timeframe_signals = {}
        weighted_scores = []
        total_weight = 0.0
        
        # Analyze each timeframe
        for config in self.timeframes:
            if not config.enabled:
                continue
            
            try:
                # Resample data to timeframe
                resampled_df = self.resample_data(df, config.period)
                
                # Analyze trend
                analysis = self.analyze_timeframe_trend(resampled_df, config.name)
                
                # Convert trend to numeric score
                if analysis['trend'] == 'bullish':
                    trend_score = analysis['strength']
                elif analysis['trend'] == 'bearish':
                    trend_score = -analysis['strength']
                else:
                    trend_score = 0.0
                
                # Apply timeframe weight
                weighted_score = trend_score * config.weight
                weighted_scores.append(weighted_score)
                total_weight += config.weight
                
                timeframe_signals[config.name] = {
                    'trend': analysis['trend'],
                    'strength': analysis['strength'],
                    'confidence': analysis['confidence'],
                    'weighted_score': weighted_score
                }
                
            except Exception as e:
                print(f"Error analyzing timeframe {config.name}: {e}")
                continue
        
        # Calculate overall weighted score
        if total_weight > 0:
            overall_score = sum(weighted_scores) / total_weight
        else:
            overall_score = 0.0
        
        # Determine overall trend direction
        if overall_score > 0.2:
            trend_direction = 'bullish'
        elif overall_score < -0.2:
            trend_direction = 'bearish'
        else:
            trend_direction = 'neutral'
        
        # Determine signal strength
        abs_score = abs(overall_score)
        if abs_score > 0.6:
            strength = 'strong'
        elif abs_score > 0.3:
            strength = 'moderate'
        else:
            strength = 'weak'
        
        # Calculate overall confidence
        confidences = [tf['confidence'] for tf in timeframe_signals.values()]
        overall_confidence = np.mean(confidences) if confidences else 0.0
        
        return MultiTimeframeSignal(
            primary_timeframe=self.primary_timeframe,
            signals=timeframe_signals,
            weighted_score=overall_score,
            confidence=overall_confidence,
            trend_direction=trend_direction,
            strength=strength
        )
    
    def run_multi_timeframe_backtest(self, 
                                   df: pd.DataFrame,
                                   initial_capital: float = 10000.0,
                                   risk_per_trade: float = 0.02,
                                   min_confidence: float = 0.6,
                                   min_strength: str = 'moderate') -> Dict[str, Any]:
        """
        Run backtest with multi-timeframe analysis
        
        Args:
            df: DataFrame with OHLC data
            initial_capital: Initial capital
            risk_per_trade: Risk per trade
            min_confidence: Minimum confidence threshold
            min_strength: Minimum strength threshold ('weak', 'moderate', 'strong')
            
        Returns:
            Dict: Backtest results
        """
        capital = initial_capital
        position = None
        trades = []
        equity_curve = []
        
        # Strength hierarchy
        strength_levels = {'weak': 1, 'moderate': 2, 'strong': 3}
        min_strength_level = strength_levels.get(min_strength, 2)
        
        for i in range(50, len(df)):  # Start after enough data for indicators
            current_price = df['close'].iloc[i]
            current_data = df.iloc[:i+1]
            
            # Generate multi-timeframe signal
            mtf_signal = self.generate_multi_timeframe_signals(current_data)
            
            # Check if signal meets criteria
            signal_strength_level = strength_levels.get(mtf_signal.strength, 1)
            
            should_enter = (
                mtf_signal.confidence >= min_confidence and
                signal_strength_level >= min_strength_level and
                mtf_signal.trend_direction in ['bullish', 'bearish']
            )
            
            # Entry logic
            if position is None and should_enter:
                side = 'buy' if mtf_signal.trend_direction == 'bullish' else 'sell'
                risk_amount = capital * risk_per_trade
                
                # Simple position sizing
                stop_loss_pct = 0.02  # 2% stop loss
                if side == 'buy':
                    stop_price = current_price * (1 - stop_loss_pct)
                else:
                    stop_price = current_price * (1 + stop_loss_pct)
                
                risk_per_share = abs(current_price - stop_price)
                quantity = risk_amount / risk_per_share
                
                position = {
                    'entry_price': current_price,
                    'quantity': quantity,
                    'side': side,
                    'entry_time': df['timestamp'].iloc[i] if 'timestamp' in df.columns else i,
                    'stop_loss': stop_price,
                    'mtf_signal': mtf_signal
                }
                
                trades.append({
                    'entry_price': current_price,
                    'quantity': quantity,
                    'side': side,
                    'entry_time': position['entry_time'],
                    'mtf_confidence': mtf_signal.confidence,
                    'mtf_strength': mtf_signal.strength,
                    'mtf_trend': mtf_signal.trend_direction
                })
            
            # Exit logic
            elif position is not None:
                exit_triggered = False
                exit_reason = None
                
                # Stop loss
                if position['side'] == 'buy' and current_price <= position['stop_loss']:
                    exit_triggered = True
                    exit_reason = 'stop_loss'
                elif position['side'] == 'sell' and current_price >= position['stop_loss']:
                    exit_triggered = True
                    exit_reason = 'stop_loss'
                
                # Take profit (simple 2:1 R:R)
                elif position['side'] == 'buy' and current_price >= position['entry_price'] * 1.04:
                    exit_triggered = True
                    exit_reason = 'take_profit'
                elif position['side'] == 'sell' and current_price <= position['entry_price'] * 0.96:
                    exit_triggered = True
                    exit_reason = 'take_profit'
                
                # Trend reversal
                elif mtf_signal.trend_direction != position['side'] and mtf_signal.confidence > 0.7:
                    exit_triggered = True
                    exit_reason = 'trend_reversal'
                
                if exit_triggered:
                    # Calculate P&L
                    if position['side'] == 'buy':
                        pnl = (current_price - position['entry_price']) * position['quantity']
                    else:
                        pnl = (position['entry_price'] - current_price) * position['quantity']
                    
                    capital += pnl
                    
                    trades[-1].update({
                        'exit_price': current_price,
                        'exit_time': df['timestamp'].iloc[i] if 'timestamp' in df.columns else i,
                        'pnl': pnl,
                        'exit_reason': exit_reason
                    })
                    
                    position = None
            
            # Update equity curve
            if position is not None:
                unrealized_pnl = (current_price - position['entry_price']) * position['quantity'] if position['side'] == 'buy' else (position['entry_price'] - current_price) * position['quantity']
                equity = capital + unrealized_pnl
            else:
                equity = capital
            
            equity_curve.append(equity)
        
        # Calculate final metrics
        total_return = (capital - initial_capital) / initial_capital
        closed_trades = [t for t in trades if 'pnl' in t]
        win_rate = len([t for t in closed_trades if t['pnl'] > 0]) / len(closed_trades) if closed_trades else 0
        
        return {
            'final_capital': capital,
            'total_return': total_return,
            'total_trades': len(closed_trades),
            'win_rate': win_rate,
            'equity_curve': equity_curve,
            'trades': trades,
            'mtf_signals': self.signal_history
        }
    
    def get_timeframe_summary(self) -> Dict[str, Any]:
        """Get summary of configured timeframes"""
        return {
            'primary_timeframe': self.primary_timeframe,
            'total_timeframes': len(self.timeframes),
            'enabled_timeframes': len([tf for tf in self.timeframes if tf.enabled]),
            'timeframes': [
                {
                    'name': tf.name,
                    'period': tf.period,
                    'type': tf.timeframe_type.value,
                    'weight': tf.weight,
                    'enabled': tf.enabled
                } for tf in self.timeframes
            ]
        }
