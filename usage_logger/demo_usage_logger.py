import os
import json
import asyncio
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Numeric,
    TIMESTAMP,
    JSON,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from neuro_san.interfaces.usage_logger import UsageLogger

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True)
    username = Column(String(100), nullable=True)
    email = Column(String(150), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class Request(Base):
    __tablename__ = "requests"

    request_id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.user_id", ondelete="CASCADE"))
    session_id = Column(String(64), nullable=True)
    model_provider = Column(String(50), default="unknown")
    model_name = Column(String(100), default="unknown")
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 4), default=0.0)
    time_taken_sec = Column(Numeric(10, 3), default=0.0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship("User", backref="requests")


class UsageLog(Base):
    __tablename__ = "usage_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), ForeignKey("requests.request_id", ondelete="CASCADE"))
    raw_metadata = Column(JSON)
    raw_usage = Column(JSON)
    logged_at = Column(TIMESTAMP, default=datetime.utcnow)

    request = relationship("Request", backref="usage_logs")


class DemoUsageLogger(UsageLogger):
    """
    Usage Logger implementation for PostgreSQL.
    Logs per-request usage data into normalized tables (users, requests, usage_logs).
    """

    def __init__(self):
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL environment variable must be set")

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _normalize_usage(self, token_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Unwrap token_dict if nested under a provider key (like 'all')."""
        if not token_dict:
            return {}
        if isinstance(next(iter(token_dict.values())), dict):
            _, stats = next(iter(token_dict.items()))
            return stats
        return token_dict

    async def log_usage(self, token_dict: Dict[str, Any], request_metadata: Dict[str, Any]):
        session = self.Session()
        try:
            # Normalize usage stats
            stats = self._normalize_usage(token_dict)

            # Ensure user exists
            user_id = request_metadata.get("user_id", "unknown")
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                user = User(user_id=user_id)
                session.add(user)

            # Create request entry
            request = Request(
                request_id=request_metadata.get("request_id", f"req_{datetime.utcnow().timestamp()}"),
                user_id=user_id,
                session_id=request_metadata.get("session_id"),  # may be None
                model_provider=request_metadata.get("model_provider", "unknown"),
                model_name=request_metadata.get("model_name", "unknown"),
                prompt_tokens=stats.get("prompt_tokens", 0),
                completion_tokens=stats.get("completion_tokens", 0),
                total_tokens=stats.get("total_tokens", 0),
                total_cost=stats.get("total_cost", 0.0),
                time_taken_sec=stats.get("time_taken_in_seconds", 0.0),
                created_at=datetime.utcnow(),
            )
            session.merge(request)

            # Create usage log entry
            usage_log = UsageLog(
                request_id=request.request_id,
                raw_metadata=request_metadata,
                raw_usage=token_dict,
                logged_at=datetime.utcnow(),
            )
            session.add(usage_log)

            session.commit()

        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

