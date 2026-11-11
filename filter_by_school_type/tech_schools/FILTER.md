# Technical and technology school filter

This list is the technical colleges, technology centers, colleges of applied technology, and special-focus technical schools that are not already on the community-college list.

A school that meets the community-college rules stays there. Milwaukee Area Technical College and Los Angeles Trade Technical College are associate's colleges, so they stay with community colleges even though the name says technical. The sheet "Kept with community colleges" lists every school that also matched a technical rule.

Public and private schools are both included.

The source is the IPEDS Institutional Directory, `HD2019` through `HD2025`. `C21BASIC` is available from 2021 onward. The name rule covers 2019 and 2020 as well.

## Include

Sector 0 rows are ignored. Any one of these is enough:

1. The name contains one of: technical college, technical institute, technical school, technology center, technical center, college of technology, college of applied technology, applied technology, technological college, technological institute.
2. `C21BASIC` is 11. In the 2024 directory this is the code on Universal Technical Institute, Lincoln College of Technology, and Spartan College of Aeronautics and Technology.
3. The name contains "institute of technology" and `SECTOR` is 4, 6, 7, or 9. Those are the 2-year and less-than-2-year sectors. Four-year institutes of technology, including Georgia Tech and MIT, stay out.

This puts the Oklahoma technology centers, the Florida district technical colleges, and the Tennessee Colleges of Applied Technology here. They were left out of the community-college list on purpose.

## Where the list is

`tech_schools.csv` and `tech_schools.xlsx` in this folder. `In_41_CIP_completions` says whether the school appears in the 41-CIP completions file used for the figures.
