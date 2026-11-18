"""Contact form tables (EXW1): site_enquiries and site_form_hits.

Revision ID: 0001
Revises:
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE site_enquiries (
          id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
          created_at        timestamptz NOT NULL DEFAULT now(),
          name              text        NOT NULL CHECK (char_length(name)    BETWEEN 2 AND 100),
          email             text        NOT NULL CHECK (char_length(email)   BETWEEN 3 AND 254),
          company           text        NOT NULL CHECK (char_length(company) BETWEEN 2 AND 150),
          role              text        NULL     CHECK (char_length(role) <= 100),
          topic             text        NOT NULL CHECK (topic IN ('legacy_modernisation',
                              'ai_product_delivery', 'product_data_early_access',
                              'partnership', 'other')),
          data_region       text        NULL     CHECK (data_region IN ('eu_uk', 'india', 'other')),
          message           text        NOT NULL CHECK (char_length(message) BETWEEN 20 AND 2000),
          delete_after      timestamptz NOT NULL DEFAULT (now() + interval '6 months'),
          team_notified_at  timestamptz NULL,
          autoreply_sent_at timestamptz NULL,
          mail_attempts     int         NOT NULL DEFAULT 0
        )
        """
    )
    op.execute("CREATE INDEX site_enquiries_delete_after_idx ON site_enquiries (delete_after)")
    op.execute(
        "CREATE INDEX site_enquiries_mail_pending_idx ON site_enquiries (created_at) "
        "WHERE team_notified_at IS NULL OR autoreply_sent_at IS NULL"
    )
    op.execute(
        """
        CREATE TABLE site_form_hits (
          id      bigserial   PRIMARY KEY,
          ip_hash text        NOT NULL,
          hit_at  timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX site_form_hits_ip_idx ON site_form_hits (ip_hash, hit_at)")


def downgrade() -> None:
    op.execute("DROP TABLE site_form_hits")
    op.execute("DROP TABLE site_enquiries")
