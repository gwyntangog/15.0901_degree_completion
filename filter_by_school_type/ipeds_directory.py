"""Load the IPEDS Institutional Directory files used by the school-type filters."""

import os

import pandas as pd

DATA_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(DATA_ROOT, "full_data_files")
YEARS = list(range(2019, 2026))

CORE_COLUMNS = ["UNITID", "INSTNM", "STABBR", "SECTOR", "CONTROL"]
OPTIONAL_COLUMNS = ["C21BASIC"]


def _read(path, columns):
    header = None
    encoding = None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            header = pd.read_csv(path, nrows=0, encoding=encoding)
            break
        except UnicodeDecodeError:
            header = None
    if header is None:
        raise OSError(f"Could not read {path}")
    rename = {col: col.replace("\ufeff", "").strip() for col in header.columns}
    present = [col for col in columns if col in rename.values()]
    wanted = [raw for raw, clean in rename.items() if clean in present]
    frame = pd.read_csv(path, encoding=encoding, dtype=str, usecols=wanted)
    frame.columns = [rename[col] for col in frame.columns]
    for col in columns:
        if col not in frame.columns:
            frame[col] = pd.NA
    return frame


def _code(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if text.lstrip("-").isdigit():
        return str(int(text))
    return text or None


def load_directory():
    """One row per institution per year, with sector, control, and Carnegie code.

    C21BASIC is absent from the 2019 and 2020 directories. Those years still
    supply the name, sector, and control.
    """
    frames = []
    for year in YEARS:
        path = os.path.join(FULL, f"HD{year}", f"hd{year}.csv")
        frame = _read(path, CORE_COLUMNS + OPTIONAL_COLUMNS)
        frame["Year"] = year
        frame["UnitID"] = frame["UNITID"].map(_code)
        frame["Institution"] = frame["INSTNM"].fillna("").str.strip()
        frame["State"] = frame["STABBR"].fillna("").str.strip()
        frame["Sector"] = frame["SECTOR"].map(_code)
        frame["Control"] = frame["CONTROL"].map(_code)
        frame["Carnegie"] = frame["C21BASIC"].map(_code)
        frames.append(frame[["Year", "UnitID", "Institution", "State", "Sector", "Control", "Carnegie"]])
    panel = pd.concat(frames, ignore_index=True)
    return panel.dropna(subset=["UnitID"])
