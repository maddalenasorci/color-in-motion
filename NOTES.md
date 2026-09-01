# Project notes (for the final deck)

## Critical issue: downloading trailers from YouTube (2026)

Downloading a few hundred trailers turned out to be hard. YouTube in 2026 actively blocks bulk downloading. Full
sequence of what I tried, in order:

### 1. Single / small test — worked
A test on 3 trailers downloaded fine using yt-dlp with the `android`
player client (needed to bypass YouTube's "SABR streaming").

### 2. Full bulk download — blocked after ~70 files
Running over the whole sample worked for the first ~79 files (mostly
Action, since the sample was ordered by genre), then YouTube started
returning "Sign in to confirm you're not a bot". Everything after failed.

### 3. Browser cookies — conflict
The standard fix is passing browser cookies. But the `android` client
does not support cookies, and the default web clients are blocked by
SABR streaming. The two fixes are mutually exclusive.

### 4. mweb client — needs a PO Token
The `mweb` client accepts cookies and is a known SABR workaround, but it
required a "GVS PO Token" I didn't have, and returned HTTP 403.

### 5. Working solution — small shuffled, targeted batches
Went back to the `android` client (no cookies) and changed strategy:
- shuffled the sample so genres alternate
- downloaded in small batches (30–40 at a time)
- added 2s pauses between downloads
- ran targeted batches only on under-represented genres
YouTube "forgets" between batches, so downloads accumulated steadily
without triggering the block.

### 6. Result — reduced but balanced sample
Final: 133 films across 5 genres
(Action 72, Crime 19, Horror 18, Comedy 13, Drama 11).
See `DATA_QUALITY.md` for a full discussion of why 133, and of the
Action/Drama imbalance and its consequences.

### Other minor issues
- A few trailers were age-restricted ("Sign in to confirm your age")
  and were skipped.
- yt-dlp had to be updated to the latest dev version early on, because
  YouTube had changed something that broke the stable release.
- Some videos didn't have the exact 360p format, so the format request
  was made flexible ("best[height<=480]/best").

## First results: colour by genre

### Brightness — strong, clean signal
Average brightness clearly separates genres, exactly as the theory
predicts (lower = darker):
- Horror    12.3  (by far the darkest)
- Crime     18.9
- Action    19.4
- Drama     20.4
- Comedy    23.6  (the lightest)

Horror stands out sharply — almost half the brightness of Comedy.
This is the clearest result of the project: brightness is a strong
genre signal.

### Temperature — weaker, more nuanced signal
Average temperature (lower = cooler) tells a subtler story:
- Horror    2.0  (coolest)
- Action    2.4
- Comedy    3.4
- Drama     3.7
- Crime     3.8  (warmest)

Only the extreme (Horror: dark AND cool) behaves as expected.
The middle genres are barely separated by temperature.
Surprisingly, Crime is dark but NOT cool — it's the warmest genre,
which contradicts the automatic "dark = cool" assumption.

### Saturation — genre averages
Added later, alongside the classifier experiment (see below). Kept as
a third descriptive bar chart next to brightness and temperature.
Coloured a bit differently per genre; used mainly as a classifier
feature rather than a standalone finding, since no genre stood out as
sharply on saturation alone as Horror does on brightness.

### Takeaway
Brightness is a reliable genre discriminator; temperature is not,
except for the horror extreme. Letting the data speak: the orange-teal
cliché holds for brightness but only partly for temperature.

## Genre classifier — Baseline (colour medio: brightness + temperature)

### Result
Random Forest predicts genre from 4 colour features (mean and std of
brightness and temperature) with **52.9% accuracy**, vs 20% for random
guessing (5 genres) — 2.6x better.

### Feature importance
All four features contribute fairly evenly:
- brightness_media   0.291  (most useful, as expected)
- temperature_std    0.261  (surprising: the VARIATION of temperature
                             matters more than its average)
- brightness_std     0.230
- temperature_media  0.218  (least useful)

Interesting: temperature *average* was a weak per-genre signal, but
temperature *variability* is one of the most useful features. The model
revealed something a single-metric analysis missed.

### Where it fails (confusion matrix)
The 52.9% is partly inflated by class imbalance:
- Action: 14/15 correct — but the model over-predicts Action because
  the sample is Action-heavy (72 of 133 films).
- Horror: 3/6 correct — genuinely distinguishable (very dark).
- Comedy, Crime, Drama: almost all wrongly labelled as Action.

Honest reading: colour clearly separates the EXTREME (horror), but the
central genres are not separable by colour alone. The high accuracy is
driven, at least in part, by the abundance of Action films.

### Link to the download issue
The Action imbalance comes from the YouTube download problem: Action
trailers were downloaded first before the block hit. A data-collection
issue became an analysis issue — a good end-to-end lesson, and the
reason the next experiment tests for it directly.

## Experiment: balancing the classes

### Why
To check whether Action's dominance in the confusion matrix is really
just a numbers effect. If it is, telling the model to weigh classes
equally (`class_weight="balanced"`) should fix it.

### Result
Accuracy 47.1% (was 52.9%), and the confusion matrix is almost
identical. Comedy, Crime, Drama are still nearly all classified as
Action; only Horror is reliably recognised.

### Key insight
Balancing didn't help because the problem isn't class imbalance — it's
that colour alone doesn't carry enough information to separate the
central genres. They share similar colour signatures.

Deeper explanation: Action does not win because it is frequent — it
wins because it is the most chromatically "average" genre (dark scenes,
bright explosions, warm and cool tones all mixed), sitting near the
centre of the colour space. When the model cannot characterise a film
confidently, it defaults to the class closest to that centre, which
happens to be Action. This is a property of the *colour distribution
of the genres*, not of the sample size — and it is the reason later
experiments (saturation, colour-distribution, frame filtering) were
run: to see whether a richer or cleaner signal could break this
pattern. None of them did (see below), which strengthens rather than
weakens this conclusion.

## Experiment: adding saturation (6 features)

### Hypothesis
Maybe Comedy has bright, saturated colours while Drama/Crime are more
muted — a dimension that brightness and temperature don't capture.

### Result
Accuracy 47.1% → **55.9%** (+8.8 points, the best result across all
experiments). BUT the confusion matrix shows the gain comes entirely
from Action (15/15) and Horror (4/6, up from 3/6) — genres the model
already recognised. Comedy, Crime, Drama remain at 0/expected.

### Conclusion
Colour reliably identifies the visual EXTREMES (dark horror,
high-contrast action) but cannot separate the central genres, which
share similar colour signatures. Adding saturation raises overall
accuracy but does not unlock the central genres.

## Diagnostic check: physically undersampling Action

**What this is, and what it is not.** This is a one-off diagnostic
test, not a new dataset and not a replacement for the project's real
sample. The project's actual dataset remains the 133 films described
throughout this document and in `DATA_QUALITY.md`; nothing here
changes that. The only purpose of this test is to answer one narrow
question as rigorously as possible: *does the confusion between the
central genres come from Action simply having more films in the
sample?*

The class-weight balancing experiment (above) already answered this —
weighting the classes barely changed the result — but weighting only
re-scales the influence of each class during training; all 72 Action
films are still physically present. To remove any doubt, Action was
additionally **physically reduced** to 18 films (matching Horror,
roughly matching Crime), by random sampling
(`colori_df["genere_principale"]=="Action"].sample(n=18, random_state=42)`),
and the classifier was retrained from scratch on this reduced set (79
films total), using the same 6 features (mean+std of brightness,
temperature, saturation). No class weighting was applied on top of
this, deliberately: since the imbalance is already removed physically,
adding `class_weight="balanced"` again would be redundant and would
muddy the comparison.

This is a **disposable, throwaway experiment**: its output (a
temporary `colori_df_bilanciato` variable, never written to MongoDB or
SQLite) exists only inside this one notebook cell group and is
discarded after being read. It is reported here purely as
corroborating evidence for the class-imbalance question, with its own
limitation stated plainly: a 79-film sample produces a test set of
only ~20 films, so the resulting numbers are noisy and should not be
over-interpreted on their own — they are read alongside, not instead
of, the class-weighted result on the full 133-film sample.

**Result:** accuracy dropped (see the reduced-data table), and — more
informative than the single number — no genre emerged as the dominant
"catch-all" the way Action did in the original, unbalanced runs. This
is consistent with, and reinforces, the class-weighting result: the
central-genre confusion is not an artefact of Action's larger count in
the sample.

## Movie barcodes

Two barcode approaches were tried:
1. **Average colour per genre** — normalise all sequences to 100
   points, average pixel colours across all films of a genre,
   frame-by-frame. Rigorous (it truly represents the whole genre) but
   visually poor: averaging many different colours mathematically
   trends toward dark grey, so these barcodes carried almost no visual
   information. **Decision: dropped from the final deliverables.**
   Mentioned only verbally if asked, not included in the deck or
   dashboard, because it does not give a reader anything actionable.
2. **One real film per genre** — instead of averaging, pick the single
   film whose average brightness is closest to its genre's mean, and
   draw its true, unaveraged colour sequence. This is not a "sample
   representative" in a strict statistical sense — it is a real,
   concrete, recognisable example of what a typical trailer of that
   genre looks like. **This is the one used in the deck and dashboard.**

The example barcodes show clear genre signatures:
- Horror: dark, blacks and night-blues, red tail toward the end
- Crime: black with recurring bright RED (noir/violence)
- Action: varied, cool blues/teals with warm accents (orange-teal look)
- Drama: cool blues and greys, sober
- Comedy: lightest and warmest, earthy tones, low contrast

## Key insight: barcodes reveal what the features miss

The classifier fails on Crime, but the Crime barcode shows a STRONG
signature: recurring bright red. Contradiction? No — it reveals a
limitation of the features.

The 6 features are means and stds: they average colours over the whole
trailer and discard time. Crime's red appears at intervals; averaged
with surrounding black, it becomes an insignificant dark brown in the
numbers. The model never "sees" the red — only the average.

So: the colour information to identify Crime EXISTS (the eye sees the
red in the barcode), but mean/std features throw it away. This later
motivated two follow-up experiments — colour distribution (Crime's
red as a % of frames) and frame filtering (removing non-informative
frames) — both aimed at recovering that signal. Neither succeeded (see
below); together they show the Crime signal is punctual and rare, not
statistical, and no re-weighting of the existing colour signal
recovers it.

## Auteur films — qualitative colour analysis

Beyond the quantitative work on 133 trailers, I analysed 9 auteur films
with strong, deliberate cinematography. Here the goal is not
classification but reading each film's colour signature. The barcodes
are far more distinct than the genre averages, because these are
visually intentional works.

Key observations:
- **The Elephant Man (1980)** — pure black and white (Lynch shot it in B&W).
  The barcode is greyscale: here the ABSENCE of colour is the signature.
- **Eternal Sunshine of the Spotless Mind (2004)** — the most striking: an
  electric-blue block, then warm yellows and recurring teal. The cold/warm
  alternation mirrors the film's theme of memory and erasure.
- **American Honey (2016)** and **Mommy (2014)** — warm, earthy, golden tones
  (sun, skin, outdoors).
- **All These Sleepless Nights (2016)** — the most varied and saturated:
  night blues, oranges, purples — a film about neon-lit youth nightlife.
- **The Florida Project (2017)** — muted pastels (mauve, faded pink, soft
  green): the pastel motels of its setting.
- **The Worst Person in the World / Fish Tank** — sober greys and greens,
  fitting their realist drama.

Takeaway: when a film has intentional cinematography, colour genuinely
carries meaning and identity. This is the opposite of the "central
genres" in the quantitative study, where averaged trailers had no
distinctive fingerprint. Auteur cinema uses colour as a deliberate
language.

## Experiment: colour distribution ("how much of each colour")

### Hypothesis
The classifier misses Crime, but the Crime barcode shows a strong
recurring red. So: build colour-distribution features — the percentage
of frames in each hue family (red, orange, yellow, green, blue,
purple, dark_neutral) — expecting Crime to score high on red.

### Result (average % of frames per genre)

| Genre  | red | dark_neutral | notable |
|--------|-----|--------------|---------|
| Horror | 0.1 | 77.7 | overwhelmingly dark/neutral |
| Action | 0.3 | 58.0 | — |
| Crime  | 0.3 | 57.9 | almost identical to Action |
| Drama  | 0.1 | 53.9 | most BLUE (18.6%) |
| Comedy | 0.0 | 42.9 | least dark, most GREEN (30.6%) |

Key finding: Crime's red is NOT there in the numbers (0.3%, same as
everyone). The red seen in the barcode is a few vivid frames — rare in
FREQUENCY but strong in IMPACT. The eye weights red by how much it
stands out; the counts weight it by how often it appears. These are
different things, and the barcode misleads: that red occupies only a
few seconds.

