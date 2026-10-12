import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.express.colors import sample_colorscale

master_df = pd.read_csv('master_all_CIPs_2021-2025.csv')

STATE_NAME_TO_ABBR = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
    'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
    'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
    'District of Columbia': 'DC',
    'Virgin Islands': 'VI',
    'Puerto Rico': 'PR',
    'Guam': 'GU',
    'American Samoa': 'AS',
    'Northern Mariana Islands': 'MP',
}

TERRITORY_COORDS = {
    'VI': {'lon': -64.896, 'lat': 18.335, 'name': 'Virgin Islands'},
    'PR': {'lon': -66.589, 'lat': 18.220, 'name': 'Puerto Rico'},
    'GU': {'lon': 144.793, 'lat': 13.444, 'name': 'Guam'},
    'AS': {'lon': -170.132, 'lat': -14.271, 'name': 'American Samoa'},
    'MP': {'lon': 145.738, 'lat': 15.213, 'name': 'Northern Mariana Islands'},
}

def add_state_abbr(df):
    df = df.copy()
    df['State_Abbr'] = df['State'].map(STATE_NAME_TO_ABBR)
    return df.dropna(subset=['State_Abbr'])

def get_color_for_value(value, min_val, max_val, colorscale):
    """Get the color for a value based on the colorscale"""
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)

    # Clamp to [0, 1]
    normalized = max(0, min(1, normalized))

    # Sample the colorscale
    color = sample_colorscale(colorscale, [normalized])[0]
    return color

def add_territories_overlay(fig, data_with_abbr, colorscale, min_val, max_val):
    """Add territory markers to choropleth with matching colors"""
    for abbr, coords in TERRITORY_COORDS.items():
        territory_data = data_with_abbr[data_with_abbr['State_Abbr'] == abbr]

        if len(territory_data) > 0:
            value = territory_data.iloc[0]['Completions']
            state_name = territory_data.iloc[0]['State']

            # Get color matching the heatmap scale
            marker_color = get_color_for_value(value, min_val, max_val, colorscale)

            fig.add_trace(go.Scattergeo(
                lon=[coords['lon']],
                lat=[coords['lat']],
                mode='markers+text',
                marker=dict(
                    size=20,
                    color=marker_color,
                    line=dict(width=2, color='white'),
                    sizemode='diameter'
                ),
                text=[f"{abbr}<br>{int(value)}"],
                textposition='top center',
                textfont=dict(size=9, color='black'),
                hovertemplate=f"<b>{state_name}</b><br>Completions: {int(value)}<extra></extra>",
                name=state_name,
                showlegend=False
            ))

    return fig

def get_geo_layout():
    return dict(
        scope='north america',
        lonaxis=dict(range=[-130, -60]),
        lataxis=dict(range=[20, 50]),
    )

# ===== MAP 1: Total Completions by State (All Years) =====
state_totals = master_df.groupby('State')['Completions'].sum().reset_index()
state_totals = add_state_abbr(state_totals)

min_completions = state_totals['Completions'].min()
max_completions = state_totals['Completions'].max()
colorscale = 'YlOrRd'

territories = state_totals[state_totals['State_Abbr'].isin(TERRITORY_COORDS.keys())]
states_only = state_totals[~state_totals['State_Abbr'].isin(TERRITORY_COORDS.keys())]

fig = px.choropleth(
    states_only,
    locations='State_Abbr',
    locationmode='USA-states',
    color='Completions',
    scope='usa',
    title='Mining/Petroleum/Engineering Completions by Location (2021-2025)',
    color_continuous_scale=colorscale,
    labels={'Completions': 'Total Completions'},
    hover_name='State',
    hover_data={'State_Abbr': False, 'Completions': True}
)

fig = add_territories_overlay(fig, state_totals, colorscale, min_completions, max_completions)

fig.update_layout(
    geo=get_geo_layout(),
    height=700,
    width=1200,
    font=dict(size=12)
)

fig.write_html('map_completions_by_state.html')
print("✓ Saved: map_completions_by_state.html")
fig.show()

# ===== MAP 2: Latest Year Completions by State =====
latest_year = master_df['Year'].max()
latest_state = master_df[master_df['Year'] == latest_year].groupby('State')['Completions'].sum().reset_index()
latest_state = add_state_abbr(latest_state)

min_latest = latest_state['Completions'].min()
max_latest = latest_state['Completions'].max()
colorscale_latest = 'Viridis'

territories_latest = latest_state[latest_state['State_Abbr'].isin(TERRITORY_COORDS.keys())]
states_only_latest = latest_state[~latest_state['State_Abbr'].isin(TERRITORY_COORDS.keys())]

fig = px.choropleth(
    states_only_latest,
    locations='State_Abbr',
    locationmode='USA-states',
    color='Completions',
    scope='usa',
    title=f'Mining/Petroleum/Engineering Completions by Location ({latest_year})',
    color_continuous_scale=colorscale_latest,
    labels={'Completions': 'Completions'},
    hover_name='State',
    hover_data={'State_Abbr': False, 'Completions': True}
)

fig = add_territories_overlay(fig, latest_state, colorscale_latest, min_latest, max_latest)

fig.update_layout(
    geo=get_geo_layout(),
    height=700,
    width=1200
)

fig.write_html(f'map_completions_by_state_{latest_year}.html')
print(f"✓ Saved: map_completions_by_state_{latest_year}.html")
fig.show()

# ===== MAP 3: By CIP Code (Total) =====

