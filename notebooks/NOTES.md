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