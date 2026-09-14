# Mass disclosure campaign: `image-size` dependents → `image-size-next`

Contact **npm packages** that depend on abandoned/vulnerable `image-size` (~2,370), not the ~961k application repositories.

## Scope

| In | Out |
|----|-----|
| ~2.37k npm dependent packages | ~961k dependent repos |
| One GitHub Discussion (or Issue) per package repo | Spam PRs to every repo |
| Maintainer @mention + X queue when found | Cold mass email dumps |
| English only | Other languages for public posts |

## Layout

```
campaign/
  templates/          # frozen English message kit
  scripts/            # Phase A–E tooling
  data/               # generated (gitignored)
    dependents.raw.jsonl
    targets.jsonl
    batches/batch-NNN.json
    x_queue.jsonl
    ledger.jsonl
```

## Snapshot (after Phase A+B)

| Metric | Value |
|--------|------:|
| npm Dependents tab | **2874** (includes unpublished / noise; not all are live packages) |
| ecosyste.ms inventory (2026-09-14) | **2065** |
| Batches of 20 | **104** |
| GitHub repos | 1572 |
| **Contactable** (Discussion / Issue / existing thread) | **~1015** |
| Pending Discussions | ~117 |
| Pending Issues | ~873 |
| Comment on existing thread | ~25 |
| Skipped (no surface / T3 / non-GH) | ~734 |
| Failed (404 / dead repo URL) | ~323 |
| With X handles (profile) | ~253 |
| T0 / T1 / T2 / T3 | 13 / 81 / 1856 / 122 |

Data lives under `campaign/data/` (gitignored). Re-run metrics anytime:

```bash
python3 campaign/scripts/metrics.py
```

## Phases

### Phase A — Inventory

```bash
python3 campaign/scripts/fetch_dependents.py
```

Fetches all dependents from ecosyste.ms, sorts by downloads, writes batches of 20.

### Phase B — Enrichment (read-only)

```bash
# single batch
python3 campaign/scripts/enrich_batch.py --batch 0

# parallel wave (up to 20 workers)
python3 campaign/scripts/run_enrich_wave.py --from 0 --to 19 --workers 20
```

Probes GitHub for Discussions/Issues, maintainers, `twitter_username`. Writes/updates `data/targets.jsonl` (file-locked, parallel-safe).

### Phase C — Templates

Edit `templates/*.md` and set `x_announce_url` in `templates/config.json` once the X thread is live.

### Phase D — Outreach (**writes to GitHub — requires explicit approval**)

```bash
# dry-run (default)
python3 campaign/scripts/open_discussion.py --batch 0

# actually create Discussion/Issue (T0/T1 only, after classify_major)
python3 campaign/scripts/open_discussion.py --batch 0 --execute
```

Does **not** write until you pass `--execute`. Uses `gh` as the logged-in account (`lcf2212dev`).

Do **not** loop batches 0–19 with `--execute`. Human-paced T0/T1 only (daily cap in `templates/config.json`).

### Phase E — Metrics

```bash
python3 campaign/scripts/metrics.py
```

## Worker model

- **20 packages** per batch file (`batch-000.json` … `batch-103.json`).
- Run **up to 20 workers** in parallel for enrichment.
- Outreach: T0/T1 only, after `classify_major.py`. Sequential `--execute`, daily cap 5. Hub discussion: https://github.com/lcf2212dev/image-size-next/discussions/3

## Safety

- One public thread per repo (Discussion **or** Issue).
- Ledger in `data/ledger.jsonl` prevents double-post.
- **Major gate:** skip if `resolved_major` is not `1` or `2`. Never suggest `2.1.1` to a 1.x / Metro tree.
- Default outreach is **dry-run**. `--execute` is sequential, ≥300s between writes, daily cap 5.
- `run_outreach_wave.py` defaults to dry-run and `workers=1`; refuses `--execute` with `workers>1`.
- No exploit PoCs; not affiliated with original maintainer.
- `campaign/` is not included in npm `files` — never published.

## Dual line

| Upstream | Fork | Dist-tag |
| --- | --- | --- |
| `image-size@1.2.1` (Metro `^1.0.2`) | `image-size-next@1.2.2` | `legacy` |
| `image-size@2.0.2` | `image-size-next@2.1.1` | `latest` |

Classify before any write:

```bash
python3 campaign/scripts/classify_major.py --tiers T0,T1
```
