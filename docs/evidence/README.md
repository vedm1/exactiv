# Claim evidence (PRD-W section 6, EXW3)

One file for each claim in `site/claims.yaml` that has written evidence. A claim becomes `ready` only when its
file is approved by the owner and (for a policy) the described step really exists. The pages show a sentence
only while its claim is `ready` (`{% if ready('...') %}`), so no page edit is needed.

| Claim | Evidence file | State (19 Nov 2026) |
|---|---|---|
| `team-experience`, `reply-time` | CVs and the inbox routine (held by the owner, not in the repository) | ready |
| `eu-cra`, `eu-data-act`, `eu-nis2`, `eu-ai-act` | [why-now-dates.md](why-now-dates.md) | ready, dates checked |
| `human-approval` | [human-approval.md](human-approval.md) | ready, approved 19 Nov 2026 |
| `access-logged` | [access-logged.md](access-logged.md) | draft, needs the real mechanism and a sample log |
| `retention` | [retention.md](retention.md) | draft, needs the real deletion step and a sample record |
| `findings-sourced` | none | off the site: the legacy analyser does not exist yet |
| `in-region`, `no-training` | none | off the site: no model endpoint per region is chosen (EXK2) |
| `nda-dpa` | none | off the site: no NDA or DPA templates yet |

Rule: no personal, employer or client name in an evidence file (W-G1).
