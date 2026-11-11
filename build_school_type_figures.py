"""Rebuild the community-college and tech-school completions sheets and figures.

Institution lists come from filter_by_school_type. A school that qualifies is
kept for every year in the completions file, including years after its sector
changes.
"""

import importlib.util
import os
import shutil

import pandas as pd

import build_all_cip_completions as pipeline

DATA_ROOT = os.path.dirname(os.path.abspath(__file__))
COMPLETIONS = os.path.join(DATA_ROOT, "all_cip_data", "all", "school_level_2019-2025.csv")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reset_folder(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def completions_for(unit_ids):
    school = pd.read_csv(COMPLETIONS, dtype={"UnitID": str, "CIP_Code": str})
    school["UnitID"] = school["UnitID"].map(lambda value: str(int(float(value))) if str(value).strip() else value)
    school["Year"] = school["Year"].astype(int)
    school["Completions"] = pd.to_numeric(school["Completions"], errors="coerce").fillna(0).astype(int)
    return school[school["UnitID"].isin(unit_ids)].copy()


def main():
    cc_filter = load_module(
        os.path.join(DATA_ROOT, "filter_by_school_type", "community_colleges", "filter_community_colleges.py"),
        "filter_community_colleges",
    )
    tech_filter = load_module(
        os.path.join(DATA_ROOT, "filter_by_school_type", "tech_schools", "filter_tech_schools.py"),
        "filter_tech_schools",
    )
    community, cc_removed = cc_filter.build_community_colleges()
    cc_filter.write_list(community, cc_removed)
    tech, overlap = tech_filter.build_tech_schools(community_college_ids=set(community["UnitID"]))
    tech_filter.write_list(tech, overlap)

    titles = pipeline.load_target_cips(pipeline.PROGRAM_LIST)
    groups = [
        (
            set(community["UnitID"]),
            os.path.join(pipeline.DATA_OUT, "community_colleges"),
            os.path.join(pipeline.FIGURE_ROOT, "community_colleges"),
            "Public community colleges, associate-dominant colleges, and public tribal colleges. "
            "Rules are in filter_by_school_type/community_colleges/FILTER.md. "
            "A qualifying school is kept in every year.",
        ),
        (
            set(tech["UnitID"]),
            os.path.join(pipeline.DATA_OUT, "tech_schools"),
            os.path.join(pipeline.FIGURE_ROOT, "tech_schools"),
            "Technical and technology schools that are not on the community-college list. "
            "Rules are in filter_by_school_type/tech_schools/FILTER.md.",
        ),
    ]
    for unit_ids, data_folder, figure_folder, population in groups:
        reset_folder(data_folder)
        reset_folder(figure_folder)
        school = completions_for(unit_ids)
        print(f"{population.split('.')[0]}: {school['UnitID'].nunique()} schools in the completions file", flush=True)
        pipeline.publish(school, titles, data_folder, figure_folder, population)
    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
