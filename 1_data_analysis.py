import pandas as pd

# =============================================================================
# CONFIG
# =============================================================================
YEARS = [2021, 2022, 2023, 2024, 2025]
TARGET_CIPS = ['14.2101', '15.0901', '15.0999']

# Award levels that are TOTALS of other rows. Keeping them would double-count.
AGGREGATE_AWARDS = [
    'Degrees/certificates total',
    'Degrees total',
    'Certificates below the baccalaureate total',
    'Certificates of less than 1 year',  # = "<12 weeks" + "12 weeks to <1 year"
    'Certificates above the baccalaureate total',
]


# =============================================================================
# HELPER
# =============================================================================
def find_col(df, keyword, must_contain=(), must_not_contain=()):
    """Return the first column whose name contains `keyword`.
    Column names can shift slightly between years, so we search for them
    instead of hardcoding the exact names."""
    matches = [
        c for c in df.columns
        if keyword in c
        and all(m in c for m in must_contain)
        and not any(bad in c.lower() for bad in must_not_contain)
    ]
    return matches[0]


# =============================================================================
# STEP 1: LOAD ONE YEAR AND ATTACH EACH SCHOOL'S STATE TO ITS COMPLETIONS
# =============================================================================
def load_year(year):
    print(f"\nProcessing {year}...")

    inst_df = pd.read_csv(f"{year}_institutions.csv")
    comp_df = pd.read_csv(f"{year}_completions.csv")
    print(f"  Completions rows: {len(comp_df)}")

    # Find the column names we need
    state_col = find_col(inst_df, 'State abbreviation')
    comp_col = find_col(comp_df, 'Grand total',
                        must_not_contain=['male', 'female'])  # total, not split by sex
    cip_col = find_col(comp_df, 'CIP Code', must_contain=['Classification'])
    award_col = find_col(comp_df, 'Award Level code')
    print(f"  State col: {state_col}")
    print(f"  Completions col: {comp_col}")

    # Add the state from the institutions file to each completions row (matched on unitid)
    merged = comp_df.merge(inst_df[['unitid', state_col]], on='unitid', how='left')

    # Rename to consistent names and tag the year
    merged = merged.rename(columns={
        state_col: 'State',
        comp_col: 'Completions',
        cip_col: 'CIP_Code',
        award_col: 'Award_Level',
    })
    merged['Year'] = year
    print(f"  Merged rows: {len(merged)}")
    return merged


# =============================================================================
# STEP 2: COMBINE ALL YEARS, CLEAN CIP CODES, KEEP TARGET PROGRAMS
# =============================================================================
raw = pd.concat([load_year(y) for y in YEARS], ignore_index=True)
print(f"\n✓ Total rows combined: {len(raw)}")

# Remove quotes/spaces from CIP codes so they match TARGET_CIPS
raw['CIP_Code'] = raw['CIP_Code'].astype(str).str.replace("'", "").str.strip()

raw = raw[raw['CIP_Code'].isin(TARGET_CIPS)].copy()
print(f"✓ Rows with target CIPs: {len(raw)}")


# =============================================================================
# STEP 3: REMOVE AGGREGATE AWARD LEVELS (TOTALS) TO AVOID DOUBLE-COUNTING
# =============================================================================
print("\nAward levels BEFORE removing aggregates:")
print(raw['Award_Level'].unique())

raw = raw[~raw['Award_Level'].isin(AGGREGATE_AWARDS)].copy()

print("\nAward levels AFTER removing aggregates:")
print(raw['Award_Level'].unique())
print(f"Rows after removing aggregates: {len(raw)}\n")


# =============================================================================
# STEP 4: KEEP NEEDED COLUMNS AND GIVE THEM CLEAN NAMES
# (school-level, not padded yet)
# =============================================================================
school_df = raw[[
    'Year', 'unitid', 'institution name', 'State',
    'CIP_Code', 'CipTitle', 'Award_Level', 'Completions',
]].rename(columns={
    'unitid': 'UnitID',
    'institution name': 'Institution',
    'CipTitle': 'CIP_Title',
}).copy()

# Make sure Completions is a whole number (bad/missing values become 0)
school_df['Completions'] = (
    pd.to_numeric(school_df['Completions'], errors='coerce').fillna(0).astype(int)
)

school_df.to_csv('school_level_clean_2021-2025.csv', index=False)


# =============================================================================
# STEP 5: PAD MISSING YEAR / CIP / AWARD COMBOS WITH ZEROS
# So every CIP-award pair has a row for every year, even if the count was 0.
# =============================================================================
# Totals and school counts per Year / CIP / Award
national_raw = school_df.groupby(['Year', 'CIP_Code', 'Award_Level']).agg(
    Completions=('Completions', 'sum'),
    Num_Schools=('UnitID', 'count'),   # how many schools reported this combo
).reset_index()

