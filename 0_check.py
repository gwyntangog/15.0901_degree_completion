#for debugging
import pandas as pd

school_df = pd.read_csv('school_level_clean_2021-2025.csv', dtype={'CIP_Code': str})
print("State values:", sorted(school_df['State'].dropna().astype(str).unique()))
print("Blank states:", school_df['State'].isna().sum())
print(school_df[school_df['Institution'].str.contains('Virgin', case=False, na=False)]
      [['Year', 'Institution', 'State', 'Completions']].head(10))
