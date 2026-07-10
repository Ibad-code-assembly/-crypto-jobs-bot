import hashlib
import re
from sqlalchemy import Column, String, Integer, DateTime, Boolean, UniqueConstraint, create_engine, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

Base = declarative_base()


class Coin(Base):
    __tablename__ = "coins"

    id = Column(String, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    market_cap_rank = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Coin(id={self.id}, symbol={self.symbol}, name={self.name}, rank={self.market_cap_rank})>"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint('job_hash', name='uq_job_hash'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    url = Column(String, nullable=False)
    listed_date = Column(DateTime)
    deadline = Column(DateTime)
    source_site = Column(String, nullable=False, index=True)
    scraped_at = Column(DateTime, nullable=False)
    job_hash = Column(String, nullable=False, unique=True, index=True)
    coin_ticker = Column(String, index=True)
    duplicate_sources = Column(Text, default="")  # Track which sources posted this job
    duplicate_count = Column(Integer, default=1)   # How many times seen from different sources
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def normalize_string(s: str) -> str:
        """Normalize string for fingerprinting: lowercase, remove extra spaces, trim punctuation."""
        if not s:
            return ""
        # Lowercase and strip whitespace
        s = s.lower().strip()
        # Remove special punctuation/formatting (keep alphanumeric, spaces, hyphens)
        s = re.sub(r'[^\w\s\-]', '', s)
        # Collapse multiple spaces
        s = re.sub(r'\s+', ' ', s)
        return s

    @staticmethod
    def generate_hash(title: str, company: str, url: str) -> str:
        """Generate fingerprint hash: normalized title + company + domain."""
        # Normalize title and company
        norm_title = Job.normalize_string(title)
        norm_company = Job.normalize_string(company)

        # Extract domain from URL to avoid hash mismatches due to URL formatting
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
        except Exception:
            domain = url.lower()

        # Create fingerprint: title|company|domain
        content = f"{norm_title}|{norm_company}|{domain}"
        return hashlib.sha256(content.encode()).hexdigest()

    def __repr__(self):
        return f"<Job(id={self.id}, title={self.title}, company={self.company}, hash={self.job_hash[:8]}...)>"


class NewCoinListing(Base):
    __tablename__ = "new_coin_listings"
    __table_args__ = (
        UniqueConstraint('coin_symbol', 'exchange', name='uq_coin_exchange'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_symbol = Column(String, nullable=False, index=True)
    coin_name = Column(String)
    exchange = Column(String, nullable=False, index=True)  # Which exchange
    trading_pairs = Column(Text, default="")  # CSV list of pairs (USDT, BUSD, etc.)
    url = Column(String)  # Link to exchange listing/announcement
    listed_date = Column(DateTime)  # When listed on THIS exchange
    scraped_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def generate_hash(symbol: str, exchange: str) -> str:
        """Generate fingerprint hash from coin symbol + exchange."""
        content = f"{symbol.upper().strip()}|{exchange.upper().strip()}"
        return hashlib.sha256(content.encode()).hexdigest()

    def __repr__(self):
        return f"<NewCoinListing(id={self.id}, symbol={self.coin_symbol}, exchange={self.exchange})>"


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint('user_id', 'coin_ticker', name='uq_user_coin'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    coin_ticker = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, coin={self.coin_ticker})>"


def get_engine():
    database_url = os.getenv("DATABASE_URL", "sqlite:///crypto_jobs.db")
    return create_engine(database_url)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
