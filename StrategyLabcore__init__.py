"""
RATIO_REGNUM Core Module
Event-driven, regime-aware BTC/ETH ratio mean reversion system.
"""

__version__ = "1.0.0"
__author__ = "Evolution Ecosystem - Autonomous Architect"

from .datalayer import DataLayer
from .signal_engine import SignalEngine
from .backtest_engine import EventDrivenBacktest
from .risk_manager import RiskManager
from .portfolio import Portfolio

__all__ = [
    "DataLayer",
    "SignalEngine", 
    "EventDrivenBacktest",
    "RiskManager",
    "Portfolio"
]