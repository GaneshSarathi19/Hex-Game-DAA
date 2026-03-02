"""
Complexity Stats UI for Hex Game.
Displays per-strategy session statistics in a pygame UI table and
provides a button to open the matplotlib time complexity graph.
"""

import json
from datetime import datetime

import pygame as pg

from consts import W, H, WHITE, BLACK, ORANGE, LIGHTYELLOW, GREEN, BLUE, YELLOW
from funcs import textOut
from time_complexity_dashboard import show_time_complexity_dashboard


def _load_stats():
    """Load session-based stats from cpu_performance_log.json and aggregate per strategy."""
    log_file = 'cpu_performance_log.json'
    try:
        with open(log_file, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    if not isinstance(data, list):
        data = []

    strategies = ['Greedy', 'D&C', 'DP', 'Backtracking']
    stats = {
        s: {
            'last': None,
            'best': None,
            'worst': None,
            'count': 0,
        }
        for s in strategies
    }

    for entry in data:
        s = entry.get('strategy')
        if s not in stats:
            continue
        t_val = entry.get('avg_execution_time', entry.get('execution_time'))
        if not isinstance(t_val, (int, float)):
            continue
        # Incremental aggregation; assume file is append-only in time order.
        st = stats[s]
        st['count'] += 1
        st['last'] = t_val
        if st['best'] is None or t_val < st['best']:
            st['best'] = t_val
        if st['worst'] is None or t_val > st['worst']:
            st['worst'] = t_val

    return stats


def show_complexity_stats_ui(screen):
    """
    Show a simple pygame UI with session stats per strategy.
    Uses the existing screen surface (Game.screen).
    """
    clock = pg.time.Clock()
    running = True

    # Precompute button rects
    back_rect = pg.Rect(50, H - 70, 140, 40)
    graph_rect = pg.Rect(W - 190, H - 70, 140, 40)

    while running:
        clock.tick(30)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                # Let caller handle global quit; just return
                running = False
                return
            elif event.type == pg.MOUSEBUTTONDOWN:
                mx, my = pg.mouse.get_pos()
                if back_rect.collidepoint(mx, my):
                    running = False
                    return
                if graph_rect.collidepoint(mx, my):
                    show_time_complexity_dashboard()

        # Load stats each frame in case file is updated between sessions
        stats = _load_stats()

        # Draw background
        screen.fill(BLACK)

        # Title
        textOut(screen, 'CPU Strategy Complexity Stats', 36, ORANGE, (W // 2, 60))

        # Table header
        header_y = 120
        col_x = [80, 260, 430, 600, 770]  # approximate column centers
        textOut(screen, 'Strategy', 26, LIGHTYELLOW, (col_x[0], header_y))
        textOut(screen, 'Last Avg (s)', 26, LIGHTYELLOW, (col_x[1], header_y))
        textOut(screen, 'Best (s)', 26, LIGHTYELLOW, (col_x[2], header_y))
        textOut(screen, 'Worst (s)', 26, LIGHTYELLOW, (col_x[3], header_y))
        textOut(screen, 'Sessions', 26, LIGHTYELLOW, (col_x[4], header_y))

        # Horizontal line under header
        pg.draw.line(screen, WHITE, (40, header_y + 15), (W - 40, header_y + 15), 1)

        # Table rows
        row_y_start = header_y + 45
        row_h = 45
        row_idx = 0
        for strategy, color in [
            ('Greedy', GREEN),
            ('D&C', BLUE),
            ('DP', YELLOW),
            ('Backtracking', ORANGE),
        ]:
            st = stats.get(strategy, {})
            y = row_y_start + row_idx * row_h
            last = st.get('last')
            best = st.get('best')
            worst = st.get('worst')
            count = st.get('count', 0)

            def fmt(val):
                return f'{val:.6f}' if isinstance(val, (int, float)) else 'N/A'

            textOut(screen, strategy, 24, color, (col_x[0], y))
            textOut(screen, fmt(last), 22, WHITE, (col_x[1], y))
            textOut(screen, fmt(best), 22, WHITE, (col_x[2], y))
            textOut(screen, fmt(worst), 22, WHITE, (col_x[3], y))
            textOut(screen, str(count), 22, WHITE, (col_x[4], y))

            row_idx += 1

        # Buttons
        pg.draw.rect(screen, ORANGE, back_rect, border_radius=6)
        textOut(screen, 'Back', 24, BLACK, back_rect.center)

        pg.draw.rect(screen, LIGHTYELLOW, graph_rect, border_radius=6)
        textOut(screen, 'Open Graph', 24, BLACK, graph_rect.center)

        pg.display.flip()