As a **classifier feature**: accuracy 47.1% — worse than the 6
mean-based features (55.9%). Comedy gained 1 correct (the green), but
Horror got worse and Crime/Drama still collapse into Action.

### Decision on where this feature lives
This table is kept **only as a descriptive result** (computed on
demand in the notebook, screenshotted for the deck). It is
**deliberately not stored in MongoDB or SQLite**. Rationale: a value
belongs in the shared data layers only if it is reused by more than
one downstream process; this one is used exactly once, for one
descriptive table, and does not feed the classifier (which performs
worse with it), the warehouse, or the dashboard. See `ARCHITECTURE.md`
for the general rule.

### Final verdict on the classifier (three feature experiments)
1. Means (brightness, temperature): ~47–53%
2. + Saturation (6 features): 55.9% — best
3. Colour distributions (7 families): 47.1%

No colour-based feature set separates the central genres. The mean +
saturation features remain best. This triangulates the core
conclusion: the limit is not feature choice — colour itself, however
measured, does not carry enough information to distinguish
Action/Comedy/Crime/Drama. Only the extremes (Horror) are reliably
separable.

## Auteur films vs genres: the key comparison

Plotted the 9 auteur films against the 5 genre averages (brightness x
saturation). See `outputs/auteur_vs_genres.png`.

