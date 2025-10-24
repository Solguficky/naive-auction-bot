import asyncpg
import logging
import os
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

pool = None

async def init_db():
    global pool
    
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable is required")
        raise ValueError("DATABASE_URL environment variable is required")
    
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bids (
                id SERIAL PRIMARY KEY,
                lot_id INTEGER NOT NULL,
                user_id BIGINT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    logger.info("Database initialized successfully")

async def save_bid(lot_id: int, user_id: int, amount: float) -> int:
    async with pool.acquire() as conn:
        bid_id = await conn.fetchval(
            "INSERT INTO bids (lot_id, user_id, amount) VALUES ($1, $2, $3) RETURNING id",
            lot_id, user_id, amount
        )
        logger.info(f"Saved bid {bid_id}: lot={lot_id}, user={user_id}, amount={amount}")
        return bid_id

async def get_lot_bids(lot_id: int) -> List[Dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM bids WHERE lot_id = $1 ORDER BY created_at ASC",
            lot_id
        )
        result = []
        for row in rows:
            bid = dict(row)
            bid['amount'] = float(bid['amount'])
            result.append(bid)
        return result

async def get_current_max_bid(lot_id: int) -> Optional[Dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM bids WHERE lot_id = $1 ORDER BY amount DESC LIMIT 1",
            lot_id
        )
        if row:
            result = dict(row)
            result['amount'] = float(result['amount'])
            return result
        return None

async def get_all_bids() -> List[Dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM bids ORDER BY created_at ASC")
        result = []
        for row in rows:
            bid = dict(row)
            bid['amount'] = float(bid['amount'])
            result.append(bid)
        return result

async def get_user_bids(user_id: int) -> List[Dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM bids WHERE user_id = $1 ORDER BY created_at DESC",
            user_id
        )
        result = []
        for row in rows:
            bid = dict(row)
            bid['amount'] = float(bid['amount'])
            result.append(bid)
        return result

async def close_pool():
    global pool
    if pool:
        await pool.close()
        logger.info("Database connection pool closed")
