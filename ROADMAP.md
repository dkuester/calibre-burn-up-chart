# Roadmap

*[Deutsche Version](ROADMAP.de.md)*

What is planned for the plugin and which ideas are open, grouped by
effort and value: quick wins first, then high priority, then optional
extras. Nothing here has a fixed version. What has shipped is in the
[changelog](CHANGELOG.md).

Priorities follow a simple rule: **maintenance and quality before new
features**. A feature that breaks existing code costs more than it is
worth.

## Quick wins

### Books read per year

A bar chart of the books read per year. Shows the long-term trend at a
glance, which the 12-month averages in "Purchase rate vs. reading rate"
smooth away. The monthly counts already exist; only the yearly sum and
a dialog are missing. Effort: small.

## High priority

### Genre and category breakdown

Books read and unread by calibre tag. Shows which genres pile up in the
TBR. Needs the tags in the data export first. Effort: medium.

## Low priority (optional)

### Pages in the TBR *(optional)*

Pages in the TBR, from a configurable page-count column (pages read per
month are already in the report's "Reading speed"). Calibre 9.3.1 ships
a "Pages" column; a custom column (e.g. from the Count Pages plugin) can
be configured instead. Effort: small.

### Reading speed on the chart *(optional)*

Show the reading speed (pages per month and per day) in the burn-up
chart or the "purchase rate vs. reading rate" dialog, not only in the
report. The figures already exist (the report's "Reading speed").
Effort: small.
