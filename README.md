# Quest for Entropy #5 — Building a Wave

**Article:** [Quest for Entropy #5 — "Building a Wave"](https://questforentropy.substack.com/p/building-a-wave)

Companion code for the article *Building a Wave*.

**The question:** can a probability cloud spread into a shape, stop spreading below the flat
grey, and then keep that shape sloshing? This lab measures two things about an observer's
probability distribution in six deterministic mechanical worlds:

- **the swing** — how far the centre of the distribution still moves (is it still sloshing?)
- **the spread** — how many bits the observer is missing, and where that number levels off

A drumhead model also lives in `engine.py`; it belongs to the following article and is not
used by anything the *Building a Wave* text claims.

## Run it

```
pip install -r requirements.txt
python run_all.py
```

About ten minutes. It re-runs both experiments from scratch and checks every number the
article quotes against the fresh output, then exits non-zero if anything drifted.

To regenerate the figures as well:

```
python make_figures.py
```

## What is in here

| file | what it is |
|---|---|
| `engine.py` | the four mechanical systems, the RK4 integrator, the entropy estimator |
| `run_lab.py` | the four frictionless worlds; writes `metrics.json`, `curves.npz`, `frames.npz` |
| `attractors.py` | the two worlds WITH friction: Lorenz, and a periodically driven pendulum |
| `make_figures.py` | every figure in the article |
| `run_all.py` | reproduction check against `metrics_reference.json` |
| `metrics_reference.json` | the numbers as published |
| `attractor_reference.json` | the attractor numbers as published |
| `figures/` | the figures as published |

## Honest notes about the instruments

**The entropy estimate is a floor, and it is relative to a ruler.** It is the Shannon entropy of
one coarse-grained observable, Miller–Madow corrected, and averaged over eight placements of the
grid origin. The averaging matters: a cloud narrower than one cell would otherwise flicker
between 0 and ~1 bit as it drifts across a cell line, which reads as information being *gained*.
It cannot be. Any single number here is meaningful only against the stated cell count; the claim
the article actually rests on is the *ordering* of the four worlds, which is checked at 16, 64
and 256 cells.

**The energy check is the control on the arithmetic.** Every system here conserves energy
exactly, so drift measures how much the integrator is lying. `run_all.py` asserts the worst case
stays under 1e-6. This is not decoration: an earlier version of the double pendulum had a sign
error in the equations of motion, and the way it was caught was that its energy drift did not
shrink when the time step shrank. Integration error shrinks; wrong equations do not.

**The zero-doubt control.** The same chaotic world run with the initial spread set to zero gives
exactly 0.000 bits at every step, and the copies stay identical to ~1e-16. All the spreading in
the article comes from the one thing deliberately not known, not from the simulation.

**The four worlds in `run_lab.py` are conservative, so none of them can have an attractor** -
Liouville forbids it. `attractors.py` is the answer to the obvious follow-up: it adds two
dissipative worlds, the Lorenz attractor and a periodically driven chaotic pendulum. Its
controls are different, because energy is *supposed* to be lost there: instead of an energy
check it carries the zero-doubt control and a halved-time-step check. The Lorenz swing ratio is
already down in the noise and its exact value wanders with step size, so `run_all.py` asserts the
verdict (under 5% of where it started, with a finish time) rather than the digit.

**One measurement was discarded.** `decay_fits` in `run_lab.py` tries to separate exponential
decay (chaos) from a power law (plain phase mixing). The fits came back too close to call, so the
distinction is not in the article. The code is left in so you can see the thing that did not
work.

## Licence

Code MIT. Article text CC BY 4.0.
