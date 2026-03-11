"""
Data Layer - Point-in-time historical data management
CCXT integration with local parquet caching for speed.
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import ccxt
from pathlib import Path

logger = logging.getLogger(__name__)

class DataLayer:
    """Manages historical data fetching with point-in-time integrity."""
    
    def __init__(
        self, 
        exchange_id: str = "binance",
        cache_dir: str = "data/historical",
        use_cache: bool = True
    ):
        """
        Initialize data layer with exchange connection and local cache.
        
        Args:
            exchange_id: CCXT exchange ID (binance, bybit, etc.)
            cache_dir: Directory for cached parquet files
            use_cache: Whether to use local cache (recommended)
            
        Raises:
            ccxt.BaseError: If exchange initialization fails
            FileNotFoundError: If cache directory cannot be created
        """
        self.exchange_id = exchange_id
        self.cache_dir = Path(cache_dir)
        self.use_cache = use_cache
        
        # Initialize exchange
        try:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap'  # Perpetual contracts
                }
            })
            logger.info(f"Initialized CCXT exchange: {exchange_id}")
        except AttributeError:
            raise ValueError(f"Exchange {exchange_id} not supported by CCXT")
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Data cache in memory (point-in-time accessible)
        self.ohlcv_cache: Dict[str, pd.DataFrame] = {}
        self.funding_cache: Dict[str, pd.DataFrame] = {}
        
    def fetch_ohlcv(
        self, 
        symbol: str, 
        timeframe: str = "1h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data with local caching.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT:USDT")
            timeframe: CCXT timeframe string
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Max candles per request
            
        Returns:
            DataFrame with OHLCV data, indexed by timestamp
        """
        cache_key = f"{symbol.replace('/', '_')}_{timeframe}"
        cache_file = self.cache_dir / f"{cache_key}.parquet"
        
        # Try to load from cache first
        if self.use_cache and cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                logger.info(f"Loaded {len(df)} rows from cache: {cache_file}")
                
                # Filter by date range if specified
                if start_date or end_date:
                    if start_date:
                        start_dt = pd.Timestamp(start_date)
                        df = df[df.index >= start_dt]
                    if end_date:
                        end_dt = pd.Timestamp(end_date)
                        df = df[df.index <= end_dt]
                
                self.ohlcv_cache[cache_key] = df
                return df
            except Exception as e:
                logger.warning(f"Cache read failed: {e}, fetching fresh")
        
        # Fetch from exchange
        logger.info(f"Fetching OHLCV for {symbol} ({timeframe}) from {self.exchange_id}")
        
        since = None
        if start_date:
            since = self.exchange.parse8601(f"{start_date}T00:00:00Z")
        
        all_candles = []
        current_since = since
        
        while True:
            try:
                candles = self.exchange.fetch_ohlcv(
                    symbol, 
                    timeframe=timeframe,
                    since=current_since,
                    limit=limit
                )
                
                if not candles:
                    break
                    
                all_candles.extend(candles)
                
                # Update for next iteration
                last_timestamp = candles[-1][0]
                if current_since is None:
                    current_since = last_timestamp
                else:
                    current_since = last_timestamp + 1
                
                # Check if we've reached end_date
                if end_date:
                    end_timestamp = self.exchange.parse8601(f"{end_date}T23:59:59Z")
                    if last_timestamp >= end_timestamp:
                        break
                
                # Rate limiting
                self.exchange.sleep(self.exchange.rateLimit)
                
            except (ccxt.NetworkError, ccxt.ExchangeError) as e:
                logger.error(f"Fetch error: {e}, retrying...")
                self.exchange.sleep(5000)
                continue
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                break
        
        # Create DataFrame
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df = pd.DataFrame(all_candles, columns=columns)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Cache to disk
        if self.use_cache:
            try:
                df.to_parquet(cache_file)
                logger.info(f"Cached {len(df)} rows to {cache_file}")
            except Exception as e:
                logger.error(f"Failed to cache data: {e}")
        
        self.ohlcv_cache[cache_key] = df
        return df
    
    def fetch_funding_rates(
        self, 
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch historical funding rates for perpetual contract.
        
        Args:
            symbol: Trading pair (must be perpetual)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            DataFrame with funding rate history
        """
        cache_key = f"{symbol.replace('/', '_')}_funding"
        cache_file = self.cache_dir / f"{cache_key}.parquet"
        
        # Try cache first
        if self.use_cache and cache_file.exists():
            try:
                df = pd.read_parquet(cache_file)
                logger.info(f"Loaded {len(df)} funding rates from cache")
                
                # Filter by date
                if start_date or end_date:
                    if start_date:
                        start_dt = pd.Timestamp(start_date)
                        df = df[df.index >= start_dt]
                    if end_date:
                        end_dt = pd.Timestamp(end_date)
                        df = df[df.index <= end_dt]
                
                self.funding