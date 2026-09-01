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
  "hue_family": "dark_neutral",
  "is_title_card": false,
  "gruppo": "genere"
}
```

### What is in this layer, and why
| Field | What it is | Why it's here |
|---|---|---|
| `brightness`, `temperature`, `saturation` | Per-frame colour metrics (each already a spatial mean over the frame's pixels) | Core features, aggregated (mean + std) into the warehouse and used directly by the classifier |
| `mean_colour` | Per-frame average RGB colour (3 numbers) | Reused by **more than one** downstream process: the per-genre barcode and the auteur-film barcode both read it directly from Mongo, instead of re-reading the source videos |
| `hue_family` | Which of 7 hue families the frame falls into (red, orange, yellow, green, blue, purple, dark_neutral) | Promoted here after the classifier refactor (see `NOTES.md`): the "distribuzione colori" representation built from this field is now part of the classifier's active pipeline, not a one-off experiment. Previously recomputed from video on every run; aggregated into per-film percentages by the same MongoDB pipeline as the other metrics |
| `is_title_card` | Whether the frame is a probable title card / logo, from the same heuristic used in the classifier notebook | Promoted for the same reason as `hue_family`: title-card filtering is now part of the active pipeline ("+ Filtro cartelli" step), not a discarded experiment. Lets the "filtered" aggregates be computed once in MongoDB (`$match` before `$group`) instead of re-detected from video every run |
| `tconst`, `secondo`, `gruppo` | Identifiers (film, timestamp, genre-set vs auteur-set) | Needed to query and reassemble sequences |

### What is deliberately NOT in this layer, and why
The guiding rule: **a value belongs in the shared staging layer only if
it is reused by more than one downstream process, or is part of the
classifier's active pipeline.** Anything computed for a single, one-off
exploratory analysis stays local to the notebook that produced it, and
is recomputed from the source video if ever needed again. This keeps
the staging schema from growing without bound every time a new
exploratory idea comes up — `hue_family` and `is_title_card` (above)
used to be here, until the classifier results that had excluded them
were found to rest on a fold-alignment bug (see `NOTES.md`); once
corrected, both became part of the active pipeline and were promoted.

| Not included | Why not | Where it's computed instead |
|---|---|---|
| Full pixel data of each frame | Volume: ~230,000 pixels per frame × ~18,000 frames ≈ billions of values; no declared use justifies this scale | Never computed at all — the source video remains the ultimate raw layer if ever needed |

**Honest caveat on the promotion above:** the classifier notebook
(`03_color_extraction.ipynb`) has *not* been rewired to read
`hue_family`/`is_title_card` back out of MongoDB or the warehouse — it
still recomputes both from the source video independently, using its
own copies of the same detection functions. The promotion so far means
the values are now centrally available and validated (see Warehouse
section below), not that the classifier already consumes them from
there. Pointing the classifier at the warehouse instead of the raw
video is a reasonable next step, not yet done, mainly to avoid
disturbing a notebook that was mid-verification (fold-alignment bugs,
significance testing) at the time this promotion was made.

## Warehouse — SQLite
Clean, analysis-ready data. One row per film, fixed columns — a
genuinely relational shape, hence a relational database.

**Database:** `data/warehouse/color_in_motion.db`, table `films`.

**How it's built:** two MongoDB aggregation pipelines, both grouping by
`tconst`. The first (`$group`, `$avg`, `$stdDevPop`) computes the mean
and standard deviation of brightness, temperature and saturation across
*all* frame documents, plus the percentage of frames in each of the 7
`hue_family` values (via `$avg` of a `$cond` on equality — the fraction
of frames matching a family is exactly its percentage). The second adds
a `$match: {is_title_card: false}` stage before the same `$group`,
producing the "filtered" equivalents (`_filtrato` suffix) of every
metric above. Both results are joined (in pandas) with title, genre and
year from the Source layer, and written into SQLite with
`to_sql(..., if_exists="replace")`.

**Validation performed:** two rounds, same method both times — compare
the MongoDB aggregation against an independent computation in Python
from the same source frames. Round 1 (original): brightness/
temperature/saturation means matched exactly. Round 2 (after promoting
`hue_family`/`is_title_card`): three sample films' hue-family
percentages and filtered statistics were recomputed directly in Python
(`color_distribution`, `curve_from_frames` on the title-card-filtered
frame list) and compared against the MongoDB aggregation — all matched
exactly. Both rounds confirm the Mongo → SQLite pipeline introduces no
error.

**Columns (33 total):** the original `tconst, brightness_media,
brightness_std, temperature_media, temperature_std, saturation_media,
saturation_std, n_secondi, primaryTitle, genere_principale, startYear`,
plus seven `colore_<famiglia>` percentages (red, orange, yellow, green,
blue, purple, dark_neutral), six `*_filtrato` mean/std columns
(brightness, temperature, saturation), seven `colore_<famiglia>_filtrato`
percentages, `n_secondi_filtrato`, and `pct_title_card`. 142 rows: 133
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
                colour metrics + mean_colour + hue_family + is_title_card)
    -> [aggregation: two MongoDB pipelines - all frames, and
        title-card-filtered ($match before $group)]
    -> WAREHOUSE (SQLite: one row per film, mean + std features,
                  hue-family percentages, filtered variants)
    -> analysis (classifier, descriptive charts) + dashboard
```

One side branch still reads directly from the SOURCE videos, bypassing
staging: the classifier notebook (`03_color_extraction.ipynb`)
recomputes `hue_family`/title-card detection independently rather than
reading the now-available warehouse columns (see the caveat in the
staging section above).
```
SOURCE videos -> [hue-family + title-card, computed inline] -> classifier notebook (03)
```
This is temporary duplication, kept deliberately for now rather than
rewiring a notebook that was mid-verification (fold-alignment bugs,
significance testing — see `NOTES.md`) at the time `hue_family`/
`is_title_card` were promoted to MongoDB.

## Design notes
- Raw source data is never overwritten, so any step can be traced back.
- Expensive work (extracting colour from 133+9 videos) is separated
  from cheap work (computing averages), so re-summarising doesn't
  require re-reading the videos — except for the classifier notebook's
  still-independent computation of `hue_family`/title-card detection
  (see Flow above), a deliberate, temporary duplication rather than a
  design default.
- Each storage layer uses the paradigm that matches its data's shape:
  CSV for small regular metadata (source), a document database for
  irregular frame-level sequences (staging), a relational database for
  the clean tabular result (warehouse). This is the practical
  demonstration of "RDBMS and NoSQL approaches": not using both
  because the assignment asks for it, but using each where its data
  actually fits.
- Not everything a video *could* yield is stored centrally. Only
  features reused by more than one process, or part of the active
  classifier pipeline, live in MongoDB; genuinely one-off exploratory
  features are recomputed on demand. This avoids the staging schema
  growing without bound every time a new idea is tested, which would
  itself be a design smell.
- This is a two-way door, not a one-time decision: `hue_family` and
  `is_title_card` moved from "recomputed on demand" to "stored
  centrally" once the classifier work they support stopped being a
  discarded experiment and became part of the active pipeline. The
  schema is expected to reflect what the analysis actually uses, even
  when that changes after the schema was first designed.
