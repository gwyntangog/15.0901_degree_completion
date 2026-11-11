"""
Completions by CIP code and award level, 2019-2025.

IPEDS award codes 20 and 21 (certificates under 12 weeks, and certificates of
at least 12 weeks but less than 1 year) are added together. In 2019 those two
lengths are already one code, "Award of less than 1 academic year", so every
year uses the same level: Certificates of less than 1 year.

Counts are first major only, grand total (CTOTALT). Revised completions files
are used when they exist. 2025 has no revision yet.

Two versions are written. "all" keeps every institution, including universities.
"community_colleges" keeps public 2-year institutions (IPEDS sector 4).

Figures: all_cip_figures/all and all_cip_figures/community_colleges
Sheets: all_cip_data/all and all_cip_data/community_colleges
"""

import os
import re

import matplotlib

matplotlib.use("Agg")

import matplotlib.colors
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

DATA_ROOT = os.path.dirname(os.path.abspath(__file__))
FULL = os.path.join(DATA_ROOT, "full_data_files")
PROGRAM_LIST = os.path.join(DATA_ROOT, "Programs_Instituion list (1).xlsx")
FIGURE_ROOT = os.path.join(DATA_ROOT, "all_cip_figures")
DATA_OUT = os.path.join(DATA_ROOT, "all_cip_data")

YEARS = list(range(2019, 2026))

# Codes 1 (2019), 20, and 21 all become the first label.
AWARD_CODE_TO_LABEL = {
    "1": "Certificates of less than 1 year",
    "20": "Certificates of less than 1 year",
    "21": "Certificates of less than 1 year",
    "2": "Certificates of at least 1 but less than 2 years",
    "4": "Certificates of at least 2 but less than 4 years",
    "3": "Associate's degree",
    "5": "Bachelor's degree",
    "6": "Postbaccalaureate certificate",
    "7": "Master's degree",
    "8": "Post-master's certificate",
    "17": "Doctor's degree - research/scholarship",
    "18": "Doctor's degree - professional practice",
    "19": "Doctor's degree - other",
}

AWARD_ORDER = [
    "Certificates of less than 1 year",
    "Certificates of at least 1 but less than 2 years",
    "Certificates of at least 2 but less than 4 years",
    "Associate's degree",
    "Bachelor's degree",
    "Postbaccalaureate certificate",
    "Master's degree",
    "Post-master's certificate",
    "Doctor's degree - research/scholarship",
    "Doctor's degree - professional practice",
    "Doctor's degree - other",
]

SECTOR_NAMES = {
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

PUBLIC_2YEAR = "4"

AWARD_COLORS = dict(zip(AWARD_ORDER, sns.color_palette("tab20", n_colors=len(AWARD_ORDER))))

# Map helpers follow 3_geographic_heatmap.py
TERRITORY_CODE = "VI"
MAP_WIDTH = 1200
MAP_HEIGHT = 700
IMAGE_SCALE = 2
ALL_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
    "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
    "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
    "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV",
    "WI", "WY", "DC",
]


def cip_key(code):
    return tuple(int(part) for part in str(code).split("."))


def norm_cip(value):
    if pd.isna(value):
        return None
    text = str(value).replace("'", "").strip()
    if text.lower() in {"", "nan", "none", "n/a"}:
        return None
    try:
        if "." not in text:
            digits = re.sub(r"\D", "", text)
            if len(digits) < 5:
                return None
            return f"{int(digits[:-4]):02d}.{digits[-4:]}"
        left, right = text.split(".", 1)
        right = re.sub(r"\D", "", right)
        return f"{int(left):02d}.{right.zfill(4)}"
    except ValueError:
        return None


def norm_sector(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if text.lstrip("-").isdigit():
        return str(int(text))
    return text


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(text)).strip("_")


