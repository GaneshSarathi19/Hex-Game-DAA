"""
CPU Strategy Time Complexity Dashboard.
Reads cpu_performance_log.json and plots avg_execution_time vs session index.
"""
import json
from collections import defaultdict


def show_time_complexity_dashboard():
    """Read log file, group by strategy, plot all on same graph. Opens matplotlib window."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed. Run: pip install matplotlib")
        return

    log_file = 'cpu_performance_log.json'
    try:
        with open(log_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
    except json.JSONDecodeError:
        data = []

    if not isinstance(data, list):
        data = []

    if not data:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_title('CPU Strategy Time Complexity Comparison')
        ax.set_xlabel('Session Number')
        ax.set_ylabel('Average CPU Execution Time (milliseconds)')
        ax.text(0.5, 0.5, 'No performance data yet.\nPlay some games to log execution times.',
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        plt.tight_layout()
        plt.show()
        return

    # Group by strategy using ONLY session-based entries, preserving file order
    by_strategy = defaultdict(list)
    for entry in data:
        s = entry.get('strategy', 'Unknown')
        et = entry.get('avg_execution_time', None)
        if isinstance(et, (int, float)):
            by_strategy[s].append(et)

    if not by_strategy:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_title('CPU Strategy Time Complexity Comparison')
        ax.set_xlabel('Session Number')
        ax.set_ylabel('Average CPU Execution Time (milliseconds)')
        ax.text(0.5, 0.5, 'No valid performance data.',
                ha='center', va='center', fontsize=14, transform=ax.transAxes)
        plt.tight_layout()
        plt.show()
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = {'Greedy': 'green', 'D&C': 'blue', 'DP': 'gold', 'Backtracking': 'orange'}
    for strategy in ('Greedy', 'D&C', 'DP', 'Backtracking'):
        if strategy not in by_strategy:
            continue
        times = by_strategy[strategy]
        if not times:
            continue
        # Convert seconds to milliseconds for finer scale on Y-axis
        times_ms = [t * 1000.0 for t in times]
        x = list(range(1, len(times_ms) + 1))
        ax.plot(x, times_ms, 'o-', label=strategy, color=colors.get(strategy, 'gray'))

    ax.set_title('CPU Strategy Time Complexity Comparison')
    ax.set_xlabel('Session Number')
    ax.set_ylabel('Average CPU Execution Time (milliseconds)')
    ax.legend()
    plt.tight_layout()
    plt.show()