# Exaktiv site deploy (EXW2)

The site (`exaktiv.com`) is two containers on the shared Hetzner host (Nuremberg), project `exaktiv-site`:

| Service | Image | What it does |
|---|---|---|
| `web` | `ghcr.io/vedm1/exaktiv/web:<sha>` | Caddy. Serves the static site, security headers, staging password and noindex, masked access log, routes `/enquiries` and `/form-token` to the form. Alias `exaktiv-web`, port 8080 on the network `edge`. |
| `form` | `ghcr.io/vedm1/exaktiv/site-form:<sha>` | The EXW1 form service (uvicorn, `--no-access-log`). Alias `exaktiv-form`, port 8000. Secrets from Doppler `site_prd` through `doppler run`. |
| `migrate` | same as `form` | Profile `migrate`. `bin/deploy` runs it after `pull` and before `up`. |
| `jobs` | same as `form` | Profile `jobs`. The systemd timers run `retention` (daily), `retry-mail` (every minute) and `purge-hits` (hourly). |

The MinIO stack is another project (`deploy/server`, `deploy-infra`, user `exaktiv-deploy`). Nothing here touches it.

## How a deploy works

1. A push to `main` passes the five CI jobs. `build-images` builds the staging build of the site and both images, runs the image
   tests, and pushes `:<commit sha>` to ghcr.io (it needs `GHCR_PUSH_TOKEN` in Doppler `ci`; without it the job stops with a message).
2. `deploy-app` runs `ssh deploy@$APPS_HOST <40-char sha>`. The key is forced to `/opt/stack/bin/deploy exaktiv-site`.
3. `bin/deploy` (shared, root-owned, owned by the unveilio repository) fetches the commit (it must be in the history of `main`),
   writes `deploy/site/docker-compose.yml` of that commit, checks it against its policy, pulls the images, checks that each image
   label `org.opencontainers.image.revision` equals the SHA, runs `migrate`, then `up -d --wait`. A failed `migrate` restarts nothing.
4. The shared Caddy proxies `exaktiv.com` to `exaktiv-web:8080` (`deploy/site/caddy/exaktiv-site.caddy`).

## One-time host steps (you run them; each one changes the shared host)

Do them in this order. Nothing here changes Caddy, `bin/deploy` or another project's files.

1. **Deploy key for CircleCI.** On your machine:
   `ssh-keygen -t ed25519 -N '' -C circleci-exaktiv-app -f ~/vultr-keys/circleci-exaktiv-app`, then
   `ssh-keygen -lf ~/vultr-keys/circleci-exaktiv-app.pub` for the fingerprint.
2. **Forced command.** As root on the host, add one line to `/home/deploy/.ssh/authorized_keys`:
   `command="/opt/stack/bin/deploy exaktiv-site",no-pty,no-port-forwarding,no-agent-forwarding,no-X11-forwarding <contents of circleci-exaktiv-app.pub>`
3. **Project folder and read-only repository key.**
   `install -d -o deploy -g deploy /opt/stack/exaktiv-site`, then
   `/opt/stack/bin/init-deploy-source exaktiv-site git@github.com:vedm1/exactiv.git deploy/site ghcr.io/vedm1/exaktiv/`.
   Add the printed public key in GitHub (repository, Settings, Deploy keys, write access OFF). Then
   `/opt/stack/bin/init-deploy-source exaktiv-site --check`.
4. **Doppler.** Project `exaktiv`, new config `site_prd` with: `DATABASE_URL` (Neon, pooled host, `sslmode=require`), `BREVO_API_KEY`,
   `IP_HASH_SECRET`, `FORM_TOKEN_SECRET` (random, at least 32 bytes each), `MAIL_SENDER_EMAIL`, `MAIL_SENDER_NAME`, `TEAM_INBOX_EMAIL`,
   `SITE_BASE_URL=https://exaktiv.com`, `TRUSTED_PROXY_HOPS=1`. Create a service token for `site_prd` only.
   In config `ci` add `GHCR_PUSH_TOKEN` and `GHCR_USER`: the **same two values the unveilio CI already uses** (its Doppler `ci` config,
   pushes to `ghcr.io/vedm1/unveilio/*`). Decision 19 Nov 2026 (user): same pattern, no machine user. **Known risk, accepted**: this
   token can write every `vedm1` package, and `load-doppler` exports every `ci` secret to every step of `build-images`. A bad step could
   overwrite `ghcr.io/vedm1/unveilio/*` tags. The revision label check cannot stop that (whoever can push can set a label). A machine user
   limited to `exaktiv/web` and `exaktiv/site-form` would close it; do that if the account ever holds more than your own projects.
