"""Probability distributions carried by deterministic mechanics.

Every system here is exact and reversible. The only thing that is uncertain is where the
observer thinks it started: an ensemble of worlds drawn from a narrow Gaussian around one
initial condition. That ensemble IS the observer's probability distribution. We then watch
what the dynamics does to it.

The question the whole lab answers: does the distribution keep waving, or does it flatten?

Four mechanical systems, one acoustic cavity, one instrument (coarse entropy in bits,
inherited from the break-shot lab, grid-offset averaged so a sub-cell cloud cannot appear
to gain information).
"""

import numpy as np

G = 1.0
L1 = L2 = 1.0
M1 = M2 = 1.0


# ------------------------------------------------------------------------- integrator

def rk4(deriv, y, dt):
    k1 = deriv(y)
    k2 = deriv(y + 0.5 * dt * k1)
    k3 = deriv(y + 0.5 * dt * k2)
    k4 = deriv(y + dt * k3)
    return y + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


# ---------------------------------------------------------------------------- systems
# Each system is (deriv, y0, observable, obs_range, name). State is (m, d).

def _harmonic(m, sigma, rng):
    """x'' = -x. Isochronous: every member has the same period, whatever its amplitude."""
    y = np.zeros((m, 2))
    y[:, 0] = 1.0
    y[1:] += rng.normal(0.0, sigma, (m - 1, 2))
    return y


def _harmonic_deriv(y):
    out = np.empty_like(y)
    out[:, 0] = y[:, 1]
    out[:, 1] = -y[:, 0]
    return out


def _pendulum(m, sigma, rng):
    """th'' = -sin(th), released from 2.0 rad. Integrable, but the period depends on
    amplitude - so the members shear past each other."""
    y = np.zeros((m, 2))
    y[:, 0] = 3.0
    y[1:] += rng.normal(0.0, sigma, (m - 1, 2))
    return y


def _pendulum_deriv(y):
    out = np.empty_like(y)
    out[:, 0] = y[:, 1]
    out[:, 1] = -np.sin(y[:, 0])
    return out


def _double_deriv(y):
    t1, t2, w1, w2 = y[:, 0], y[:, 1], y[:, 2], y[:, 3]
    d = t2 - t1              # this sign matters: sin is odd, and getting it backwards
    cd, sd = np.cos(d), np.sin(d)    # gives a system that does not conserve energy
    den1 = (M1 + M2) * L1 - M2 * L1 * cd * cd
    den2 = (L2 / L1) * den1

    dw1 = (M2 * L1 * w1 * w1 * sd * cd
           + M2 * G * np.sin(t2) * cd
           + M2 * L2 * w2 * w2 * sd
           - (M1 + M2) * G * np.sin(t1)) / den1

    dw2 = (-M2 * L2 * w2 * w2 * sd * cd
           + (M1 + M2) * G * np.sin(t1) * cd
           - (M1 + M2) * L1 * w1 * w1 * sd
           - (M1 + M2) * G * np.sin(t2)) / den2

    out = np.empty_like(y)
    out[:, 0], out[:, 1], out[:, 2], out[:, 3] = w1, w2, dw1, dw2
    return out


def _double(angle):
    def start(m, sigma, rng):
        y = np.zeros((m, 4))
        y[:, 0] = angle
        y[:, 1] = angle
        y[1:] += rng.normal(0.0, sigma, (m - 1, 4))
        return y
    return start


def _tip_x(y):
    return L1 * np.sin(y[:, 0]) + L2 * np.sin(y[:, 1])


def tip_xy(y):
    return np.stack([L1 * np.sin(y[:, 0]) + L2 * np.sin(y[:, 1]),
                     -L1 * np.cos(y[:, 0]) - L2 * np.cos(y[:, 1])], axis=1)


# Energy per member. Conserved exactly by the real system, so its drift under our
# integrator is the honest measure of how much the arithmetic is lying to us.

def _harmonic_energy(y):
    return 0.5 * (y[:, 0] ** 2 + y[:, 1] ** 2)


