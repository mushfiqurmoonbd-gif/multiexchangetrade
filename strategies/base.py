from abc import ABC, abstractmethod
import pandas as pd


class Strategy(ABC):
    """Abstract base for all strategies.

    Each strategy must implement generate_signals and may compute internal indicators
    on the provided DataFrame. The function should return a boolean pd.Series named
    'signal' aligned to df.index where True indicates an entry trigger for the next bar.
    """

    name: str = "base"

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame, **params) -> pd.Series:
        raise NotImplementedError


