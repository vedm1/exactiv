"""Settings for the site form service. Secrets are SecretStr and never print (G9)."""

from exaktiv_core.db import PostgresSettings
from pydantic import SecretStr


class SiteFormSettings(PostgresSettings):
    brevo_api_key: SecretStr
    ip_hash_secret: SecretStr
    form_token_secret: SecretStr

    mail_sender_email: str
    mail_sender_name: str = "Exaktiv"
    team_inbox_email: str
    site_base_url: str  # No trailing slash. Redirect targets are built from it.

    trusted_proxy_hops: int = 0
    min_fill_seconds: int = 3
    rate_limit_max: int = 5
    rate_limit_max_no_token: int = 2
    rate_limit_window_s: int = 600
    mail_max_attempts: int = 5
    max_body_bytes: int = 16384
