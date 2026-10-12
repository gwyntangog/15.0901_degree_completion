import pandas as pd

comp_2025 = pd.read_csv('2025_completions.csv')

print("Column Names:")
print(comp_2025.columns.tolist())

print("\n\nCIP Codes Present:")
cip_cols = [col for col in comp_2025.columns if 'CIP' in col.upper()]
print(cip_cols)
if cip_cols:
    print(comp_2025[cip_cols[0]].unique())

print("\n\nAward Level Column:")
award_cols = [col for col in comp_2025.columns if 'Award' in col]
print(award_cols)
if award_cols:
    print(comp_2025[award_cols[0]].unique()[:20])  # First 20
