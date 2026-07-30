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