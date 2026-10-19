import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =============================================================================
# SETUP
# =============================================================================
sns.set_style("whitegrid")

# Padded national data (one row per Year / CIP / Award Level, zeros filled in)
master_df = pd.read_csv('master_all_CIPs_2021-2025.csv', dtype={'CIP_Code': str})

# School-level data (has UnitID and Institution, used for the top schools plot)
school_df = pd.read_csv('school_level_clean_2021-2025.csv', dtype={'CIP_Code': str})

all_years = sorted(master_df['Year'].unique())


# =============================================================================
# TIME SERIES 1: National completions by CIP over time
# =============================================================================
fig, ax = plt.subplots(figsize=(12, 6))

# Add up all award levels for each CIP in each year
national_by_cip = (
    master_df.groupby(['Year', 'CIP_Code', 'CIP_Title'], as_index=False)['Completions']
    .sum()
)

# One line per CIP, sorted so the legend order is predictable
for cip in sorted(national_by_cip['CIP_Code'].unique()):
    data = national_by_cip[national_by_cip['CIP_Code'] == cip].sort_values('Year')
    title = data['CIP_Title'].iloc[0]
    ax.plot(data['Year'], data['Completions'], marker='o', linewidth=2,
            markersize=8, label=f"{cip} - {title}")

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Completions', fontsize=12)
ax.set_title('Mining & Petroleum Completions by CIP Code (2021-2025)',
             fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('timeseries_by_cip.png', dpi=300, bbox_inches='tight')
print("✓ Saved: timeseries_by_cip.png")
plt.show()
plt.close(fig)


# =============================================================================
# TIME SERIES 2: National completions by award level over time
# =============================================================================
fig, ax = plt.subplots(figsize=(14, 7))

# Add up all CIPs for each award level in each year
national_by_award = (
    master_df.groupby(['Year', 'Award_Level'], as_index=False)['Completions']
    .sum()
)

# One line per award level
for award in sorted(national_by_award['Award_Level'].unique()):
    data = national_by_award[national_by_award['Award_Level'] == award].sort_values('Year')
    ax.plot(data['Year'], data['Completions'], marker='s', linewidth=2,
            markersize=8, label=award)

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Completions', fontsize=12)
ax.set_title('Completions by Award Level (2021-2025)', fontsize=14, fontweight='bold')
ax.legend(fontsize=9, loc='best')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('timeseries_by_award.png', dpi=300, bbox_inches='tight')
print("✓ Saved: timeseries_by_award.png")
plt.show()
plt.close(fig)


# =============================================================================
# TIME SERIES 3: Top 5 schools over time
# =============================================================================
fig, ax = plt.subplots(figsize=(14, 7))

# Top 5 schools by total completions across all programs and years.
# Group by UnitID too, so two schools with the same name stay separate.
top_schools = (
    school_df.groupby(['UnitID', 'Institution'], as_index=False)['Completions']
    .sum()
    .nlargest(5, 'Completions')
)

for _, school in top_schools.iterrows():
    # Yearly totals for this school. Years with no data show as 0.
    data = (
        school_df[school_df['UnitID'] == school['UnitID']]
        .groupby('Year')['Completions'].sum()
        .reindex(all_years, fill_value=0)
    )
    ax.plot(all_years, data.values, marker='o', linewidth=2,
            markersize=8, label=school['Institution'])

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Completions', fontsize=12)
ax.set_title('Top 5 Schools: Completions Trends (2021-2025)',
             fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('timeseries_top_schools.png', dpi=300, bbox_inches='tight')
print("✓ Saved: timeseries_top_schools.png")
plt.show()
plt.close(fig)


print("\n✓ All visualizations complete!")
