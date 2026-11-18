from tests.unit.site_form_fakes import make_settings


def test_g9_secrets_not_in_repr() -> None:
    text = repr(make_settings()) + str(make_settings())
    for secret in ("brevo-sentinel-1b2c", "iphash-sentinel-3d4e", "token-sentinel-5f6a"):
        assert secret not in text
    assert "pw-sentinel-9f3a" not in text