5. **Server `.env`** (mode 600, owner `deploy`) at `/opt/stack/exaktiv-site/.env`, single-quoted values:
   `DOPPLER_TOKEN='<site_prd service token>'`, `SITE_MODE='staging'`, `STAGING_BASIC_AUTH_HASH='<bcrypt>'`. Make the hash with
   `docker run --rm caddy:2-alpine caddy hash-password` (it asks for the password; keep the password in your password manager).
   A `$` in the hash reaches Caddy unchanged (probed 19 Nov 2026 with Docker Compose: `config` shows `$$`, the container gets `$`).
6. **GHCR pull token.** The `deploy` user's docker config already holds a read-only GHCR token for the unveilio images. Check that it can
   pull `ghcr.io/vedm1/exaktiv/web` after the first push (`sudo -u deploy docker pull ghcr.io/vedm1/exaktiv/web:<sha>`). If not, add a token.
7. **CircleCI.** Project Settings, SSH Keys, add the private key `circleci-exaktiv-app` for the host address. Put its fingerprint into
   `.circleci/config.yml` job `deploy-app` (done 19 Nov 2026: `SHA256:WfZbao8U9HSoOjcTZcN7d/I0y53qIgb+7dN9Xsqz6Vk`; CircleCI must show the same one).
   Without the private key in CircleCI the job fails at `add_ssh_keys`. The context `exaktiv_deploy` stays restricted to `main`.
8. **First deploy.** Merge to `main`. (19 Nov 2026: the very first push of `web` created the private package but the tag write was
   refused with `denied`; "Rerun from failed" then passed and created both packages. Expect this once for a new package name.) Check `docker ps` (containers `exaktiv-site-web-1` and `exaktiv-site-form-1` healthy; the other projects unchanged).
9. **DNS** (at your DNS host) for `exaktiv.com`:

   | Record | Value |
   |---|---|
   | `A exaktiv.com` | `188.245.25.106` (add `AAAA` only if the host has a public IPv6) |
   | `CNAME www` | `exaktiv.com` |
   | `CAA` (optional) | `0 issue "letsencrypt.org"` |
   | `TXT exaktiv.com` (SPF) | one record only: `v=spf1 include:_spf.google.com include:spf.brevo.com ~all` |
   | DKIM | the records the Brevo "authenticate domain" page shows |
   | `TXT _dmarc` | `v=DMARC1; p=none; adkim=s; aspf=s; rua=mailto:<dmarc mailbox>`; move to `p=quarantine` after two clean weeks and before EXW3 |
   | `MX exaktiv.com` | Google Workspace: priority 1, `smtp.google.com` (use the value the Google setup page shows) |
   | `TXT exaktiv.com` (Google verification) | `google-site-verification=...` from the Google setup page. A second TXT record next to the SPF record is fine |
   | Google DKIM | `TXT google._domainkey` with the key from Admin console, Apps, Google Workspace, Gmail, Authenticate email |
   | Brevo domain code | `TXT brevo-code:...` or the record the Brevo page shows |
   | mailboxes | `hello@` (enquiries and contact), `security@` (security.txt), `dmarc@` (DMARC reports; an alias is enough) |

   Confirm the SPF include and the DKIM selector in Brevo (they are not copied from memory). Then
   `python3 scripts/check_dns.py` (add `--dkim-selector <selector>` if Brevo uses another one).
10. **Shared Caddy block.** After DNS points at the host and the first deploy is healthy, append the contents of
    `deploy/site/caddy/exaktiv-site.caddy` to `/opt/stack/caddy/Caddyfile` and run
    `docker compose -f /opt/stack/caddy/docker-compose.yml exec caddy caddy reload --config /etc/caddy/Caddyfile`.
11. **Jobs: the scheduler container (EXW3, replaces the systemd timers).** The `scheduler` service of the compose file starts with
    `up` and runs `retry-mail` (every minute), `purge-hits` (hourly) and `retention` (daily, and once at each start). It stays up, so
    Alloy captures its log. **One time, as root, after the first deploy that contains the scheduler:** stop the old timers so no job runs twice:
    `systemctl disable --now exaktiv-site-retention.timer exaktiv-site-retry-mail.timer exaktiv-site-purge-hits.timer`, then
    `rm /etc/systemd/system/exaktiv-site-*.{service,timer}` and `systemctl daemon-reload`. Check: `docker logs exaktiv-site-scheduler-1 2>&1 | grep job_done`
    shows `retry-mail`, `purge-hits` and `retention` lines.
