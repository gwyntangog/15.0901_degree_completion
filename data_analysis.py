import pandas as pd
import os

# Define years
years = [2021, 2022, 2023, 2024, 2025]

# Step 1: Load and merge each year
all_data = []

for year in years:
    print(f"Processing {year}...")

    # Load institutional file
    inst_file = f"{year}_institutions.csv"  # Adjust filename as needed
    inst_df = pd.read_csv(inst_file)

    print(inst_df.columns)

    # Load completions file
    comp_file = f"{year}_completions.csv"  # Adjust filename as needed
    comp_df = pd.read_csv(comp_file)

    print(comp_df.columns)

    # Find state column dynamically
    state_col = [col for col in inst_df.columns if 'State abbreviation' in col][0]

    # Find completions column dynamically (Grand total)
    comp_col = [col for col in comp_df.columns if 'Grand total' in col and 'male' not in col.lower() and 'female' not in col.lower()][0]

    # Find CIP code column (should be consistent)
    cip_col = [col for col in comp_df.columns if 'CIP Code' in col][0]

    # Find award level column (should be consistent)
    award_col = [col for col in comp_df.columns if 'Award Level code' in col][0]

    #  # Find state column dynamically
    # state_col = f'HD{year}.State abbreviation'

    # # Find completions column dynamically (Grand total)
    # comp_col = f'C{year}_A_RV.Grand total'

    # # Find CIP code column (should be consistent)
    # cip_col = f'C{year}_A.CIP Code -  2020 Classification'

    # # Find award level column (should be consistent)
    # award_col = f'C{year}_A.Award Level code'

    # Merge on UnitID
    merged = pd.merge(
        comp_df,
        inst_df[['unitid', state_col]],  # Adjust column name if needed
        on='unitid',
        how='left'
    )

    merged = merged.rename(columns={
        state_col: 'State',
        comp_col: 'Completions',
        cip_col: 'CIP_Code',
        award_col: 'Award_Level'
    })

    # print(merged.columns)

    # print(merged.columns)

    all_data.append(merged)
    print(f"  {len(merged)} rows")

# Step 2: Combine all years
master_df = pd.concat(all_data, ignore_index=True)
print(f"\nTotal rows combined: {len(master_df)}")

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

print(master_df.columns)

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

# Step 3
# Filter by Award Level

# Remove double counting by removing different certificate types
master_df = master_df[~master_df['Award_Level'].isin(['Certificates of less than 1 year','Certificates below the baccalaureate total'])]

# Clean CIP code
master_df['CIP_Code'] = master_df['CIP_Code'].str.replace("'", "").str.strip()
master_df = master_df[master_df['CIP_Code'] == '15.0901'].copy()

print(f"Rows with CIP 15.0901: {len(master_df)}\n")

# Save master
master_df.to_csv('mining_master_2021-2025.csv', index=False)
print("✓ Saved: mining_master_2021-2025.csv")

# National totals by year & award
national = master_df.groupby(['Year', 'Award_Level'])['Completions'].sum().reset_index()
national = national.sort_values(['Year', 'Award_Level'])
national.to_csv('mining_national_totals.csv', index=False)
print("✓ Saved: mining_national_totals.csv")

# Award level breakdown by school
award_breakdown = master_df.groupby(['Institution', 'State', 'Award_Level'])['Completions'].sum().unstack(fill_value=0)
award_breakdown.to_csv('mining_award_breakdown.csv')
print("✓ Saved: mining_award_breakdown.csv")

# Summary by school
latest_year = master_df['Year'].max()
three_year_start = latest_year - 2

# START WITH BASE: Get all unique schools from latest year
base = master_df[master_df['Year'] == latest_year][['UnitID', 'Institution', 'State']].drop_duplicates().set_index(['UnitID', 'Institution', 'State'])

# Latest year completions (all schools)
latest = master_df[master_df['Year'] == latest_year].groupby(['UnitID', 'Institution', 'State'])['Completions'].sum().rename('Latest_Year_Completions')

# 3-year average (all schools, 2023-2025)
three_year_avg = master_df[master_df['Year'] >= three_year_start].groupby(['UnitID', 'Institution', 'State'])['Completions'].mean().round(1).rename('Three_Year_Avg_Completions')

# Award level breakdown - REINDEX to match base
certificates = master_df[master_df['Award_Level'].str.contains('Certificate', case=False, na=False)].groupby(['UnitID', 'Institution', 'State'])['Completions'].sum().rename('Certificates').reindex(base.index, fill_value=0)

associates = master_df[master_df['Award_Level'] == "Associate's degree"].groupby(['UnitID', 'Institution', 'State'])['Completions'].sum().rename('Associates_Degrees').reindex(base.index, fill_value=0)

other = master_df[~master_df['Award_Level'].str.contains('Certificate|Associate', case=False, na=False)].groupby(['UnitID', 'Institution', 'State'])['Completions'].sum().rename('Other_Awards').reindex(base.index, fill_value=0)

# Combine all - NOW they're all same length!
summary = pd.concat([latest, three_year_avg, certificates, associates, other], axis=1).reset_index()

# Fill any remaining NaN with 0 and convert to int
summary = summary.fillna(0)
summary['Latest_Year_Completions'] = summary['Latest_Year_Completions'].astype(int)
summary['Certificates'] = summary['Certificates'].astype(int)
summary['Associates_Degrees'] = summary['Associates_Degrees'].astype(int)
summary['Other_Awards'] = summary['Other_Awards'].astype(int)

# Sort by latest year completions
summary = summary.sort_values('Latest_Year_Completions', ascending=False)

summary.to_csv('mining_summary_by_school.csv', index=False)
print("✓ Saved: mining_summary_by_school.csv\n")


print("\n✓ Analysis Complete!")


# print(master_df.columns)

# print(master_df['CIP_Code'].unique())
# print(master_df['CIP_Code'].value_counts())
# print(summary[summary['Institution'] == 'Central Technology Center'].T)
