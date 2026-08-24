# Data architecture

The pipeline organises data in three layers, from raw to analysis-ready.

## Source
Raw data as collected from external sources, before any processing.
- `campione_film.csv` — films sampled from IMDb (metadata, genre, votes)
- `film_with_trailers.csv` — same films plus the YouTube trailer link from TMDB

## Staging
Intermediate, semi-processed data. Voluminous and variable in shape.
- `color_sequences.json` — for each trailer, the full per-second sequences
  of brightness, temperature and saturation (lengths vary by trailer, so
  stored as JSON rather than CSV)

This is the natural NoSQL layer: nested, variable-length documents, one
per film. Ready to be loaded into MongoDB.

## Warehouse
Clean, analysis-ready data. One row per film.
- `color_features.csv` — the 6 summary colour features (mean and std of
  brightness, temperature, saturation) plus genre, title and year.
  This table feeds the classifier and the dashboard.

## Flow
```
IMDb + TMDB → SOURCE → [download + colour extraction] → STAGING → [aggregation] → WAREHOUSE → analysis + dashboard
```


## Design notes
- Raw source data is never overwritten, so any step can be traced back.
- Expensive work (extracting colour from 133 videos) is separated from
  cheap work (computing averages), so re-summarising doesn't require
  re-reading the videos.
- The staging layer keeps the full temporal sequences, which the
  warehouse summaries discard — useful for barcodes and any future
  time-based analysis.