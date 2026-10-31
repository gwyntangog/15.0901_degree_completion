import os
import re

import matplotlib
import matplotlib.colors
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# SETUP
# =============================================================================
TERRITORY_CODE = 'VI'
MAP_WIDTH = 1200
MAP_HEIGHT = 700
IMAGE_SCALE = 2  # higher = sharper PNG
OUTPUT_ROOT = 'maps'

# Colormap for each map group. Use the same name as the matching heatmap
# so that a zero is the same color in both.
MAP_COLORMAPS = {
    'overall': 'YlOrRd',       # matches Heatmap 1
    'by_year': 'YlOrRd',
    'by_cip': 'Blues',         # matches Heatmap 2
    'by_cip_year': 'Blues',
    'by_award_year': 'Purples',  # matches Heatmap 4
    'by_cip_award_year': 'Purples',
}

# Subfolder for each map type, created inside OUTPUT_ROOT
FOLDERS = {
    'overall': 'overall',
    'by_year': 'by_year',
    'by_cip': 'by_cip',
    'by_cip_year': 'by_cip_year',
    'by_award_year': 'by_award_year',
    'by_cip_award_year': 'by_cip_award_year',
}

# Every state Plotly can draw. States with zero completions still get colored.
ALL_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID',
    'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS',
    'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK',
    'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV',
    'WI', 'WY', 'DC',
]

# Full state name -> two-letter code (what Plotly needs)
STATE_NAME_TO_CODE = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI',
    'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY',
    'Virgin Islands': 'VI', 'Puerto Rico': 'PR', 'Guam': 'GU',
}


# =============================================================================
# LOAD AND CLEAN DATA
# =============================================================================
school_df = pd.read_csv('school_level_clean_2021-2025_no_universities.csv', dtype={'CIP_Code': str})

# Convert full state names to two-letter codes (unlisted values are left as-is)
school_df['State'] = school_df['State'].str.strip().replace(STATE_NAME_TO_CODE)

unmatched = sorted(set(school_df['State'].dropna()) - set(STATE_NAME_TO_CODE.values()))
if unmatched:
    print("Unrecognized state values (add to STATE_NAME_TO_CODE):", unmatched)

all_years = sorted(school_df['Year'].unique())
all_cips = sorted(school_df['CIP_Code'].unique())
all_awards = sorted(school_df['Award_Level'].dropna().unique())

# CIP code -> title, for use in map titles
cip_titles = school_df.drop_duplicates('CIP_Code').set_index('CIP_Code')['CIP_Title'].to_dict()

# Create every output folder up front
for folder in FOLDERS.values():
    os.makedirs(os.path.join(OUTPUT_ROOT, folder), exist_ok=True)


# =============================================================================
# HELPERS
# =============================================================================
def vi_value(df):
    """Total Virgin Islands completions in a slice of school_df."""
    return int(df.loc[df['State'] == TERRITORY_CODE, 'Completions'].sum())


def state_totals(df, group_cols=('State',)):
    """Sum completions by state. VI is kept here so it counts toward the
    color max. build_state_frame() leaves VI off the map itself, because
    the USA map has no VI shape."""
    out = df.groupby(list(group_cols), as_index=False)['Completions'].sum()
    return out.rename(columns={'State': 'State Code'})


def shared_max(totals):
    """Largest state total in a table, at least 1 so the color range never collapses."""
    if totals.empty:
        return 1
    return max(int(totals['Completions'].max()), 1)


def build_state_frame(state_data, vmax=None):
    """Give every state a row (zero if no data) and work out the color max."""
    full = (
        pd.DataFrame({'State Code': ALL_STATES})
        .merge(state_data[['State Code', 'Completions']], on='State Code', how='left')
    )
    full['Completions'] = full['Completions'].fillna(0).astype(int)
    if vmax is None:
        vmax = shared_max(full)
    return full, max(int(vmax), 1)


