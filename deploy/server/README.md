# Exaktiv server deploy (EXK0b)

Host: Hetzner Nuremberg (`eu-central nbg1`), shared with other projects. Exaktiv changes only its own files.
Postgres is on Neon (Frankfurt). DBOS (workflows) keeps its tables there, in schema `dbos`, and connects to the Neon direct host (not the pooled host). This stack is MinIO only.

## How a deploy works

1. A push to `main` passes the five CI jobs in CircleCI (`.circleci/config.yml`).
2. The `deploy-infra` job (context `exaktiv_deploy`) runs `ssh exaktiv-deploy@$APPS_HOST <40-char sha>`.
3. The key is forced to `/opt/stack/bin/deploy-infra`. It deploys only a SHA that is in the history of `main` and is not
   older than the live one.
4. `deploy-infra` reads `deploy/server/docker-compose.yml` of that SHA. Secrets come from Doppler (`prd` config). Only
   `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` are kept, into a temporary env file. Other Doppler keys never reach Docker.
5. `/opt/stack/bin/exaktiv-policy.py` checks the file text, then the INTERPOLATED config (same project name `-p exaktiv`,
   all profiles, same env file as the run). It is an allowlist: images from `cgr.dev/chainguard/` pinned by digest, numeric
   non-root user, ports on 127.0.0.1 only, plain named volumes `exaktiv_*`, the default network only, healthcheck, memory
   limit above 0 and up to 1 GiB, at most 4 services, no other keys. On a violation nothing is pulled or started.
6. `pull` runs first, while the live files are in place. Then the files switch and `up -d --wait` runs.
7. A failed health check puts the previous compose file and env file back.

Nothing from the repository runs on the server. `deploy-infra` and the policy are installed by root from a reviewed commit.

## One-time setup

1. On the server, as root, from a reviewed checkout: `deploy/server/setup.sh --dry-run ~/circleci-exaktiv.pub`, then without `--dry-run`.
   The script writes `/etc/exaktiv/deploy.conf` (root-owned) and installs the two scripts (root-owned).
2. GitHub: add the printed public key as a read-only deploy key of the repository.
3. Doppler: project `exaktiv`, configs `ci` (APPS_HOST) and `prd` (MINIO_ACCESS_KEY, MINIO_SECRET_KEY, `DATABASE_URL` from Neon, the pooled host with `-pooler` in its name, `sslmode=require`).
   Put the `prd` service token on the server (command printed by `setup.sh`).
4. CircleCI: context `exaktiv_deploy` with `DOPPLER_TOKEN` (the `ci` service token). Project Settings, SSH Keys, add the private
   key `circleci-exaktiv` for the server address. The fingerprint must equal the one in `.circleci/config.yml`.
   **Restrict the context to the main branch** (Organization Settings, Contexts, `exaktiv_deploy`, Security: expression
   `pipeline.git.branch == "main"`) and keep "Pass secrets to builds from forked pull requests" OFF. A branch can edit
   `.circleci/config.yml`, so only the context can stop it. Protect `main` in GitHub (pull request and CI required).
5. `deploy/known_hosts` holds the server's public SSH host key. If the host key changes, update it in a reviewed commit.

## Update the scripts

Change `deploy-infra` or `policy.py` in a pull request, then re-run `setup.sh` on the server from the merged commit.

## Rollback

Automatic on a failed health check. By hand: re-run the deploy job for an older commit (the SHA must be in `main`).

## Neon restore test

**Skipped by the owner, 19 Nov 2026 (risk accepted).** The steps below stay valid if the test is done later.

**Moved to EXW3, before the site goes public (decision 19 Nov 2026).** Do it before `SITE_MODE=live`, because the first real enquiries cannot be recreated.
Steps (Neon console, project of the `exaktiv` database, Frankfurt). Read only `id` and `created_at`, never the message (G11):

1. In the production database run `SELECT id, created_at FROM site_enquiries ORDER BY created_at DESC LIMIT 1;` (use a test enquiry). Write down the `id` and the time.
2. Neon console, Branches, **Create branch**. Parent: `main` (production). Choose **Past data** and set a time a few minutes AFTER the `created_at` of that row and before now (the time must be inside the plan's restore window). Name it `restore-test-<date>`. Create.
3. Open the branch, **Connect**, copy the connection string (direct, not pooled). Run `psql "<string>" -c "SELECT id, created_at FROM site_enquiries WHERE id = '<id from step 1>';"`. Pass: one row, the same `id` and `created_at`.
4. Delete the branch (Branches, the branch, Delete). Check that only `main` is left, so no compute keeps running and costing money.
5. Fill the table below (date, `PASS` or `FAIL` and the branch time you used), then set `neon-restore-test` in `docs/launch/EXW3-record.yaml` to `done` with the date.

If step 3 returns no row: the time was before the row existed, or outside the restore window. Delete the branch and try again with a later time. Neon bills branch compute while it runs. The cost of a few minutes is small. Tell the owner of the 10 dollar limit if the plan shows more.

| Date | Result |
|------|--------|
| (not done yet) | |

## Cost record

| Item | Monthly cost | Note |
|------|--------------|------|
| Hetzner server (shared with other projects) | share not counted | Marginal cost for Exaktiv is zero. |
| Neon plan | 10 dollars per month (stated by the user, 19 Nov 2026; plan name not given) | Counts against the 10 dollar limit. With the server share at zero, Neon alone uses the whole 10 dollars of the EU region. |