def read_ipeds(path, columns):
    last_error = None
    header = None
    encoding = None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            header = pd.read_csv(path, encoding=encoding, nrows=0)
            break
        except UnicodeDecodeError as exc:
            last_error = exc
            header = None
    if header is None:
        raise last_error
    rename = {col: col.replace("\ufeff", "").strip() for col in header.columns}
    wanted = [raw for raw, clean in rename.items() if clean in columns]
    missing = [col for col in columns if col not in rename.values()]
    if missing:
        raise ValueError(f"{os.path.basename(path)} is missing {missing}")
    frame = pd.read_csv(path, encoding=encoding, dtype=str, usecols=wanted, low_memory=False)
    frame.columns = [rename[col] for col in frame.columns]
    return frame


def completions_file(year):
    folder = os.path.join(FULL, f"C{year}_A")
    files = [name for name in os.listdir(folder) if name.lower().endswith(".csv")]
    revised = [name for name in files if re.search(r"_rv\.csv$", name, re.I)]
    if revised:
        return os.path.join(folder, sorted(revised)[0])
    plain = [name for name in files if name.lower() == f"c{year}_a.csv"]
    if not plain:
        raise FileNotFoundError(f"No completions file for {year} in {folder}")
    return os.path.join(folder, plain[0])


def directory_file(year):
    folder = os.path.join(FULL, f"HD{year}")
    name = f"hd{year}.csv"
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return path


def load_target_cips(path):
    raw = pd.read_excel(path, sheet_name="CIP-Program match")
    raw.columns = [str(col).strip() for col in raw.columns]
    cip_col = next(col for col in raw.columns if "CIP Code" in col)
    title_col = next(col for col in raw.columns if col.startswith("CIP Title"))
    titles = {}
    for code, title in zip(raw[cip_col], raw[title_col]):
        cip = norm_cip(code)
        if cip is None or (isinstance(title, float) and pd.isna(title)):
            continue
        title_text = str(title).strip()
        if not title_text or title_text.lower() == "nan":
            continue
        titles.setdefault(cip, title_text)
    return dict(sorted(titles.items(), key=lambda item: cip_key(item[0])))


def load_school_level(cip_titles):
    cip_set = set(cip_titles)
    frames = []
    for year in YEARS:
        comp_path = completions_file(year)
        print(f"{year}: {os.path.basename(comp_path)}", flush=True)
        comp = read_ipeds(comp_path, ["UNITID", "CIPCODE", "MAJORNUM", "AWLEVEL", "CTOTALT"])
        comp["MAJORNUM"] = pd.to_numeric(comp["MAJORNUM"], errors="coerce")
        comp = comp[comp["MAJORNUM"] == 1].copy()
        comp["CIP_Code"] = comp["CIPCODE"].map(norm_cip)
        comp = comp[comp["CIP_Code"].isin(cip_set)].copy()
        comp["Award_Code"] = pd.to_numeric(comp["AWLEVEL"], errors="coerce")
        known = set(int(code) for code in AWARD_CODE_TO_LABEL)
        unexpected = sorted(set(comp["Award_Code"].dropna().astype(int)) - known)
        if unexpected:
            raise ValueError(f"{year} has unexpected award codes: {unexpected}")
        comp = comp[comp["Award_Code"].notna()].copy()
        comp["Award_Level"] = comp["Award_Code"].astype(int).astype(str).map(AWARD_CODE_TO_LABEL)
        comp["Completions"] = pd.to_numeric(comp["CTOTALT"], errors="coerce")
        bad = int(comp["Completions"].isna().sum())
        if bad:
            print(f"  dropped {bad} rows with a non-numeric completion count", flush=True)
        comp = comp[comp["Completions"].notna()].copy()
        comp["UnitID"] = pd.to_numeric(comp["UNITID"], errors="coerce").astype("Int64")
        comp = comp[comp["UnitID"].notna()]
        grouped = (
            comp.groupby(["UnitID", "CIP_Code", "Award_Level"], as_index=False)["Completions"].sum()
        )
        grouped["Year"] = year

        directory = read_ipeds(directory_file(year), ["UNITID", "INSTNM", "STABBR", "SECTOR"])
        directory["UnitID"] = pd.to_numeric(directory["UNITID"], errors="coerce").astype("Int64")
        directory = directory.dropna(subset=["UnitID"]).drop_duplicates("UnitID")
        directory["Institution"] = directory["INSTNM"].str.strip()
        directory["State"] = directory["STABBR"].str.strip()
        directory["Sector_Code"] = directory["SECTOR"].map(norm_sector)
        grouped = grouped.merge(
            directory[["UnitID", "Institution", "State", "Sector_Code"]],
            on="UnitID",
            how="left",
        )
        unmatched = int(grouped["Institution"].isna().sum())
        print(
            f"  institutions {grouped['UnitID'].nunique():,}  "
            f"rows {len(grouped):,}  "
            f"completions {int(grouped['Completions'].sum()):,}  "
            f"unmatched {unmatched}",
            flush=True,
        )
        frames.append(grouped)

    school = pd.concat(frames, ignore_index=True)
    school["CIP_Title"] = school["CIP_Code"].map(cip_titles)
    school["Sector"] = school["Sector_Code"].map(SECTOR_NAMES).fillna("Not in directory")
    school["Completions"] = school["Completions"].round().astype(int)
    school = school[
        [
            "Year", "UnitID", "Institution", "State", "Sector_Code", "Sector",
            "CIP_Code", "CIP_Title", "Award_Level", "Completions",
        ]
    ]
    return school.sort_values(["CIP_Code", "Year", "Institution", "Award_Level"]).reset_index(drop=True)


