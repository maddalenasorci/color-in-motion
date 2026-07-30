# Color in Motion

**Do film genres have a colour signature you can see over time?**
A data pipeline that analyses movie trailers to find out whether genres
differ in how colour moves across a trailer — and whether that signal is
strong enough to predict the genre from colour alone.

---

## What this is

Most colour analysis of film produces a single average value per movie.
This project treats colour as a **signal over time**: every trailer becomes
a sequence of brightness and warmth measurements, from first frame to last.

The core question: an horror and a comedy — do their colour curves have
different shapes? And is the difference sharp enough that a model can guess
the genre just by looking at the colour?

## How it works

1. **Sampling** — build a balanced set of films from IMDb (top-voted titles,
   stratified across five genres), then fetch each trailer's YouTube link from TMDB.
2. **Ingestion** — download the trailers with yt-dlp and extract one frame per second.
3. **Colour metrics** — for every frame, measure brightness and temperature
   in the perceptually-uniform CIELAB colour space.
4. **Storage** — organise the data in three layers: source tables, staging, warehouse.
5. **Analysis** — compare average colour curves by genre and train a classifier
   that predicts genre from colour features.
6. **Dashboard** — visualise curves, movie barcodes and genre comparisons.

## Repository structure

```
src/          Reusable functions:
              frames.py   – extract frames from a video
              metrics.py  – colour metrics (brightness, temperature) in CIELAB
              plots.py    – draw colour curves and movie barcodes
notebooks/    Step-by-step analysis, one notebook per phase
              01_sampling.ipynb – build the film sample and fetch trailer links
data/         Local only, not tracked on GitHub (raw downloads and processed tables)
outputs/      Generated charts and figures
prototype.py  Early end-to-end test on a single trailer
```

## Tech stack

- **Scraping & data**: Python, requests, yt-dlp, pandas
- **Image processing**: OpenCV, scikit-image
- **Modelling**: scikit-learn
- **Storage**: MongoDB, SQL
- **Visualisation**: Power BI

## Status

- [x] Phase 0 — end-to-end prototype on one trailer
- [x] Phase 1 — clean project setup
- [x] Phase 2 — film sampling and trailer links (source table: 399 films)
- [ ] Phase 3 — trailer download and frame extraction
- [ ] Phase 4 — storage layers
- [ ] Phase 5 — analysis and genre classifier
- [ ] Phase 6 — dashboard