def _pendulum_energy(y):
    return 0.5 * y[:, 1] ** 2 + G * (1.0 - np.cos(y[:, 0]))


def _double_energy(y):
    t1, t2, w1, w2 = y[:, 0], y[:, 1], y[:, 2], y[:, 3]
    ke = (0.5 * (M1 + M2) * L1 ** 2 * w1 ** 2 + 0.5 * M2 * L2 ** 2 * w2 ** 2
          + M2 * L1 * L2 * w1 * w2 * np.cos(t1 - t2))
    pe = -(M1 + M2) * G * L1 * np.cos(t1) - M2 * G * L2 * np.cos(t2)
    return ke + pe


SYSTEMS = {
    "harmonic": dict(
        start=_harmonic, deriv=_harmonic_deriv, energy=_harmonic_energy,
        obs=lambda y: y[:, 0], lo=-1.35, hi=1.35,
        label="harmonic spring (isochronous)"),
    "pendulum": dict(
        start=_pendulum, deriv=_pendulum_deriv, energy=_pendulum_energy,
        obs=lambda y: y[:, 0], lo=-3.25, hi=3.25,
        label="single pendulum, near the top (integrable, anharmonic)"),
    "double_low": dict(
        start=_double(0.35), deriv=_double_deriv, energy=_double_energy,
        obs=_tip_x, lo=-2.05, hi=2.05,
        label="double pendulum, small swing (near-integrable)"),
    "double_high": dict(
        start=_double(np.pi / 2), deriv=_double_deriv, energy=_double_energy,
        obs=_tip_x, lo=-2.05, hi=2.05,
        label="double pendulum, wide swing (chaotic)"),
}


def run_frames(name, m, sigma, T, dt, seed=20260729, stride=1):
    """Same run, but keeping the pendulum tip in the plane - the picture of the cloud."""
    s = SYSTEMS[name]
    rng = np.random.default_rng(seed)
    y = s["start"](m, sigma, rng)
    n = int(round(T / dt))
    times, frames = [], []
    for i in range(n + 1):
        if i % stride == 0:
            times.append(i * dt)
            frames.append(tip_xy(y))
        if i < n:
            y = rk4(s["deriv"], y, dt)
    return np.array(times), np.array(frames)


def run(name, m, sigma, T, dt, seed=20260729, stride=1):
    """Evolve the ensemble. Member 0 is the exact world; the rest are the observer's doubt.

    Returns times, the observable for every member at every kept frame, and the worst
    energy drift any member suffered - the control that says whether we are watching
    physics or arithmetic.
    """
    s = SYSTEMS[name]
    rng = np.random.default_rng(seed)
    y = s["start"](m, sigma, rng)
    deriv, energy = s["deriv"], s["energy"]
    e0 = energy(y)

    n = int(round(T / dt))
    times = np.array([i * dt for i in range(0, n + 1, stride)])
    obs = np.empty((len(times), m))

    j, drift = 0, 0.0
    for i in range(n + 1):
        if i % stride == 0:
            obs[j] = s["obs"](y)
            j += 1
            drift = max(drift, float(np.abs(energy(y) - e0).max()))
        if i < n:
            y = rk4(deriv, y, dt)
    return times, obs, drift


# ------------------------------------------------------------------------- instrument

_OFFSETS = np.linspace(0.0, 1.0, 8, endpoint=False)


def coarse_entropy(x, lo, hi, nbins):
    """Shannon entropy of the coarse-grained observable, in bits.

    Miller-Madow corrected and averaged over eight placements of the grid origin, so a
    cloud narrower than one cell reads as ~0 bits instead of flickering between 0 and 1
    as it drifts across a cell line. Same instrument as the break-shot lab: information
    must never appear to be GAINED because of where the ruler happens to lie.
    """
    m = x.size
    span = hi - lo
    total = 0.0
    for o in _OFFSETS:
        idx = np.floor((x - lo) / span * nbins + o).astype(int)
        np.clip(idx, 0, nbins, out=idx)
        counts = np.bincount(idx, minlength=nbins + 1)
        p = counts[counts > 0] / m
        total += -(p * np.log2(p)).sum() + (len(p) - 1) / (2 * m * np.log(2))
    return total / len(_OFFSETS)


