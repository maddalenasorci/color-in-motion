# Classifier methodology: how the genre-from-colour model was built

This document explains, for a reader evaluating the project, how the
final colour-based genre classifier was constructed and validated. It
complements `ARCHITECTURE.md` (the data pipeline) and `DATA_QUALITY.md`
(data problems and treatment) by focusing specifically on the modelling
decisions and the evidence behind each one.

## The question

Can a film's genre be predicted from the colour of its trailer alone?
And where does that signal work well, and where does it break down?

## The two decisions behind the model

Rather than picking one classifier configuration and reporting its
accuracy, the model was built by resolving two independent design
questions in sequence, each backed by a dedicated comparison.

### Decision 1 — which colour representation to use

Two ways of summarising a trailer's colour were compared:

- **Mean-based features**: the mean and standard deviation of brightness
  and colour temperature across all frames of the trailer (4 features).
- **Colour-distribution features**: the percentage of frames falling
  into each of 7 hue families — red, orange, yellow, green, blue,
  purple, dark/neutral (7 features).

Both were evaluated with identical treatment (no class balancing, same
5-fold stratified cross-validation, same random seed), so the comparison
isolates a single variable: the choice of representation, not how
imbalance or randomness is handled.

**Result: a near-tie.** Mean-based and distribution-based features
scored within a fraction of a percentage point of each other
(52.6% vs 52.6%), with a slight edge in genre balance toward the
mean-based version. Given how close the result was, the project does not
force a single choice: **both representations were carried forward as
two complete, parallel pipelines**, described below, so the final
comparison is made at the level of the whole modelling chain, not a
single early measurement.

### Decision 2 — how to handle Action's over-representation

The sample has 72 Action films out of 133 — substantially more than any
other genre. Two ways of addressing this were compared, for each colour
representation:

- **Class weighting**: all 133 films are used; the model is told to
  weigh each genre equally during training (`class_weight="balanced"`
  in scikit-learn).
- **Physical undersampling**: Action is reduced to 18 films (in line
  with the other genres), so the training data itself is balanced, at
  the cost of using fewer films overall (79 instead of 133).

**Result:** class weighting alone was not enough to stop the model
defaulting to "Action" for uncertain cases — the confusion matrix still
showed Action dominating the predicted column, with other genres left
at or near 0% recognised. Physical undersampling produced a lower
overall accuracy (fewer training examples), but no genre was left
completely unrecognised — recognition was distributed more evenly across
all five genres. **Undersampling was chosen** as the basis for the final
model on this basis: a model that is only "accurate" because it
defaults to the majority class is not a meaningful genre classifier,
even if its headline number looks higher.

## Building the final model: two parallel chains

Starting from the undersampled base (79 films, Action reduced to 18),
each colour representation (Mean, Distribution) was extended through the
same two additional steps, so that both final models can be compared on
equal footing:

1. **Base** — the winning balancing method (undersampling) on the chosen
   colour representation alone.
2. **+ Saturation** — saturation mean and standard deviation added to
   the feature set.
3. **+ Title-card filtering** — frames identified as probable title
   cards or logos (see `DATA_QUALITY.md` for the detection method) are
   excluded before recomputing the features.

Both chains use the **same 79-film subset** throughout (the same 18
sampled Action films at every step), so that differences between the
two chains reflect the colour representation and its extensions, not a
different random sample.

## Isolating the effect of saturation from the effect of filtering

Because step 3 (filtering) is applied on top of step 2 (saturation), a
change in accuracy at the final step could come from either
modification, or from their interaction. To avoid that ambiguity, a
dedicated experiment computes "+ Saturation only" and "+ Filtering only"
independently, both starting from the same base, so each modification's
effect on the confusion matrix — in particular, whether the model still
over-predicts Action — can be attributed to a single, specific cause
rather than a combination.

## Validation method: stratified cross-validation, not a single split

Every reported accuracy in this project comes from **5-fold stratified
cross-validation**, not a single train/test split. With genres this
small (11 to 72 films), a single 75/25 split leaves only a handful of
films per genre in the test set, and the result can swing considerably
depending on which films happen to fall into that one split.

Cross-validation trains and tests the model 5 separate times, so that
every film is used as test data exactly once (across different folds),
and reports:

- the **mean accuracy** across the 5 folds, with its standard deviation
  (how much the result varies from fold to fold — a direct measure of
  how stable the estimate is);
- the **aggregated confusion matrix**, summed across all 5 folds, so it
  reflects predictions on every film in the dataset rather than one
  quarter of it.

Where a class has fewer than 5 films (relevant once Action is reduced to
18 in the balancing comparisons), the number of folds is automatically
reduced so that no fold is left without an example of the smallest
class.

## Reading the results: accuracy alone is not the whole picture

Throughout this project, an accuracy percentage is treated as
insufficient on its own. The reported evidence for each comparison
always includes the **per-genre breakdown** — what percentage of each
individual genre's films were correctly classified — because a single
aggregate number can look strong while one genre (typically the most
numerous) is driving nearly all of it, with others left unrecognised.
This is why every classifier comparison in the project is presented as
a paired chart: an accuracy bar chart alongside a small heatmap showing
per-genre performance, not the accuracy number in isolation.

## Headline finding

Across every version tested — different colour representations,
different balancing strategies, added saturation, frame filtering,
isolated or combined — the same pattern holds: **colour reliably
separates the most visually extreme genre (Horror) but does not reliably
separate the genres that share a similar visual register** (Comedy,
Crime, Drama). This was tested from multiple independent angles
(re-weighting, physical resampling, an alternative feature space,
frame-level cleaning) specifically to rule out that the limitation was
an artefact of any one modelling choice. It was not: the same central
finding survives every version of the pipeline, which is what makes it
the project's central, evidence-backed conclusion rather than a
one-off observation from a single model run.
