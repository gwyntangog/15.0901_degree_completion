import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

# Load your master data
master_df = pd.read_csv('master_all_CIPs_2021-2025.csv')

# ===== TIME SERIES 1: National Completions by CIP Over Time =====
fig, ax = plt.subplots(figsize=(12, 6))

national_by_cip = master_df.groupby(['Year', 'CIP_Code', 'CIP_Title'])['Completions'].sum().reset_index()

for cip in national_by_cip['CIP_Code'].unique():
    data = national_by_cip[national_by_cip['CIP_Code'] == cip]
    title = data['CIP_Title'].iloc[0]
    ax.plot(data['Year'], data['Completions'], marker='o', linewidth=2, label=f"{cip} - {title}", markersize=8)

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Completions', fontsize=12)
ax.set_title('Mining & Petroleum Completions by CIP Code (2021-2025)', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('timeseries_by_cip.png', dpi=300, bbox_inches='tight')
print("✓ Saved: timeseries_by_cip.png")
plt.show()

# ===== TIME SERIES 2: National Completions by Award Level Over Time =====
fig, ax = plt.subplots(figsize=(14, 7))

national_by_award = master_df.groupby(['Year', 'Award_Level'])['Completions'].sum().reset_index()

for award in national_by_award['Award_Level'].unique():
    data = national_by_award[national_by_award['Award_Level'] == award]
    ax.plot(data['Year'], data['Completions'], marker='s', linewidth=2, label=award, markersize=8)

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Completions', fontsize=12)
ax.set_title('Completions by Award Level (2021-2025)', fontsize=14, fontweight='bold')
ax.legend(fontsize=9, loc='best')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('timeseries_by_award.png', dpi=300, bbox_inches='tight')
print("✓ Saved: timeseries_by_award.png")
plt.show()

# ===== TIME SERIES 3: Top Schools Over Time =====
fig, ax = plt.subplots(figsize=(14, 7))

# Get top 5 schools by total completions
top_schools = master_df.groupby('Institution')['Completions'].sum().nlargest(5).index

for school in top_schools:
    data = master_df[master_df['Institution'] == school].groupby('Year')['Completions'].sum().reset_index()
    ax.plot(data['Year'], data['Completions'], marker='o', linewidth=2, label=school, markersize=8)

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Completions', fontsize=12)
ax.set_title('Top 5 Schools: Completions Trends (2021-2025)', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('timeseries_top_schools.png', dpi=300, bbox_inches='tight')
print("✓ Saved: timeseries_top_schools.png")
plt.show()

# # ===== HEATMAP 1: Schools × Years =====
# fig, ax = plt.subplots(figsize=(10, 12))

# # Pivot: Schools as rows, Years as columns
# schools_by_year = master_df.groupby(['Institution', 'Year'])['Completions'].sum().unstack(fill_value=0)

# sns.heatmap(schools_by_year, annot=True, fmt='d', cmap='YlOrRd', cbar_kws={'label': 'Completions'}, ax=ax)
# ax.set_title('Completions Heatmap: Schools × Years', fontsize=14, fontweight='bold')
# ax.set_xlabel('Year', fontsize=12)
# ax.set_ylabel('Institution', fontsize=12)
# plt.tight_layout()
# plt.savefig('heatmap_schools_years.png', dpi=300, bbox_inches='tight')
# print("✓ Saved: heatmap_schools_years.png")
# plt.show()

# # ===== HEATMAP 2: CIP Code × Award Level =====
# fig, ax = plt.subplots(figsize=(12, 5))

# # Pivot: CIPs as rows, Award Levels as columns
# cip_by_award = master_df.groupby(['CIP_Code', 'Award_Level'])['Completions'].sum().unstack(fill_value=0)

# sns.heatmap(cip_by_award, annot=True, fmt='d', cmap='Blues', cbar_kws={'label': 'Completions'}, ax=ax)
# ax.set_title('Completions Heatmap: CIP Code × Award Level', fontsize=14, fontweight='bold')
# ax.set_xlabel('Award Level', fontsize=12)
# ax.set_ylabel('CIP Code', fontsize=12)
# plt.xticks(rotation=45, ha='right')
# plt.tight_layout()
# plt.savefig('heatmap_cip_award.png', dpi=300, bbox_inches='tight')
# print("✓ Saved: heatmap_cip_award.png")
# plt.show()

# # ===== HEATMAP 3: Schools × CIPs (Latest Year) =====
# fig, ax = plt.subplots(figsize=(10, 12))

# latest_year = master_df['Year'].max()
# latest_data = master_df[master_df['Year'] == latest_year]

# schools_by_cip = latest_data.groupby(['Institution', 'CIP_Code'])['Completions'].sum().unstack(fill_value=0)

# sns.heatmap(schools_by_cip, annot=True, fmt='d', cmap='Greens', cbar_kws={'label': 'Completions'}, ax=ax)
# ax.set_title(f'Completions Heatmap: Schools × CIP ({latest_year})', fontsize=14, fontweight='bold')
# ax.set_xlabel('CIP Code', fontsize=12)
# ax.set_ylabel('Institution', fontsize=12)
# plt.tight_layout()
# plt.savefig('heatmap_schools_cips_latest.png', dpi=300, bbox_inches='tight')
# print("✓ Saved: heatmap_schools_cips_latest.png")
# plt.show()

# # ===== HEATMAP 4: Award Level × Year (National) =====
# fig, ax = plt.subplots(figsize=(8, 6))

# award_by_year = master_df.groupby(['Award_Level', 'Year'])['Completions'].sum().unstack(fill_value=0)

# sns.heatmap(award_by_year, annot=True, fmt='d', cmap='Purples', cbar_kws={'label': 'Completions'}, ax=ax)
# ax.set_title('Completions Heatmap: Award Level × Year (National)', fontsize=14, fontweight='bold')
# ax.set_xlabel('Year', fontsize=12)
# ax.set_ylabel('Award Level', fontsize=12)
# plt.tight_layout()
# plt.savefig('heatmap_award_year.png', dpi=300, bbox_inches='tight')
# print("✓ Saved: heatmap_award_year.png")
# plt.show()

print("\n✓ All visualizations complete!")
