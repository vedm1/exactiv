"""W-G4: form submissions are stored in the EU only and deleted after 6 months."""

import asyncpg  # type: ignore[import-untyped]
import pytest
from exaktiv_site_form.jobs import run_job
from exaktiv_site_form.models import EnquiryIn
from exaktiv_site_form.store import PgStore
from exaktiv_site_form.validation import validate

from tests.unit.site_form_fakes import VALID_FORM, FakeMailer, make_settings

pytestmark = pytest.mark.integration


def enquiry() -> EnquiryIn:
    result = validate(VALID_FORM)
    assert isinstance(result, EnquiryIn)
    return result


async def test_w_g4_row_past_delete_after_is_deleted(pg_pool: asyncpg.Pool) -> None:
    store = PgStore(pg_pool)
    old = await store.insert_enquiry(enquiry())
    await pg_pool.execute(
        "UPDATE site_enquiries SET delete_after = now() - interval '1 day' WHERE id = $1", old
    )
    count = await run_job("retention", store, FakeMailer(), make_settings())
    assert count == 1
    assert await pg_pool.fetchval("SELECT count(*) FROM site_enquiries") == 0


async def test_w_g4_row_before_delete_after_is_kept(pg_pool: asyncpg.Pool) -> None:
    store = PgStore(pg_pool)
    await store.insert_enquiry(enquiry())
    assert await run_job("retention", store, FakeMailer(), make_settings()) == 0
    assert await pg_pool.fetchval("SELECT count(*) FROM site_enquiries") == 1


async def test_w_g4_delete_after_defaults_to_six_months(pg_pool: asyncpg.Pool) -> None:
    await PgStore(pg_pool).insert_enquiry(enquiry())
    days = await pg_pool.fetchval(
        "SELECT extract(day FROM delete_after - created_at) FROM site_enquiries"
    )
    assert 181 <= days <= 184


async def test_w_g4_extended_row_survives_retention(pg_pool: asyncpg.Pool) -> None:
    """Staff move delete_after by hand when an enquiry leads to a contract."""
    store = PgStore(pg_pool)
    keep = await store.insert_enquiry(enquiry())
    await pg_pool.execute(
        "UPDATE site_enquiries SET delete_after = now() + interval '3 years' WHERE id = $1", keep
    )
    assert await run_job("retention", store, FakeMailer(), make_settings()) == 0