for cip in sorted(master_df['CIP_Code'].unique()):
    cip_title = master_df[master_df['CIP_Code'] == cip]['CIP_Title'].iloc[0]

    cip_state = master_df[master_df['CIP_Code'] == cip].groupby('State')['Completions'].sum().reset_index()
    cip_state = add_state_abbr(cip_state)

    # Calculate min/max only from states with actual data (> 0)
    cip_with_data = cip_state[cip_state['Completions'] > 0]

    if len(cip_with_data) > 0:
        min_cip = cip_with_data['Completions'].min()
        max_cip = cip_with_data['Completions'].max()
    else:
        min_cip = 0
        max_cip = 1

    print(f"\n{cip} - Min: {min_cip}, Max: {max_cip}")

    colorscale_cip = 'Blues'

    territories_cip = cip_state[cip_state['State_Abbr'].isin(TERRITORY_COORDS.keys())]
    states_only_cip = cip_state[~cip_state['State_Abbr'].isin(TERRITORY_COORDS.keys())]

    fig = px.choropleth(
        states_only_cip,
        locations='State_Abbr',
        locationmode='USA-states',
        color='Completions',
        scope='usa',
        title=f'{cip} - {cip_title} Completions by Location (2021-2025)',
        color_continuous_scale=colorscale_cip,
        labels={'Completions': 'Completions'},
        hover_name='State',
        hover_data={'State_Abbr': False, 'Completions': True}
    )

    fig = add_territories_overlay(fig, cip_state, colorscale_cip, 0, max_cip)

    fig.update_layout(
        geo=get_geo_layout(),
        coloraxis=dict(cmin=0, cmax=max_cip),  # ← SET COLOR SCALE RANGE HERE
        height=700,
        width=1200
    )

    filename = f'map_completions_{cip}.html'
    fig.write_html(filename)
    print(f"✓ Saved: {filename}")
    fig.show()

# ===== MAP 4: Animation Over Years =====
state_by_year = master_df.groupby(['Year', 'State'])['Completions'].sum().reset_index()
state_by_year = add_state_abbr(state_by_year)

# Get min/max across all years for consistent scale
min_all_years = state_by_year['Completions'].min()
max_all_years = state_by_year['Completions'].max()
colorscale_anim = 'RdYlGn'

states_only_anim = state_by_year[~state_by_year['State_Abbr'].isin(TERRITORY_COORDS.keys())]

fig = px.choropleth(
    states_only_anim,
    locations='State_Abbr',
    locationmode='USA-states',
    color='Completions',
    scope='usa',
    animation_frame='Year',
    title='Mining/Petroleum/Engineering Completions by Location (2021-2025)',
    color_continuous_scale=colorscale_anim,
    labels={'Completions': 'Completions'},
    hover_name='State',
    hover_data={'State_Abbr': False, 'Completions': True}
)

# Add territories for each frame
for year in sorted(state_by_year['Year'].unique()):
    year_data = state_by_year[state_by_year['Year'] == year]

    for abbr, coords in TERRITORY_COORDS.items():
        territory_data = year_data[year_data['State_Abbr'] == abbr]

        if len(territory_data) > 0:
            value = territory_data.iloc[0]['Completions']
            state_name = territory_data.iloc[0]['State']

            # Get color matching the scale
            marker_color = get_color_for_value(value, min_all_years, max_all_years, colorscale_anim)

            fig.add_trace(go.Scattergeo(
                lon=[coords['lon']],
                lat=[coords['lat']],
                mode='markers+text',
                marker=dict(size=20, color=marker_color, line=dict(width=2, color='white'), sizemode='diameter'),
                text=[f"{abbr}<br>{int(value)}"],
                textposition='top center',
                textfont=dict(size=9, color='black'),
                hovertemplate=f"<b>{state_name}</b><br>Completions: {int(value)}<extra></extra>",
                name=state_name,
                showlegend=False
            ))

fig.update_layout(
    geo=get_geo_layout(),
    coloraxis=dict(cmin=min_all_years, cmax=max_all_years),  # ← SET COLOR SCALE RANGE HERE
    height=700,
    width=1200
)

fig.write_html('map_completions_animated.html')
print("✓ Saved: map_completions_animated.html (INTERACTIVE - Play to see 2021-2025!)")
fig.show()
# ===== MAP 5: By Award Level (Latest Year) =====
latest_award = master_df[master_df['Year'] == latest_year].groupby(['State', 'Award_Level'])['Completions'].sum().reset_index()

for award in sorted(latest_award['Award_Level'].unique()):
    award_state = latest_award[latest_award['Award_Level'] == award].copy()
    award_state = add_state_abbr(award_state)

    min_award = award_state['Completions'].min()
    max_award = award_state['Completions'].max()
    colorscale_award = 'Purples'

    territories_award = award_state[award_state['State_Abbr'].isin(TERRITORY_COORDS.keys())]
    states_only_award = award_state[~award_state['State_Abbr'].isin(TERRITORY_COORDS.keys())]

    fig = px.choropleth(
        states_only_award,
        locations='State_Abbr',
        locationmode='USA-states',
        color='Completions',
        scope='usa',
        title=f'{award} Completions by Location ({latest_year})',
        color_continuous_scale=colorscale_award,
        labels={'Completions': 'Completions'},
        hover_name='State',
        hover_data={'State_Abbr': False, 'Completions': True}
    )

    fig = add_territories_overlay(fig, award_state, colorscale_award, min_award, max_award)

    fig.update_layout(
        geo=get_geo_layout(),
        height=700,
        width=1200
    )

    safe_award = award.replace('/', '_').replace(' ', '_')[:30]
    filename = f'map_{safe_award}_{latest_year}.html'
    fig.write_html(filename)
    print(f"✓ Saved: {filename}")

print("\n✓ All geographic maps complete with color-aligned territories!")
