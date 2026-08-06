"""Figures for episode #5. Light theme: the Substack page is white."""

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

import engine as E

BG = "#faf8f4"
INK = "#1a1a1a"
MUTED = "#8a8580"
RED = "#c1362f"
BLUE = "#2f5fa8"
GREEN = "#2e7d4f"
AMBER = "#c98a1b"

C = json.load(open("metrics.json", encoding="utf-8"))
D = np.load("curves.npz")
F = np.load("frames.npz")
times = D["times"]

plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})

STYLE = {
    "harmonic":    (BLUE,  "a spring"),
    "double_low":  (GREEN, "a double pendulum, barely swinging"),
    "pendulum":    (AMBER, "a pendulum swung near the top"),
    "double_high": (RED,   "a double pendulum, swung hard"),
}


# ------------------------------------------------------------------ 1. the hero: a drum

def hero():
    modes = [(1, 0, "one lump"), (1, 1, "two lobes"),
             (2, 0, "a lump inside a ring"), (1, 2, "four petals")]
    fig, axes = plt.subplots(1, 4, figsize=(13.2, 3.7), facecolor=BG)
    for ax, (n, m, cap) in zip(axes, modes):
        X, Y, psi, k = E.bessel_mode(n, m)
        d = psi ** 2
        d = d / d.max()
        ax.set_facecolor(BG)
        ax.pcolormesh(X, Y, np.ma.masked_where(np.hypot(X, Y) > 1.0, d),
                      shading="auto", cmap="magma_r", vmin=0, vmax=1)
        ax.add_patch(plt.Circle((0, 0), 1.0, color=MUTED, fill=False, lw=1.1))
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(cap, color=INK, fontsize=11, pad=8)
    fig.text(0.5, 0.055, "the only distributions a round drum will hold still",
             color=MUTED, fontsize=11, ha="center")
    fig.subplots_adjust(0.01, 0.13, 0.99, 0.88, wspace=0.06)
    fig.savefig("hero_acoustic.png", dpi=160, facecolor=BG)
    plt.close(fig)
    print("hero_acoustic.png")


# --------------------------------------------------------------- 2. does it keep waving

def keeps_waving():
    fig, ax = plt.subplots(figsize=(8.6, 4.8), facecolor=BG)
    ax.set_facecolor(BG)
    for name in ("harmonic", "double_low", "pendulum", "double_high"):
        col, lab = STYLE[name]
        env = D[f"{name}_env"]
        ok = np.isfinite(env)
        ax.plot(times[ok], env[ok] / env[ok][0], color=col, lw=2.5, label=lab)
    ax.axhline(1 / np.e, color=MUTED, lw=1, ls=":")
    ax.text(302, 1 / np.e, "  1/e", color=MUTED, fontsize=9, va="center")
    ax.text(120, 1.10, "still waving", color=INK, fontsize=10.5)
    ax.text(202, 0.115, "the wave in the picture is gone", color=MUTED, fontsize=10.5)
    ax.set_xlabel("time")
    ax.set_ylabel("how far the distribution still swings\n(share of where it started)")
    ax.set_xlim(0, 300)
    ax.set_ylim(0, 1.20)
    ax.legend(frameon=False, loc="center right", fontsize=10,
              bbox_to_anchor=(1.0, 0.62))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig("keeps_waving.png", dpi=160, facecolor=BG)
    plt.close(fig)
    print("keeps_waving.png")


# ------------------------------------------------------------ 3. the missing information

def missing_information():
    ceil = C["systems"]["harmonic"]["entropy_ceiling_bits"]["64"]
    fig, ax = plt.subplots(figsize=(8.6, 4.8), facecolor=BG)
    ax.set_facecolor(BG)
    ax.axhline(ceil, color=MUTED, lw=1, ls=":")
    ax.text(4, ceil + 0.13, "the ceiling: everything this ruler can tell apart - 6 bits",
            color=MUTED, fontsize=9)
    for name in ("harmonic", "double_low", "pendulum", "double_high"):
        col, lab = STYLE[name]
        ax.plot(times, D[f"{name}_S64"], color=col, lw=2.5, label=lab)
    ax.plot(times, D["control_S64"], color=INK, lw=1.4, ls="--",
            label="the control: doubt removed - exactly zero, forever")
    ax.set_xlabel("time")
    ax.set_ylabel("what I am missing  (bits)")
    ax.set_xlim(0, 300)
    ax.set_ylim(-0.25, ceil + 0.7)
    ax.legend(frameon=False, loc="center left", fontsize=9.5,
              bbox_to_anchor=(0.30, 0.60))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig("missing_information.png", dpi=160, facecolor=BG)
    plt.close(fig)
    print("missing_information.png")