Finding: the 5 genres cluster in a TIGHT region (saturation 0.29-0.35,
except Horror which sits left, darker). This visualises why colour
can't separate them — they occupy nearly the same colour space.

The auteur films SCATTER in every direction, each breaking the norm:
- The Elephant Man: saturation ~0.00 (black & white) — total outlier,
  no genre reaches there.
- Eternal Sunshine: brightest of all (33), brighter than any genre.
- All These Sleepless Nights: most saturated (~0.50), neon nightlife.
- Florida Project, Laurence Anyways, Worst Person, Fish Tank, Mommy:
  BELOW the genre cluster — less saturated than the average genre,
  fitting their sober realist palettes.

### The core insight (connects both halves of the project)
Colour does NOT predict genre (commercial genres cluster together),
but it does reveal AUTHORSHIP: auteur films leave the cluster, each in
a deliberate direction. Colour doesn't measure "what genre" — it
measures how far a film departs from convention. When a director makes
a strong colour choice, the film exits the crowd.

---

## Rebuilding staging as MongoDB (moving beyond local JSON)

The original staging layer was a local JSON file
(`color_sequences.json`) holding one entry per film, each with the
full per-second sequences of brightness, temperature and saturation.
This worked, but had two limits: it lived only on one machine, and it
was not queryable — any aggregation had to be done in Python, re-reading
the whole file into memory.

