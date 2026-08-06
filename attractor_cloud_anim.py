"""The butterfly keeps flying. My picture of it stops moving.

    uv run python attractor_cloud_anim.py

One concept, and it is the hardest one in episode #5: on a strange attractor, the SYSTEM
never stops and the DISTRIBUTION does. Nothing slows down, nothing cools, nothing is
damped away. What dies is the observer's ability to say where on the butterfly the state is.

Left  - one exact Lorenz trajectory. Loops forever.
Right - 20,000 copies of the same trajectory, each started 0.02 off (the same doubt used in
        the episode). Starts as a dot, sloshes wing to wing a few times, then fills the
        butterfly and goes still.
Below - the two instruments, drawn live: the swing (how far the cloud's centre still travels)
        and the bits the observer is missing, against the 6-bit ceiling.

Both panels are the SAME equations with the SAME parameters. The only difference is that the
right one does not know exactly where it started.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0
N = 12000                      # copies in the cloud
DOUBT = 0.02                   # same as the episode
DT, SUB = 0.0025, 20           # integration step, steps per rendered frame
FRAMES = 360                   # -> t runs to 18.0
K = 64                         # ruler cells -> 6-bit ceiling
CEILING = np.log2(K)
ENV_WIN = 48                   # frames in the swing envelope window (~2.4 time units)

BG, INK, MUTED = "#faf8f4", "#1a1a1a", "#8a8580"
BLUE, AMBER, RED = "#2f5fa8", "#c98a1e", "#c1362f"


def deriv(s):
    x, y, z = s[..., 0], s[..., 1], s[..., 2]
    return np.stack([SIGMA * (y - x), x * (RHO - z) - y, x * y - BETA * z], axis=-1)


def rk4(s, dt):
    k1 = deriv(s)
    k2 = deriv(s + 0.5 * dt * k1)
    k3 = deriv(s + 0.5 * dt * k2)
    k4 = deriv(s + dt * k3)
    return s + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def bits_missing(x, lo, hi):
    """Shannon entropy of the cloud's x-coordinate over a K-cell ruler."""
    c = np.histogram(x, bins=K, range=(lo, hi))[0].astype(float)
    p = c / c.sum()
    nz = p[p > 0]
    return float(-(nz * np.log2(nz)).sum())


