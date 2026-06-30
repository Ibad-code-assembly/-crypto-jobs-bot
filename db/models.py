import hashlib
from sqlalchemy import Column, String, Integer, DateTime, Boolean, UniqueConstraint, create_engine
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
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def generate_hash(title: str, company: str, url: str) -> str:
        content = f"{title}|{company}|{url}".lower().strip()
        return hashlib.sha256(content.encode()).hexdigest()

    def __repr__(self):
        return f"<Job(id={self.id}, title={self.title}, company={self.company}, hash={self.job_hash[:8]}...)>"


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