Decision: move the staging layer to **MongoDB Atlas** (cloud, free
tier). Rationale, stated honestly: at this scale (~18,000 frame
documents) MongoDB is not strictly necessary — a local file would work
fine. The choice is deliberately made to demonstrate the NoSQL
approach the course covers, on data whose shape (variable-length,
frame-level sequences) is a natural fit for a document database, not
because volume demands it. This is stated explicitly rather than
implied, since a self-aware architectural choice is worth more than
pretending the data required it.

### What went into MongoDB, and why
Each document = one frame (one second) of one trailer:
`{tconst, secondo, brightness, temperature, saturation, mean_colour,
gruppo}`. `mean_colour` (the average RGB colour of that frame) was
added specifically because it is reused by more than one process (the
per-genre barcode and the auteur-film barcode) — see `ARCHITECTURE.md`
for the full decision table of what is and is not in the staging
layer.

### Aggregation in MongoDB, not in Python
Instead of computing per-film averages in Python and only using Mongo
as storage, a MongoDB aggregation pipeline (`$group`, `$avg`,
`$stdDevPop`) computes the mean and standard deviation of brightness,
temperature and saturation directly in the database. This is then
written into the SQLite warehouse. Validation: the averages computed
this way were checked against the original Python-computed averages
(same source frames, two different computation paths) and matched
exactly, confirming the pipeline is correct end to end.

