import os
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# =============================================================================
# SETUP
# =============================================================================
OUTPUT_ROOT = 'line_plots'

# One subfolder per plot type
FOLDERS = {
    'cip_by_award': 'cip_by_award_lines',         # Plot 1
    'cip_award_single': 'cip_award_single_lines', # Plot 2
    'cip_stacked': 'cip_stacked_area',            # Plot 3
    'all_cips': 'all_cips_comparison',            # Plot 4
}

sns.set_style("whitegrid")

master_df = pd.read_csv('master_all_CIPs_2021-2025.csv', dtype={'CIP_Code': str})

all_cips = sorted(master_df['CIP_Code'].unique())
all_awards = sorted(master_df['Award_Level'].dropna().unique())
all_years = sorted(master_df['Year'].unique())

# CIP code -> title, for titles and legends
cip_titles = master_df.drop_duplicates('CIP_Code').set_index('CIP_Code')['CIP_Title'].to_dict()

# Create every output folder up front
for folder in FOLDERS.values():
    os.makedirs(os.path.join(OUTPUT_ROOT, folder), exist_ok=True)


# =============================================================================
# HELPERS
# =============================================================================
def safe_name(text):
    """Turn a label into a filename-safe string."""
    return re.sub(r'[^A-Za-z0-9]+', '_', str(text)).strip('_')


def save_figure(fig, folder, filename):
    """Save a figure as a 300 dpi PNG inside OUTPUT_ROOT/folder, then close it."""
    path = os.path.join(OUTPUT_ROOT, folder, filename)
    fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"✓ Saved: {path}")


def cip_award_year_totals(cip):
    """Completions for one CIP, summed by award level and year."""
    cip_df = master_df[master_df['CIP_Code'] == cip]
    return cip_df.groupby(['Year', 'Award_Level'], as_index=False)['Completions'].sum()


# =============================================================================
# PLOT 1: One chart per CIP, one line per award level
# =============================================================================
for cip in all_cips:
    cip_title = cip_titles[cip]
    data = cip_award_year_totals(cip)

    fig, ax = plt.subplots(figsize=(12, 7))
    for award in sorted(data['Award_Level'].unique()):
        award_data = data[data['Award_Level'] == award].sort_values('Year')
        ax.plot(award_data['Year'], award_data['Completions'], marker='o',
                linewidth=2.5, markersize=8, label=award)

    ax.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Completions', fontsize=12, fontweight='bold')
    ax.set_title(f'{cip} - {cip_title}\nCompletions by Award Level (2021-2025)',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(all_years)
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    save_figure(fig, FOLDERS['cip_by_award'], f'lineplot_{safe_name(cip)}_all_awards.png')


# =============================================================================
# PLOT 2: One chart per CIP x award level
# =============================================================================
for cip in all_cips:
    cip_title = cip_titles[cip]
    data = cip_award_year_totals(cip)

    for award in all_awards:
        award_data = data[data['Award_Level'] == award].sort_values('Year')

        # Skip combinations with no completions in any year
        if award_data.empty or award_data['Completions'].sum() == 0:
            continue

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(award_data['Year'], award_data['Completions'], marker='o',
                linewidth=3, markersize=10, color='#2E86AB')
        ax.fill_between(award_data['Year'], award_data['Completions'],
                        alpha=0.3, color='#2E86AB')

        ax.set_xlabel('Year', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Completions', fontsize=12, fontweight='bold')
        ax.set_title(f'{cip} - {cip_title}\n{award}', fontsize=14, fontweight='bold')
        ax.set_xticks(all_years)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        save_figure(fig, FOLDERS['cip_award_single'],
                    f'lineplot_{safe_name(cip)}_{safe_name(award)}.png')


# =============================================================================
# PLOT 3: One stacked area chart per CIP
# =============================================================================
for cip in all_cips:
    cip_title = cip_titles[cip]
    data = cip_award_year_totals(cip)

    pivot = data.pivot(index='Year', columns='Award_Level', values='Completions').fillna(0)

    # Drop award levels that are zero in every year, so the legend stays clean
    pivot = pivot.loc[:, pivot.sum() > 0]
    if pivot.empty:
        continue

    fig, ax = plt.subplots(figsize=(12, 7))
    pivot.plot(kind='area', stacked=True, ax=ax, alpha=0.7)

    ax.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Completions', fontsize=12, fontweight='bold')
    ax.set_title(f'{cip} - {cip_title}\nCompletions by Award Level (Stacked)',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(all_years)
    ax.legend(title='Award Level', fontsize=9, loc='best')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    save_figure(fig, FOLDERS['cip_stacked'], f'stacked_area_{safe_name(cip)}.png')


# =============================================================================
# PLOT 4: All CIPs on one chart, total completions by year
# =============================================================================
fig, ax = plt.subplots(figsize=(12, 7))

for cip in all_cips:
    data = (
        master_df[master_df['CIP_Code'] == cip]
        .groupby('Year', as_index=False)['Completions'].sum()
        .sort_values('Year')
    )
    ax.plot(data['Year'], data['Completions'], marker='s', linewidth=2.5,
            markersize=8, label=f"{cip} - {cip_titles[cip]}")

ax.set_xlabel('Year', fontsize=12, fontweight='bold')
ax.set_ylabel('Total Completions', fontsize=12, fontweight='bold')
ax.set_title('All CIP Codes: Total Completions Over Time (2021-2025)',
             fontsize=14, fontweight='bold')
ax.set_xticks(all_years)
ax.legend(fontsize=10, loc='best')
ax.grid(True, alpha=0.3)
fig.tight_layout()

save_figure(fig, FOLDERS['all_cips'], 'lineplot_all_cips_comparison.png')


print(f"\n✓ All line plots saved under '{OUTPUT_ROOT}/'.")
