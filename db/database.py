"""
PostgreSQL (NeonDB) persistence: user profiles (name, role, interests, freeform notes)
and recent chat history, so Atlas never asks the same thing twice and can
ground replies in the last few turns of conversation.

All calls use asyncpg for native async PostgreSQL operations.
"""

import json
import time
from typing import Any, Dict, List, Optional

import asyncpg
import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    chat_id     BIGINT PRIMARY KEY,
    profile     TEXT NOT NULL DEFAULT '{}',
    created_at  DOUBLE PRECISION NOT NULL,
    last_seen   DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id          BIGSERIAL PRIMARY KEY,
    chat_id     BIGINT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    created_at  DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages (chat_id, created_at);
"""

_pool: Optional[asyncpg.Pool] = None


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if config.DATABASE_URL:
            _pool = await asyncpg.create_pool(config.DATABASE_URL)
        else:
            # Fallback to SQLite if no DATABASE_URL provided
            raise ValueError("DATABASE_URL not set. Please configure NeonDB connection.")
    return _pool


async def init_db() -> None:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(_SCHEMA)


# --------------------------------------------------------------------------
# User profile (persistent memory)
# --------------------------------------------------------------------------

async def get_profile(chat_id: int) -> Dict[str, Any]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT profile FROM users WHERE chat_id = $1", chat_id
        )
        return json.loads(row["profile"]) if row else {}


async def touch_user(chat_id: int) -> None:
    now = time.time()
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (chat_id, profile, created_at, last_seen)
            VALUES ($1, '{}', $2, $3)
            ON CONFLICT(chat_id) DO UPDATE SET last_seen = excluded.last_seen
            """,
            chat_id, now, now,
        )


async def update_profile(chat_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT profile FROM users WHERE chat_id = $1", chat_id
        )
        profile = json.loads(row["profile"]) if row else {}
        profile.update({k: v for k, v in updates.items() if v not in (None, "")})

        now = time.time()
        await conn.execute(
            """
            INSERT INTO users (chat_id, profile, created_at, last_seen)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT(chat_id) DO UPDATE SET profile = excluded.profile, last_seen = excluded.last_seen
            """,
            chat_id, json.dumps(profile), now, now,
        )
        return profile


async def all_chat_ids() -> List[int]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT chat_id FROM users")
        return [r["chat_id"] for r in rows]


# --------------------------------------------------------------------------
# Chat history
# --------------------------------------------------------------------------

async def save_message(chat_id: int, role: str, content: str) -> None:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES ($1, $2, $3, $4)",
            chat_id, role, content, time.time(),
        )


async def recent_messages(chat_id: int, limit: Optional[int] = None) -> List[Dict[str, str]]:
    limit = limit or config.MAX_HISTORY_MESSAGES
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT role, content FROM messages
            WHERE chat_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            chat_id, limit,
        )
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None