# ------------------------------------------------------------------- 4. the two clouds

def cloud_gif():
    step = 2                      # halve the frame count: the gif has to travel
    tl, xl = F["double_low_t"][::step], F["double_low_xy"][::step]
    th, xh = F["double_high_t"][::step], F["double_high_xy"][::step]
    n = min(len(tl), len(th))

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.9), facecolor=BG)
    caps = ("barely swinging - the cloud keeps its shape",
            "swung hard - the cloud fills everything it is allowed to")
    arts = []
    for ax, cap, col in zip(axes, caps, (GREEN, RED)):
        ax.set_facecolor(BG)
        ax.set_xlim(-2.15, 2.15)
        ax.set_ylim(-2.15, 1.35)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.add_patch(plt.Circle((0, 0), 2.0, color=MUTED, fill=False, lw=0.9, ls=":"))
        ax.scatter([0], [0], s=18, color=MUTED, zorder=5)
        sc = ax.scatter([], [], s=5.0, color=col, alpha=0.16, linewidths=0)
        ax.set_title(cap, color=col, fontsize=10.5, pad=6)
        arts.append(sc)
    clock = fig.text(0.5, 0.045, "", color=MUTED, fontsize=11, ha="center")

    def draw(i):
        arts[0].set_offsets(xl[i])
        arts[1].set_offsets(xh[i])
        clock.set_text(f"t = {tl[i]:5.1f}")
        return arts + [clock]

    fig.subplots_adjust(0.01, 0.10, 0.99, 0.91, wspace=0.02)
    ani = FuncAnimation(fig, draw, frames=range(n), blit=True)
    ani.save("cloud.gif", writer=PillowWriter(fps=12), dpi=84,
             savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    print("cloud.gif")


# ---------------------------------------------------------------------- 5. the drum beat

def drum_gif():
    period = C["drum"]["beat_period"]
    ts = np.linspace(0.0, period, 48, endpoint=False)
    dens = [E.two_mode(float(t))[2] for t in ts]
    X, Y, _, _ = E.two_mode(0.0)
    vmax = max(d.max() for d in dens)
    mask = np.hypot(X, Y) > 1.0

    fig, ax = plt.subplots(figsize=(4.9, 5.2), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_aspect("equal")
    ax.axis("off")
    im = ax.pcolormesh(X, Y, np.ma.masked_where(mask, dens[0]),
                       shading="auto", cmap="magma_r", vmin=0, vmax=vmax)
    ax.add_patch(plt.Circle((0, 0), 1.0, color=MUTED, fill=False, lw=1.1))
    ax.set_title("two notes at once, ringing forever", color=INK, fontsize=11.5, pad=10)
    cap = fig.text(0.5, 0.045, "", color=MUTED, fontsize=10, ha="center")

    def draw(i):
        im.set_array(np.ma.masked_where(mask, dens[i % len(dens)]).ravel())
        cap.set_text(f"beat {i / len(dens):4.2f} of 1 - and then it does it again")
        return [im, cap]

    fig.subplots_adjust(0.02, 0.10, 0.98, 0.92)
    ani = FuncAnimation(fig, draw, frames=range(len(dens)), blit=True)
    ani.save("drum.gif", writer=PillowWriter(fps=16), dpi=100,
             savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    print("drum.gif")


# ------------------------------------------------------------------- 6. the attractors

def attractors():
    A = np.load("attractor_curves.npz")
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.3), facecolor=BG)
    spec = [("lorenz", RED, "a strange attractor,\nno outside clock",
             "the ringing dies: 1% left"),
            ("driven", BLUE, "chaos riding on\na periodic drive",
             "it never stops: 57% left, forever")]
    for ax, (name, col, title, note) in zip(axes, spec):
        t, env = A[f"{name}_t"], A[f"{name}_env"]
        ok = np.isfinite(env)
        ax.set_facecolor(BG)
        ax.plot(t[ok], env[ok] / env[ok][0], color=col, lw=2.5)
        ax.axhline(1 / np.e, color=MUTED, lw=1, ls=":")
        ax.set_title(title, color=col, fontsize=11, pad=8)
        ax.set_xlabel("time")
        ax.set_ylim(0, 1.12)
        ax.set_xlim(0, t[ok][-1])
        ax.text(0.5, 0.86, note, transform=ax.transAxes, color=MUTED,
                fontsize=10, ha="center")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("how far the distribution still swings\n(share of where it started)")
    fig.tight_layout()
    fig.savefig("attractors.png", dpi=160, facecolor=BG)
    plt.close(fig)
    print("attractors.png")


if __name__ == "__main__":
    attractors()
    hero()
    keeps_waving()
    missing_information()
    drum_gif()
    cloud_gif()
