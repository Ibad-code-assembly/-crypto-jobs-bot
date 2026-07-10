import logging
import asyncio
from datetime import datetime
from typing import List, Dict
import httpx
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CoinListingScraper(ABC):
    """Base class for coin listing scrapers."""

    def __init__(self):
        self.source_site = "Unknown"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def run(self) -> List[Dict]:
        """Scrape and return list of new coins: {symbol, name, exchange, trading_pairs, url, listed_date}"""
        pass


class BinanceScraper(CoinListingScraper):
    def __init__(self):
        super().__init__()
        self.source_site = "Binance"

    async def run(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # Binance API for recent listings
                url = "https://api.binance.com/api/v3/exchangeInfo"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                coins = []
                symbols_seen = set()

                # Get symbols from symbols list, filter for recent ones
                for symbol_info in data.get("symbols", [])[-50:]:  # Last 50 symbols (newest)
                    symbol = symbol_info.get("baseAsset", "").upper()
                    if symbol and symbol not in symbols_seen:
                        symbols_seen.add(symbol)
                        quote_assets = set()
                        for filt in symbol_info.get("filters", []):
                            if filt.get("filterType") == "PRICE_FILTER":
                                quote_assets.add("USDT")
                                quote_assets.add("BUSD")
                                quote_assets.add("USDC")

                        coins.append({
                            "symbol": symbol,
                            "name": symbol,
                            "source_site": self.source_site,
                            "trading_pairs": ",".join(sorted(quote_assets)) or "USDT",
                            "url": f"https://www.binance.com/en/trade/{symbol}_USDT",
                            "listed_date": datetime.utcnow()
                        })

                logger.info(f"[Binance] Found {len(coins)} coins")
                return coins

        except Exception as e:
            logger.error(f"[Binance] Error: {str(e)}")
            return []


class CoinbaseScraper(CoinListingScraper):
    def __init__(self):
        super().__init__()
        self.source_site = "Coinbase"

    async def run(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # Coinbase products API
                url = "https://api.exchange.coinbase.com/products"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                coins = []
                symbols_seen = set()

                for product in data[-50:]:  # Last 50 products
                    base = product.get("base_currency", "").upper()
                    if base and base not in symbols_seen:
                        symbols_seen.add(base)
                        coins.append({
                            "symbol": base,
                            "name": base,
                            "source_site": self.source_site,
                            "trading_pairs": product.get("quote_currency", "USD").upper(),
                            "url": f"https://coinbase.com/price/{base}",
                            "listed_date": datetime.utcnow()
                        })

                logger.info(f"[Coinbase] Found {len(coins)} coins")
                return coins

        except Exception as e:
            logger.error(f"[Coinbase] Error: {str(e)}")
            return []


class BybitScraper(CoinListingScraper):
    def __init__(self):
        super().__init__()
        self.source_site = "Bybit"

    async def run(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # Bybit symbols
                url = "https://api.bybit.com/v5/market/instruments-info"
                params = {"category": "spot"}
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

                coins = []
                symbols_seen = set()

                for symbol_info in data.get("result", {}).get("list", [])[-50:]:
                    symbol = symbol_info.get("baseCoin", "").upper()
                    if symbol and symbol not in symbols_seen:
                        symbols_seen.add(symbol)
                        coins.append({
                            "symbol": symbol,
                            "name": symbol,
                            "source_site": self.source_site,
                            "trading_pairs": symbol_info.get("quoteCoin", "USDT").upper(),
                            "url": f"https://www.bybit.com/spot/{symbol}/",
                            "listed_date": datetime.utcnow()
                        })

                logger.info(f"[Bybit] Found {len(coins)} coins")
                return coins

        except Exception as e:
            logger.error(f"[Bybit] Error: {str(e)}")
            return []


class OKXScraper(CoinListingScraper):
    def __init__(self):
        super().__init__()
        self.source_site = "OKX"

    async def run(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # OKX market data
                url = "https://www.okx.com/api/v5/market/instruments"
                params = {"instType": "SPOT"}
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

                coins = []
                symbols_seen = set()

                for inst in data.get("data", [])[-50:]:
                    parts = inst.get("instId", "").split("-")
                    if len(parts) >= 2:
                        symbol = parts[0].upper()
                        if symbol and symbol not in symbols_seen:
                            symbols_seen.add(symbol)
                            coins.append({
                                "symbol": symbol,
                                "name": symbol,
                                "source_site": self.source_site,
                                "trading_pairs": parts[1].upper(),
                                "url": f"https://www.okx.com/trade-spot/{symbol}",
                                "listed_date": datetime.utcnow()
                            })

                logger.info(f"[OKX] Found {len(coins)} coins")
                return coins

        except Exception as e:
            logger.error(f"[OKX] Error: {str(e)}")
            return []


class BitgetScraper(CoinListingScraper):
    def __init__(self):
        super().__init__()
        self.source_site = "Bitget"

    async def run(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # Bitget public products
                url = "https://api.bitget.com/spot/v1/public/products"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                coins = []
                symbols_seen = set()

                for product in data.get("data", [])[-50:]:
                    symbol = product.get("baseCoin", "").upper()
                    if symbol and symbol not in symbols_seen:
                        symbols_seen.add(symbol)
                        coins.append({
                            "symbol": symbol,
                            "name": symbol,
                            "source_site": self.source_site,
                            "trading_pairs": product.get("quoteCoin", "USDT").upper(),
                            "url": f"https://www.bitget.com/spot/{symbol}",
                            "listed_date": datetime.utcnow()
                        })

                logger.info(f"[Bitget] Found {len(coins)} coins")
                return coins

        except Exception as e:
            logger.error(f"[Bitget] Error: {str(e)}")
            return []


class KrakenScraper(CoinListingScraper):
    def __init__(self):
        super().__init__()
        self.source_site = "Kraken"

    async def run(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # Kraken asset pairs
                url = "https://api.kraken.com/0/public/AssetPairs"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                coins = []
                symbols_seen = set()

                for pair_name, pair_info in list(data.get("result", {}).items())[-50:]:
                    base = pair_info.get("base", "").upper()
                    if base and base not in symbols_seen and len(base) <= 5:
                        symbols_seen.add(base)
                        coins.append({
                            "symbol": base,
                            "name": base,
                            "source_site": self.source_site,
                            "trading_pairs": pair_info.get("quote", "USD").upper(),
                            "url": f"https://www.kraken.com/prices/{base}",
                            "listed_date": datetime.utcnow()
                        })

                logger.info(f"[Kraken] Found {len(coins)} coins")
                return coins

        except Exception as e:
            logger.error(f"[Kraken] Error: {str(e)}")
            return []


class KuCoinScraper(CoinListingScraper):
    def __init__(self):
        super().__init__()
        self.source_site = "KuCoin"

    async def run(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # KuCoin symbols
                url = "https://api.kucoin.com/api/v1/symbols"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                coins = []
                symbols_seen = set()

                for symbol_info in data.get("data", [])[-50:]:
                    base = symbol_info.get("baseCurrency", "").upper()
                    if base and base not in symbols_seen:
                        symbols_seen.add(base)
                        coins.append({
                            "symbol": base,
                            "name": base,
                            "source_site": self.source_site,
                            "trading_pairs": symbol_info.get("quoteCurrency", "USDT").upper(),
                            "url": f"https://www.kucoin.com/trade/{base}",
                            "listed_date": datetime.utcnow()
                        })

                logger.info(f"[KuCoin] Found {len(coins)} coins")
                return coins

        except Exception as e:
            logger.error(f"[KuCoin] Error: {str(e)}")
            return []


class GateIOScraper(CoinListingScraper):
    def __init__(self):
        super().__init__()
        self.source_site = "Gate.io"

    async def run(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # Gate.io spot pairs
                url = "https://api.gateio.ws/api/v4/spot/currency_pairs"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                coins = []
                symbols_seen = set()

                for pair_info in data[-50:]:
                    base = pair_info.get("base", "").upper()
                    if base and base not in symbols_seen:
                        symbols_seen.add(base)
                        coins.append({
                            "symbol": base,
                            "name": base,
                            "source_site": self.source_site,
                            "trading_pairs": pair_info.get("quote", "USDT").upper(),
                            "url": f"https://www.gate.io/trade/{base}",
                            "listed_date": datetime.utcnow()
                        })

                logger.info(f"[Gate.io] Found {len(coins)} coins")
                return coins

        except Exception as e:
            logger.error(f"[Gate.io] Error: {str(e)}")
            return []


class MEXCScraper(CoinListingScraper):
    def __init__(self):
        super().__init__()
        self.source_site = "MEXC"

    async def run(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # MEXC exchange info
                url = "https://api.mexc.com/api/v3/exchangeInfo"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                coins = []
                symbols_seen = set()

                for symbol_info in data.get("symbols", [])[-50:]:
                    base = symbol_info.get("baseAsset", "").upper()
                    if base and base not in symbols_seen:
                        symbols_seen.add(base)
                        coins.append({
                            "symbol": base,
                            "name": base,
                            "source_site": self.source_site,
                            "trading_pairs": symbol_info.get("quoteAsset", "USDT").upper(),
                            "url": f"https://www.mexc.com/exchange/{base}_USDT",
                            "listed_date": datetime.utcnow()
                        })

                logger.info(f"[MEXC] Found {len(coins)} coins")
                return coins

        except Exception as e:
            logger.error(f"[MEXC] Error: {str(e)}")
            return []


class HTXScraper(CoinListingScraper):
    def __init__(self):
        super().__init__()
        self.source_site = "HTX"

    async def run(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # HTX (Huobi) symbols
                url = "https://api.huobi.pro/v1/common/symbols"
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

                coins = []
                symbols_seen = set()

                for symbol_info in data.get("data", [])[-50:]:
                    base = symbol_info.get("base-currency", "").upper()
                    if base and base not in symbols_seen:
                        symbols_seen.add(base)
                        coins.append({
                            "symbol": base,
                            "name": base,
                            "source_site": self.source_site,
                            "trading_pairs": symbol_info.get("quote-currency", "USDT").upper(),
                            "url": f"https://www.huobi.com/exchange/{base}",
                            "listed_date": datetime.utcnow()
                        })

                logger.info(f"[HTX] Found {len(coins)} coins")
                return coins

        except Exception as e:
            logger.error(f"[HTX] Error: {str(e)}")
            return []
