# Community college filter

A school is included for every year from 2019 through 2025 when it qualifies in any of those years. A community college that starts awarding bachelor's degrees stays in the list after IPEDS moves it from sector 4 to sector 1.

The source is the IPEDS Institutional Directory, `HD2019` through `HD2025`. The columns are `CONTROL`, `SECTOR`, `C21BASIC`, and `INSTNM`. `C21BASIC` is on the 2021 through 2025 files. The 2019 and 2020 files have no Carnegie column, so those years can qualify a school only through the name rule.

## Include

The school must be public (`CONTROL` = 1). Private colleges are not included. A sector 0 row is a district office and cannot qualify the school.

Any one of these is enough:

1. `C21BASIC` is 1 through 9, or 14. Codes 1 through 9 are the associate's-college groups. Code 14 is the associate-dominant group. In the 2024 directory that code includes Bakersfield College, Modesto Junior College, Foothill College, and MiraCosta College, which IPEDS now codes as public 4-year schools.
2. The name contains "community college" and `SECTOR` is 1 (public, 4-year or above) or 4 (public, 2-year).
3. `C21BASIC` is 33 and `CONTROL` is 1. Code 33 is the tribal-college code. This keeps public tribal colleges such as Diné College and Salish Kootenai College. Private tribal colleges stay out.

## Remove even if a rule matched

- The institution is only a sector 0 administrative unit.
- Any year's name contains "career center", "adult education", "BOCES", or "technology center".

Those name exclusions are the local career centers and technology centers. Florida district technical colleges, the Tennessee Colleges of Applied Technology, and the Oklahoma technology centers do not have an associate's Carnegie code, so they are not in this list. They are handled by the technical-school filter.

Code 15 is not used. In this directory it is research universities.

## Where the list is

`community_colleges.csv` and `community_colleges.xlsx` in this folder. The sheet "Removed by exclusion" shows schools that matched a rule and were then removed. `In_41_CIP_completions` says whether the school appears in the 41-CIP completions file used for the figures.
