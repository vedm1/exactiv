"""Storage: the Store interface and the Postgres implementation (asyncpg)."""

import uuid
from typing import Protocol

import asyncpg  # type: ignore[import-untyped]

from exaktiv_site_form.models import DataRegion, EnquiryIn, PendingMail, Topic


class Store(Protocol):
    async def check_and_record_hit(self, ip_hash: str, limit: int, window_s: int) -> bool: ...
    async def insert_enquiry(self, e: EnquiryIn) -> uuid.UUID: ...
    async def get_pending_mail(self, max_attempts: int) -> list[PendingMail]: ...
    async def record_mail_attempt(self, enquiry_id: uuid.UUID) -> int: ...
    async def mark_team_notified(self, enquiry_id: uuid.UUID) -> None: ...
    async def mark_autoreply_sent(self, enquiry_id: uuid.UUID) -> None: ...
    async def delete_expired(self) -> int: ...
    async def purge_hits(self, older_than_s: int) -> int: ...


def _count(status: str) -> int:
    return int(status.rsplit(" ", 1)[-1])


class PgStore:
    def __init__(self, pool: asyncpg.Pool | None = None) -> None:
        self._pool = pool

    async def open(self, dsn: str, **connect_kwargs: str) -> None:
        self._pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5, **connect_kwargs)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("PgStore is not open")
        return self._pool

    async def check_and_record_hit(self, ip_hash: str, limit: int, window_s: int) -> bool:
        """Count recent hits for this IP hash. Refuse at the limit, else record this attempt.

        The advisory lock makes count-then-insert atomic for one IP hash.
        """
        async with self.pool.acquire() as conn, conn.transaction():
            await conn.execute("SELECT pg_advisory_xact_lock(hashtext($1))", ip_hash)
            count = await conn.fetchval(
                "SELECT count(*) FROM site_form_hits "
                "WHERE ip_hash = $1 AND hit_at > now() - make_interval(secs => $2)",
                ip_hash,
                float(window_s),
            )
            if count >= limit:
                return False
            await conn.execute("INSERT INTO site_form_hits (ip_hash) VALUES ($1)", ip_hash)
            return True

    async def insert_enquiry(self, e: EnquiryIn) -> uuid.UUID:
        value: uuid.UUID = await self.pool.fetchval(
            "INSERT INTO site_enquiries (name, email, company, role, topic, data_region, message) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id",
            e.name,
            e.email,
            e.company,
            e.role,
            e.topic.value,
            e.data_region.value if e.data_region else None,
            e.message,
        )
        return value

    async def get_pending_mail(self, max_attempts: int) -> list[PendingMail]:
        rows = await self.pool.fetch(
            "SELECT id, name, email, company, role, topic, data_region, message, "
            "team_notified_at IS NULL AS team_pending, autoreply_sent_at IS NULL AS reply_pending "
            "FROM site_enquiries "
            "WHERE (team_notified_at IS NULL OR autoreply_sent_at IS NULL) AND mail_attempts < $1 "
            "ORDER BY created_at LIMIT 50",
            max_attempts,
        )
        return [
            PendingMail(
                r["id"],
                EnquiryIn(
                    r["name"],
                    r["email"],
                    r["company"],
                    r["role"],
                    Topic(r["topic"]),
                    DataRegion(r["data_region"]) if r["data_region"] else None,
                    r["message"],
                ),
                r["team_pending"],
                r["reply_pending"],
            )
            for r in rows
        ]

    async def record_mail_attempt(self, enquiry_id: uuid.UUID) -> int:
        value: int = await self.pool.fetchval(
            "UPDATE site_enquiries SET mail_attempts = mail_attempts + 1 "
            "WHERE id = $1 RETURNING mail_attempts",
            enquiry_id,
        )
        return value

    async def mark_team_notified(self, enquiry_id: uuid.UUID) -> None:
        await self.pool.execute(
            "UPDATE site_enquiries SET team_notified_at = now() WHERE id = $1", enquiry_id
        )

    async def mark_autoreply_sent(self, enquiry_id: uuid.UUID) -> None:
        await self.pool.execute(
            "UPDATE site_enquiries SET autoreply_sent_at = now() WHERE id = $1", enquiry_id
        )

    async def delete_expired(self) -> int:
        """W-G4: remove every enquiry past delete_after."""
        return _count(
            await self.pool.execute("DELETE FROM site_enquiries WHERE delete_after <= now()")
        )

    async def purge_hits(self, older_than_s: int) -> int:
        return _count(
            await self.pool.execute(
                "DELETE FROM site_form_hits WHERE hit_at < now() - make_interval(secs => $1)",
                float(older_than_s),
            )
        )
