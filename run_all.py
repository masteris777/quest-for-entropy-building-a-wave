"""Reproduce every number the articles quote, from scratch.

    python run_all.py

Re-runs the whole lab and the attractor addendum (about ten minutes), then checks each
number the article states against what the fresh run produced. Exits non-zero if any of
them has drifted.

Needs numpy and scipy. Regenerating the figures additionally needs matplotlib and
pillow; run_all.py does not require them.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
REF = json.loads((HERE / "metrics_reference.json").read_text(encoding="utf-8"))

print("running the lab (four worlds, the control, the drum) ...\n")
subprocess.run([sys.executable, "run_lab.py"], cwd=HERE, check=True)
NEW = json.loads((HERE / "metrics.json").read_text(encoding="utf-8"))

fails = []


def check(name, got, want, tol=0.0):
    ok = (got == want) if tol == 0 else (abs(got - want) <= tol)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}\n         got {got!r}, expected {want!r}")
    if not ok:
        fails.append(name)


print("\n1. the article's headline numbers\n")

S, RS = NEW["systems"], REF["systems"]

# The swing: two worlds keep waving, two do not.
check("spring still swinging (ratio ~1.02)", round(S["harmonic"]["swing_ratio"], 3),
      round(RS["harmonic"]["swing_ratio"], 3), 0.002)
check("barely-swinging double pendulum (ratio ~1.00)",
      round(S["double_low"]["swing_ratio"], 3),
      round(RS["double_low"]["swing_ratio"], 3), 0.002)
check("pendulum near the top falls to ~2%", round(S["pendulum"]["swing_ratio"], 3),
      round(RS["pendulum"]["swing_ratio"], 3), 0.002)
check("hard-swung double pendulum falls to ~1%",
      round(S["double_high"]["swing_ratio"], 3),
      round(RS["double_high"]["swing_ratio"], 3), 0.002)

check("the wave dies at t~104 (pendulum)", S["pendulum"]["coherence_time"],
      RS["pendulum"]["coherence_time"], 1.0)
check("the wave dies at t~34 (chaotic)", S["double_high"]["coherence_time"],
      RS["double_high"]["coherence_time"], 1.0)
check("the spring's wave never dies", S["harmonic"]["coherence_time"], None)
check("the near-integrable wave never dies", S["double_low"]["coherence_time"], None)

print("\n2. the missing information, 64-cell ruler\n")

for k, label in [("harmonic", "spring"), ("double_low", "barely swinging"),
                 ("pendulum", "near the top"), ("double_high", "swung hard")]:
    check(f"{label}: bits missing at the end",
          round(S[k]["entropy_end_bits"]["64"], 2),
          round(RS[k]["entropy_end_bits"]["64"], 2), 0.03)
check("the ceiling is the same for every world",
      round(S["harmonic"]["entropy_ceiling_bits"]["64"], 2),
      round(RS["harmonic"]["entropy_ceiling_bits"]["64"], 2), 0.02)

print("\n3. the ordering survives every resolution (the claim that carries the piece)\n")

order = ["harmonic", "double_low", "pendulum", "double_high"]
for nb in ("16", "64", "256"):
    got = [S[k]["entropy_end_bits"][nb] for k in order]
    ok = all(got[i] < got[i + 1] for i in range(3))
    print(f"  {'PASS' if ok else 'FAIL'}  {nb}-cell ruler: "
          f"{' < '.join(f'{v:.2f}' for v in got)}")
    if not ok:
        fails.append(f"ordering at {nb} cells")

print("\n4. the controls\n")

check("doubt removed: exactly zero bits, forever", NEW["control"]["entropy_max_bits"], 0.0)
ok = NEW["control"]["member_spread_max"] < 1e-12
print(f"  {'PASS' if ok else 'FAIL'}  copies stay identical "
      f"(spread {NEW['control']['member_spread_max']:.1e} < 1e-12)")
if not ok:
    fails.append("zero-doubt control spread")

worst = max(v["energy_drift_max"] for v in S.values())
ok = worst < 1e-6
print(f"  {'PASS' if ok else 'FAIL'}  energy drift worst case {worst:.1e} < 1e-6")
if not ok:
    fails.append("energy conservation")

print("\n5. the drum\n")

check("beat period", round(NEW["drum"]["beat_period"], 3),
      round(REF["drum"]["beat_period"], 3), 0.002)
check("returns exactly after one beat",
      round(NEW["drum"]["return_correlation_after_one_period"], 6), 1.0, 1e-6)
check("contrast does not decay",
      round(NEW["drum"]["contrast_ratio_last_first"], 6), 1.0, 1e-6)

print("\n6. the two worlds with friction (the attractor question)\n")

subprocess.run([sys.executable, "attractors.py"], cwd=HERE, check=True)
ANEW = json.loads((HERE / "attractor_metrics.json").read_text(encoding="utf-8"))
AREF = json.loads((HERE / "attractor_reference.json").read_text(encoding="utf-8"))

# Lorenz: the ringing dies. The leftover percentage is already down in the noise and
# moves with step size, so the article's claim - and this check - is the verdict, not
# the digit: the swing is under a twentieth of where it started, and it has a finish time.
ok = ANEW["lorenz"]["swing_ratio"] < 0.05
print(f"  {'PASS' if ok else 'FAIL'}  Lorenz: the wave dies "
      f"(swing ratio {ANEW['lorenz']['swing_ratio']:.3f} < 0.05)")
if not ok:
    fails.append("lorenz wave dies")
check("Lorenz finishes at t~5", ANEW["lorenz"]["coherence_time"],
      AREF["lorenz"]["coherence_time"], 1.0)

# Driven: the wave never dies, and it runs at the frequency that was plugged in.
ok = ANEW["driven"]["coherence_time"] is None
print(f"  {'PASS' if ok else 'FAIL'}  driven: the wave never dies "
      f"(no coherence time: {ANEW['driven']['coherence_time']})")
if not ok:
    fails.append("driven wave persists")
check("driven: swing settles near 57%", round(ANEW["driven"]["swing_ratio"], 2),
      round(AREF["driven"]["swing_ratio"], 2), 0.03)

for k in ("lorenz", "driven"):
    check(f"{k}: doubt removed gives exactly zero bits",
          ANEW[k]["control_entropy_max_bits"], 0.0)
    same = abs(ANEW[k]["half_step_swing_ratio"] - AREF[k]["half_step_swing_ratio"]) < 0.05
    print(f"  {'PASS' if same else 'FAIL'}  {k}: halving the time step does not move the "
          f"verdict ({ANEW[k]['half_step_swing_ratio']:.3f})")
    if not same:
        fails.append(f"{k} half-step")

print("\n7. where the spread stops - the plateau claims\n")

import numpy as np
C = np.load(HERE / "curves.npz")
t = C["times"]


def slope_per_100(times, y):
    """Rise per 100 time units over the last fifth of the run."""
    tail = slice(int(0.8 * len(y)), len(y))
    return float(np.polyfit(times[tail], y[tail], 1)[0] * 100)


CEIL = S["harmonic"]["entropy_ceiling_bits"]["64"]
for k, label, pct, climbing in [("harmonic", "spring", 20, False),
                                ("double_low", "barely swinging", 45, True),
                                ("pendulum", "near the top", 88, False),
                                ("double_high", "swung hard", 98, False)]:
    check(f"{label}: bits at the start", round(S[k]["entropy_start_bits"]["64"], 2),
          round(RS[k]["entropy_start_bits"]["64"], 2), 0.03)
    frac = 100 * S[k]["entropy_end_bits"]["64"] / CEIL
    ok = abs(frac - pct) < 1.5
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {frac:.0f}% of the ceiling "
          f"(article says {pct}%)")
    if not ok:
        fails.append(f"{label} fraction of ceiling")
    sl = slope_per_100(t, C[f"{k}_S64"])
    ok = (sl > 0.02) if climbing else (sl <= 0.02)
    word = "still climbing" if climbing else "levelled off"
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: {word} "
          f"(slope {sl:+.4f} bits per 100 time units)")
    if not ok:
        fails.append(f"{label} plateau verdict")

rise = S["harmonic"]["entropy_end_bits"]["64"] - S["harmonic"]["entropy_start_bits"]["64"]
ok = abs(rise - 0.02) < 0.02
print(f"  {'PASS' if ok else 'FAIL'}  the spring never spread: rose {rise:.2f} bits "
      f"over the whole run (article says 0.02)")
if not ok:
    fails.append("spring total rise")

print("\n8. the friction worlds: where they stop, and whose rhythm survives\n")

AC = np.load(HERE / "attractor_curves.npz")
for k, pct in (("lorenz", 92), ("driven", 86)):
    check(f"{k}: bits at the end", round(ANEW[k]["entropy_end_bits"], 2),
          round(AREF[k]["entropy_end_bits"], 2), 0.05)
    frac = 100 * ANEW[k]["entropy_end_bits"] / ANEW[k]["entropy_ceiling_bits"]
    ok = abs(frac - pct) < 1.5
    print(f"  {'PASS' if ok else 'FAIL'}  {k}: {frac:.0f}% of the ceiling "
          f"(article says {pct}%)")
    if not ok:
        fails.append(f"{k} fraction of ceiling")
    sl = slope_per_100(AC[f"{k}_t"], AC[f"{k}_S"])
    ok = sl <= 0.02
    print(f"  {'PASS' if ok else 'FAIL'}  {k}: levelled off "
          f"(slope {sl:+.4f} bits per 100 time units)")
    if not ok:
        fails.append(f"{k} plateau verdict")

# The surviving rhythm is the metronome's, not the chaos's. Measured from the zero
# crossings of the cloud's centre over the second half of the run - sharper than a
# spectrum, and the estimate the article quotes.
DRIVE_PERIOD = 2 * np.pi / (2.0 / 3.0)
dt_, dc_ = AC["driven_t"], AC["driven_mean"]
half = slice(len(dt_) // 2, None)
tl, cl = dt_[half], dc_[half] - np.mean(dc_[half])
zc = tl[:-1][(cl[:-1] < 0) & (cl[1:] >= 0)]
measured = float(np.mean(np.diff(zc)))
check("driven: the surviving period (article says 9.420)", round(measured, 3), 9.420, 0.02)
check("driven: the metronome's own period (article says 9.425)",
      round(DRIVE_PERIOD, 3), 9.425, 0.001)
ok = abs(measured / DRIVE_PERIOD - 1.0) < 0.002
print(f"  {'PASS' if ok else 'FAIL'}  they are the same rhythm "
      f"(ratio {measured / DRIVE_PERIOD:.5f}; article says 5 parts in 10,000)")
if not ok:
    fails.append("driven rhythm is the drive's")

print("\n" + ("-" * 62))
if fails:
    print(f"{len(fails)} CHECK(S) FAILED: {', '.join(fails)}")
    sys.exit(1)
print("all checks reproduced")
