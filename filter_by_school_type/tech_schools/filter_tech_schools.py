"""Build the technical and technology school list.

Schools that qualify as community colleges are left in that list. The rules
are documented in FILTER.md in this folder.
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "community_colleges"))
import ipeds_directory
import filter_community_colleges as community_colleges

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.dirname(os.path.dirname(HERE))
COMPLETIONS = os.path.join(DATA_ROOT, "all_cip_data", "all", "school_level_2019-2025.csv")

NAME_PATTERNS = (
    "technical college",
    "technical institute",
    "technical school",
    "technology center",
    "technical center",
    "college of technology",
    "college of applied technology",
    "applied technology",
    "technological college",
    "technological institute",
)
SHORT_SECTORS = {"4", "6", "7", "9"}
TECHNICAL_CARNEGIE = "11"

SECTOR_LABELS = community_colleges.SECTOR_LABELS


def _reasons(row):
    if row["Sector"] in {None, "0"}:
        return []
    reasons = []
    name = row["Institution"].lower()
    matched = [pattern for pattern in NAME_PATTERNS if pattern in name]
    if matched:
        reasons.append("Name: " + ", ".join(matched))
    if row["Carnegie"] == TECHNICAL_CARNEGIE:
        reasons.append("Carnegie special-focus technical (C21BASIC 11)")
    if "institute of technology" in name and row["Sector"] in SHORT_SECTORS:
        reasons.append("Institute of technology at a 2-year or shorter sector")
    return reasons


def build_tech_schools(directory=None, community_college_ids=None):
    panel = ipeds_directory.load_directory() if directory is None else directory
    if community_college_ids is None:
        kept, _dropped = community_colleges.build_community_colleges(panel)
        community_college_ids = set(kept["UnitID"])
    panel = panel.copy()
    panel["Reasons"] = panel.apply(_reasons, axis=1)
    matched = panel[panel["Reasons"].map(bool) & ~panel["UnitID"].isin(community_college_ids)].copy()

    records = []
    held_with_colleges = []
    also = panel[panel["Reasons"].map(bool) & panel["UnitID"].isin(community_college_ids)]
    for unit_id, hits in also.groupby("UnitID"):
        latest = panel[panel["UnitID"] == unit_id].sort_values("Year").iloc[-1]
        reasons = sorted({reason for bundle in hits["Reasons"] for reason in bundle})
        held_with_colleges.append({
            "UnitID": unit_id,
            "Institution": latest["Institution"],
            "State": latest["State"],
            "Why_not_in_this_list": "Kept on the community-college list",
            "Technical_rules_that_also_matched": "; ".join(reasons),
        })

    for unit_id, hits in matched.groupby("UnitID"):
        years = panel[panel["UnitID"] == unit_id]
        latest = years.sort_values("Year").iloc[-1]
        if set(years["Sector"].dropna()) <= {"0"}:
            continue
        carnegie_years = years[years["Carnegie"].notna()]
        latest_carnegie = carnegie_years.sort_values("Year").iloc[-1]["Carnegie"] if not carnegie_years.empty else ""
        reasons = sorted({reason for bundle in hits["Reasons"] for reason in bundle})
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
    overlap = pd.DataFrame(held_with_colleges)
    return kept.sort_values(["State", "Institution"]).reset_index(drop=True), overlap


def _add_completions_flag(kept):
    if not os.path.exists(COMPLETIONS):
        kept["In_41_CIP_completions"] = ""
        return kept
    completions = pd.read_csv(COMPLETIONS, dtype=str, usecols=["UnitID"])
    present = set(completions["UnitID"].map(ipeds_directory._code))
    kept["In_41_CIP_completions"] = kept["UnitID"].map(lambda unit: "Yes" if unit in present else "No")
    return kept


def write_list(kept, overlap):
    kept = _add_completions_flag(kept)
    csv_path = os.path.join(HERE, "tech_schools.csv")
    xlsx_path = os.path.join(HERE, "tech_schools.xlsx")
    kept.to_csv(csv_path, index=False)
    notes = pd.DataFrame({
        "Item": [
            "Who is included",
            "Control",
            "Name rule",
            "Carnegie",
            "Institutes of technology",
            "Community colleges",
            "Administrative units",
            "Years",
            "Completions flag",
            "Full write-up",
        ],
        "Detail": [
            "Technical colleges, technology centers, colleges of applied technology, and special-focus technical schools that are not on the community-college list.",
            "Public and private schools are both included. CONTROL is not limited to 1.",
            "technical college, technical institute, technical school, technology center, technical center, college of technology, college of applied technology, applied technology, technological college, or technological institute.",
            "C21BASIC 11 in 2021-2025. In the 2024 directory this is the code on Universal Technical Institute, Lincoln College of Technology, and Spartan College of Aeronautics and Technology.",
            "A name containing institute of technology qualifies only when SECTOR is 4, 6, 7, or 9. Four-year institutes such as Georgia Tech and MIT stay out.",
            "A school that meets the community-college rules stays on that list only. Milwaukee Area Technical College and Los Angeles Trade Technical College are examples of technical colleges kept with community colleges because their Carnegie code is an associate's code.",
            "SECTOR 0 rows are ignored.",
            "2019-2025. Carnegie code 11 is available from 2021 onward. The name rule covers 2019 and 2020.",
            "In_41_CIP_completions is Yes when the school has a row in all_cip_data/all/school_level_2019-2025.csv.",
            "FILTER.md in this folder.",
        ],
    })
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        notes.to_excel(writer, sheet_name="Notes", index=False)
        kept.to_excel(writer, sheet_name="Tech schools", index=False)
        if not overlap.empty:
            overlap.sort_values(["State", "Institution"]).to_excel(
                writer, sheet_name="Kept with community colleges", index=False
            )
    print(f"{len(kept)} tech schools")
    print(f"Saved {csv_path}")
    print(f"Saved {xlsx_path}")
    return kept


def main():
    kept, overlap = build_tech_schools()
    write_list(kept, overlap)
    print(f"Also matched a technical rule but kept with community colleges: {len(overlap)}")


if __name__ == "__main__":
    main()
