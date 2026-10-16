#!/usr/bin/env python3
"""
Creates the plugin icon (burn-up chart motif) as a PNG.

Run with: /opt/homebrew/bin/python3 make_icon.py
Result:   readingprogress/images/icon.png (256×256)
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, 'readingprogress', 'images', 'icon.png')
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

SIZE_PX = 256
DPI = 100

fig = plt.figure(figsize=(SIZE_PX / DPI, SIZE_PX / DPI), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 64)
ax.set_ylim(0, 64)
ax.axis('off')

# Background: rounded square in dark blue
bg = FancyBboxPatch(
    (0.8, 0.8), 62.4, 62.4,
    boxstyle="round,pad=0,rounding_size=13",
    facecolor="#264653", edgecolor="none",
)
ax.add_patch(bg)

# Suggested axes
ax.plot([13, 13], [11, 50], color='white', lw=1.6, alpha=0.30,
        solid_capstyle='round')
ax.plot([13, 52], [11, 11], color='white', lw=1.6, alpha=0.30,
        solid_capstyle='round')

# Rising line (burn-up)
xs = [17, 25, 33, 41, 49]
ys = [18, 25, 33, 41, 50]
ax.plot(xs, ys, color='#2a9d8f', lw=4.5, solid_capstyle='round',
        solid_joinstyle='round', zorder=3)

# Data points
for x, y in zip(xs, ys):
    ax.scatter([x], [y], s=42, color='white', zorder=4,
               edgecolors='#2a9d8f', linewidths=1.8)

fig.savefig(OUTPUT, dpi=DPI, transparent=True)
plt.close(fig)
print(f"Icon written: {OUTPUT}")