12. **Alert (mail path).** Alloy turns each compose project into its own Loki tenant (`project` label = tenant), so Grafana needs a data source
    for the tenant `exaktiv-site`: add to `/opt/stack/observability/datasources.yml` an entry `Loki exaktiv-site` (type `loki`, url
    `http://observability-loki-1:3100`, header `X-Scope-OrgID: exaktiv-site`), then restart `observability-grafana-1`. Rule: Loki query
    `sum(count_over_time({project="exaktiv-site", service="form"} |= "mail_attempt_failed" [15m]) )` above 0. It catches a broken Brevo path at the
    first failure (the 401 of 19 Nov 2026 showed as this event). **Built 19 Nov 2026** (user, in the shared Grafana): data source `Exaktiv site logs`,
    rule "Exaktiv site: mail send failed", every 1m, contact point Exaktiv Discord. Set "Alert state if no data" to Normal (the form logs only when
    something happens, so most windows have no data).
    **Job alerts (EXW3, W-G4).** Alloy did not capture the short-lived `jobs` containers (tested 19 Nov 2026), so the jobs now run in the long-lived
    `scheduler` container (step 11). Two more Grafana rules on the data source `Exaktiv site logs`:
    (1) retention freshness: `absent_over_time({project="exaktiv-site", service="scheduler"} |= "job_done" |= "retention" [26h])`, fire when it returns
    a value; (2) a failing job or a mail that failed five times: `sum(count_over_time({project="exaktiv-site", service="scheduler"} |~ "job_failed|enquiry_mail_failed" [15m]))` above 0.
    Set "Alert state if no data" to Alerting for rule 1 and to Normal for rule 2. Check rule 1 once by stopping the scheduler for a short test window
    with a 5 minute range, then restore the 26 hour range. Record the date in `docs/launch/EXW3-record.yaml` (`retention-alert`).
12b. **Brevo authorised IP.** Brevo refuses API calls from an unknown address (`401`, message "unrecognised IP address"). In Brevo open
    SMTP & API, Security, Authorised IPs and add the host address `188.245.25.106`. Found 19 Nov 2026 on the first test enquiry: the log showed
    `mail_attempt_failed` with `status: 401`. Test the key from the host: `docker exec exaktiv-site-form-1 doppler run --no-fallback -- python -c
    "import os,httpx;r=httpx.get('https://api.brevo.com/v3/account',headers={'api-key':os.environ['BREVO_API_KEY']});print(r.status_code)"`
    must print `200`. If the host IP changes, add the new one.
12c. **Brevo tracking (accepted, anonymous; the privacy notice says so since EXW3).** Brevo adds an open-tracking pixel and a tracked unsubscribe link to transactional mail, and has no
    per-message switch to remove them (checked 19 Nov 2026). Set Brevo, Settings, Transactional emails, Tracking, "Anonymous email tracking" to **Yes**:
    opens and clicks are then not linked to a contact. Decision of the user, 19 Nov 2026. The privacy notice must say so before EXW3. Verified on a
    test mail: DKIM `PASS` (`d=exaktiv.com`, selector `brevo1`), SPF `PASS` (`mail.exaktiv.com`), DMARC `PASS` (`p=none`).
13. **Smoke test.** `STAGING_PASSWORD='...' python3 scripts/smoke_staging.py`. Then send one real test enquiry through
    `POST /enquiries` and check the team mail, the automatic reply and the SPF, DKIM and DMARC results in the received headers.

## Staging password and launch

Staging is `SITE_MODE=staging` in `/opt/stack/exaktiv-site/.env`: one password for the whole site, `X-Robots-Tag: noindex, nofollow`.
To change the password, put a new bcrypt hash in `.env` and re-run the deploy job (or `docker compose ... up -d` as `deploy`).
EXW3 builds a launch image, sets `SITE_MODE='live'` and deploys. See "Go live (EXW3)" below.

## Go live (EXW3)

Do these in order. Every step is reversible until step 5.

1. **Launch record.** Every item in `docs/launch/EXW3-record.yaml` is `done` or `accepted`, except `go-live-approval`.
   Check: `uv run python scripts/check_launch_record.py` (it lists what is open).
2. **DMARC.** Change the TXT record `_dmarc.exaktiv.com` from `p=none` to `p=quarantine` (keep your `rua=` address and the other tags).
   After the change: `python3 scripts/check_dns.py --launch` passes.
3. **Name list in Doppler.** Doppler project `exaktiv`, config `ci`: add `SITE_NAMES_B64` = base64 of your name list (one name per line; no person,
   employer or client name goes into the repository). Make it with `base64 < names.txt | tr -d '\n'`. Run the gate on your machine first:
   `uv run python scripts/build_site.py --launch --names names.txt --out /tmp/launch-check` must pass.
4. **Launch flag.** Add the file `site/launch.flag` (any text, for example one line "go live") in a commit on `main` (the go-live commit). CI `build-images` then builds the
   launch site, and fails if `SITE_NAMES_B64` is missing or the record is not complete. `deploy-app` deploys it. At this point the site is still
   behind the staging password (`SITE_MODE=staging`), so check the launch build there: indexable pages, no `noindex` meta (the password wall still adds the header).
