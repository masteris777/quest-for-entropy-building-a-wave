"""Episode #5. Does a probability wave keep waving, or does it flatten?

One observer, one uncertainty (0.02 in every coordinate), four deterministic mechanical
worlds and one drum. We watch the observer's probability distribution and measure two
things about it:

  the swing  - how far the distribution's centre of mass still moves (is it still waving?)
  the spread - how many bits the observer is missing (has it flattened?)

Writes metrics.json, curves.npz, frames.npz.
"""

import json
import time

import numpy as np

import engine as E

M = 6000
SIGMA = 0.02
DT = 0.005
T_END = 300.0
STRIDE = 40
WINDOW = 15.0
GRIDS = [16, 64, 256]
SYS = ["harmonic", "pendulum", "double_low", "double_high"]


def decay_fits(env, times, ref):
    """Chaos should kill the swing exponentially; plain anharmonic shear should only
    manage a power law. Fit both over the decay window and let R^2 decide."""
    ok = np.isfinite(env) & (times > 0)
    band = ok & (env < 0.9 * ref) & (env > 0.02 * ref)
    if band.sum() < 8:
        return None
    t, e = times[band], env[band]
    out = {}
    for kind, x, y in (("exponential", t, np.log(e)),
                       ("power_law", np.log(t), np.log(e))):
        a, b = np.polyfit(x, y, 1)
        pred = a * x + b
        ss = ((y - pred) ** 2).sum()
        tot = ((y - y.mean()) ** 2).sum()
        out[kind] = {"slope": float(a), "r2": float(1 - ss / tot) if tot > 0 else None}
    out["verdict"] = ("exponential" if out["exponential"]["r2"] > out["power_law"]["r2"]
                      else "power_law")
    out["n_points"] = int(band.sum())
    return out


def main():
    t0 = time.time()
    met = {"params": dict(members=M, sigma=SIGMA, dt=DT, T=T_END, stride=STRIDE,
                          window=WINDOW, grids=GRIDS), "systems": {}}
    store = {}

    print("A. four worlds, one observer")
    for name in SYS:
        times, obs, drift = E.run(name, M, SIGMA, T_END, DT, stride=STRIDE)
        s = E.SYSTEMS[name]
        mean = obs.mean(axis=1)
        env = E.envelope(mean, times, WINDOW)
        ref = env[np.isfinite(env)][0]
        tc = E.coherence_time(env, times)

        ent = {}
        for nb in GRIDS:
            ent[nb] = E.entropy_curve(obs, s["lo"], s["hi"], nb)
        ceil = {nb: E.entropy_ceiling(s["lo"], s["hi"], nb, 40000) for nb in GRIDS}

        met["systems"][name] = {
            "label": s["label"],
            "energy_drift_max": drift,
            "swing_start": float(ref),
            "swing_end": float(env[np.isfinite(env)][-1]),
            "swing_ratio": float(env[np.isfinite(env)][-1] / ref),
            "coherence_time": tc,
            "entropy_start_bits": {str(nb): float(ent[nb][0]) for nb in GRIDS},
            "entropy_end_bits": {str(nb): float(ent[nb][-1]) for nb in GRIDS},
            "entropy_ceiling_bits": {str(nb): float(ceil[nb]) for nb in GRIDS},
            "entropy_fraction_of_ceiling": {
                str(nb): float(ent[nb][-1] / ceil[nb]) for nb in GRIDS},
            "decay": decay_fits(env, times, ref),
        }
        store[f"{name}_mean"] = mean
        store[f"{name}_env"] = env
        for nb in GRIDS:
            store[f"{name}_S{nb}"] = ent[nb]
        store["times"] = times

        print(f"  {name:12s} swing {ref:.3f}->{env[np.isfinite(env)][-1]:.3f}"
              f"  S {ent[64][0]:.2f}->{ent[64][-1]:.2f}/{ceil[64]:.2f} bits"
              f"  t_coh={tc}  dE={drift:.1e}")

    print("A'. the control: the same run with the doubt removed")
    times_c, obs_c, drift_c = E.run("double_high", 400, 0.0, T_END, DT, stride=STRIDE)
    mean_c = obs_c.mean(axis=1)
    env_c = E.envelope(mean_c, times_c, WINDOW)
    s = E.SYSTEMS["double_high"]
    S_c = E.entropy_curve(obs_c, s["lo"], s["hi"], 64)
    met["control"] = {
        "note": "same chaotic world, sigma = 0: every member is the same world",
        "entropy_max_bits": float(S_c.max()),
        "swing_ratio": float(env_c[np.isfinite(env_c)][-1] / env_c[np.isfinite(env_c)][0]),
        "member_spread_max": float(obs_c.std(axis=1).max()),
    }
    store["control_S64"] = S_c
    store["control_env"] = env_c
    print(f"  entropy max {S_c.max():.3e} bits, member spread max "
          f"{obs_c.std(axis=1).max():.3e}, swing ratio {met['control']['swing_ratio']:.3f}")

    print("B. the drum: two modes ringing together")
    _, _, _, beat = E.two_mode(0.0)
    period = 2 * np.pi / beat
    ts = np.linspace(0.0, period, 61)
    d0 = E.two_mode(0.0)[2]
    corr, contrast = [], []
    for t in ts:
        d = E.two_mode(float(t))[2]
        corr.append(float(np.corrcoef(d0.ravel(), d.ravel())[0, 1]))
        contrast.append(float(d.max() - d.min()))
    corr, contrast = np.array(corr), np.array(contrast)
    met["drum"] = {
        "beat_frequency": float(beat),
        "beat_period": float(period),
        "return_correlation_after_one_period": float(corr[-1]),
        "contrast_min": float(contrast.min()),
        "contrast_max": float(contrast.max()),
        "contrast_ratio_last_first": float(contrast[-1] / contrast[0]),
        "note": ("the pattern beats forever and returns exactly: the interference term "
                 "has a fixed coefficient, so nothing decays"),
    }
    store["drum_t"] = ts
    store["drum_corr"] = corr
    store["drum_contrast"] = contrast
    print(f"  beat period {period:.3f}, correlation back to {corr[-1]:.6f} after one "
          f"period, contrast ratio {contrast[-1]/contrast[0]:.6f}")

    print("C. cloud frames for the pictures")
    frames = {}
    for name in ("double_low", "double_high"):
        ft, ff = E.run_frames(name, 4000, SIGMA, 120.0, DT, stride=80)
        frames[f"{name}_t"] = ft
        frames[f"{name}_xy"] = ff
        print(f"  {name}: {ff.shape}")

    np.savez_compressed("curves.npz", **store)
    np.savez_compressed("frames.npz", **frames)
    met["runtime_seconds"] = round(time.time() - t0, 1)
    with open("metrics.json", "w", encoding="utf-8") as f:
        json.dump(met, f, indent=2)
    print(f"\nwrote metrics.json, curves.npz, frames.npz  ({met['runtime_seconds']}s)")


if __name__ == "__main__":
    main()
