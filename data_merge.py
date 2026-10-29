import re
import pandas as pd

XLSX_PATH = "uni_mining.xlsx"
CSV_PATH = "school_level_clean_2021-2025.csv"  # Key: Value blocks

CIP_TO_ENGLISH = {
    "14.2101": "Mining Engineering and Geology",
    "15.0901": "Mining and Heavy Equipment Operations",
    "15.0999": "Mining and Heavy Equipment Operations",
}
MINING_FOCUS = set(CIP_TO_ENGLISH.values())
COUNT_COLS = ["BSc. Degree Awarded", "MSc. Degree Awarded", "PhD. Degree Awarded"]

ALIASES = {
    "southern illinois university": "southern illinois university carbondale",
    "pennsylvania state university": "pennsylvania state university main campus",
}

def norm(s):
    s = str(s).lower().replace("&", " and ").strip()
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return ALIASES.get(s, s)

REQUIRED = ["Year", "UnitID", "Institution", "State", "CIP_Code", "Award_Level", "Completions"]

def load_completions(path):
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    df.columns = df.columns.str.strip()

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns {missing}. Found: {list(df.columns)}")

    # Drop junk rows, such as a stray backtick line or blank lines from pasting
    df = df[df["Year"].str.fullmatch(r"\d{4}", na=False)].copy()

    df["Year"] = df["Year"].astype(int).astype("Int64")
    df["UnitID"] = pd.to_numeric(df["UnitID"], errors="coerce").astype("Int64")
    df["Completions"] = pd.to_numeric(df["Completions"], errors="coerce")
    for c in ["Institution", "State", "CIP_Code", "Award_Level"]:
        df[c] = df[c].str.strip()
    return df

# ---------- Load xlsx (mining focus only) ----------
prog = pd.read_excel(XLSX_PATH)
prog.columns = prog.iloc[0]
prog.columns = prog.columns.str.strip()
prog = prog[prog["Focus area"].isin(MINING_FOCUS)].copy()
for c in COUNT_COLS:
    prog[c] = pd.to_numeric(prog[c], errors="coerce")
prog["Year"] = pd.to_numeric(prog["Year"], errors="coerce").astype("Int64")
prog["inst_key"] = prog["Institution name"].map(norm)
prog["State"] = prog["State_name"].str.strip()
prog["Program_EN"] = prog["Focus area"]
prog["row_has_counts"] = prog[COUNT_COLS].notna().any(axis=1)

# Institution-level lock: any xlsx count -> do not merge
lock = (
    prog.groupby(["inst_key", "State"])["row_has_counts"]
    .any().rename("locked").reset_index()
)
prog = prog.merge(lock, on=["inst_key", "State"], how="left")
prog["locked"] = prog["locked"].astype(bool)

# ---------- Load csv (mining CIPs only) ----------
comp = load_completions(CSV_PATH)
comp = comp[comp["CIP_Code"].isin(CIP_TO_ENGLISH)].copy()
comp["Program_EN"] = comp["CIP_Code"].map(CIP_TO_ENGLISH)
comp["inst_key"] = comp["Institution"].map(norm)
comp["State"] = comp["State"].str.strip()

comp_w = (
    comp.pivot_table(
        index=["UnitID", "Institution", "inst_key", "State", "Year", "Program_EN"],
        columns="Award_Level",
        values="Completions",
        aggfunc="sum",
    )
    .add_prefix("csv: ")
    .reset_index()
)
comp_w = comp_w.merge(lock, on=["inst_key", "State"], how="left")
comp_w["locked"] = comp_w["locked"].fillna(False).astype(bool)

# ---------- Path 1: locked universities (no merge) ----------
xlsx_locked = (
    prog[prog["locked"]]
    .groupby(["inst_key", "State", "Year", "Program_EN"], dropna=False)
    .agg(
        xlsx_institution=("Institution name", "first"),
        xlsx_programs=("Program name", lambda s: "; ".join(sorted(set(s.dropna().astype(str))))),
        xlsx_BSc=("BSc. Degree Awarded", lambda s: s.sum(min_count=1)),
        xlsx_MSc=("MSc. Degree Awarded", lambda s: s.sum(min_count=1)),
        xlsx_PhD=("PhD. Degree Awarded", lambda s: s.sum(min_count=1)),
    )
    .reset_index()
)
xlsx_locked["Source"] = "xlsx only"

csv_locked = comp_w[comp_w["locked"]].drop(columns=["locked"]).copy()
csv_locked["Source"] = "csv only"

# ---------- Path 2: merge-eligible institutions (one row per csv year) ----------
xlsx_free = (
    prog[~prog["locked"]]
    .groupby(["inst_key", "State", "Program_EN"], dropna=False)
    .agg(
        xlsx_institution=("Institution name", "first"),
        xlsx_programs=("Program name", lambda s: "; ".join(sorted(set(s.dropna().astype(str))))),
    )
    .reset_index()
)

csv_free = comp_w[~comp_w["locked"]].drop(columns=["locked"]).copy()

merged_free = csv_free.merge(
    xlsx_free,
    on=["inst_key", "State", "Program_EN"],
    how="outer",
    indicator=True,
)
merged_free["Source"] = merged_free.pop("_merge").map(
    {"both": "both", "left_only": "csv only", "right_only": "xlsx only"}
)

# ---------- Combine and tidy ----------
out = pd.concat([xlsx_locked, csv_locked, merged_free], ignore_index=True)
out["Institution"] = out["Institution"].fillna(out["xlsx_institution"])
out = out.drop(columns=["xlsx_institution", "inst_key"])
out = out.sort_values(["Institution", "Program_EN", "Year"], na_position="last")

out.to_csv("mining_institution_year_program.csv", index=False)
print(out["Source"].value_counts())
