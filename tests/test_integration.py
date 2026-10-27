"""End-to-end test: a realistic mixed library through both data functions."""

from datetime import date

import export_reading_status as ers


def test_full_pipeline(make_db):
    books = {
        1:  {'timestamp': date(2023, 1, 15), '#gelesen': True,
             '#last_read': date(2023, 3, 1)},
        2:  {'timestamp': date(2023, 2, 10), '#gelesen': True,
             '#last_read': date(2023, 5, 20)},
        3:  {'timestamp': date(2023, 6, 1),  '#gelesen': False},
        4:  {'timestamp': date(2024, 1, 5),  '#gelesen': True,
             '#last_read': date(2024, 2, 15)},
        5:  {'timestamp': date(2024, 3, 20), '#gelesen': False},
        6:  {'timestamp': date(2024, 7, 1),  '#gelesen': True,
             '#last_read': date(2024, 9, 1)},
        7:  {'timestamp': date(2025, 1, 10), '#gelesen': False},
        8:  {'timestamp': date(2025, 5, 5),  '#gelesen': True,
             '#last_read': date(2025, 6, 1)},
        # edge cases:
        9:  {'#gelesen': True, '#last_read': date(2024, 1, 1)},     # no timestamp
        10: {'timestamp': date(2024, 4, 1), '#gelesen': True},      # read, no last_read
        11: {'timestamp': date(2024, 8, 1), '#gelesen': True,
             '#last_read': date(2023, 1, 1)},                       # inconsistent
    }
    db = make_db(books)

    info = ers.export_snapshots(db, today=date(2025, 10, 1))

    assert info['total'] == 10
    assert info['read'] == 7
    assert info['backlog'] == 3
    assert info['missing_timestamp'] == 1
    assert info['missing_last_read'] == 1
    assert info['last_read_before_added'] == 1

    rows = info['rows']
    assert rows[0][0] == date(2023, 1, 31)      # earliest event month
    assert rows[-1][0] == date(2025, 10, 1)     # clamped to "today"
    assert all(r[3] == r[1] - r[2] for r in rows)          # backlog = total - read
    assert all(rows[i][1] <= rows[i + 1][1]               # total monotonic
               for i in range(len(rows) - 1))

    fc = ers.forecast_backlog(rows)
    assert fc['status'] == ers.FORECAST_OK
    assert fc['months'] == 24
    assert fc['start'] == 3
