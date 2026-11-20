# EXL0 decision record: Legacy Analyser scope gate

This record names no person and no company (W-G1, W-G5, L-G7).

| Item | Date | Decision | By | What it means |
|---|---|---|---|---|
| Employment risk | 19 Nov 2026 | Risk accepted. The user moves forward in place of a contract check. | User | The clean room (L-G7) stays in force. No code, prompt, template, test data or method from any current or past employer of the founders. Each fixture has a `SOURCE.md`. |
| Earlier analyser code | 20 Nov 2026 | Start clean. | User | No code, prompt, template or test data from any earlier analyser build enters the repository. A reversal needs a new row here and the user's written confirmation that the work is personal work made outside employment. |
| Analyser server | 19 Nov 2026 | A new permanent EU server at up to 15 US dollars per month is acceptable. | User | Belongs to EXL3. Counts apart from the 10 dollar limit of the core regions. |
| Corpus licences | 20 Nov 2026 | Spring PetClinic and Apache OFBiz recorded (Apache-2.0, upstream `LICENSE` read). The large public code base and the C# or C++ project are not chosen. | Claude (upstream licence files read). Not yet reviewed by the user | Rows are in `LICENCES.md`, Datasets. A row for each unchosen set is recorded before first use (EXL8, EXL11). |

## Open for later phases

- L-G7 pre-commit term check (`scripts/check_clean_room.py`, term list kept outside the repository): built in EXL1 (20 Nov 2026). The user keeps the list and sets `EXAKTIV_CLEAN_ROOM_TERMS`.
- Each guardrail L-G1 to L-G15 gets its named test in the phase that builds the guarded code.
