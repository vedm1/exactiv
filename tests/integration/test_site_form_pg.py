import asyncio
from pathlib import Path

import asyncpg  # type: ignore[import-untyped]
import httpx
import pytest
from alembic import command
from alembic.script import ScriptDirectory
from exaktiv_site_form.main import create_app
from exaktiv_site_form.models import EnquiryIn
from exaktiv_site_form.spam import make_token
from exaktiv_site_form.store import PgStore
from exaktiv_site_form.validation import validate

from tests.conftest import alembic_config
from tests.unit.site_form_fakes import (
    TEST_IP,
    VALID_FORM,
    Clock,
    FakeMailer,
    make_settings,
)

pytestmark = pytest.mark.integration


def enquiry() -> EnquiryIn:
    result = validate(VALID_FORM)
    assert isinstance(result, EnquiryIn)
    return result


async def tables(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    return {r["tablename"] for r in rows}


async def test_migration_0001_up_and_down(temp_dsn: str) -> None:
    cfg = alembic_config(temp_dsn)
    script = ScriptDirectory.from_config(cfg)
    assert script.get_revision("0001").down_revision is None
    await asyncio.to_thread(command.upgrade, cfg, "head")
    conn = await asyncpg.connect(temp_dsn)
    try:
        assert {"site_enquiries", "site_form_hits"} <= await tables(conn)
        indexes = {r["indexname"] for r in await conn.fetch("SELECT indexname FROM pg_indexes")}
        assert {
            "site_enquiries_delete_after_idx",
            "site_enquiries_mail_pending_idx",
            "site_form_hits_ip_idx",
        } <= indexes
        with pytest.raises(asyncpg.CheckViolationError):
            await conn.execute(
                "INSERT INTO site_enquiries (name,email,company,topic,message) "
                "VALUES ('Test Person','a@example.test','Example Test Ltd','bogus', repeat('x',20))"
            )
        await asyncio.to_thread(command.downgrade, cfg, "base")
        assert not ({"site_enquiries", "site_form_hits"} & await tables(conn))
    finally:
        await conn.close()


async def test_migration_applies_twice_without_error(migrated_dsn: str) -> None:
    await asyncio.to_thread(command.upgrade, alembic_config(migrated_dsn), "head")


async def test_insert_and_read_back(pg_pool: asyncpg.Pool) -> None:
    store = PgStore(pg_pool)
    enquiry_id = await store.insert_enquiry(enquiry())
    row = await pg_pool.fetchrow("SELECT * FROM site_enquiries WHERE id = $1", enquiry_id)
    assert row["email"] == VALID_FORM["email"]
    assert row["role"] == "Tester" and row["data_region"] == "eu_uk"
    assert row["team_notified_at"] is None and row["mail_attempts"] == 0


async def test_pending_mail_lifecycle(pg_pool: asyncpg.Pool) -> None:
    store = PgStore(pg_pool)
    enquiry_id = await store.insert_enquiry(enquiry())
    pending = await store.get_pending_mail(max_attempts=5)
    assert [(p.id, p.team_pending, p.reply_pending) for p in pending] == [(enquiry_id, True, True)]
    assert await store.record_mail_attempt(enquiry_id) == 1
    await store.mark_team_notified(enquiry_id)
    pending = await store.get_pending_mail(max_attempts=5)
    assert [(p.team_pending, p.reply_pending) for p in pending] == [(False, True)]
    await store.mark_autoreply_sent(enquiry_id)
    assert await store.get_pending_mail(max_attempts=5) == []


async def test_sixth_submission_in_ten_minutes_is_refused_pg(pg_pool: asyncpg.Pool) -> None:
    store = PgStore(pg_pool)
    results = [await store.check_and_record_hit("h1", 5, 600) for _ in range(6)]
    assert results == [True] * 5 + [False]
    assert await store.check_and_record_hit("h2", 5, 600) is True
    await pg_pool.execute("UPDATE site_form_hits SET hit_at = now() - interval '11 minutes'")
    assert await store.check_and_record_hit("h1", 5, 600) is True


async def test_rate_limit_is_race_safe(pg_pool: asyncpg.Pool) -> None:
    store = PgStore(pg_pool)
    results = await asyncio.gather(*(store.check_and_record_hit("h1", 5, 600) for _ in range(10)))
    assert sum(results) == 5


async def test_purge_hits(pg_pool: asyncpg.Pool) -> None:
    store = PgStore(pg_pool)
    await store.check_and_record_hit("h1", 5, 600)
    await pg_pool.execute("UPDATE site_form_hits SET hit_at = now() - interval '2 hours'")
    await store.check_and_record_hit("h1", 5, 600)
    assert await store.purge_hits(3600) == 1
    assert await pg_pool.fetchval("SELECT count(*) FROM site_form_hits") == 1


async def test_w_g4_no_raw_ip_stored_end_to_end(pg_pool: asyncpg.Pool, tmp_path: Path) -> None:
    clock = Clock()
    settings = make_settings()
    app = create_app(settings, PgStore(pg_pool), FakeMailer(), clock=clock)
    token = make_token(settings.form_token_secret.get_secret_value(), clock() - 10)
    transport = httpx.ASGITransport(app=app, client=(TEST_IP, 1))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        response = await client.post("/enquiries", json={**VALID_FORM, "form_token": token})
    assert response.status_code == 201
    dump = ""
    for table in ("site_enquiries", "site_form_hits"):
        rows = await pg_pool.fetch(f"SELECT t::text AS r FROM {table} t")  # noqa: S608
        dump += "\n".join(r["r"] for r in rows)
    assert dump
    assert TEST_IP not in dump
    assert await pg_pool.fetchval("SELECT count(*) FROM site_form_hits") == 1
