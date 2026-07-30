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
Consistent

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

### Takeaway
Brightness is a reliable genre discriminator; temperature is not,
except for the horror extreme. Letting the data speak: the orange-teal
cliché holds for brightness but only partly for temperature.

## Genre classifier (first version)

### Result
Random Forest predicts genre from the 4 colour features with
**52.9% accuracy**, vs 20% for random guessing (5 genres) — 2.6x better.

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
driven by the abundance of Action films.

### Link to the download issue
The Action imbalance comes from the YouTube download problem: Action
trailers were downloaded first before the block hit. A data-collection
issue became an analysis issue — a good end-to-end lesson.

### Next step
Re-train with balanced classes to check whether the signal holds without
the "Action crutch".

### Balanced classifier — conclusion
Re-training with class_weight="balanced" barely changed anything:
accuracy 47.1% (was 52.9%), and the confusion matrix is almost identical.
Comedy, Crime, Drama are still all classified as Action; only Horror is
reliably recognised.

Key insight: balancing didn't help because the problem isn't class
imbalance — it's that colour alone doesn't carry enough information to
separate the central genres. They share similar colour signatures.

Final conclusion: colour is a strong predictor for the EXTREME (horror:
dark and distinct) but cannot separate the central genres. The
orange-teal / genre-colour intuition holds only for the most visually
extreme genre.

## Improving the classifier: adding saturation

### Hypothesis
The first classifier only separates Horror; the central genres
(Action, Comedy, Crime, Drama) share too-similar colour signatures.
The 4 features so far only capture brightness and temperature.

Idea: add **saturation** (how vivid vs muted the colours are).
Maybe Comedy has bright, saturated colours while Drama/Crime are more
muted — a dimension that brightness and temperature don't capture.

### Plan
- add saturation to the colour metrics (HSV S channel)
- re-process all 133 trailers
- add saturation_mean and saturation_std as features (6 total)
- re-train and check whether the central genres separate better

### Expected outcome
Either saturation helps separate the central genres (accuracy up,
confusion matrix cleaner) — or it doesn't, proving that colour alone,
even enriched, can't distinguish them. Both are valid results.

## Adding saturation — result

Added saturation (mean + std), going from 4 to 6 features.
Same train/test split and balanced model as before.

Accuracy: 47.1% → 55.9% (+8.8 points). Hypothesis partly confirmed:
saturation does add information.

BUT the confusion matrix tells the real story:
- Action: 15/15, Horror: 4/6 (improved from 3/6)
- Comedy 0/3, Crime 0/7, Drama 0/3 — still all misclassified as Action

The accuracy gain comes entirely from the genres the model already
recognised (Action, Horror). The three central genres remain
indistinguishable by colour.

### Final conclusion of the classifier
Colour reliably identifies the visual EXTREMES (dark horror, high-contrast
action) but cannot separate the central genres, which share similar colour
signatures. Adding saturation raises overall accuracy but does not unlock
the central genres. Colour alone is not enough for fine-grained genre
classification — other signals (editing rhythm, audio, motion) would be
needed.

### Why the central genres collapse into Action (clarification)

Important: Action does NOT win just because it has more films.
Proof: with class_weight="balanced" (which removes the numeric
advantage), the behaviour barely changed — central genres still
collapse into Action. If it were only an imbalance problem, balancing
would have fixed it.

The real reason: Action is the most cromatically "average" / varied
genre (dark scenes, bright explosions, warm and cool tones). It sits
in the middle of the colour space. When the model cannot characterise
a film (Comedy, Crime, Drama have no distinctive colour signature of
their own), it assigns it to the most generic/central class — which
is Action.

So Action acts as the "default bucket" for uncertain films, not
because it's frequent, but because it occupies the centre of the
colour space. This reinforces the conclusion: the central genres lack
a distinctive colour fingerprint.

## Movie barcodes

Generated two barcode visualisations by genre:
1. Average colour per genre (rigorous, but muted — averaging colours
   tends toward dark grey).
2. Representative trailer per genre (the film closest to its genre's
   mean brightness) — vivid and readable.

The representative barcodes show clear genre signatures:
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
red in the barcode), but mean/std features throw it away. This visually
justifies why temporal / distributional features (when and how much a
colour appears) could separate genres that means and stds cannot.

## Movie barcodes — technical steps

### Why a second pass over the trailers was needed
The colour features table (color_features.csv) only stored summary
statistics (mean and std of brightness, temperature, saturation).
It did not store the actual per-frame colours needed to draw barcodes.
So I re-read the trailers, this time keeping the full colour sequence.

### Step 1 — collect the colour sequence of each trailer
For every downloaded trailer:
- extracted one frame per second (extract_frames)
- computed per-frame metrics (curve_from_frames), which also returns
  the mean colour of each frame
- stored the full list of mean colours in a dictionary
  (barcode_per_film: tconst -> list of RGB colours)
Result: 133 colour sequences, one per film.

### Step 2 — average barcode per genre
Trailers have different lengths (120–155 frames), so before averaging
I normalised each sequence to a fixed length of 100 points
(linear interpolation on each RGB channel).
Then, for each genre, I averaged the normalised sequences of all its
films frame-by-frame.
Problem: averaging many different colours tends toward dark grey, so
the average barcodes came out muted and hard to read.

### Step 3 — representative barcode per genre
To get vivid, readable barcodes I switched approach: instead of
averaging, I picked one representative film per genre — the film whose
average brightness is closest to its genre's mean brightness.
Then I drew that film's real colour sequence (no averaging, true colours).
This produced clear, readable genre signatures.

### Output
Two images saved in outputs/:
- barcode_by_genre.png (average per genre — rigorous but muted)
- barcode_representative.png (representative trailer per genre — vivid)