def entropy_ceiling(lo, hi, nbins, m, seed=11):
    """What this estimator reads when the observer knows nothing but the range."""
    rng = np.random.default_rng(seed)
    return coarse_entropy(rng.uniform(lo, hi, m), lo, hi, nbins)


def entropy_curve(obs, lo, hi, nbins):
    return np.array([coarse_entropy(f, lo, hi, nbins) for f in obs])


# --------------------------------------------------------------------- is it waving?

def envelope(signal, times, window):
    """RMS of the signal about its own running mean, over a sliding window.

    This is the amplitude of the wave in the probability distribution: how far the
    ensemble's centre of mass still swings. It is the thing that dies when the
    distribution stops waving.
    """
    dt = times[1] - times[0]
    w = max(int(round(window / dt)), 3)
    h = w // 2
    out = np.full(len(signal), np.nan)
    for i in range(h, len(signal) - h):
        seg = signal[i - h:i + h + 1]          # only full windows: a half-window at the
        out[i] = np.sqrt(((seg - seg.mean()) ** 2).mean())   # edge reads as a fake decay
    return out


def coherence_time(env, times, frac=1 / np.e):
    """When the swing of the mean first falls to 1/e of its starting value, and stays
    below it. Returns None if it never does."""
    ok = np.nonzero(np.isfinite(env))[0]
    if ok.size == 0:
        return None
    ref = env[ok[0]]
    if ref <= 0:
        return None
    below = np.isfinite(env) & (env < frac * ref)
    hit = np.nonzero(below)[0]
    if hit.size == 0:
        return None
    for i in hit:
        rest = env[i:][np.isfinite(env[i:])]
        if (rest < frac * ref).all():
            return float(times[i])
    return float(times[hit[-1]])


# ------------------------------------------------------------------- acoustic cavity

def bessel_mode(n, m_ang, grid=320, R=1.0):
    """One standing wave of a drum: J_m(k r) cos(m th), k fixed by the rim.

    The observer who knows only 'it is in this cavity, at this energy' holds exactly this
    distribution. Nothing here is quantum - it is a drumhead.
    """
    from scipy.special import jn, jn_zeros
    x = np.linspace(-R, R, grid)
    X, Y = np.meshgrid(x, x)
    r = np.hypot(X, Y)
    th = np.arctan2(Y, X)
    k = jn_zeros(m_ang, n)[-1]
    psi = jn(m_ang, k * r) * np.cos(m_ang * th)
    psi[r > R] = 0.0
    return X, Y, psi, k


def two_mode(t, a=(1, 0), b=(1, 2), c=0.75, grid=320, R=1.0, weights=(0.6, 0.8)):
    """Two drum modes ringing together, in the standard complex (analytic) form.

        |psi|^2  =  ca^2 pa^2  +  cb^2 pb^2  +  2 ca cb pa pb cos((wa - wb) t)

    The first two terms are the two modes' own patterns and never move. The third is the
    interference term, and it beats forever at |wa - wb| without ever spreading: a
    probability distribution that keeps waving. Total intensity is constant because the
    modes are orthogonal. Nothing here is quantum - it is a drumhead.
    """
    X, Y, pa, ka = bessel_mode(*a, grid=grid, R=R)
    _, _, pb, kb = bessel_mode(*b, grid=grid, R=R)
    wa, wb = c * ka, c * kb
    ca, cb = weights
    dens = (ca * pa) ** 2 + (cb * pb) ** 2 + 2 * ca * cb * pa * pb * np.cos((wa - wb) * t)
    s = dens.sum()
    return X, Y, dens / (s if s > 0 else 1.0), abs(wa - wb)
