import re
import pandas as pd

XLSX_PATH = "uni_mining.xlsx"
CSV_PATH = "school_level_clean_2021-2025.csv"
OUT_PATH = "school_level_clean_2021-2025_no_universities.csv"

# Same normalization and aliases as the merge script, so names match the same way
ALIASES = {
    "southern illinois university": "southern illinois university carbondale",
    "pennsylvania state university": "pennsylvania state university main campus",
}

def norm(s):
    s = str(s).lower().replace("&", " and ").strip()
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return ALIASES.get(s, s)

# 1. Build the set of university institutions from the xlsx (all rows, any focus area)
xlsx = pd.read_excel(XLSX_PATH)
xlsx.columns = xlsx.iloc[0]
xlsx.columns = xlsx.columns.str.strip()
unis = xlsx[xlsx["Institution type"].astype(str).str.strip() == "Universities"]
uni_keys = set(zip(unis["Institution name"].map(norm), unis["State_name"].astype(str).str.strip()))

# 2. Load the original csv as text so values are written back unchanged
csv = pd.read_csv(CSV_PATH, encoding="utf-8-sig", dtype=str)
csv.columns = csv.columns.str.strip()

# 3. Drop rows whose (institution, state) is a university in the xlsx
keys = list(zip(csv["Institution"].map(norm), csv["State"].astype(str).str.strip()))
is_uni = pd.Series([k in uni_keys for k in keys], index=csv.index)

removed = csv.loc[is_uni, ["Institution", "State"]].drop_duplicates()
kept = csv.loc[~is_uni]

# Drop institutions with "university" in their name (case-insensitive)
mask = kept["Institution"].str.contains("university", case=False, na=False)

print("Removed institutions:")
print(kept.loc[mask, "Institution"].drop_duplicates().to_string(index=False))

kept = kept.loc[~mask].copy()

kept.to_csv(OUT_PATH, index=False)

# 4. Check
print(f"Rows in: {len(csv)}  removed: {is_uni.sum()}  kept: {len(kept)}")
print("Removed institutions:")
print(removed.to_string(index=False))
