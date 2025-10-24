import pandas as pd
import numpy as np
from typing import Dict, Tuple
from .rsi import rsi
from .wavetrend import wavetrend

class WeightedSignalGenerator:
    """
    Weighted signal generator implementing:
    - RSI: 40% weight
    - WaveTrend: 40% weight  
    - Buy/Sell signals: 20% weight
    """
    
    def __init__(self, 
                 rsi_weight: float = 0.4,
                 wavetrend_weight: float = 0.4, 
                 buy_sell_weight: float = 0.2):
        """
        Initialize weighted signal generator
        
        Args:
            rsi_weight: Weight for RSI signals (default: 0.4)
            wavetrend_weight: Weight for WaveTrend signals (default: 0.4)
            buy_sell_weight: Weight for buy/sell signals (default: 0.2)
        """
        self.rsi_weight = rsi_weight
        self.wavetrend_weight = wavetrend_weight
        self.buy_sell_weight = buy_sell_weight
        
        # Validate weights sum to 1.0
        total_weight = rsi_weight + wavetrend_weight + buy_sell_weight
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def generate_rsi_signal(self, df: pd.DataFrame, 
                           rsi_length: int = 14,
                           oversold: float = 30,
                           overbought: float = 70) -> pd.Series:
        """
        Generate RSI-based signals
        
        Returns:
            pd.Series: RSI signal strength (-1 to 1)
        """
        rsi_values = rsi(df['close'], length=rsi_length)
        
        # Normalize RSI to -1 to 1 range
        # Oversold (30) = 1 (strong buy)
        # Overbought (70) = -1 (strong sell)
        # Neutral (50) = 0
        
        rsi_signal = np.where(
            rsi_values <= oversold, 1.0,  # Strong buy
            np.where(
                rsi_values >= overbought, -1.0,  # Strong sell
                np.where(
                    rsi_values < 50, 
                    (50 - rsi_values) / (50 - oversold),  # Buy signal strength
                    -(rsi_values - 50) / (overbought - 50)  # Sell signal strength
                )
            )
        )
        
        return pd.Series(rsi_signal, index=df.index)
    
    def generate_wavetrend_signal(self, df: pd.DataFrame,
                                 channel_length: int = 10,
                                 average_length: int = 21) -> pd.Series:
        """
        Generate WaveTrend-based signals
        
        Returns:
            pd.Series: WaveTrend signal strength (-1 to 1)
        """
        # Calculate hlc3 for WaveTrend
        if set(['high', 'low', 'close']).issubset(df.columns):
            hlc3 = (df['high'] + df['low'] + df['close']) / 3.0
        else:
            hlc3 = df['close']
        
        wt = wavetrend(hlc3, channel_length=channel_length, average_length=average_length)
        
        # Generate signals based on WaveTrend crossovers and levels
        wt1 = wt['wt1']
        wt2 = wt['wt2']
        
        # Signal based on crossovers and extreme levels
        wt_signal = np.where(
            (wt1 > wt2) & (wt1 < -50), 1.0,  # Strong buy: WT1 above WT2 and oversold
            np.where(
                (wt1 < wt2) & (wt1 > 50), -1.0,  # Strong sell: WT1 below WT2 and overbought
                np.where(
                    wt1 > wt2, 0.5,  # Weak buy: WT1 above WT2
                    -0.5  # Weak sell: WT1 below WT2
                )
            )
        )
        
        return pd.Series(wt_signal, index=df.index)
    
    def generate_buy_sell_signal(self, df: pd.DataFrame,
                                price_col: str = 'close',
                                lookback: int = 20) -> pd.Series:
        """
        Generate buy/sell signals based on price momentum
        
        Returns:
            pd.Series: Buy/sell signal strength (-1 to 1)
        """
        price = df[price_col]
        
        # Calculate price momentum
        sma_short = price.rolling(window=5, min_periods=1).mean()
        sma_long = price.rolling(window=lookback, min_periods=1).mean()
        
        # Price relative to moving averages
        price_vs_short = (price - sma_short) / sma_short
        price_vs_long = (price - sma_long) / sma_long
        
        # Combine momentum signals
        momentum_signal = (price_vs_short + price_vs_long) / 2
        
        # Normalize to -1 to 1 range
        momentum_signal = np.clip(momentum_signal * 10, -1, 1)
        
        return pd.Series(momentum_signal, index=df.index)
    
    def generate_weighted_signal(self, df: pd.DataFrame,
                               rsi_length: int = 14,
                               rsi_oversold: float = 30,
                               rsi_overbought: float = 70,
                               wt_channel_length: int = 10,
                               wt_average_length: int = 21,
                               momentum_lookback: int = 20) -> Dict[str, pd.Series]:
        """
        Generate weighted signals combining all indicators
        
        Returns:
            Dict containing:
            - 'rsi_signal': RSI signal strength
            - 'wavetrend_signal': WaveTrend signal strength  
            - 'buy_sell_signal': Buy/sell signal strength
            - 'weighted_signal': Final weighted signal
            - 'final_signal': Boolean buy/sell signal
        """
        # Generate individual signals
        rsi_sig = self.generate_rsi_signal(df, rsi_length, rsi_oversold, rsi_overbought)
        wt_sig = self.generate_wavetrend_signal(df, wt_channel_length, wt_average_length)
        bs_sig = self.generate_buy_sell_signal(df, 'close', momentum_lookback)
        
        # Calculate weighted signal
        weighted_signal = (
            rsi_sig * self.rsi_weight +
            wt_sig * self.wavetrend_weight +
            bs_sig * self.buy_sell_weight
        )
        
        # Generate final boolean signals
        # Long when weighted signal > 0.3, Short when < -0.3
        final_long = weighted_signal > 0.3
        final_short = weighted_signal < -0.3
        
        return {
            'rsi_signal': rsi_sig,
            'wavetrend_signal': wt_sig,
            'buy_sell_signal': bs_sig,
            'weighted_signal': weighted_signal,
            'final_long': final_long,
            'final_short': final_short
        }
    
    def get_signal_strength(self, weighted_signal: float) -> str:
        """
        Convert weighted signal value to descriptive strength
        
        Args:
            weighted_signal: Signal value between -1 and 1
            
        Returns:
            str: Signal strength description
        """
        if weighted_signal >= 0.7:
            return "Very Strong Buy"
        elif weighted_signal >= 0.3:
            return "Strong Buy"
        elif weighted_signal >= 0.1:
            return "Weak Buy"
        elif weighted_signal <= -0.7:
            return "Very Strong Sell"
        elif weighted_signal <= -0.3:
            return "Strong Sell"
        elif weighted_signal <= -0.1:
            return "Weak Sell"
        else:
            return "Neutral"