### Warehouse: SQLite
The final, one-row-per-film table (`films`, in `color_in_motion.db`)
is written from the MongoDB aggregation result, joined with
title/genre/year from the Source layer. This table is queried with
SQL (see the example query in `05_databases.ipynb`) and is the single
source read by the rest of the analysis via `src/data_access.py ->
load_warehouse()`. No script reads the old CSV any more.

## Experiment: filtering probable title-card frames

### Hypothesis
Some frames are title cards or logos, not real scenes — they are dark
and visually flat, and they bias the mean/std calculations, especially
for genres whose real scenes are also dark (Horror).

### Method
A three-signal heuristic, applied to frames already extracted (not
re-writing MongoDB — this is a single-use experimental feature, see
the staging decision table):
1. **Frame uniformity** — a title card has low pixel variance
   (`frame.std()` below a threshold).
2. **Border uniformity** — same check restricted to the top strip of
   the frame, to also catch cards with text in the centre but a flat
   background/border.
3. **Temporal position** — cards mostly sit at the very start or very
   end of a trailer (first/last ~3 seconds).
A frame is treated as a probable card only if it is uniform (by
signal 1 or 2) AND near the temporal edges (signal 3).

### Result
Accuracy 52.9%, vs 55.9% without the filter — a small **decrease**.

### Interpretation
The most likely explanation: the filter also removes real, dark scenes
that happen to be uniform and sit near the edges of the trailer —
particularly plausible for Horror, the genre the classifier relies on
most for its accuracy, and the genre whose real footage is most likely
to be dark and low-contrast. In other words, the heuristic cannot
fully separate "noise" (title cards) from "signal" (genuinely dark,
uniform footage) when the two look statistically similar. This is a
legitimate negative result: it shows that a plausible, principled
data-cleaning step can hurt as much as help when the noise and the
signal share the same statistical fingerprint.

### Why the filter was not folded into MongoDB
Same rule as the colour-distribution experiment: it is used once, for
one test, does not improve on the existing warehouse features, and
does not feed any other process. Kept local to the notebook.

## Second refactor: three decision phases, cross-validation, dual chains

After the sessions above, the classifier notebook was rebuilt again, this
time to fix a real methodological bug and to answer a question the
earlier version could not: *is "distribuzione colori" really better than
"medie", or did it only look that way because of how the data happened to
be split?*

### Bug found: Fase 1 was not a fair comparison

The original "Media vs Distribuzione colori" comparison used two
DataFrames built through different code paths (`colori_df` from the
warehouse, `dist_con_genere` from a fresh loop over `trailer_scaricati`),
in different row orders. `train_test_split(..., random_state=42)` picks
rows by *position*, not by content — so the same `random_state` was
silently selecting **different films** as the test set in the two
comparisons. The two accuracies were not measured on the same 34 films.

Fix: both DataFrames are now sorted by `tconst` before splitting, so the
same `random_state` produces the same test set in both cases. This is a
general lesson, not specific to this one comparison: any time two
DataFrames are compared with the same `random_state`, they must be in
the same row order first, or the "fair" comparison is an illusion.

### Bigger problem found: a single split is too noisy for this dataset size

Even after fixing the alignment, a single 75/25 split leaves only ~26-34
films in the test set, spread across 5 genres — Drama and Comedy end up
with 2-4 test films each. A single unlucky or lucky split can swing the
result by many points, and does not really tell you which feature set
generalises better; it tells you what happened on one particular random
draw.

Fix: replaced the single split with **5-fold stratified cross-validation**
(`StratifiedKFold`, via a new `valuta_con_cv()` helper). Every film ends
up in the test set exactly once, across 5 different folds; the reported
accuracy is the mean across folds, with a standard deviation attached;
the confusion matrix is the **sum across all 5 folds**, so it reflects
every film in the dataset, not just one quarter of it. When the smallest
class in a comparison has fewer than 5 films (relevant once Action is
reduced to 18 in the balancing experiments), the fold count is
automatically capped (`n_splits_sicuro = min(5, n_min_classe)`) so no
fold ends up without an example of the rarest class.

### Result: Fase 1 was actually a near-tie