def plotly_scale_from_mpl(cmap_name, n=256):
    """Copy a matplotlib colormap into a Plotly color scale."""
    cmap = matplotlib.colormaps[cmap_name]
    return [
        [i / (n - 1), matplotlib.colors.to_hex(cmap(i / (n - 1)))]
        for i in range(n)
    ]


def color_for_value(value, cmap_name, vmax):
    """The exact color a state with this value gets on the map.
    Used to color the Virgin Islands dot so it matches the map's scale."""
    cmap = matplotlib.colormaps[cmap_name]
    fraction = min(max(value / vmax, 0), 1)
    return matplotlib.colors.to_hex(cmap(fraction))

def label_text_color(fraction, cmap_name):
    """Black text on light colors, white text on dark colors."""
    r, g, b, _ = matplotlib.colormaps[cmap_name](fraction)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return 'white' if luminance < 0.5 else 'black'


def make_choropleth(full, title, cmap_name, vmax):
    """USA choropleth with the matplotlib colormap, 0 as the zero color,
    and a two-letter state label on every state."""
    fig = px.choropleth(
        full,
        locations='State Code',
        locationmode='USA-states',
        color='Completions',
        scope='usa',
        title=title,
        color_continuous_scale=plotly_scale_from_mpl(cmap_name),
        range_color=(0, vmax),
        labels={'Completions': 'Completions'},
    )

    # Text color for each state, based on how dark its fill is
    fractions = (full['Completions'] / vmax).clip(0, 1)
    text_colors = [label_text_color(f, cmap_name) for f in fractions]

    # Plotly places each label at its state's center, so no coordinates are needed.
    # hoverinfo='skip' keeps the labels from cluttering the hover tooltips.
    fig.add_trace(go.Scattergeo(
        locations=full['State Code'],
        locationmode='USA-states',
        text=full['State Code'],
        mode='text',
        textfont=dict(size=11, color=text_colors),
        hoverinfo='skip',
        showlegend=False,
    ))
    return fig

def add_vi_dot(fig, value, dot_color):
    """Dot for the Virgin Islands in the lower right, colored on the map's scale.
    The position is a fixed placeholder, not a real location."""
    fig.add_annotation(
        x=0.97, y=0.05, xref='paper', yref='paper',
        xanchor='right', yanchor='bottom', showarrow=False,
        text=(f'<span style="font-size:24px;color:{dot_color}">●</span> '
              f'US Virgin Islands: {value:,} completions'),
        font=dict(size=12),
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor=dot_color, borderwidth=1, borderpad=4,
    )


def safe_name(text):
    """Turn a label into a filename-safe string."""
    return re.sub(r'[^A-Za-z0-9]+', '_', str(text)).strip('_')


def render_map(slice_df, title, folder, filename, cmap_name, vmax=None):
    """Build one map from a slice of school_df and save it as a PNG.
    If vmax is not given, the max includes the Virgin Islands."""
    totals = state_totals(slice_df)
    if vmax is None:
        vmax = shared_max(totals)  # VI included in the max

    full, vmax_used = build_state_frame(totals, vmax)  # VI not drawn on the map
    fig = make_choropleth(full, title, cmap_name, vmax_used)
    fig.update_layout(
        geo=dict(scope='usa'),
        width=MAP_WIDTH,
        height=MAP_HEIGHT,
        font=dict(size=12),
    )

    vi = vi_value(slice_df)
    dot_color = color_for_value(vi, cmap_name, vmax_used)
    add_vi_dot(fig, vi, dot_color)

    path = os.path.join(OUTPUT_ROOT, folder, filename)
    fig.write_image(path, scale=IMAGE_SCALE)  # needs kaleido
    print(f"✓ Saved: {path}")


# =============================================================================
# 1. OVERALL: all CIPs, all years, all awards
# =============================================================================
render_map(
    school_df,
    title='Total Mining/Petroleum/Engineering Completions by State (2021-2025)',
    folder=FOLDERS['overall'],
    filename='overall_2021-2025.png',
    cmap_name=MAP_COLORMAPS['overall'],
)


