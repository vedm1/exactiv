"""Check the DNS records of the site domain (EXW2). Run by hand after the DNS change; it needs `dig`.

Usage: python3 scripts/check_dns.py [--domain exaktiv.com] [--ip 188.245.25.106] [--dkim-selector brevo1] [--launch]
Exit 0 when every check passes. The DKIM selector and record type are the ones Brevo shows on its "authenticate
domain" page; confirm them there (they are not in this repository on purpose).
"""

import argparse
import subprocess
import sys
from collections.abc import Callable

Dig = Callable[[str, str], list[str]]
Result = tuple[str, bool, str]


def real_dig(rtype: str, name: str) -> list[str]:
    out = subprocess.run(  # noqa: S603
        ["dig", "+short", "+time=5", "+tries=2", rtype, name],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def _txt(values: list[str]) -> list[str]:
    """dig prints a TXT record as one or more quoted chunks. Join the chunks, drop the quotes."""
    return ["".join(part for part in v.replace('" "', "").split('"') if part) for v in values]


def check(
    domain: str, ip: str, dig: Dig, dkim_selector: str = "brevo1", *, launch: bool = False
) -> list[Result]:
    out: list[Result] = []
    a = dig("A", domain)
    out.append(("A record", ip in a, f"{domain} -> {', '.join(a) or 'nothing'} (want {ip})"))
    www = [v.rstrip(".") for v in dig("CNAME", f"www.{domain}")]
    out.append(("www CNAME", domain in www, f"www.{domain} -> {', '.join(www) or 'nothing'}"))
    spf = [t for t in _txt(dig("TXT", domain)) if t.lower().startswith("v=spf1")]
    spf_ok = len(spf) == 1 and "include:spf.brevo.com" in spf[0]
    out.append(
        ("SPF", spf_ok, f"{len(spf)} SPF record(s); want exactly one with include:spf.brevo.com")
    )
    dkim = dig("CNAME", f"{dkim_selector}._domainkey.{domain}") or dig(
        "TXT", f"{dkim_selector}._domainkey.{domain}"
    )
    out.append(
        (
            "DKIM",
            bool(dkim),
            f"{dkim_selector}._domainkey.{domain}: {'found' if dkim else 'missing'}",
        )
    )
    dmarc = [t for t in _txt(dig("TXT", f"_dmarc.{domain}")) if t.startswith("v=DMARC1")]
    policy = (
        next(
            (
                p.split("=", 1)[1]
                for p in dmarc[0].replace(" ", "").split(";")
                if p.startswith("p=")
            ),
            "",
        )
        if dmarc
        else ""
    )
    out.append(
        (
            "DMARC",
            policy in {"quarantine", "reject"} if launch else bool(policy),
            f"policy p={policy or 'missing'}"
            + (
                " (launch needs quarantine or reject)"
                if launch
                else " (use --launch before EXW3 go-live)"
            ),
        )
    )
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="exaktiv.com")
    parser.add_argument("--ip", default="188.245.25.106")
    parser.add_argument("--dkim-selector", default="brevo1")
    parser.add_argument(
        "--launch", action="store_true", help="DMARC must be quarantine or reject (EXW3)"
    )
    args = parser.parse_args(argv)
    results = check(args.domain, args.ip, real_dig, args.dkim_selector, launch=args.launch)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