With the alignment bug fixed and cross-validation in place, "Media" and
"Distribuzione colori" came out at **52.6% vs 52.6%** — a near-exact tie,
with the genre balance slightly favouring Media. The earlier "clear win"
for Distribuzione colori was, at least in part, an artefact of the
unfair single split. This is an important methodological finding in its
own right: a plausible-looking result (from a real bug) evaporated once
measured correctly. Worth stating explicitly rather than hiding: the
first "Distribuzione colori wins" conclusion was wrong, caught only
because the confusion matrix looked internally inconsistent with the
accuracy number, which is what triggered re-checking the comparison.

### Decision: build both chains, not just one

Given the near-tie, arbitrarily picking one feature set to carry forward
would have thrown away signal. Instead, **both full chains** (Fase 2 +
Fase 3) were built for **both** Media and Distribuzione colori, sharing
the exact same reduced 79-film subset (same 18 sampled Action films,
`random_state=42`) so the two complete chains can be compared fairly at
every step, not just at the start.

Each chain follows: Sottocampionato (base) → + Saturazione →
+ Filtro cartelli. A final combined chart compares all 6 resulting
models (bar chart with CV error bars) and a combined heatmap stacks
both chains' confusion matrices, genres in columns, with a horizontal
line separating the two chains for a genre-by-genre, step-by-step
comparison.

### Isolating saturation from the cartello filter

The "+ Filtro cartelli" step in each chain applies the filter *on top
of* the saturation step, so a change in accuracy at that step could come
from either modification, or their interaction — not obviously from one
alone. A dedicated isolation experiment was added: starting from the
same Sottocampionato base, "+ Saturazione (sola)" and "+ Filtro cartelli
(solo)" are each computed independently, so their individual effect on
each genre — especially on the Action column, where the "catch-all"
pattern lives — can be read separately before looking at them combined.

### Feature importance

For the saturation model, `RandomForestClassifier.feature_importances_`
is now captured (averaged across the 5 CV folds) and plotted as a
horizontal bar chart. This answers a natural follow-up question — *of
the 6 features, which ones does the model actually rely on?* — directly,
instead of leaving it implicit in the accuracy number alone.

### Two more instances of the same alignment bug

The tconst-sorting fix applied to Fase 1 turned out not to be the whole
story. The same failure mode reappeared twice more, further along the
pipeline:

1. `dist_con_genere_bilanciato` (the 79-film Sottocampionato subset for
   the Distribuzione chain) was built via `pd.concat([action_ridotto,
   altri_generi])` and never re-sorted — `action_ridotto` is a
   `.sample()`, so the concat result is not in `tconst` order. The
   paired significance test (below) sorts both sides internally, so its
   numbers did not match the officially reported Fase 2 accuracy for
   this chain until this was fixed.
