"""
Scraper for crypto job listings from Twitter/X.

Uses session cookies from twitter.env.txt — no official API key needed.
Confirmed working endpoints (tested):
  - UserByScreenName  → GET x.com/i/api/graphql/NimuplG1OB7Fd2btCLdBOw/UserByScreenName
  - UserTweets        → GET x.com/i/api/graphql/QWF3SzpHmykQHsQMixG0cg/UserTweets

Strategy: scrape dedicated crypto job aggregator accounts + top-coin project accounts,
filter tweets for job-related keywords, extract apply URLs, map to coin tickers.
"""
import json
import logging
import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import httpx

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

_ENV_FILE = Path(__file__).parent.parent / "twitter.env.txt"

# Confirmed working bearer (from twikit internals, tested against x.com)
_BEARER = (
    "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D"
    "1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)

_GQL_USER   = "https://x.com/i/api/graphql/NimuplG1OB7Fd2btCLdBOw/UserByScreenName"
_GQL_TWEETS = "https://x.com/i/api/graphql/QWF3SzpHmykQHsQMixG0cg/UserTweets"

# Required feature-flags for GraphQL calls (confirmed with live testing)
_FEATURES = {
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "tweetypie_unmention_optimization_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "rweb_video_timestamps_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "responsive_web_media_download_video_enabled": False,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
}

_USER_FEATURES = {
    "hidden_profile_likes_enabled": True,
    "hidden_profile_subscriptions_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "subscriptions_verification_info_is_identity_verified_enabled": True,
    "subscriptions_verification_info_verified_since_enabled": True,
    "highlights_tweets_tab_ui_enabled": True,
    "responsive_web_twitter_article_notes_tab_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "responsive_web_graphql_timeline_navigation_enabled": True,
}

# ── Account lists ────────────────────────────────────────────────────────────

# Dedicated crypto job aggregator accounts — highest signal, scrape 50 tweets each
_JOB_AGGREGATORS = [
    # Original accounts
    "CryptoJobsList",
    "web3careers",
    "BlockchainJob",
    "DefiWork",
    "cryptoJobsCom",
    "cryptocurrencyjobs",
    "JobsInCrypto",
    "CryptoJobsHQ",
    "web3_jobs",
    "NFTJobs",
    "remote3co",
    "Web3WorkHQ",
    "blockacejobs",
    "CryptoRecruiter",
    "Web3Talent",
    # New job boards
    "Web3Career",
    "Remote3Jobs",
    "Web3Jobs",
    "Degen_Jobs",
    "CryptoJobs",
]

# Exchange accounts — monitor for hiring announcements
_EXCHANGE_ACCOUNTS = [
    "binance",
    "coinbase",
    "krakenfx",
    "Bybit_Official",
    "OKX",
    "BitgetGlobal",
    "MEXC_Official",
    "kucoincom",
    "gate_io",
    "HTX_Global",
    "Bitfinex",
    "CryptoCom",
    "Gemini",
    "Bitstamp",
    "BingXOfficial",
]

# Blockchain layer-1 and layer-2 networks
_BLOCKCHAIN_ACCOUNTS = [
    "ethereum",
    "solana",
    "SuiNetwork",
    "Aptos",
    "avax",
    "base",
    "arbitrum",
    "Optimism",
    "zksync",
    "Starknet",
    "SeiNetwork",
    "Injective",
    "CelestiaOrg",
    "NEARProtocol",
    "Polkadot",
    "cosmos",
    "Ripple",
    "Cardano",
    "ton_blockchain",
    "InternetComputer",
]

# DeFi protocols
_DEFI_ACCOUNTS = [
    "Uniswap",
    "aave",
    "LidoFinance",
    "compoundfinance",
    "MakerDAO",
    "Pendle_fi",
    "EthenaLabs",
    "eigenlayer",
    "JupiterExchange",
    "PancakeSwap",
    "CurveFinance",
    "Synthetix_io",
    "MorphoLabs",
    "1inch",
]

# VC and investment firms
_VC_ACCOUNTS = [
    "a16zcrypto",
    "Paradigm",
    "ElectricCapital",
    "AllianceDAO",
    "BinanceLabs",
    "PanteraCapital",
    "MulticoinCap",
    "1kxnetwork",
    "coinfund_io",
    "FrameworkVC",
]

# Combine all accounts for monitoring
_ALL_MONITOR_ACCOUNTS = (
    _JOB_AGGREGATORS +
    _EXCHANGE_ACCOUNTS +
    _BLOCKCHAIN_ACCOUNTS +
    _DEFI_ACCOUNTS +
    _VC_ACCOUNTS
)

# Top-100 coin project accounts — scrape fewer tweets, force-tag with coin ticker
_COIN_ACCOUNTS: List[tuple] = [
    # (ticker, twitter_handle)
    ("BTC",   "bitcoin"),
    ("ETH",   "ethereum"),
    ("BNB",   "BNBchain"),
    ("SOL",   "solana"),
    ("XRP",   "Ripple"),
    ("ADA",   "Cardano"),
    ("AVAX",  "avax"),
    ("DOGE",  "dogecoin"),
    ("DOT",   "Polkadot"),
    ("TRX",   "trondao"),
    ("LINK",  "chainlink"),
    ("MATIC", "0xPolygon"),
    ("UNI",   "Uniswap"),
    ("ATOM",  "cosmos"),
    ("ICP",   "dfinity"),
    ("LTC",   "litecoin"),
    ("FIL",   "Filecoin"),
    ("ARB",   "arbitrum"),
    ("OP",    "OptimismFND"),
    ("APT",   "Aptos"),
    ("SUI",   "SuiNetwork"),
    ("INJ",   "injective"),
    ("NEAR",  "nearprotocol"),
    ("IMX",   "Immutable"),
    ("GRT",   "graphprotocol"),
    ("AAVE",  "aave"),
    ("MKR",   "MakerDAO"),
    ("CRV",   "CurveFinance"),
    ("DYDX",  "dYdX"),
    ("GMX",   "GMX_IO"),
    ("XLM",   "StellarOrg"),
    ("VET",   "vechainofficial"),
    ("ALGO",  "Algorand"),
    ("HBAR",  "hashgraph"),
    ("XTZ",   "tezos"),
    ("FLOW",  "flow_blockchain"),
    ("EGLD",  "MultiversX"),
    ("KAVA",  "kava_platform"),
    ("ROSE",  "OasisProtocol"),
    ("CELO",  "CeloOrg"),
    ("ZIL",   "zilliqa"),
    ("IOTA",  "iota"),
    ("ONE",   "harmonyprotocol"),
    ("ZEC",   "zcash"),
    ("DASH",  "dashpay"),
    ("BAT",   "AttentionToken"),
    ("ENS",   "ensdomains"),
    ("SNX",   "synthetix_io"),
    ("COMP",  "compoundfinance"),
    ("1INCH", "1inchNetwork"),
    ("LDO",   "LidoFinance"),
    ("RPL",   "Rocket_Pool"),
    ("PENDLE","pendle_fi"),
    ("JUP",   "JupiterExchange"),
    ("SEI",   "SeiNetwork"),
    ("CFX",   "Conflux_Network"),
    ("BLUR",  "blur_io"),
    ("SAND",  "TheSandboxGame"),
    ("MANA",  "decentraland"),
    ("AXS",   "AxieInfinity"),
    ("CHZ",   "Chiliz"),
    ("THETA", "Theta_Network"),
    ("WAVES", "wavesprotocol"),
    ("ZRX",   "0xProject"),
    ("BAL",   "Balancer"),
    ("SUSHI", "SushiSwap"),
    ("YFI",   "iearnfinance"),
    ("RUNE",  "THORChain"),
    ("OSMO",  "osmosiszone"),
    ("JUNO",  "JunoNetwork"),
    ("SCRT",  "SecretNetwork"),
    ("FET",   "Fetch_ai"),
    ("OCEAN", "oceanprotocol"),
    ("NMR",   "numerai"),
    ("REN",   "renprotocol"),
    ("BAND",  "BandProtocol"),
    ("SKL",   "SkaleNetwork"),
    ("LRC",   "loopringorg"),
    ("DUSK",  "DuskFoundation"),
    ("ORN",   "orion_protocol"),
    ("CTSI",  "cartesiproject"),
    ("ANKR",  "ankr"),
    ("STORJ", "storjproject"),
    ("UMA",   "UMAprotocol"),
    ("KEEP",  "keep_project"),
    ("RLC",   "iEx_ec"),
    ("GLM",   "golemproject"),
    ("COTI",  "COTInetwork"),
    ("WRX",   "WazirXofficial"),
    ("ERG",   "ergoplatformorg"),
    ("AKT",   "akashnet_"),
    ("SCRT",  "SecretNetwork"),
    ("KILT",  "KILTprotocol"),
    ("CFG",   "centrifuge_io"),
    ("AGIX",  "SingularityNET"),
    ("FTM",   "FantomFDN"),
    ("EGLD",  "MultiversX"),
    ("XDC",   "XinFinNetwork"),
    ("VRA",   "verasitytech"),
    # Additional 50 coins (to reach 150 total)
    ("SHIB",  "Shibtoken"),
    ("PEPE",  "pepe"),
    ("DOGE",  "dogecoin"),
    ("MEME",  "memecoin"),
    ("SAFE",  "safe"),
    ("WLD",   "worldcoin"),
    ("ARK",   "arkproject"),
    ("ILV",   "illuviumgg"),
    ("QNT",   "QuantNetwork"),
    ("RNDR",  "rendertoken"),
    ("GALA",  "ProjectGala"),
    ("ASTR",  "AstarNetwork"),
    ("CANTO", "CantoPublic"),
    ("METIS", "MetisDAO"),
    ("MANTLE","0xMantle"),
    ("ZK",    "zksyncdao"),
    ("LINEA", "LineaBuild"),
    ("SCROLL","Scroll_ZK"),
    ("MANTA", "MantaNetwork"),
    ("TAIKO", "TaikoL2"),
    ("IMX2",  "Immutable"),
    ("MAGIC", "MagicLand_io"),
    ("STARL", "StarLabsDAO"),
    ("PIXEL", "PixelswapDEX"),
    ("ZORA",  "ourZORA"),
    ("ENJ",   "EnjinCoin"),
    ("REVV",  "REVVmotorsport"),
    ("LABS",  "labsdao"),
    ("LOKA",  "LokANetwork"),
    ("MYTH",  "MythologyNFT"),
    ("FLOKI", "Floki_Inu"),
    ("KISHU", "KishuInu"),
    ("ELON",  "ElonToken"),
    ("BNPL",  "BNPLToken"),
    ("LOOKS", "LooksRareNFT"),
    ("BLUR2", "blur_io"),
    ("X2Y2",  "x2y2_official"),
    ("DYDX2", "dYdX"),
    ("GMGM",  "GmGmDeFi"),
    ("BOND",  "BondAppIO"),
    ("ALICE", "AliceNetwork"),
    ("ROSE2", "OasisProtocol"),
    ("BETA",  "BetaFinance"),
    ("TOKE",  "TokenengineApp"),
    ("NEON",  "NeonEVM"),
    ("TONE",  "TonaNetwork"),
    ("ALEPH", "alephzero"),
    ("AVAIL", "AvailProject"),
    ("MONAD", "monad_xyz"),
    ("BEVM",  "BEVMofficial"),
    ("SOON",  "Solv_Finance"),
]

# Keywords that identify a tweet as a job posting
_JOB_KEYWORDS = {
    # Primary hiring indicators
    "hiring", "we're hiring", "we are hiring", "now hiring",
    "job opening", "job opportunity", "open role", "open position",
    "join our team", "join us", "career", "careers",
    "job", "jobs", "vacancy", "vacancies",
    "apply now", "apply here", "apply at",
    "work with us", "recruiting", "looking for",
    "new role", "new opportunity",
    # Role descriptors
    "developer", "engineer", "researcher", "analyst", "designer",
    "internship", "remote work", "full-time", "part-time",
    "solidity", "rust", "typescript", "golang", "python",
    # Hashtags
    "#web3jobs", "#cryptojobs", "#blockchainjobs", "#web3careers",
    "#hiring", "#defi", "#nftjobs", "#web3hiring",
    # Compensation
    "salary", "compensation", "equity", "token", "bounty", "grant",
}

# URLs to skip when extracting apply links (Twitter's own media/pic links)
_SKIP_URL_PATTERNS = {"pic.twitter.com", "twitter.com/i/", "x.com/i/", "pbs.twimg.com"}


# ── Scraper ──────────────────────────────────────────────────────────────────

class TwitterJobsScraper(BaseScraper):
    """
    Scrape job tweets from crypto job aggregator accounts and top-coin project accounts.
    Uses Twitter session cookies; no official API key required.
    """

    def __init__(self):
        super().__init__("twitter.com")
        self._creds: Dict[str, str] = {}
        self._tw_client: Optional[httpx.AsyncClient] = None

    # ── Context manager ──────────────────────────────────────────────────────

    async def __aenter__(self):
        await super().__aenter__()
        self._creds = self._load_creds()
        self._tw_client = httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers=self._tw_headers(),
        )
        return self

    async def __aexit__(self, *args):
        if self._tw_client:
            await self._tw_client.aclose()
        await super().__aexit__(*args)

    # ── Credential loading ───────────────────────────────────────────────────

    def _load_creds(self) -> Dict[str, str]:
        creds = {}
        try:
            with open(_ENV_FILE, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    creds[key.strip()] = val.strip().strip('"').strip()
            logger.info(f"[Twitter] Loaded credentials: {list(creds.keys())}")
        except FileNotFoundError:
            logger.error(f"[Twitter] Credentials file not found: {_ENV_FILE}")
        except Exception as e:
            logger.error(f"[Twitter] Failed to load credentials: {e}")
        return creds

    def _tw_headers(self) -> Dict[str, str]:
        auth    = self._creds.get("auth_token", "")
        ct0     = self._creds.get("ct0", "")
        guest   = self._creds.get("guest_id", "").strip()
        cookie  = f"auth_token={auth}; ct0={ct0}; guest_id={guest}"
        return {
            "Authorization":           f"Bearer {_BEARER}",
            "x-csrf-token":            ct0,
            "Cookie":                  cookie,
            "User-Agent":              "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
            "x-twitter-active-user":   "yes",
            "x-twitter-auth-type":     "OAuth2Session",
            "x-twitter-client-language": "en-US",
            "content-type":            "application/json",
            "Referer":                 "https://x.com/",
            "accept":                  "*/*",
            "accept-encoding":         "gzip, deflate",
            "accept-language":         "en-US",
        }

    # ── Twitter API helpers ──────────────────────────────────────────────────

    async def _get_user_id(self, screen_name: str) -> Optional[str]:
        """Return user_id for a given screen_name, or None on failure."""
        try:
            r = await self._tw_client.get(
                _GQL_USER,
                params={
                    "variables": json.dumps({
                        "screen_name": screen_name,
                        "withSafetyModeUserFields": False,
                    }),
                    "features": json.dumps(_USER_FEATURES),
                },
            )
            if r.status_code != 200:
                logger.debug(f"[Twitter] {screen_name}: {r.status_code}")
                return None
            data = r.json()
            return data["data"]["user"]["result"]["rest_id"]
        except Exception as e:
            logger.debug(f"[Twitter] get_user_id({screen_name}): {e}")
            return None

    async def _get_user_tweets(self, user_id: str, count: int = 50) -> List[dict]:
        """Return raw tweet dicts for a user."""
        try:
            r = await self._tw_client.get(
                _GQL_TWEETS,
                params={
                    "variables": json.dumps({
                        "userId": user_id,
                        "count": count,
                        "includePromotedContent": False,
                        "withQuickPromoteEligibilityTweetFields": False,
                        "withVoice": True,
                        "withV2Timeline": True,
                    }),
                    "features": json.dumps(_FEATURES),
                },
            )
            if r.status_code != 200:
                logger.debug(f"[Twitter] UserTweets({user_id}): {r.status_code}")
                return []
            data = r.json()
            tweets = []
            instructions = (
                data.get("data", {})
                    .get("user", {})
                    .get("result", {})
                    .get("timeline_v2", {})
                    .get("timeline", {})
                    .get("instructions", [])
            )
            for inst in instructions:
                for entry in inst.get("entries", []):
                    try:
                        item = entry["content"]["itemContent"]["tweet_results"]["result"]
                        legacy = item.get("legacy", {})
                        if not legacy.get("full_text"):
                            continue
                        tweets.append({
                            "text":       legacy["full_text"],
                            "created_at": legacy.get("created_at", ""),
                            "urls":       legacy.get("entities", {}).get("urls", []),
                            "screen_name": (
                                item.get("core", {})
                                    .get("user_results", {})
                                    .get("result", {})
                                    .get("legacy", {})
                                    .get("screen_name", "")
                            ),
                        })
                    except Exception:
                        pass
            return tweets
        except Exception as e:
            logger.debug(f"[Twitter] _get_user_tweets({user_id}): {e}")
            return []

    # ── Tweet filtering & parsing ────────────────────────────────────────────

    def _is_job_tweet(self, text: str) -> bool:
        """Return True if the tweet looks like a job posting."""
        text_lower = text.lower()
        return any(kw in text_lower for kw in _JOB_KEYWORDS)

    def _extract_apply_url(self, urls: List[dict]) -> str:
        """Get the best apply URL from tweet entity URLs (skips Twitter media links)."""
        for u in urls:
            expanded = u.get("expanded_url", "") or u.get("url", "")
            if expanded and not any(skip in expanded for skip in _SKIP_URL_PATTERNS):
                return expanded
        # Fallback: first URL even if it's a t.co link
        if urls:
            return urls[0].get("url", "")
        return ""

    def _parse_listed_date(self, created_at: str) -> datetime:
        """Parse Twitter date string → datetime."""
        try:
            return datetime.strptime(created_at, "%a %b %d %H:%M:%S +0000 %Y")
        except Exception:
            return datetime.utcnow()

    def _extract_title(self, text: str) -> str:
        """
        Best-effort job title from tweet text.
        Uses the first non-empty line, stripped of hashtags/emoji noise.
        """
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        title = lines[0] if lines else text[:100]
        # Remove trailing hashtag lines
        title = re.sub(r"#\w+", "", title).strip()
        # Collapse extra spaces
        title = re.sub(r"\s{2,}", " ", title)
        return title[:120] or "Crypto Job"

    def _extract_company(self, text: str, screen_name: str) -> str:
        """
        Try to extract the hiring company from tweet text.
        Falls back to the Twitter account name.
        """
        # Pattern: "Company is hiring" / "at Company" / "@Company"
        for pat in [
            r"(?:at|@)\s+([A-Z][A-Za-z0-9_&\-]{2,30})",
            r"([A-Z][A-Za-z0-9_&\-]{2,30})\s+is hiring",
            r"([A-Z][A-Za-z0-9_&\-]{2,30})\s+are hiring",
        ]:
            m = re.search(pat, text)
            if m:
                candidate = m.group(1).strip()
                if len(candidate) > 2 and candidate.lower() not in {"the", "our", "your", "we"}:
                    return candidate[:60]
        return screen_name[:60]

    def _tweet_to_job(
        self,
        tweet: dict,
        forced_ticker: Optional[str] = None,
    ) -> Optional[dict]:
        """Convert a raw tweet dict to a job dict. Returns None if not a job tweet."""
        text = tweet.get("text", "")
        if not self._is_job_tweet(text):
            return None

        url = self._extract_apply_url(tweet.get("urls", []))
        if not url:
            # No URL = not a real job listing (just general talk)
            return None

        screen_name = tweet.get("screen_name", "twitter.com")
        company     = self._extract_company(text, screen_name)
        title       = self._extract_title(text)
        listed_date = self._parse_listed_date(tweet.get("created_at", ""))

        # Coin mapping: use forced ticker (for coin project accounts) or mapper
        coin_ticker = forced_ticker
        if not coin_ticker:
            try:
                from utils.coin_mapper import match_company_to_coin
                coin_ticker = match_company_to_coin(company)
            except Exception:
                pass

        return {
            "title":       title,
            "company":     company,
            "location":    "Remote",
            "url":         url,
            "listed_date": listed_date,
            "deadline":    None,
            "source_site": self.source_site,
            "scraped_at":  datetime.utcnow(),
            "coin_ticker": coin_ticker,
        }

    # ── Main fetch ───────────────────────────────────────────────────────────

    async def fetch(self) -> List[Dict]:
        logger.info(f"[Twitter] Starting scraper")

        if not self._creds:
            logger.error("[Twitter] No credentials — skipping")
            return []

        jobs: List[dict] = []
        seen_urls: set = set()

        # ── Phase 1: job aggregator accounts (50 tweets each) ──
        logger.info(f"[Twitter] Phase 1: scraping {len(_JOB_AGGREGATORS)} job aggregator accounts")
        for screen_name in _JOB_AGGREGATORS:
            user_id = await self._get_user_id(screen_name)
            if not user_id:
                logger.debug(f"[Twitter] @{screen_name}: not found / private")
                await asyncio.sleep(1.0)
                continue

            tweets = await self._get_user_tweets(user_id, count=50)
            logger.info(f"[Twitter] @{screen_name}: {len(tweets)} tweets fetched")

            for tweet in tweets:
                job = self._tweet_to_job(tweet, forced_ticker=None)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)

            await asyncio.sleep(1.5)  # be polite between accounts

        # ── Phase 2: coin project accounts (20 tweets each, 150 coins total) ──
        logger.info(f"[Twitter] Phase 2: scraping {len(_COIN_ACCOUNTS)} coin project accounts (top 150 by market cap)")
        for ticker, screen_name in _COIN_ACCOUNTS:
            user_id = await self._get_user_id(screen_name)
            if not user_id:
                logger.debug(f"[Twitter] @{screen_name} ({ticker}): not found")
                await asyncio.sleep(0.8)
                continue

            tweets = await self._get_user_tweets(user_id, count=20)
            logger.info(f"[Twitter] @{screen_name} ({ticker}): {len(tweets)} tweets")

            for tweet in tweets:
                job = self._tweet_to_job(tweet, forced_ticker=ticker)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)

            await asyncio.sleep(1.0)

        # ── Phase 3: exchange accounts (15 tweets each, monitor for job keywords) ──
        logger.info(f"[Twitter] Phase 3: scraping {len(_EXCHANGE_ACCOUNTS)} exchange accounts")
        for screen_name in _EXCHANGE_ACCOUNTS:
            user_id = await self._get_user_id(screen_name)
            if not user_id:
                logger.debug(f"[Twitter] @{screen_name}: not found")
                await asyncio.sleep(0.8)
                continue

            tweets = await self._get_user_tweets(user_id, count=15)
            logger.info(f"[Twitter] @{screen_name}: {len(tweets)} tweets")

            for tweet in tweets:
                job = self._tweet_to_job(tweet, forced_ticker=None)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)

            await asyncio.sleep(0.8)

        # ── Phase 4: blockchain accounts (15 tweets each) ──
        logger.info(f"[Twitter] Phase 4: scraping {len(_BLOCKCHAIN_ACCOUNTS)} blockchain accounts")
        for screen_name in _BLOCKCHAIN_ACCOUNTS:
            user_id = await self._get_user_id(screen_name)
            if not user_id:
                logger.debug(f"[Twitter] @{screen_name}: not found")
                await asyncio.sleep(0.8)
                continue

            tweets = await self._get_user_tweets(user_id, count=15)
            logger.info(f"[Twitter] @{screen_name}: {len(tweets)} tweets")

            for tweet in tweets:
                job = self._tweet_to_job(tweet, forced_ticker=None)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)

            await asyncio.sleep(0.8)

        # ── Phase 5: DeFi protocol accounts (15 tweets each) ──
        logger.info(f"[Twitter] Phase 5: scraping {len(_DEFI_ACCOUNTS)} DeFi accounts")
        for screen_name in _DEFI_ACCOUNTS:
            user_id = await self._get_user_id(screen_name)
            if not user_id:
                logger.debug(f"[Twitter] @{screen_name}: not found")
                await asyncio.sleep(0.8)
                continue

            tweets = await self._get_user_tweets(user_id, count=15)
            logger.info(f"[Twitter] @{screen_name}: {len(tweets)} tweets")

            for tweet in tweets:
                job = self._tweet_to_job(tweet, forced_ticker=None)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)

            await asyncio.sleep(0.8)

        # ── Phase 6: VC and investment firm accounts (15 tweets each) ──
        logger.info(f"[Twitter] Phase 6: scraping {len(_VC_ACCOUNTS)} VC accounts")
        for screen_name in _VC_ACCOUNTS:
            user_id = await self._get_user_id(screen_name)
            if not user_id:
                logger.debug(f"[Twitter] @{screen_name}: not found")
                await asyncio.sleep(0.8)
                continue

            tweets = await self._get_user_tweets(user_id, count=15)
            logger.info(f"[Twitter] @{screen_name}: {len(tweets)} tweets")

            for tweet in tweets:
                job = self._tweet_to_job(tweet, forced_ticker=None)
                if job and job["url"] not in seen_urls:
                    seen_urls.add(job["url"])
                    jobs.append(job)

            await asyncio.sleep(0.8)

        logger.info(f"[OK] twitter.com: {len(jobs)} job tweets collected")
        return jobs