5. **Go live (needs the owner's yes).** On the host edit `/opt/stack/exaktiv-site/.env`: `SITE_MODE='live'` (remove nothing else), then re-run the deploy job.
   Check by hand: `https://exaktiv.com/` answers `200` without a password, the response has no `X-Robots-Tag`, `robots.txt` allows all, the sitemap
   lists the 10 pages, the contact form sends one test enquiry (team mail and automatic reply arrive), and `scripts/smoke_staging.py` now fails on
   its password checks (expected: the password wall is gone).
6. **Rollback.** Set `SITE_MODE='staging'` again and re-run the deploy job. To also return to the staging build, delete `site/launch.flag` in a commit.

## Team mailbox: 6-month deletion of enquiries

The team mailbox keeps a copy of each enquiry (subject `New website enquiry: <topic>`). The privacy notice promises 6 months. Google Workspace
needs Vault for this (Business Standard or Plus). Admin console, Vault, Retention, Create rule: Service Gmail, scope: the `hello@` mailbox
(or its organisational unit), custom rule with the search term `subject:"New website enquiry"`, retention period 180 days, then delete. Replies
that the team wrote to a visitor are not matched: add their label or term, or delete them by hand when a case closes. If the plan has no Vault,
say so in the record and decide: upgrade, or add a monthly manual deletion to the inbox routine. Record the date in the launch record (`mailbox-retention-rule`).

## Logs and privacy

- `form`: no access log; the EXW1 masking filter stays (G11). `web`: JSON access log on stdout with the address cut to /24 (IPv4) or /48 (IPv6),
  no `Authorization`, `Cookie`, `X-Forwarded-For` or query string. The shared Caddy writes no access log for this site.
- Alloy ships stdout to Loki. Loki keeps 336 h (14 days), checked 19 Nov 2026 in `/opt/stack/observability/loki.yml`.
- **Open (found by the independent review)**: "no `log` directive" removes the shared Caddy's access log only. Its error log still
  holds the full `remote_ip`, `client_ip`, the URI with the query string and all request headers (including the full `X-Forwarded-For`)
  on every 502 or 503 (for example while `exaktiv-web` is down or recreating, which includes each deploy) and on TLS handshake errors.
  Loki keeps it 14 days. PRD-W §8.2 ("truncated addresses only") is **not met for these lines**. Before EXW3: ask the host owner for an
  error-log filter on the shared Caddy, or accept it and word the privacy notice. Do not claim §8.2 as met without one of the two.
- **Accepted**: any container on `edge` can reach `exaktiv-form:8000` directly and could set `X-Forwarded-For` to dodge the per-IP limit.
  Only our own projects share `edge`.
- **For the host owner (unveilio repository)**: the shared `bin/deploy` policy does not limit network aliases, `labels`, `dns`,
  `extra_hosts` or `hostname`. A compose file on `main` could claim the alias `caddy` and intercept other projects' traffic on `edge`.
  Here only `test_site_compose_services_are_hardened` (exact alias list) guards it. An alias allowlist in `bin/deploy` would close it.
- **Cost note**: `retry-mail` runs every minute, so it reaches Doppler and Neon around the clock and keeps Neon from sleeping.

## Rollback

Automatic on a failed health check (`bin/deploy` brings the previous commit back). By hand: re-run the `deploy-app` job for an older commit.
The database is never rolled back (expand-then-contract revisions only; see the EXW2 spec).

## Cost record (EU, limit 10 dollars per month)

| Item | Monthly cost | Note |
|---|---|---|
| Hetzner server (shared) | share not counted | Marginal cost zero. About 0.6 GB RAM more of the 4.9 GB free. |
| Neon plan | 10 dollars | The whole limit (stated 19 Nov 2026). |
| Google Workspace (D6, chosen 19 Nov 2026) | about 6 to 7 dollars per user (price to confirm on the invoice) | **Overrun accepted by the user, 19 Nov 2026.** Data region Europe, confirmed by the user. |
| Domain `exaktiv.com` | about 1 dollar | Overrun accepted by the user on 19 Nov 2026. Confirm the price at the registrar. |
| Brevo | 0 (free plan) | Must stay on the free plan (300 mails per day). Confirm on the account. |
| ghcr.io private packages | 0 | Within the free allowance. |

Total for the EU region: about 17 to 18 dollars per month against the 10 dollar limit (Neon 10, Workspace 6 to 7, domain 1). The server share stays at zero. The user accepted the overrun on 19 Nov 2026.

## Brevo: monthly deletion of old mail content

Brevo deletes the content of transactional mail only when asked (owner, 19 Nov 2026). The privacy notice promises a monthly request for mail older
than 6 months. Routine: on the first working day of each month, ask Brevo (support request, or the deletion option in the account if it has one)
to delete the content of transactional mail older than 6 months, and write the date in the inbox routine log. No mail is older than 6 months before May 2027, so the first request
is due then (owner, 19 Nov 2026). Set a reminder.