def build_master(school, cip_titles):
    aggregated = (
        school.groupby(["Year", "CIP_Code", "Award_Level"], as_index=False)
        .agg(Completions=("Completions", "sum"), Num_Schools=("UnitID", "nunique"))
    )
    grid = pd.MultiIndex.from_product(
        [YEARS, list(cip_titles), AWARD_ORDER],
        names=["Year", "CIP_Code", "Award_Level"],
    ).to_frame(index=False)
    master = grid.merge(aggregated, on=["Year", "CIP_Code", "Award_Level"], how="left")
    master["Completions"] = master["Completions"].fillna(0).astype(int)
    master["Num_Schools"] = master["Num_Schools"].fillna(0).astype(int)
    master["CIP_Title"] = master["CIP_Code"].map(cip_titles)
    return master[
        ["Year", "CIP_Code", "CIP_Title", "Award_Level", "Completions", "Num_Schools"]
    ]


def build_summary(school):
    latest_year = int(school["Year"].max())
    recent = [latest_year - 2, latest_year - 1, latest_year]
    meta = (
        school.sort_values("Year")
        .groupby(["UnitID", "CIP_Code"], as_index=False)
        .tail(1)[["UnitID", "CIP_Code", "Institution", "State", "Sector", "CIP_Title"]]
    )
    totals = school.groupby(["UnitID", "CIP_Code", "Year"], as_index=False)["Completions"].sum()
    wide = totals.pivot_table(
        index=["UnitID", "CIP_Code"],
        columns="Year",
        values="Completions",
        aggfunc="sum",
        fill_value=0,
    )
    window = wide.reindex(columns=recent, fill_value=0)
    summary = meta.merge(
        pd.DataFrame({
            "Latest_Year_Completions": window[latest_year].astype(int),
            "Three_Year_Avg_Completions": window.mean(axis=1).round(1),
        }).reset_index(),
        on=["UnitID", "CIP_Code"],
        how="left",
    )
    summary["Latest_Year"] = latest_year
    summary["Three_Year_Window"] = f"{recent[0]}-{latest_year}"
    return summary.sort_values(
        ["CIP_Code", "Latest_Year_Completions", "Institution"],
        ascending=[True, False, True],
    )


def autosize(workbook):
    for sheet in workbook.worksheets:
        for column in sheet.columns:
            letter = get_column_letter(column[0].column)
            width = 12
            for cell in column[:50]:
                if cell.value is not None:
                    width = max(width, min(len(str(cell.value)) + 2, 46))
            sheet.column_dimensions[letter].width = width
        for cell in sheet[1]:
            cell.font = Font(bold=True)


