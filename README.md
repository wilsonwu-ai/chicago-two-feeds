# Two Feeds, One City — a Chicago guide

A bilingual (English / 简体中文) Chicago food-and-attractions guide, built from two
different social recommendation systems and stamped with which one surfaced each place.

**Live page:** see the Pages deployment for this repo.

## Why two feeds

Xiaohongshu (小红书) and TikTok recommend measurably different cities. Xiaohongshu
functions as a search engine — its Chicago results skew toward photogenic rooms,
per-person spend, Chinese food, and notes that rank on saves rather than recency.
TikTok functions as a discovery feed — its Chicago results skew toward single viral
dishes, the oversized/cheese-pull format, and skyline-shot trends, with faster churn.

Neither is wrong. They are answering different questions. This guide keeps the
provenance visible so you can weight the recommendation yourself.

## How it was built

- Parallel research sweeps across seven TikTok angles and the earlier Xiaohongshu pass.
- Every candidate place run through an adversarial verification step against live
  sources: is it open, what is it actually rated now, does the hype hold up.
  Places that failed verification were dropped rather than quietly kept.
- Both language versions are written, not machine-translated.

## Design

Colour and structure derive from the Chicago flag and the city's material palette —
Indiana limestone, Mies steel-black, the flag's light-blue bars and six-pointed stars.
Square corners throughout, referencing the steel frame. Each entry carries its real
Chicago address-grid coordinate (the city's grid runs from State & Madison at 0/0).

Type is Inter (variable, `wght` 100–900 / `opsz` 14–32) and DejaVu Sans Mono, both
subsetted to a Latin set and inlined as woff2 data URIs so the page has zero external
requests. Chinese renders through a system font stack.

## Build

```bash
python3 build.py     # inlines fonts into build/index.html
```

`build/index.html` is fully self-contained — no external requests, no CDN, no tracking.