def main():
    rng = np.random.default_rng(20260804)

    # settle one trajectory onto the attractor first, so t=0 is already on it
    s0 = np.array([1.0, 1.0, 20.0])
    for _ in range(8000):
        s0 = rk4(s0, DT)

    # A long run of the exact trajectory, drawn faintly behind every panel. Without it the
    # early frames are a dot in an empty box and the viewer cannot see WHERE the cloud is.
    sk = s0.copy()
    skel = np.empty((30000, 2))
    for i in range(30000):
        sk = rk4(sk, DT * 2)
        skel[i] = sk[0], sk[2]

    one = s0.copy()
    cloud = s0 + DOUBT * rng.standard_normal((N, 3))

    XLO, XHI = -25.0, 25.0
    centre, bits, times = [], [], []
    frames_one, frames_cloud = [], []

    s_one, s_cloud = one.copy(), cloud.copy()
    for f in range(FRAMES):
        times.append(f * SUB * DT)
        frames_one.append(s_one.copy())
        frames_cloud.append(s_cloud[:, [0, 2]].copy())
        centre.append(float(s_cloud[:, 0].mean()))
        bits.append(bits_missing(s_cloud[:, 0], XLO, XHI))
        for _ in range(SUB):
            s_one = rk4(s_one, DT)
            s_cloud = rk4(s_cloud, DT)

    centre, bits, times = np.array(centre), np.array(bits), np.array(times)

    # The SWING is the amplitude of the centre's travel, not its position: peak-to-peak of
    # the centre over a trailing window. A cloud that has stopped sloshing has a flat centre
    # and therefore zero swing, however far from the origin it happens to be parked.
    swing = np.array([np.ptp(centre[max(0, f - ENV_WIN):f + 1]) for f in range(FRAMES)])

    fig = plt.figure(figsize=(12.0, 8.4), facecolor=BG)
    gs = fig.add_gridspec(2, 2, height_ratios=[2.5, 1.0], hspace=0.34, wspace=0.16,
                          left=0.07, right=0.97, top=0.90, bottom=0.09)
    axL, axR = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    axS, axB = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])

    for a in (axL, axR):
        a.set_facecolor(BG); a.set_xlim(XLO, XHI); a.set_ylim(0, 52)
        a.set_xticks([]); a.set_yticks([])
        for sp in a.spines.values():
            sp.set_visible(False)
        a.plot(skel[:, 0], skel[:, 1], color=MUTED, lw=0.25, alpha=0.30, zorder=0)
    for a in (axS, axB):
        a.set_facecolor(BG); a.set_xlim(0, times[-1])
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
        a.tick_params(colors=INK, labelsize=9)
        a.set_xlabel("time", color=INK, fontsize=10)
    lim = np.abs(centre).max() * 1.15
    axS.set_ylim(-lim, lim); axB.set_ylim(0, CEILING * 1.05)
    axS.axhline(0, color=MUTED, lw=0.8)
    axB.axhline(CEILING, color=MUTED, lw=1.1, ls="--")
    axB.text(times[-1] * 0.02, CEILING * 0.955, "ceiling - the ruler has nothing left to say",
             color=MUTED, fontsize=8.5, va="top")

    axL.set_title("one exact butterfly", color=BLUE, fontsize=13, loc="left")
    axR.set_title(f"{N:,} copies, each started {DOUBT} off", color=AMBER, fontsize=13, loc="left")
    axS.set_title("where the cloud's centre is - it rings, then stops",
                  color=INK, fontsize=11, loc="left")
    axB.set_title("bits the observer is missing", color=INK, fontsize=11, loc="left")

    tail_ln, = axL.plot([], [], color=BLUE, lw=0.7, alpha=0.55)
    head_pt, = axL.plot([], [], "o", mfc="none", mec=BLUE, mew=1.8, ms=11, zorder=6)
    scat = axR.scatter([], [], s=0.7, c=AMBER, alpha=0.22, linewidths=0, rasterized=True)
    sw_ln, = axS.plot([], [], color=AMBER, lw=2.0)
    bt_ln, = axB.plot([], [], color=AMBER, lw=2.0)
    clock = fig.text(0.5, 0.945, "", ha="center", color=INK, fontsize=12)
    note = axR.text(0.03, 0.05, "", transform=axR.transAxes, color=RED, fontsize=11)

    tx, tz = [], []

    def update(f):
        s = frames_one[f]
        tx.append(s[0]); tz.append(s[2])
        tail_ln.set_data(tx[-900:], tz[-900:])
        head_pt.set_data([s[0]], [s[2]])
        scat.set_offsets(frames_cloud[f])
        sw_ln.set_data(times[:f + 1], centre[:f + 1])
        bt_ln.set_data(times[:f + 1], bits[:f + 1])
        clock.set_text(f"t = {times[f]:5.1f}")
        note.set_text("the cloud has stopped moving.\nthe butterfly on the left has not."
                      if times[f] > 8.0 else "")
        return tail_ln, head_pt, scat, sw_ln, bt_ln, clock, note

    def snapshot(path, picks):
        """Static fallback: three moments of the cloud plus the two finished traces."""
        f2 = plt.figure(figsize=(13.0, 7.4), facecolor=BG)
        g2 = f2.add_gridspec(2, 3, height_ratios=[2.2, 1.0], hspace=0.36, wspace=0.14,
                             left=0.05, right=0.97, top=0.88, bottom=0.10)
        caps = ["a dot - I nearly know where it is",
                "a streak, still sweeping wing to wing",
                "the whole butterfly, and no longer moving"]
        for i, fr in enumerate(picks):
            a = f2.add_subplot(g2[0, i]); a.set_facecolor(BG)
            a.set_xlim(XLO, XHI); a.set_ylim(0, 52); a.set_xticks([]); a.set_yticks([])
            for sp in a.spines.values():
                sp.set_visible(False)
            a.plot(skel[:, 0], skel[:, 1], color=MUTED, lw=0.25, alpha=0.30, zorder=0)
            pts = frames_cloud[fr]
            a.scatter(pts[:, 0], pts[:, 1], s=1.1, c=AMBER, alpha=0.30,
                      linewidths=0, rasterized=True, zorder=3)
            s1 = frames_one[fr]
            a.plot([s1[0]], [s1[2]], "o", mfc="none", mec=BLUE, mew=1.8, ms=11, zorder=6)
            a.set_title(f"t = {times[fr]:.1f}", color=INK, fontsize=13, loc="left")
            a.text(0.02, 0.02, caps[i], transform=a.transAxes, color=MUTED, fontsize=10)
        for j, (ys, ttl, sym) in enumerate(
                [(centre, "where the cloud's centre is - it rings, then stops", True),
                 (bits, "bits the observer is missing", False)]):
            a = f2.add_subplot(g2[1, j])
            a.set_facecolor(BG); a.set_xlim(0, times[-1]); a.plot(times, ys, color=AMBER, lw=1.7)
            for sp in ("top", "right"):
                a.spines[sp].set_visible(False)
            a.tick_params(colors=INK, labelsize=9); a.set_xlabel("time", color=INK, fontsize=10)
            a.set_title(ttl, color=INK, fontsize=11, loc="left")
            if sym:
                m = np.abs(centre).max() * 1.15
                a.set_ylim(-m, m); a.axhline(0, color=MUTED, lw=0.8)
            else:
                a.set_ylim(0, CEILING * 1.05); a.axhline(CEILING, color=MUTED, lw=1.1, ls="--")
        a3 = f2.add_subplot(g2[1, 2]); a3.set_facecolor(BG); a3.axis("off")
        a3.text(0.0, 0.86, "the butterfly never stops.", color=BLUE, fontsize=13)
        a3.text(0.0, 0.62, "my picture of it does.", color=RED, fontsize=13)
        a3.text(0.0, 0.30, "Nothing here has friction.\nNothing loses energy.\n"
                           "The one exact trajectory is\nstill going at the last frame.",
                color=MUTED, fontsize=10.5, va="top")
        f2.suptitle("A strange attractor stops the spread - and stops the wave with it",
                    color=INK, fontsize=15, x=0.05, ha="left")
        f2.savefig(path, dpi=150, facecolor=BG)
        plt.close(f2)
        print(f"wrote {path}")

    fig.text(0.07, 0.017,
             "Same equations, same parameters, both sides. The only difference is that the right "
             "side does not know exactly where it started.\nNothing here has friction and nothing "
             "loses energy - the trajectory on the left never slows down.",
             fontsize=9.5, color=MUTED)

    snapshot(HERE / "attractor_cloud.png", [FRAMES // 24, FRAMES // 5, FRAMES - 1])

    anim = FuncAnimation(fig, update, frames=FRAMES, blit=False)
    out = HERE / "attractor_cloud.gif"
    anim.save(out, writer=PillowWriter(fps=24), dpi=88)
    print(f"wrote {out}")

    peak = swing.max()
    tail = swing[-40:].mean()
    print(f"swing: peak {peak:.2f} -> tail {tail:.3f} ({100 * tail / peak:.1f}% of peak)")
    print(f"bits : {bits[0]:.3f} -> {bits[-1]:.3f} ({100 * bits[-1] / CEILING:.0f}% of ceiling)")
    below = np.where(swing[np.argmax(swing):] < 0.1 * peak)[0]
    if len(below):
        print(f"swing below 10% of peak from t = {times[np.argmax(swing) + below[0]]:.2f}")


if __name__ == "__main__":
    main()