# =============================================================================
# 2. BY YEAR: all CIPs and awards, one map per year
#    All years share one color max so they can be compared.
# =============================================================================
year_state_totals = state_totals(school_df, group_cols=('Year', 'State'))
year_vmax = shared_max(year_state_totals)

for year in all_years:
    render_map(
        school_df[school_df['Year'] == year],
        title=f'Mining/Petroleum/Engineering Completions by State ({year})',
        folder=FOLDERS['by_year'],
        filename=f'year_{year}.png',
        cmap_name=MAP_COLORMAPS['by_year'],
        vmax=year_vmax,
    )


# =============================================================================
# 3. BY CIP: one map per CIP code, all years combined
# =============================================================================
for cip in all_cips:
    cip_df = school_df[school_df['CIP_Code'] == cip]
    render_map(
        cip_df,
        title=f'{cip} - {cip_titles[cip]} Completions by State (2021-2025)',
        folder=FOLDERS['by_cip'],
        filename=f'cip_{safe_name(cip)}.png',
        cmap_name=MAP_COLORMAPS['by_cip'],
    )


# =============================================================================
# 4. BY CIP x YEAR: one map per CIP code and year
#    Each CIP's years share one color max so they can be compared.
# =============================================================================
for cip in all_cips:
    cip_df = school_df[school_df['CIP_Code'] == cip]
    cip_year_totals = state_totals(cip_df, group_cols=('Year', 'State'))
    cip_vmax = shared_max(cip_year_totals)

    for year in all_years:
        render_map(
            cip_df[cip_df['Year'] == year],
            title=f'{cip} - {cip_titles[cip]} Completions by State ({year})',
            folder=FOLDERS['by_cip_year'],
            filename=f'cip_{safe_name(cip)}_{year}.png',
            cmap_name=MAP_COLORMAPS['by_cip_year'],
            vmax=cip_vmax,
        )


# =============================================================================
# 5. BY AWARD x YEAR: one map per award level and year, all CIPs combined
#    Each award's years share one color max so they can be compared.
# =============================================================================
award_year_totals = state_totals(school_df, group_cols=('Award_Level', 'Year', 'State'))

for award in all_awards:
    award_df = school_df[school_df['Award_Level'] == award]
    award_vmax = shared_max(award_year_totals[award_year_totals['Award_Level'] == award])

    for year in all_years:
        render_map(
            award_df[award_df['Year'] == year],
            title=f'{award} Completions by State ({year})',
            folder=FOLDERS['by_award_year'],
            filename=f'award_{safe_name(award)}_{year}.png',
            cmap_name=MAP_COLORMAPS['by_award_year'],
            vmax=award_vmax,
        )


# =============================================================================
# 6. BY CIP x AWARD x YEAR: every combination
#    Each CIP + award pair shares one color max across its years.
# =============================================================================
cip_award_year_totals = state_totals(
    school_df, group_cols=('CIP_Code', 'Award_Level', 'Year', 'State')
)

for cip in all_cips:
    for award in all_awards:
        combo_df = school_df[
            (school_df['CIP_Code'] == cip) & (school_df['Award_Level'] == award)
        ]
        if combo_df.empty:
            continue  # this CIP never has this award level

        combo_totals = cip_award_year_totals[
            (cip_award_year_totals['CIP_Code'] == cip)
            & (cip_award_year_totals['Award_Level'] == award)
        ]
        combo_vmax = shared_max(combo_totals)

        for year in all_years:
            render_map(
                combo_df[combo_df['Year'] == year],
                title=(f'{cip} - {cip_titles[cip]}: {award} '
                       f'Completions by State ({year})'),
                folder=FOLDERS['by_cip_award_year'],
                filename=(f'cip_{safe_name(cip)}_'
                          f'award_{safe_name(award)}_{year}.png'),
                cmap_name=MAP_COLORMAPS['by_cip_award_year'],
                vmax=combo_vmax,
            )


print(f"\n✓ All geographic maps saved under '{OUTPUT_ROOT}/'.")