2. `color_dist_filtrato_df` / `brightness_temp_filtrato_df` (the "+
   Filtro cartelli" step, both chains) were built by looping over
   `trailer_scaricati`, which comes from `os.listdir()` — filesystem
   order, not alphabetical. This meant the "+ Filtro cartelli" step was
   evaluated on a *third*, different fold split from the two steps
   before it in the same chain.

Both fixed the same way: an explicit `.sort_values("tconst")` at the
point each DataFrame is created, so every downstream `.merge()` (which
preserves left-frame row order) inherits a consistent order. After
fixing both, every accuracy number in both chains is computed on
directly comparable folds.

### The result reverses after the fix

With fold alignment corrected end to end, the accuracy ordering flips
from the previous write-up:

| Step | Distribuzione | Media |
|---|---|---|
| Sottocampionato | 31.8% | 34.2% |
| + Saturazione | 34.2% | 35.4% |
| + Filtro cartelli | 34.4% | 38.2% |

Media now leads at every step — the opposite of the "Distribuzione
wins, margin grows to +9pp" conclusion drawn before these two bugs were
caught. This is the second time a headline conclusion in this project
has flipped after a code-level fix, not a new experiment. Worth stating
plainly: both "wins" were artefacts of unfixed row ordering, not real
findings. This is why the next step below (formal significance
testing) was added rather than trusting either ranking at face value.

### Formal significance testing, all three steps

A paired test (`confronta_significativita`: paired t-test + Wilcoxon
signed-rank as a non-parametric check) was run on the *same* 5 CV folds
for Distribuzione vs Media, at each of the three chain steps:

| Step | p-value (paired t-test) |
|---|---|
| Sottocampionato | 0.559 |
| + Saturazione | 0.857 |
| + Filtro cartelli | 0.607 |

None reach significance at alpha = 0.05. Combined with the fact that
the ranking between the two chains flipped after a pure bug fix (no new
data, no new method), this is strong practical confirmation that the
observed differences are noise, not signal: **the project does not
declare a winning colour representation.** Both are reported; neither is
presented as superior.

The test was deliberately *not* applied to the Bilanciato-vs-
Sottocampionato decision in Fase 2: that decision was never based on a
narrow accuracy margin — Bilanciato was rejected on a categorical
criterion (0% recognition on entire genres), which a significance test
would not have changed either way.

## Promoting winning features into MongoDB/SQLite

`ARCHITECTURE.md` originally excluded hue-family distribution and
title-card filtering from the shared staging/warehouse layers, citing
the pre-refactor numbers (47.1% vs 55.9%, 52.9% vs 55.9%) as evidence
they "made the classifier worse" and were used by exactly one process.
After the refactor above, both numbers are outdated, and both features
are part of the classifier's active final-stage pipeline (even though
neither colour representation is now declared the winner) — so the
rule already stated in `ARCHITECTURE.md` ("a value belongs in the
shared layer if reused by more than one process, or is part of the
active pipeline") now argues for promoting them, not excluding them.

### What changed in `05_databases.ipynb`

- Every frame document written to MongoDB now also carries
  `hue_family` and `is_title_card`, computed with the *same*
  `e_uniforme` / `trova_frame_cartello` functions used in the
  classifier notebook (copied verbatim, not re-implemented, to avoid a
  fourth version of the same heuristic drifting out of sync).
- A second aggregation pipeline groups on `tconst` after a `$match:
  {is_title_card: false}` stage, producing `_filtrato` variants of
  every mean/std feature plus the seven hue-family percentages — the
  MongoDB equivalent of the notebook's "+ Filtro cartelli" step,
  computed once centrally instead of re-extracted from video on every
  notebook run.
- The SQLite `films` table grew from 11 to 33 columns: the original
  brightness/temperature/saturation mean+std, seven `colore_*`
  percentages, six `*_filtrato` mean/std columns, seven
  `colore_*_filtrato` percentages, and `pct_title_card`.

### Validation

Same method as the original brightness/temperature/saturation
validation: three sample films were recomputed directly in Python from
the source video (`color_distribution`, `curve_from_frames` on the
title-card-filtered frame list) and compared against the MongoDB
aggregation. All three matched exactly, confirming the
`hue_family`/`is_title_card` → aggregation pipeline is correct end to
end, the same standard already applied to the original three metrics.

## Notebook clean-up and naming

Renumbered/renamed the classifier sections from generic "Experiment
1/2/3/4" to descriptive names (Baseline, Balancing the classes, Adding
saturation, Colour distribution, Frame-card filtering) so the notebook
reads as a narrative of what was tried and why, not an unlabelled
sequence. Also removed the average-colour-per-genre barcode from the
active pipeline (kept only as a documented, discarded attempt) and
renamed "representative barcode" to avoid the statistical implication
of the word "representative" — it is a real example film, not a
statistical representative.

## Auteur-vs-genres scatter: final label layout

The scatter plot went through several label-placement attempts before
settling on the current version. Plain in-place text labels overlapped
badly (9 auteur titles in a small region). A first fix used a side
column of labels connected to each point by a straight diagonal line —
functional, but with 9 lines converging from very different angles it
was visually busy and occasionally ambiguous about which line belonged
to which point, especially where two genres (Crime/Action) sit close
together in brightness.

Final version: each genre circle gets its own colour on the ring (not
just grey), used consistently for that genre wherever it appears; auteur
labels connect to their point through an "elbow" connector — a short
diagonal segment to a shared vertical column, then a horizontal segment
to the label — instead of one long diagonal. This reduces line crossings
noticeably compared to direct diagonals across the full width of the
plot. `adjustText` was installed as a candidate automatic label-placement
library but not used in the end; the manual elbow-connector layout gave
more control over the specific case of two circles sitting close
together, and was kept as the final approach.