def write_workbook(master, path, population):
    by_year = (
        master.groupby(["CIP_Code", "CIP_Title", "Year"], as_index=False)["Completions"].sum()
        .pivot_table(index=["CIP_Code", "CIP_Title"], columns="Year", values="Completions", aggfunc="sum")
        .reindex(columns=YEARS)
        .fillna(0)
        .astype(int)
    )
    by_year["Total"] = by_year.sum(axis=1)
    by_year = by_year.reset_index()

    by_award = (
        master.groupby(["CIP_Code", "CIP_Title", "Award_Level"], as_index=False)["Completions"].sum()
        .pivot_table(index=["CIP_Code", "CIP_Title"], columns="Award_Level", values="Completions", aggfunc="sum")
        .reindex(columns=AWARD_ORDER)
        .fillna(0)
        .astype(int)
    )
    by_award["Total"] = by_award.sum(axis=1)
    by_award = by_award.reset_index()

    notes = pd.DataFrame({
        "Item": [
            "Population",
            "Years",
            "Source",
            "What is counted",
            "Major",
            "Short certificates",
            "CIP list",
            "Zero rows",
            "Institution counts",
        ],
        "Detail": [
            population,
            "2019-2025 (IPEDS file year). 2025 is provisional; 2019-2024 use the revised completions file.",
            "IPEDS Completions (C) joined to the Institutional Directory (HD) on UnitID.",
            "Grand total completions (CTOTALT), summed across institutions.",
            "First major only (MAJORNUM = 1).",
            "Certificates of less than 1 year. This is award code 1 in 2019. In 2020-2025 it is award codes 20 and 21 added together.",
            "Distinct CIP codes with a title on the CIP-Program match sheet. N/A and blank codes are left out. Alternate codes mentioned only in notes are left out.",
            "Every CIP and award level is listed for every year. A zero means no reported completions.",
            "master_all_CIPs_2019-2025.csv has Num_Schools, the number of institutions reporting that CIP and award level.",
        ],
    })

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        notes.to_excel(writer, sheet_name="Notes", index=False)
        by_year.to_excel(writer, sheet_name="By year", index=False)
        by_award.to_excel(writer, sheet_name="By award", index=False)
        for cip in master["CIP_Code"].drop_duplicates():
            sub = master[master["CIP_Code"] == cip]
            title = sub["CIP_Title"].iloc[0]
            table = (
                sub.pivot_table(index="Year", columns="Award_Level", values="Completions", aggfunc="sum")
                .reindex(index=YEARS, columns=AWARD_ORDER)
                .fillna(0)
                .astype(int)
            )
            table["Total"] = table.sum(axis=1)
            table.to_excel(writer, sheet_name=str(cip), startrow=1)
            sheet = writer.book[str(cip)]
            sheet["A1"] = f"{cip}  {title}"
            sheet["A1"].font = Font(bold=True)
        autosize(writer.book)
    print(f"Saved {path}", flush=True)


def write_tables(school, master, summary, folder, population):
    os.makedirs(folder, exist_ok=True)
    school.drop(columns=["Sector_Code"]).to_csv(
        os.path.join(folder, "school_level_2019-2025.csv"), index=False
    )
    master.to_csv(os.path.join(folder, "master_all_CIPs_2019-2025.csv"), index=False)
    (
        master[["Year", "CIP_Code", "CIP_Title", "Award_Level", "Completions", "Num_Schools"]]
        .sort_values(["CIP_Code", "Year", "Award_Level"])
        .to_csv(os.path.join(folder, "national_totals_by_cip_award_year.csv"), index=False)
    )
    (
        master.groupby(["Year", "CIP_Code", "CIP_Title"], as_index=False)["Completions"]
        .sum()
        .sort_values(["CIP_Code", "Year"])
        .to_csv(os.path.join(folder, "national_totals_by_cip_year.csv"), index=False)
    )
    summary.to_csv(os.path.join(folder, "summary_by_cip_and_school.csv"), index=False)
    write_workbook(master, os.path.join(folder, "completions_by_cip_award_2019-2025.xlsx"), population)