# Every combination that should exist
all_index = pd.MultiIndex.from_product(
    [sorted(school_df['Year'].unique()),
     sorted(school_df['CIP_Code'].unique()),
     sorted(school_df['Award_Level'].unique())],
    names=['Year', 'CIP_Code', 'Award_Level'],
)

# Reindex: any combo with no data becomes a row of NaN, which we fill with 0
national_padded = (
    national_raw.set_index(['Year', 'CIP_Code', 'Award_Level'])
                .reindex(all_index)
                .reset_index()
)
national_padded['Completions'] = national_padded['Completions'].fillna(0).astype(int)
national_padded['Num_Schools'] = national_padded['Num_Schools'].fillna(0).astype(int)

# Add CIP titles back (padded rows have none, so look them up by CIP code)
cip_titles = school_df.drop_duplicates('CIP_Code').set_index('CIP_Code')['CIP_Title']
national_padded['CIP_Title'] = national_padded['CIP_Code'].map(cip_titles)

print(f"Rows before padding: {len(national_raw)}")
print(f"Rows after padding:  {len(national_padded)}")

national_padded.to_csv('master_all_CIPs_2021-2025.csv', index=False)
print("✓ Saved: master_all_CIPs_2021-2025.csv\n")


# =============================================================================
# STEP 6: SCHOOL SUMMARY (latest year + 3-year average)
# Uses school_df (NOT padded), because padding has no school columns.
# =============================================================================
latest_year = school_df['Year'].max()
recent_years = [latest_year - 2, latest_year - 1, latest_year]

# Total completions per school, per program, per year (all award levels added together)
school_keys = ['UnitID', 'Institution', 'State', 'CIP_Code', 'CIP_Title']
school_totals = school_df.groupby(school_keys + ['Year'])['Completions'].sum().reset_index()

# One row per school/program, one column per year (missing years = 0)
wide = school_totals.pivot_table(
    index=school_keys, columns='Year', values='Completions',
    aggfunc='sum', fill_value=0,
)

window = wide.reindex(columns=recent_years, fill_value=0)

summary = pd.DataFrame({
    'Latest_Year_Completions': window[latest_year].astype(int),
    'Three_Year_Avg_Completions': window.mean(axis=1).round(1),
}).reset_index()

summary = summary.sort_values(
    ['CIP_Code', 'Latest_Year_Completions'], ascending=[True, False]
)
summary.to_csv('summary_by_cip_and_school.csv', index=False)
print("✓ Saved: summary_by_cip_and_school.csv\n")

print("=" * 100)
print(f"SUMMARY BY CIP & SCHOOL (Latest Year: {latest_year} | 3-Year Avg: {recent_years[0]}-{latest_year})")
print("=" * 100)
print(summary.to_string(index=False))


# =============================================================================
# STEP 7: NATIONAL TOTALS
# =============================================================================
# By CIP, award, and year
national_by_award = (
    national_padded[['Year', 'CIP_Code', 'CIP_Title', 'Award_Level', 'Completions']]
    .sort_values(['CIP_Code', 'Year', 'Award_Level'])
)
national_by_award.to_csv('national_totals_by_cip_award_year.csv', index=False)
print("\n\n✓ Saved: national_totals_by_cip_award_year.csv\n")

print("=" * 100)
print("NATIONAL TOTALS BY CIP (Pivot by Award Level)")
print("=" * 100)
for cip in TARGET_CIPS:
    cip_data = national_by_award[national_by_award['CIP_Code'] == cip]
    if cip_data.empty:
        print(f"\n{cip}: no data")
        continue
    title = cip_data['CIP_Title'].iloc[0]
    print(f"\n{cip} - {title}:")
    print(cip_data.pivot_table(
        index='Year', columns='Award_Level', values='Completions',
        aggfunc='sum', fill_value=0,
    ).astype(int))

# All award levels added together, by CIP and year
national_simple = (
    national_padded.groupby(['Year', 'CIP_Code', 'CIP_Title'], as_index=False)['Completions']
    .sum()
    .sort_values(['CIP_Code', 'Year'])
)
national_simple.to_csv('national_totals_by_cip_simple.csv', index=False)
print("\n" + "=" * 100)
print("NATIONAL TOTALS BY CIP (Summed Across All Awards)")
print("=" * 100)
print(national_simple.to_string(index=False))

print("\n\n✓ All analysis complete!")
