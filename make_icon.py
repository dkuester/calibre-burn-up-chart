#!/usr/bin/env python3
"""
Erzeugt das Plugin-Icon (Burn-up-Chart-Motiv) als PNG.

Ausführen mit: /opt/homebrew/bin/python3 make_icon.py
Ergebnis:      lesefortschritt/images/icon.png (256×256)
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


HIER = os.path.dirname(os.path.abspath(__file__))
AUSGABE = os.path.join(HIER, 'lesefortschritt', 'images', 'icon.png')
os.makedirs(os.path.dirname(AUSGABE), exist_ok=True)

GROESSE_PX = 256
DPI = 100

fig = plt.figure(figsize=(GROESSE_PX / DPI, GROESSE_PX / DPI), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 64)
ax.set_ylim(0, 64)
ax.axis('off')

# Hintergrund: abgerundetes Quadrat in Dunkelblau
bg = FancyBboxPatch(
    (0.8, 0.8), 62.4, 62.4,
    boxstyle="round,pad=0,rounding_size=13",
    facecolor="#264653", edgecolor="none",
)
ax.add_patch(bg)

# Angedeutete Achsen
ax.plot([13, 13], [11, 50], color='white', lw=1.6, alpha=0.30,
        solid_capstyle='round')
ax.plot([13, 52], [11, 11], color='white', lw=1.6, alpha=0.30,
        solid_capstyle='round')

# Steigende Linie (Burn-up)
xs = [17, 25, 33, 41, 49]
ys = [18, 25, 33, 41, 50]
ax.plot(xs, ys, color='#2a9d8f', lw=4.5, solid_capstyle='round',
        solid_joinstyle='round', zorder=3)

# Datenpunkte
for x, y in zip(xs, ys):
    ax.scatter([x], [y], s=42, color='white', zorder=4,
               edgecolors='#2a9d8f', linewidths=1.8)

fig.savefig(AUSGABE, dpi=DPI, transparent=True)
plt.close(fig)
print(f"Icon erzeugt: {AUSGABE}")
