import fastf1
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# Setup cache
os.makedirs('f1_cache', exist_ok=True)
fastf1.Cache.enable_cache('f1_cache')

# F1 Points system
POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
          6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

# Sprint points system
SPRINT_POINTS = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4,
                 6: 3, 7: 2, 8: 1}

# 2026 races that took place
races = [
    'Australia', 'China', 'Japan',
    'Miami', 'Canada', 'Monaco',
    'Spain', 'Austria'
]

# Sprint races in 2026
sprint_races = ['China', 'Miami', 'Canada']

# Top drivers to track
top_drivers = ['RUS', 'ANT', 'LEC', 'HAM', 'VER', 'PIA', 'NOR']

driver_colors = {
    'RUS': '#00D2BE',
    'ANT': '#00A19C',
    'LEC': '#DC0000',
    'HAM': '#B0B0B0',
    'VER': '#FF8700',
    'PIA': '#FFD700',
    'NOR': '#FF4500',
}

print("Loading championship data...")

# Collect points per race per driver
championship = {driver: [] for driver in top_drivers}
race_labels = []

for race in races:
    try:
        session = fastf1.get_session(2026, race, 'R')
        session.load(telemetry=False, weather=False, messages=False)
        results = session.results[['Abbreviation', 'Position']].copy()
        results['Position'] = pd.to_numeric(results['Position'], errors='coerce')
        results['Points'] = results['Position'].map(POINTS).fillna(0)

        # Add sprint points if applicable
        sprint_pts = {driver: 0 for driver in top_drivers}
        if race in sprint_races:
            try:
                sprint = fastf1.get_session(2026, race, 'S')
                sprint.load(telemetry=False, weather=False, messages=False)
                sprint_results = sprint.results[['Abbreviation', 'Position']].copy()
                sprint_results['Position'] = pd.to_numeric(
                    sprint_results['Position'], errors='coerce')
                sprint_results['SprintPoints'] = sprint_results['Position'].map(
                    SPRINT_POINTS).fillna(0)
                for _, row in sprint_results.iterrows():
                    if row['Abbreviation'] in sprint_pts:
                        sprint_pts[row['Abbreviation']] = row['SprintPoints']
                print(f"  + Sprint points added for {race}")
            except Exception as e:
                print(f"  Sprint data unavailable for {race}: {e}")

        for driver in top_drivers:
            driver_result = results[results['Abbreviation'] == driver]
            race_pts = driver_result['Points'].values[0] if not driver_result.empty else 0
            total_pts = race_pts + sprint_pts[driver]
            championship[driver].append(total_pts)

        # Fix label — Austria shows as AUS clashing with Australia
        label = 'AUT' if race == 'Austria' else race[:3].upper()
        race_labels.append(label)
        print(f"Loaded {race}")

    except Exception as e:
        print(f"Skipped {race}: {e}")

# Calculate cumulative points
cumulative = {}
for driver in top_drivers:
    cumulative[driver] = np.cumsum(championship[driver])

# --- Plotting ---
fig, axes = plt.subplots(2, 1, figsize=(14, 12))
fig.suptitle('F1 2026 Championship Points Tracker\n(Race + Sprint Points)',
             fontsize=14, fontweight='bold')

x = range(len(race_labels))

# --- Plot 1: Cumulative points ---
ax1 = axes[0]
for driver in top_drivers:
    if len(cumulative[driver]) > 0:
        ax1.plot(x, cumulative[driver],
                 marker='o', linewidth=2.5,
                 color=driver_colors[driver],
                 label=f"{driver} ({int(cumulative[driver][-1])} pts)")
        ax1.annotate(driver,
                     (x[-1], cumulative[driver][-1]),
                     textcoords='offset points',
                     xytext=(8, 0), fontsize=9,
                     color=driver_colors[driver])

ax1.set_xticks(x)
ax1.set_xticklabels(race_labels, fontsize=10)
ax1.set_ylabel('Cumulative Points', fontsize=11)
ax1.set_title('Championship Standings Evolution — 2026 Season', fontsize=11)
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(True, alpha=0.3)

# --- Plot 2: Points per race ---
ax2 = axes[1]
width = 0.12
positions = np.arange(len(race_labels))

for i, driver in enumerate(top_drivers):
    if len(championship[driver]) > 0:
        offset = (i - len(top_drivers)/2) * width
        ax2.bar(positions + offset,
                championship[driver],
                width=width,
                color=driver_colors[driver],
                label=driver,
                edgecolor='none',
                alpha=0.85)

ax2.set_xticks(positions)
ax2.set_xticklabels(race_labels, fontsize=10)
ax2.set_ylabel('Points Scored', fontsize=11)
ax2.set_xlabel('Race', fontsize=11)
ax2.set_title('Points Scored Per Race (including Sprint)', fontsize=11)
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('championship_tracker.png', dpi=150, bbox_inches='tight')
plt.show()

# Print final standings
print("\n2026 Championship Standings (after Austria):")
standings = [(driver, int(cumulative[driver][-1]))
             for driver in top_drivers if len(cumulative[driver]) > 0]
standings.sort(key=lambda x: x[1], reverse=True)
for i, (driver, pts) in enumerate(standings, 1):
    print(f"P{i}: {driver} — {pts} pts")
