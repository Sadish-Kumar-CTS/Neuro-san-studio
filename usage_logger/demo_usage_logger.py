# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
#
# Licensed under the Academic Public License.
#
# Usage logger plugin implementation for Aurora PostgreSQL (via RDS).
# This is a pluggable logger that integrates with the Neuro-SAN UsageLogger interface.
#

import os
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Numeric,
    JSON, TIMESTAMP, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from neuro_san.interfaces.usage_logger import UsageLogger

# -------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

Base = declarative_base()


# -------------------------------------------------------------------
# Database Models
# -------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True)
    username = Column(String(100))
    email = Column(String(150))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class Request(Base):
    __tablename__ = "requests"

    request_id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.user_id", ondelete="CASCADE"))
    session_id = Column(String(64))
    model_provider = Column(String(50))
    model_name = Column(String(100))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    total_cost = Column(Numeric(10, 4))
    time_taken_sec = Column(Numeric(10, 3))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class UsageLog(Base):
    __tablename__ = "usage_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), ForeignKey("requests.request_id", ondelete="CASCADE"))
    raw_metadata = Column(JSON)
    raw_usage = Column(JSON)
    logged_at = Column(TIMESTAMP, default=datetime.utcnow)


# -------------------------------------------------------------------
# Postgres Usage Logger
# -------------------------------------------------------------------
class PostgresUsageLogger(UsageLogger):
    """
    A concrete implementation of UsageLogger that persists logs into
    an Aurora PostgreSQL database using SQLAlchemy ORM.

    Required environment variables:
        USAGE_DB_USER     - Database username
        USAGE_DB_PASS     - Database password
        USAGE_DB_HOST     - RDS/Aurora host endpoint
        USAGE_DB_PORT     - Database port (default: 5432)
        USAGE_DB_NAME     - Database name (default: postgres)
    """

    def __init__(self, engine_url: Optional[str] = None) -> None:
        if engine_url:
            self.DATABASE_URL = engine_url
        else:
            self.DATABASE_URL = self._construct_db_url()

        self.engine = create_engine(self.DATABASE_URL, echo=False, future=True)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)

        # ORM metadata syncs with tables (tables must already exist).
        Base.metadata.create_all(self.engine)
        logger.info("PostgresUsageLogger initialized and ready.")

    @staticmethod
    def _construct_db_url() -> str:
        """
        Constructs the database connection string from environment variables.
        """
        db_user = os.environ.get("USAGE_DB_USER")
        db_pass = os.environ.get("USAGE_DB_PASS")
        db_host = os.environ.get("USAGE_DB_HOST")
        db_port = os.environ.get("USAGE_DB_PORT", "5432")
        db_name = os.environ.get("USAGE_DB_NAME", "postgres")

        if not all([db_user, db_pass, db_host, db_name]):
            raise RuntimeError("Missing required DB environment variables for PostgresUsageLogger")

        return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    async def log_usage(self, token_dict: Dict[str, Any], request_metadata: Dict[str, Any]) -> None:
        """
        Persists usage details into PostgreSQL.

        :param token_dict: Dictionary containing token usage stats.
        :param request_metadata: Metadata describing request/session context.
        """
        session: Session = self.SessionLocal()
        try:
            request_id = request_metadata.get("request_id")
            user_id = request_metadata.get("user_id", "unknown")

            # Ensure user exists
            user = session.get(User, user_id)
            if not user:
                user = User(
                    user_id=user_id,
                    username=request_metadata.get("username"),
                    email=request_metadata.get("email")
                )
                session.add(user)

            # Persist request
            request = Request(
                request_id=request_id,
                user_id=user_id,
                session_id=request_metadata.get("session_id"),
                model_provider=request_metadata.get("model_provider", "unknown"),
                model_name=request_metadata.get("model_name", "unknown"),
                prompt_tokens=token_dict.get("prompt_tokens", 0),
                completion_tokens=token_dict.get("completion_tokens", 0),
                total_tokens=token_dict.get("total_tokens", 0),
                total_cost=token_dict.get("total_cost", 0.0),
                time_taken_sec=token_dict.get("time_taken_in_seconds", 0.0),
                created_at=datetime.utcnow(),
            )
            session.add(request)

            # Persist usage log
            usage_log = UsageLog(
                request_id=request_id,
                raw_metadata=request_metadata,
                raw_usage=token_dict,
                logged_at=datetime.utcnow(),
            )
            session.add(usage_log)

            session.commit()
            logger.info(f"Usage logged successfully [request_id={request_id}]")

        except Exception as ex:
            session.rollback()
            logger.error(f" Failed to log usage: {ex}", exc_info=True)
            raise
        finally:
            session.close()
