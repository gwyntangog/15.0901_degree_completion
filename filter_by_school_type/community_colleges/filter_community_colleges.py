"""Build the community-college institution list.

The rules are documented in FILTER.md in this folder. Running this file writes
community_colleges.csv and community_colleges.xlsx.
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ipeds_directory

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.dirname(os.path.dirname(HERE))
COMPLETIONS = os.path.join(DATA_ROOT, "all_cip_data", "all", "school_level_2019-2025.csv")

ASSOCIATE_CARNEGIE = {str(code) for code in range(1, 10)} | {"14"}
TRIBAL_CARNEGIE = "33"
NAME_EXCLUSIONS = (
    "career center",
    "adult education",
    "boces",
    "technology center",
)

SECTOR_LABELS = {
    "0": "Administrative unit",
    "1": "Public, 4-year or above",
    "2": "Private not-for-profit, 4-year or above",
    "3": "Private for-profit, 4-year or above",
    "4": "Public, 2-year",
    "5": "Private not-for-profit, 2-year",
    "6": "Private for-profit, 2-year",
    "7": "Public, less-than-2-year",
    "8": "Private not-for-profit, less-than-2-year",
    "9": "Private for-profit, less-than-2-year",
    "99": "Sector unknown",
}


def _reasons(row):
    if row["Control"] != "1" or row["Sector"] in {None, "0"}:
        return []
    reasons = []
    if row["Carnegie"] in ASSOCIATE_CARNEGIE:
        reasons.append(f"Carnegie associate's or associate-dominant (C21BASIC {row['Carnegie']})")
    name = row["Institution"].lower()
    if "community college" in name and row["Sector"] in {"1", "4"}:
        reasons.append("Name contains community college and sector is 1 or 4")
    if row["Carnegie"] == TRIBAL_CARNEGIE:
        reasons.append("Public tribal college (C21BASIC 33)")
    return reasons


def _excluded_name(names):
    text = " ".join(str(name).lower() for name in names)
    hits = [pattern for pattern in NAME_EXCLUSIONS if pattern in text]
    return hits


def build_community_colleges(directory=None):
    """Return kept institutions and the institutions removed by an exclusion."""
    panel = ipeds_directory.load_directory() if directory is None else directory
    panel = panel.copy()
    panel["Reasons"] = panel.apply(_reasons, axis=1)
    matched = panel[panel["Reasons"].map(bool)].copy()

    records = []
    removed = []
    for unit_id, years in panel.groupby("UnitID"):
        hits = matched[matched["UnitID"] == unit_id]
        if hits.empty:
            continue
        latest = years.sort_values("Year").iloc[-1]
        name_hits = _excluded_name(years["Institution"])
        only_admin = set(years["Sector"].dropna()) <= {"0"}
        reasons = sorted({reason for bundle in hits["Reasons"] for reason in bundle})
        if name_hits or only_admin:
            removed.append({
                "UnitID": unit_id,
                "Institution": latest["Institution"],
                "State": latest["State"],
                "Exclusion": "Sector 0 administrative unit" if only_admin and not name_hits else "Name exclusion: " + ", ".join(name_hits),
                "Rules_that_matched": "; ".join(reasons),
            })
            continue
        carnegie_years = years[years["Carnegie"].notna()]
        latest_carnegie = carnegie_years.sort_values("Year").iloc[-1]["Carnegie"] if not carnegie_years.empty else ""
        records.append({
            "UnitID": unit_id,
            "Institution": latest["Institution"],
            "State": latest["State"],
            "Latest_year": int(latest["Year"]),
            "Latest_sector_code": latest["Sector"] or "",
            "Latest_sector": SECTOR_LABELS.get(latest["Sector"], latest["Sector"] or ""),
            "Latest_C21BASIC": latest_carnegie or "",
            "Rules": "; ".join(reasons),
            "Years_matched": ", ".join(str(year) for year in sorted(hits["Year"].unique())),
        })
    kept = pd.DataFrame(records)
    if kept.empty:
        kept = pd.DataFrame(columns=[
            "UnitID", "Institution", "State", "Latest_year", "Latest_sector_code",
            "Latest_sector", "Latest_C21BASIC", "Rules", "Years_matched",
        ])
    dropped = pd.DataFrame(removed)
    return kept.sort_values(["State", "Institution"]).reset_index(drop=True), dropped


def _add_completions_flag(kept):
    if not os.path.exists(COMPLETIONS):
        kept["In_41_CIP_completions"] = ""
        return kept
    completions = pd.read_csv(COMPLETIONS, dtype=str, usecols=["UnitID"])
    present = set(completions["UnitID"].map(ipeds_directory._code))
    kept["In_41_CIP_completions"] = kept["UnitID"].map(lambda unit: "Yes" if unit in present else "No")
    return kept


def write_list(kept, dropped):
    kept = _add_completions_flag(kept)
    csv_path = os.path.join(HERE, "community_colleges.csv")
    xlsx_path = os.path.join(HERE, "community_colleges.xlsx")
    kept.to_csv(csv_path, index=False)
    notes = pd.DataFrame({
        "Item": [
            "Who is included",
            "Control",
            "Carnegie",
            "Name rule",
            "Tribal colleges",
            "Exclusions",
            "Years",
            "Once a school qualifies",
            "Completions flag",
            "Full write-up",
        ],
        "Detail": [
            "Public community colleges, public associate-dominant colleges, and public tribal colleges.",
            "CONTROL = 1 in the Institutional Directory. Private colleges are not included.",
            "C21BASIC 1 through 9, or 14, in any directory year that has the column (2021-2025). Codes 1-9 are the associate's groups. Code 14 is the associate-dominant group, including bachelor's-granting community colleges such as Bakersfield College and Modesto Junior College.",
            "The name contains community college, and SECTOR is 1 (public, 4-year or above) or 4 (public, 2-year).",
            "C21BASIC 33 and CONTROL 1. Private tribal colleges are not included.",
            "SECTOR 0 district offices are removed. A name containing career center, adult education, BOCES, or technology center is removed even if another rule matched.",
            "2019-2025. The 2019 and 2020 directories have no C21BASIC column, so those years can qualify a school only through the name rule.",
            "The school is kept for every year. A later move from sector 4 to sector 1 does not drop it.",
            "In_41_CIP_completions is Yes when the school has a row in all_cip_data/all/school_level_2019-2025.csv.",
            "FILTER.md in this folder.",
        ],
    })
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        notes.to_excel(writer, sheet_name="Notes", index=False)
        kept.to_excel(writer, sheet_name="Community colleges", index=False)
        if not dropped.empty:
            dropped.sort_values(["State", "Institution"]).to_excel(writer, sheet_name="Removed by exclusion", index=False)
    print(f"{len(kept)} community colleges")
    print(f"Saved {csv_path}")
    print(f"Saved {xlsx_path}")
    return kept


def main():
    kept, dropped = build_community_colleges()
    write_list(kept, dropped)
    if not dropped.empty:
        print(f"Removed by an exclusion: {len(dropped)}")


if __name__ == "__main__":
    main()
