import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .models import Job, Subscription, Coin

logger = logging.getLogger(__name__)


def insert_or_update_jobs(jobs: List[Dict], db: Session) -> Tuple[int, int]:
    """
    Insert new jobs or update existing ones based on job_hash.
    Returns (new_count, updated_count).
    """
    new_count = 0
    updated_count = 0

    for job_data in jobs:
        try:
            job_hash = Job.generate_hash(
                job_data["title"],
                job_data["company"],
                job_data["url"]
            )

            existing_job = db.query(Job).filter(Job.job_hash == job_hash).first()

            if existing_job:
                existing_job.is_active = True
                existing_job.updated_at = datetime.utcnow()
                updated_count += 1
                logger.debug(f"Updated job: {existing_job.title} ({job_hash[:8]}...)")
            else:
                new_job = Job(
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data.get("location", "Unknown"),
                    url=job_data["url"],
                    listed_date=job_data.get("listed_date"),
                    deadline=job_data.get("deadline"),
                    source_site=job_data["source_site"],
                    scraped_at=job_data.get("scraped_at", datetime.utcnow()),
                    job_hash=job_hash,
                    coin_ticker=job_data.get("coin_ticker"),
                    is_active=True
                )
                db.add(new_job)
                new_count += 1
                logger.debug(f"Inserted job: {new_job.title} ({job_hash[:8]}...)")

        except IntegrityError:
            db.rollback()
            logger.warning(f"Integrity error for job: {job_data.get('title')}")
            continue
        except Exception as e:
            logger.error(f"Error processing job {job_data.get('title')}: {str(e)}")
            continue

    try:
        db.commit()
        logger.info(f"Jobs: {new_count} inserted, {updated_count} updated")
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing jobs: {str(e)}")
        raise

    return new_count, updated_count


def mark_expired_jobs(source_site: str, current_job_urls: List[str], db: Session) -> int:
    """
    Mark jobs as inactive if their URLs are not in current_job_urls.
    Returns count of expired jobs.
    """
    expired_jobs = db.query(Job).filter(
        Job.source_site == source_site,
        Job.is_active == True,
        ~Job.url.in_(current_job_urls)
    ).all()

    expired_count = 0
    for job in expired_jobs:
        job.is_active = False
        job.updated_at = datetime.utcnow()
        expired_count += 1
        logger.debug(f"Marked expired: {job.title}")

    try:
        db.commit()
        logger.info(f"Marked {expired_count} jobs as expired from {source_site}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking expired jobs: {str(e)}")
        raise

    return expired_count


def get_jobs_by_coin(coin_ticker: str, db: Session) -> List[Job]:
    """Get all active jobs for a coin."""
    return db.query(Job).filter(
        Job.coin_ticker == coin_ticker,
        Job.is_active == True
    ).order_by(Job.created_at.desc()).all()


def find_new_jobs(hours: int = 24, db: Session = None) -> List[Job]:
    """Find active jobs created in last N hours."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    return db.query(Job).filter(
        Job.created_at >= cutoff_time,
        Job.is_active == True
    ).order_by(Job.created_at.desc()).all()


def find_expiring_jobs(hours: int = 48, db: Session = None) -> List[Job]:
    """Find active jobs with deadline in next N hours."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()

    now = datetime.utcnow()
    cutoff_time = now + timedelta(hours=hours)
    return db.query(Job).filter(
        Job.deadline >= now,
        Job.deadline <= cutoff_time,
        Job.is_active == True
    ).order_by(Job.deadline.asc()).all()


def add_subscription(user_id: int, coin_ticker: str, db: Session) -> bool:
    """Add a subscription. Returns True if successful, False if already exists."""
    try:
        existing = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.coin_ticker == coin_ticker
        ).first()

        if existing:
            logger.warning(f"User {user_id} already subscribed to {coin_ticker}")
            return False

        subscription = Subscription(user_id=user_id, coin_ticker=coin_ticker)
        db.add(subscription)
        db.commit()
        logger.info(f"Added subscription: user {user_id} -> {coin_ticker}")
        return True

    except IntegrityError:
        db.rollback()
        logger.warning(f"Integrity error adding subscription for user {user_id}")
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding subscription: {str(e)}")
        raise


def remove_subscription(user_id: int, coin_ticker: str, db: Session) -> bool:
    """Remove a subscription. Returns True if successful, False if not found."""
    try:
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.coin_ticker == coin_ticker
        ).first()

        if not subscription:
            logger.warning(f"Subscription not found for user {user_id} -> {coin_ticker}")
            return False

        db.delete(subscription)
        db.commit()
        logger.info(f"Removed subscription: user {user_id} -> {coin_ticker}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error removing subscription: {str(e)}")
        raise


def get_user_subscriptions(user_id: int, db: Session) -> List[str]:
    """Get list of coin tickers user is subscribed to."""
    subscriptions = db.query(Subscription.coin_ticker).filter(
        Subscription.user_id == user_id
    ).all()
    return [sub[0] for sub in subscriptions]


def get_subscribers_for_coin(coin_ticker: str, db: Session) -> List[int]:
    """Get list of user IDs subscribed to a coin."""
    subscribers = db.query(Subscription.user_id).filter(
        Subscription.coin_ticker == coin_ticker
    ).all()
    return [sub[0] for sub in subscribers]


def job_exists(job_hash: str, db: Session) -> bool:
    """Check if job with given hash exists."""
    return db.query(Job).filter(Job.job_hash == job_hash).first() is not None


def get_all_active_jobs(db: Session) -> List[Job]:
    """Get all active jobs."""
    return db.query(Job).filter(Job.is_active == True).all()


def get_job_count(db: Session) -> int:
    """Get count of active jobs."""
    return db.query(Job).filter(Job.is_active == True).count()


def map_jobs_to_coins(jobs: List[Job], db: Session) -> List[Job]:
    """
    Map jobs to coin tickers using fuzzy matching.
    Updates job.coin_ticker and saves to database.
    Returns updated jobs list.
    """
    from utils.coin_mapper import match_company_to_coin

    mapped_count = 0
    unmapped_count = 0

    for job in jobs:
        try:
            ticker = match_company_to_coin(job.company)

            if ticker:
                job.coin_ticker = ticker
                mapped_count += 1
                logger.debug(f"Mapped: {job.company} -> {ticker}")
            else:
                unmapped_count += 1
                logger.debug(f"Unmapped: {job.company}")

        except Exception as e:
            logger.error(f"Error mapping job {job.id}: {str(e)}")
            unmapped_count += 1
            continue

    try:
        db.commit()
        logger.info(f"Jobs mapped: {mapped_count} mapped, {unmapped_count} unmapped")
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing mapped jobs: {str(e)}")
        raise

    return jobs
