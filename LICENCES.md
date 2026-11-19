# LICENCES.md — Models and datasets (G12)

Record each model and dataset here before first use. Base models: Apache 2.0 or MIT only.

## Models

| Model | Version | Licence | Source URL | Checked on |
|-------|---------|---------|------------|------------|

## Fonts (brand package)

| Font | Version | Licence | Source URL | Used for | Checked on |
|------|---------|---------|------------|----------|------------|
| Young Serif | Fontsource 5.3.0 | SIL OFL 1.1 (`brand/fonts/OFL-young-serif.txt`) | https://fonts.google.com/specimen/Young+Serif | Wordmark, headings | 18 Nov 2026 |
| Instrument Sans | Fontsource 5.3.0 | SIL OFL 1.1 (`brand/fonts/OFL-instrument-sans.txt`) | https://fonts.google.com/specimen/Instrument+Sans | Body, UI | 18 Nov 2026 |
| Gelasio | Fontsource 5.3.0 | SIL OFL 1.1 (`brand/fonts/OFL-gelasio.txt`) | https://fonts.google.com/specimen/Gelasio | Citations | 18 Nov 2026 |

## Infrastructure software (container images)

| Component | Version | Licence | Source | Image (pinned by digest) | Use | Checked on |
|-----------|---------|---------|--------|--------------------------|-----|------------|
| MinIO (S3-compatible object storage) | RELEASE.2026-10-23 | AGPL-3.0 | https://github.com/minio/minio (the official image is no longer public; built by Chainguard) | `cgr.dev/chainguard/minio:latest@sha256:3c60a2a8c4d33409a9bc7a623a7fcbfb4605adc3d89422d2f53b3f673a6e5597` | Internal object storage. Unmodified. Bound to 127.0.0.1 on the EU server (`deploy/server/docker-compose.yml`) and to localhost in development. Not offered to any user over a network. | 19 Nov 2026 |
| Caddy (web server of the site image) | 2.11.4 | Apache-2.0 | https://github.com/caddyserver/caddy | `caddy:2-alpine@sha256:6aeddd44c3078b0f9a35206472a11420648a79c184603ef95957d0a20044cb2b` | Serves the static site behind the shared Caddy (`site/Dockerfile`). Unmodified. | 19 Nov 2026 |
| Doppler CLI | 3.76.6 | Apache-2.0 (upstream `LICENSE`, read 19 Nov 2026) | https://github.com/DopplerHQ/cli | package pinned by SHA-256 in `services/site_form/doppler-cli.sha256` | Hands secrets to the form service at start (`doppler run`). Unmodified. | 19 Nov 2026 |

AGPL-3.0 note: Exaktiv runs MinIO unmodified for its own internal use. It does not distribute MinIO and does not offer it as a network service to others. If we ever modify MinIO, or expose it to customers, record a new review here first.

## Datasets

| Dataset | Version | Licence | Source URL | Used for | Checked on |
|---------|---------|---------|------------|----------|------------|
