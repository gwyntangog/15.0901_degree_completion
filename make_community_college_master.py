import pandas as pd

IN_PATH = "school_level_clean_2021-2025_no_universities.csv"
OUT_PATH = "master_all_CIPs_2021-2025_no_universities.csv"

# Same award levels and order as master_all_CIPs_2021-2025.csv
AWARD_LEVELS = [
    "Associate's degree",
    "Bachelor's degree",
    "Certificates of at least 1 but less than 2 years",
    "Certificates of at least 12 weeks but less than 1 year",
    "Certificates of less than 12 weeks",
    "Doctor's degree - research/scholarship",
    "Master's degree",
    "Postbaccalaureate certificate",
]

df = pd.read_csv(IN_PATH, dtype=str, encoding="utf-8-sig")
df.columns = df.columns.str.strip()
for c in ["UnitID", "CIP_Code", "CIP_Title", "Award_Level"]:
    df[c] = df[c].str.strip()
df["Year"] = pd.to_numeric(df["Year"]).astype(int)
df["Completions"] = pd.to_numeric(df["Completions"], errors="coerce").fillna(0)

# Totals per year, CIP, and award level
# Num_Schools counts distinct UnitIDs, including schools reporting 0
agg = (
    df.groupby(["Year", "CIP_Code", "Award_Level"])
    .agg(Completions=("Completions", "sum"), Num_Schools=("UnitID", "nunique"))
    .reset_index()
)

# Fill in every year x CIP x award level combination, so missing ones show as 0
titles = df.groupby("CIP_Code")["CIP_Title"].first()
grid = pd.MultiIndex.from_product(
    [sorted(df["Year"].unique()), sorted(titles.index), AWARD_LEVELS],
    names=["Year", "CIP_Code", "Award_Level"],
).to_frame(index=False)

out = grid.merge(agg, on=["Year", "CIP_Code", "Award_Level"], how="left")
out["Completions"] = out["Completions"].fillna(0).astype(int)
out["Num_Schools"] = out["Num_Schools"].fillna(0).astype(int)
out["CIP_Title"] = out["CIP_Code"].map(titles)

out = out[["Year", "CIP_Code", "Award_Level", "Completions", "Num_Schools", "CIP_Title"]]
out.to_csv(OUT_PATH, index=False)

print(f"Rows written: {len(out)}")
print(out.groupby(["Year", "CIP_Code"])[["Completions", "Num_Schools"]].sum())
