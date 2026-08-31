# Data architecture

The pipeline organises data in three layers, from raw to analysis-ready,
using a different storage paradigm for each layer's data shape: plain
files for the source, a NoSQL document store for the irregular
frame-level staging data, and a relational database for the clean,
tabular warehouse.

## Source
Raw data as collected from external sources, before any processing.
Plain CSV files, one row per film — regular, tabular, small.

- `data/source/campione_film.csv` — films sampled from IMDb (metadata,
  genre, votes), before trailer links are attached.
- `data/source/film_with_trailers.csv` — same films plus the YouTube
  trailer link from TMDB. 399 films sampled, 133 successfully
  downloaded (see `DATA_QUALITY.md` for why).
- `data/source/auteur_films.csv` — the 9 hand-picked auteur films, with
  TMDB id, title, year, trailer link.

This layer is never overwritten in place; every later step can be
traced back to it.

## Staging — MongoDB
Intermediate, semi-processed data: the colour metrics of every frame
(one second) of every trailer. This is the natural NoSQL layer,
because the data is **frame-level and variable-length** — a 120-second
trailer and a 169-second trailer produce different numbers of
documents, and forcing them into a fixed-column table would either
waste space (padding) or lose information (truncating). A document
database has no such constraint.

**Honest note on scale:** at ~18,000 frame documents, a local file
would work fine — MongoDB is not required by data volume here. It was
chosen to demonstrate the NoSQL approach on data whose *shape* fits
the paradigm, not because the size demands it. This is a deliberate,
disclosed choice, not an assumption that bigger tools are always
better.

**Database:** `color_in_motion`, collection `frames`, hosted on
MongoDB Atlas (free tier).

**Document shape**, one per (film, second):
```json
{
  "tconst": "tt0133093",
  "secondo": 42,
  "brightness": 33.6,
  "temperature": -1.8,
  "saturation": 0.41,
  "mean_colour": [0.42, 0.31, 0.28],
  "gruppo": "genere"
}
```

### What is in this layer, and why
| Field | What it is | Why it's here |
|---|---|---|
| `brightness`, `temperature`, `saturation` | Per-frame colour metrics (each already a spatial mean over the frame's pixels) | Core features, aggregated (mean + std) into the warehouse and used directly by the classifier |
| `mean_colour` | Per-frame average RGB colour (3 numbers) | Reused by **more than one** downstream process: the per-genre barcode and the auteur-film barcode both read it directly from Mongo, instead of re-reading the source videos |
| `tconst`, `secondo`, `gruppo` | Identifiers (film, timestamp, genre-set vs auteur-set) | Needed to query and reassemble sequences |

### What is deliberately NOT in this layer, and why
The guiding rule: **a value belongs in the shared staging layer only if
it is reused by more than one downstream process.** Anything computed
for a single, one-off exploratory analysis stays local to the notebook
that produced it, and is recomputed from the source video if ever
needed again. This keeps the staging schema stable — it is not
rewritten every time a new exploratory idea comes up.

| Not included | Why not | Where it's computed instead |
|---|---|---|
| Full pixel data of each frame | Volume: ~230,000 pixels per frame × ~18,000 frames ≈ billions of values; no declared use justifies this scale | Never computed at all — the source video remains the ultimate raw layer if ever needed |
| Hue-family distribution (% red, % green, etc. per frame) | Used by exactly one descriptive experiment (colour distribution by genre); it also made the classifier *worse* (47.1% vs 55.9%), so it does not feed any active process | Recomputed on demand in the notebook, from the source videos, each time the experiment is run |
| Frame uniformity / "is this a title card" score | Used by exactly one experiment (title-card filtering); did not improve the classifier (52.9% vs 55.9%), so it does not feed any active process | Computed on demand in the notebook, from the source videos |

This is also why the **movie-barcode colour distribution and the
title-card filter both re-read the source videos** rather than reading
from Mongo: they need frame-level detail (the full image, or a
per-frame histogram) that the staging layer intentionally does not
carry, because no recurring process needs it. `mean_colour` is the one
exception, because it *is* reused (by the barcodes), so it earned a
place in the shared layer.

## Warehouse — SQLite
Clean, analysis-ready data. One row per film, fixed columns — a
genuinely relational shape, hence a relational database.

**Database:** `data/warehouse/color_in_motion.db`, table `films`.

**How it's built:** a MongoDB aggregation pipeline (`$group`, `$avg`,
`$stdDevPop`) computes, for every `tconst`, the mean and standard
deviation of brightness, temperature and saturation across all its
frame documents. This result is joined (in pandas) with title, genre
and year from the Source layer, and written into SQLite with
`to_sql(..., if_exists="replace")`.

**Validation performed:** the per-film means computed by the MongoDB
aggregation were compared against the means computed directly in
Python from the same source frames (two independent computation
paths on the same raw data). They matched exactly, confirming the
Mongo → SQLite pipeline introduces no error.

**Columns:** `tconst, brightness_media, brightness_std,
temperature_media, temperature_std, saturation_media, saturation_std,
n_secondi, primaryTitle, genere_principale, startYear`. 142 rows: 133
genre-labelled films + 9 auteur films (`genere_principale = "Auteur"`,
excluded from genre-classification analysis, used only for the
auteur-vs-genres comparison).

**Single access point:** every notebook reads this table through
`src/data_access.py -> load_warehouse()`, so there is exactly one code
path to the warehouse, not several `pd.read_csv` calls to files that
could drift out of sync.

## Flow
```
IMDb + TMDB
    -> SOURCE (CSV: film metadata, genre, trailer links)
    -> [download + per-frame colour extraction]
    -> STAGING (MongoDB: one document per film-second,
                core colour metrics + mean_colour)
    -> [aggregation: MongoDB $group / $avg / $stdDevPop]
    -> WAREHOUSE (SQLite: one row per film, mean + std features)
    -> analysis (classifier, descriptive charts) + dashboard
```

Two side branches read directly from the SOURCE videos, bypassing
staging, because they need per-frame detail the staging layer does not
carry (see table above):
```
SOURCE videos -> [hue-family histogram]     -> colour-distribution experiment (descriptive only)
SOURCE videos -> [frame uniformity check]   -> title-card-filter experiment (classifier variant)
```

## Design notes
- Raw source data is never overwritten, so any step can be traced back.
- Expensive work (extracting colour from 133+9 videos) is separated
  from cheap work (computing averages), so re-summarising doesn't
  require re-reading the videos — except for the two exploratory
  branches above, which by design trade re-computation cost for a
  smaller, more stable staging schema.
- Each storage layer uses the paradigm that matches its data's shape:
  CSV for small regular metadata (source), a document database for
  irregular frame-level sequences (staging), a relational database for
  the clean tabular result (warehouse). This is the practical
  demonstration of "RDBMS and NoSQL approaches": not using both
  because the assignment asks for it, but using each where its data
  actually fits.
- Not everything a video *could* yield is stored centrally. Only
  features reused by more than one process live in MongoDB; one-off
  exploratory features are recomputed on demand. This avoids the
  staging schema growing without bound every time a new idea is
  tested, which would itself be a design smell.
