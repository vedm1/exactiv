from exaktiv_site_form.spam import check_token, client_ip, ip_hash, make_token

SECRET = "token-sentinel-5f6a"
NOW = 1_800_000_000.0


def test_token_valid_after_min_age() -> None:
    token = make_token(SECRET, NOW)
    assert check_token(SECRET, token, NOW + 3, min_age_s=3) == "valid"


def test_token_too_fast_is_rejected() -> None:
    token = make_token(SECRET, NOW)
    assert check_token(SECRET, token, NOW + 2, min_age_s=3) == "rejected"


def test_token_expired_is_rejected() -> None:
    token = make_token(SECRET, NOW)
    assert check_token(SECRET, token, NOW + 7201, min_age_s=3) == "rejected"


def test_token_forged_is_rejected() -> None:
    forged = make_token("other-secret", NOW)
    assert check_token(SECRET, forged, NOW + 10, min_age_s=3) == "rejected"
    assert check_token(SECRET, "garbage", NOW + 10, min_age_s=3) == "rejected"
    assert check_token(SECRET, f"{NOW}.", NOW + 10, min_age_s=3) == "rejected"


def test_token_missing() -> None:
    assert check_token(SECRET, None, NOW, min_age_s=3) == "missing"
    assert check_token(SECRET, "", NOW, min_age_s=3) == "missing"


def test_token_from_the_future_is_rejected() -> None:
    token = make_token(SECRET, NOW + 1000)
    assert check_token(SECRET, token, NOW, min_age_s=3) == "rejected"


def test_client_ip_uses_peer_without_proxy() -> None:
    assert client_ip("198.51.100.1", "203.0.113.9", hops=0) == "198.51.100.1"


def test_client_ip_takes_nth_from_right_behind_proxy() -> None:
    header = "192.0.2.50, 203.0.113.9"
    assert client_ip("10.0.0.2", header, hops=1) == "203.0.113.9"
    assert client_ip("10.0.0.2", header, hops=2) == "192.0.2.50"


def test_client_ip_falls_back_to_peer_when_header_too_short() -> None:
    assert client_ip("10.0.0.2", None, hops=1) == "10.0.0.2"
    assert client_ip("10.0.0.2", "203.0.113.9", hops=2) == "10.0.0.2"


def test_ip_hash_is_stable_keyed_and_hides_ip() -> None:
    a = ip_hash("secret-a", "203.0.113.7")
    assert a == ip_hash("secret-a", "203.0.113.7")
    assert a != ip_hash("secret-b", "203.0.113.7")
    assert a != ip_hash("secret-a", "203.0.113.8")
    assert "203.0.113.7" not in a


def test_non_ascii_token_is_rejected_not_an_error() -> None:
    assert check_token(SECRET, "123.é", NOW, min_age_s=3) == "rejected"
    assert check_token(SECRET, "١٢٣.abc", NOW, min_age_s=3) == "rejected"