def save_figure(fig, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {path}", flush=True)


def label_for(cip, title, limit=52):
    text = f"{cip}  {title}"
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def draw_lines(master, folder):
    """One chart per CIP, one line per award level that has any completions."""
    line_dir = os.path.join(folder, "line_plots", "cip_by_award_lines")
    stack_dir = os.path.join(folder, "line_plots", "cip_stacked_area")
    for cip, sub in master.groupby("CIP_Code", sort=False):
        title = sub["CIP_Title"].iloc[0]
        pivot = (
            sub.pivot_table(index="Year", columns="Award_Level", values="Completions", aggfunc="sum")
            .reindex(index=YEARS, columns=AWARD_ORDER)
            .fillna(0)
        )
        pivot = pivot.loc[:, pivot.sum() > 0]
        if pivot.empty:
            continue

        fig, ax = plt.subplots(figsize=(12, 7))
        for award in pivot.columns:
            ax.plot(
                pivot.index, pivot[award], marker="o", linewidth=2.5, markersize=7,
                color=AWARD_COLORS[award], label=award,
            )
        ax.set_xlabel("Year", fontsize=12, fontweight="bold")
        ax.set_ylabel("Number of completions", fontsize=12, fontweight="bold")
        ax.set_title(f"{cip} - {title}\nCompletions by award level (2019-2025)", fontsize=14, fontweight="bold")
        ax.set_xticks(YEARS)
        ax.legend(fontsize=9, loc="best")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        save_figure(fig, os.path.join(line_dir, f"lineplot_{safe_name(cip)}_all_awards.png"))

        fig, ax = plt.subplots(figsize=(12, 7))
        colors = [AWARD_COLORS[award] for award in pivot.columns]
        pivot.plot(kind="area", stacked=True, ax=ax, alpha=0.75, color=colors, linewidth=0)
        ax.set_xlabel("Year", fontsize=12, fontweight="bold")
        ax.set_ylabel("Number of completions", fontsize=12, fontweight="bold")
        ax.set_title(f"{cip} - {title}\nCompletions by award level", fontsize=14, fontweight="bold")
        ax.set_xticks(YEARS)
        ax.legend(title="Award level", fontsize=9, loc="best")
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        save_figure(fig, os.path.join(stack_dir, f"stacked_area_{safe_name(cip)}.png"))


def draw_heatmap(master, folder):
    pivot = (
        master.groupby(["CIP_Code", "CIP_Title", "Year"], as_index=False)["Completions"].sum()
        .pivot_table(index=["CIP_Code", "CIP_Title"], columns="Year", values="Completions", aggfunc="sum")
        .reindex(columns=YEARS)
        .fillna(0)
        .astype(int)
    )
    pivot = pivot.reset_index()
    labels = [label_for(code, title, 58) for code, title in zip(pivot["CIP_Code"], pivot["CIP_Title"])]
    values = pivot[YEARS]
    fig, ax = plt.subplots(figsize=(11, 18))
    sns.heatmap(values, ax=ax, cmap="YlOrRd", annot=True, fmt="d", linewidths=0.4, cbar_kws={"label": "Completions"})
    ax.set_yticklabels(labels, rotation=0, fontsize=8)
    ax.set_xticklabels(YEARS, rotation=0)
    ax.set_xlabel("Year", fontsize=12, fontweight="bold")
    ax.set_ylabel("")
    ax.set_title("Completions by CIP code and year (2019-2025)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    save_figure(fig, os.path.join(folder, "heatmap", "completions_by_cip_year.png"))


def draw_cip_bars(master, folder):
    totals = (
        master.groupby(["CIP_Code", "CIP_Title"], as_index=False)["Completions"].sum()
        .sort_values("Completions", ascending=True)
    )
    fig, ax = plt.subplots(figsize=(12, 14))
    ax.barh(
        [label_for(code, title, 58) for code, title in zip(totals["CIP_Code"], totals["CIP_Title"])],
        totals["Completions"],
        color="#2E86AB",
    )
    ax.set_xlabel("Completions, 2019-2025", fontsize=12, fontweight="bold")
    ax.set_title("Total completions by CIP code", fontsize=14, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    save_figure(fig, os.path.join(folder, "bar_completions_by_cip.png"))


def draw_award_lines(master, folder):
    grouped = master.groupby(["Year", "Award_Level"], as_index=False)["Completions"].sum()
    fig, ax = plt.subplots(figsize=(12, 7))
    for award in AWARD_ORDER:
        data = grouped[grouped["Award_Level"] == award].sort_values("Year")
        if data.empty or data["Completions"].sum() == 0:
            continue
        ax.plot(
            data["Year"], data["Completions"], marker="o", linewidth=2.5, markersize=7,
            color=AWARD_COLORS[award], label=award,
        )
    ax.set_xlabel("Year", fontsize=12, fontweight="bold")
    ax.set_ylabel("Number of completions", fontsize=12, fontweight="bold")
    ax.set_title("Completions by award level (2019-2025)", fontsize=14, fontweight="bold")
    ax.set_xticks(YEARS)
    ax.legend(fontsize=9, loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save_figure(fig, os.path.join(folder, "timeseries_by_award.png"))


def draw_top_schools(school, folder, how_many=10):
    totals = (
        school.groupby(["UnitID", "Institution", "State"], as_index=False)["Completions"].sum()
        .nlargest(how_many, "Completions")
    )
    counts = totals["Institution"].value_counts()
    fig, ax = plt.subplots(figsize=(12, 7))
    for _, row in totals.iterrows():
        yearly = (
            school[school["UnitID"] == row["UnitID"]]
            .groupby("Year")["Completions"].sum()
            .reindex(YEARS, fill_value=0)
        )
        name = row["Institution"]
        if counts[name] > 1:
            name = f"{name} ({row['State']})"
        ax.plot(YEARS, yearly.values, marker="o", linewidth=2, markersize=7, label=name)
    ax.set_xlabel("Year", fontsize=12, fontweight="bold")
    ax.set_ylabel("Number of completions", fontsize=12, fontweight="bold")
    ax.set_title(f"Top {how_many} institutions: completions (2019-2025)", fontsize=14, fontweight="bold")
    ax.set_xticks(YEARS)
    ax.legend(fontsize=9, loc="best")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save_figure(fig, os.path.join(folder, "timeseries_top_schools.png"))


def plotly_scale_from_mpl(cmap_name, n=256):
    cmap = matplotlib.colormaps[cmap_name]
    return [[i / (n - 1), matplotlib.colors.to_hex(cmap(i / (n - 1)))] for i in range(n)]


def color_for_value(value, cmap_name, vmax):
    fraction = min(max(value / vmax, 0), 1)
    return matplotlib.colors.to_hex(matplotlib.colormaps[cmap_name](fraction))


def label_text_color(fraction, cmap_name):
    red, green, blue, _ = matplotlib.colormaps[cmap_name](fraction)
    luminance = 0.299 * red + 0.587 * green + 0.114 * blue
    return "white" if luminance < 0.5 else "black"


def render_map(slice_df, title, path, cmap_name, vmax=None):
    import plotly.express as px
    import plotly.graph_objects as go

    totals = slice_df.groupby("State", as_index=False)["Completions"].sum()
    totals = totals.rename(columns={"State": "State Code"})
    if vmax is None:
        vmax = max(int(totals["Completions"].max()) if not totals.empty else 1, 1)
    full = pd.DataFrame({"State Code": ALL_STATES}).merge(
        totals[["State Code", "Completions"]], on="State Code", how="left"
    )
    full["Completions"] = full["Completions"].fillna(0).astype(int)
    vmax = max(int(vmax), 1)
    fig = px.choropleth(
        full,
        locations="State Code",
        locationmode="USA-states",
        color="Completions",
        scope="usa",
        title=title,
        color_continuous_scale=plotly_scale_from_mpl(cmap_name),
        range_color=(0, vmax),
        labels={"Completions": "Completions"},
    )
    fractions = (full["Completions"] / vmax).clip(0, 1)
    text_colors = [label_text_color(fraction, cmap_name) for fraction in fractions]
    fig.add_trace(go.Scattergeo(
        locations=full["State Code"],
        locationmode="USA-states",
        text=full["State Code"],
        mode="text",
        textfont=dict(size=11, color=text_colors),
        hoverinfo="skip",
        showlegend=False,
    ))
    vi = int(slice_df.loc[slice_df["State"] == TERRITORY_CODE, "Completions"].sum())
    dot = color_for_value(vi, cmap_name, vmax)
    fig.add_annotation(
        x=0.97, y=0.05, xref="paper", yref="paper",
        xanchor="right", yanchor="bottom", showarrow=False,
        text=(f'<span style="font-size:24px;color:{dot}">●</span> '
              f"US Virgin Islands: {vi:,} completions"),
        font=dict(size=12),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=dot, borderwidth=1, borderpad=4,
    )
    fig.update_layout(geo=dict(scope="usa"), width=MAP_WIDTH, height=MAP_HEIGHT, font=dict(size=12))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.write_image(path, scale=IMAGE_SCALE)
    print(f"Saved {path}", flush=True)


def draw_maps(school, folder):
    map_root = os.path.join(folder, "maps")
    render_map(
        school,
        "Completions by state (2019-2025)",
        os.path.join(map_root, "overall", "overall_2019-2025.png"),
        "YlOrRd",
    )
    year_totals = school.groupby(["Year", "State"], as_index=False)["Completions"].sum()
    year_max = max(int(year_totals["Completions"].max()), 1)
    for year in YEARS:
        render_map(
            school[school["Year"] == year],
            f"Completions by state ({year})",
            os.path.join(map_root, "by_year", f"year_{year}.png"),
            "YlOrRd",
            vmax=year_max,
        )
    titles = school.drop_duplicates("CIP_Code").set_index("CIP_Code")["CIP_Title"]
    for cip in sorted(school["CIP_Code"].unique(), key=cip_key):
        cip_df = school[school["CIP_Code"] == cip]
        if int(cip_df["Completions"].sum()) == 0:
            continue
        render_map(
            cip_df,
            f"{cip} - {titles[cip]} completions by state (2019-2025)",
            os.path.join(map_root, "by_cip", f"cip_{safe_name(cip)}.png"),
            "Blues",
        )


def draw_figures(school, master, folder):
    sns.set_style("whitegrid")
    print(f"Figures in {folder}", flush=True)
    draw_lines(master, folder)
    draw_heatmap(master, folder)
    draw_cip_bars(master, folder)
    draw_award_lines(master, folder)
    draw_top_schools(school, folder)
    outside = sorted(set(school["State"].dropna()) - set(ALL_STATES) - {TERRITORY_CODE})
    if outside:
        held = (
            school[school["State"].isin(outside)]
            .groupby("State")["Completions"].sum()
            .sort_values(ascending=False)
        )
        print("States and territories kept in the sheets but not drawn as US states:", flush=True)
        print(held.to_string(), flush=True)
    draw_maps(school, folder)


def publish(school, cip_titles, data_folder, figure_folder, population):
    print(f"\n=== {population} ===", flush=True)
    master = build_master(school, cip_titles)
    summary = build_summary(school)
    write_tables(school, master, summary, data_folder, population)
    totals = master.groupby(["CIP_Code", "CIP_Title"])["Completions"].sum().sort_values(ascending=False)
    print(totals.to_string(), flush=True)
    draw_figures(school, master, figure_folder)


def main():
    sns.set_style("whitegrid")
    cip_titles = load_target_cips(PROGRAM_LIST)
    print(f"{len(cip_titles)} CIP codes", flush=True)
    school = load_school_level(cip_titles)
    publish(
        school,
        cip_titles,
        os.path.join(DATA_OUT, "all"),
        os.path.join(FIGURE_ROOT, "all"),
        "All institutions, including universities",
    )
    community_colleges = school[school["Sector_Code"] == PUBLIC_2YEAR].copy()
    publish(
        community_colleges,
        cip_titles,
        os.path.join(DATA_OUT, "community_colleges"),
        os.path.join(FIGURE_ROOT, "community_colleges"),
        "Community colleges only: public 2-year institutions (IPEDS sector 4)",
    )
    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
