import pandas as pd
import re

years = [2021, 2022, 2023, 2024, 2025]
target_cips = ['14.2101', '15.0901', '15.0999']

all_data = []

for year in years:
    print(f"\nProcessing {year}...")

    # Load files
    inst_file = f"{year}_institutions.csv"
    comp_file = f"{year}_completions.csv"

    inst_df = pd.read_csv(inst_file)
    comp_df = pd.read_csv(comp_file)

    print(f"  Completions rows: {len(comp_df)}")

    # Find dynamic column names
    state_col = [col for col in inst_df.columns if 'State abbreviation' in col][0]
    comp_col = [col for col in comp_df.columns if 'Grand total' in col and 'male' not in col.lower() and 'female' not in col.lower()][0]
    cip_col = [col for col in comp_df.columns if 'CIP Code' in col and 'Classification' in col][0]
    award_col = [col for col in comp_df.columns if 'Award Level code' in col][0]

    print(f"  State col: {state_col}")
    print(f"  Completions col: {comp_col}")

    # Merge
    merged = pd.merge(
        comp_df,
        inst_df[['unitid', state_col]],
        on='unitid',
        how='left'
    )

    # Rename for standardization
    merged = merged.rename(columns={
        state_col: 'State',
        comp_col: 'Completions',
        cip_col: 'CIP_Code',
        award_col: 'Award_Level'
    })

    all_data.append(merged)
    print(f"  Merged rows: {len(merged)}")

# Combine all years
master_df = pd.concat(all_data, ignore_index=True)
print(f"\n✓ Total rows combined: {len(master_df)}")

# Clean CIP codes (remove quotes)
master_df['CIP_Code'] = master_df['CIP_Code'].str.replace("'", "").str.strip()

# Filter for target CIPs
master_df = master_df[master_df['CIP_Code'].isin(target_cips)].copy()
print(f"✓ Rows with target CIPs: {len(master_df)}")

# ===== AWARD LEVEL HIERARCHY MAPPING =====
# This defines which award levels are AGGREGATES (sum of others)
# Use this to filter out double-counting
AWARD_HIERARCHY = {
    'aggregates': [
        'Degrees/certificates total',
        'Degrees total',
        'Certificates below the baccalaureate total',
        'Certificates of less than 1 year',  # ← YOU HAVE THIS - it's an aggregate!
        'Certificates above the baccalaureate total',
    ],
    'specific_degrees': [
        "Associate's degree",
        "Bachelor's degree",
        "Master's degree",
        "Doctor's degree - research/scholarship",
        "Doctor's degree - professional practice",
        "Doctor's degree - other",
    ],
    'specific_certificates': [
        'Certificates of less than 12 weeks',
        'Certificates of at least 12 weeks but less than 1 year',
        'Certificates of at least 1 but less than 2 years',
        'Certificates of at least 2 but less than 4 years',
        'Postbaccalaureate certificate',
        "Post-master's certificate",
    ]
}

# Define all SPECIFIC (non-aggregate) awards
SPECIFIC_AWARDS = AWARD_HIERARCHY['specific_degrees'] + AWARD_HIERARCHY['specific_certificates']

# ===== FILTER OUT AGGREGATES =====
print("\nAward levels in data BEFORE filtering:")
print(master_df['Award_Level'].unique())

# Remove aggregates
master_df = master_df[~master_df['Award_Level'].isin(AWARD_HIERARCHY['aggregates'])].copy()

print("\nAward levels in data AFTER filtering:")
print(master_df['Award_Level'].unique())
print(f"Rows after filtering aggregates: {len(master_df)}\n")

# Keep only needed columns
master_df = master_df[[
    'year',
    'unitid',
    'institution name',
    'State',
    'CIP_Code',
    'CipTitle',
    'Award_Level',
    'Completions'
]].copy()

master_df.columns = [
    'Year',
    'UnitID',
    'Institution',
    'State',
    'CIP_Code',
    'CIP_Title',
    'Award_Level',
    'Completions'
]

# Convert completions to numeric (handle any missing)
master_df['Completions'] = pd.to_numeric(master_df['Completions'], errors='coerce').fillna(0).astype(int)

master_df.to_csv('master_all_CIPs_2021-2025.csv', index=False)
print("✓ Saved: master_all_CIPs_2021-2025.csv\n")

# ===== SUMMARY BY CIP & SCHOOL =====
latest_year = master_df['Year'].max()
three_year_start = latest_year - 2

# Get latest year data
latest = master_df[master_df['Year'] == latest_year].groupby(['UnitID', 'Institution', 'State', 'CIP_Code', 'CIP_Title'])['Completions'].sum().rename('Latest_Year_Completions')

# Get 3-year average
three_year_avg = master_df[master_df['Year'] >= three_year_start].groupby(['UnitID', 'Institution', 'State', 'CIP_Code', 'CIP_Title'])['Completions'].mean().round(1).rename('Three_Year_Avg_Completions')

# Combine
summary = pd.concat([latest, three_year_avg], axis=1).reset_index()
summary = summary.fillna(0)
summary['Latest_Year_Completions'] = summary['Latest_Year_Completions'].astype(int)
summary = summary.sort_values(['CIP_Code', 'Latest_Year_Completions'], ascending=[True, False])

summary.to_csv('summary_by_cip_and_school.csv', index=False)
print("✓ Saved: summary_by_cip_and_school.csv\n")

print("="*100)
print("SUMMARY BY CIP & SCHOOL (Latest Year & 3-Year Average)")
print("="*100)
print(summary.to_string(index=False))

# ===== NATIONAL TOTALS BY CIP & AWARD =====
national = master_df.groupby(['Year', 'CIP_Code', 'CIP_Title', 'Award_Level'])['Completions'].sum().reset_index()
national = national.sort_values(['CIP_Code', 'Year', 'Award_Level'])
national.to_csv('national_totals_by_cip_award_year.csv', index=False)
print("\n\n✓ Saved: national_totals_by_cip_award_year.csv\n")

print("="*100)
print("NATIONAL TOTALS BY CIP (All Years)")
print("="*100)
for cip in target_cips:
    cip_data = national[national['CIP_Code'] == cip]
    cip_title = cip_data['CIP_Title'].iloc[0]
    print(f"\n{cip} - {cip_title}:")
    print(cip_data.pivot_table(index='Year', columns='Award_Level', values='Completions', fill_value=0).astype(int))

# ===== NATIONAL TOTALS BY CIP ONLY (Simplified) =====
national_simple = master_df.groupby(['Year', 'CIP_Code', 'CIP_Title'])['Completions'].sum().reset_index()
national_simple = national_simple.sort_values(['CIP_Code', 'Year'])
print("\n" + "="*100)
print("NATIONAL TOTALS BY CIP (Summed Across All Awards)")
print("="*100)
print(national_simple.to_string(index=False))
national_simple.to_csv('national_totals_by_cip_simple.csv', index=False)

print("\n\n✓ All analysis complete!")
