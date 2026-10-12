import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load your master data
master_df = pd.read_csv('master_all_CIPs_2021-2025.csv')



# ===== MAP 1: Total Completions by State (All Years) =====
state_totals = master_df.groupby('State')['Completions'].sum().reset_index()
state_totals = state_totals.rename(columns={'State': 'State Code'})

fig = px.choropleth(
    state_totals,
    locations='State Code',
    locationmode='USA-states',
    color='Completions',
    scope='usa',
    title='Total Mining/Petroleum/Engineering Completions by State (2021-2025)',
    color_continuous_scale='YlOrRd',
    labels={'Completions': 'Total Completions'},
    hover_data={'State Code': True, 'Completions': True}
)

fig.update_layout(
    geo=dict(scope='usa'),
    height=700,
    width=1200,
    font=dict(size=12)
)

fig.write_html('map_completions_by_state.html')
print("✓ Saved: map_completions_by_state.html")
fig.show()

# ===== MAP 2: Latest Year (2025) Completions by State =====
latest_year = master_df['Year'].max()
latest_state = master_df[master_df['Year'] == latest_year].groupby('State')['Completions'].sum().reset_index()
latest_state = latest_state.rename(columns={'State': 'State Code'})

fig = px.choropleth(
    latest_state,
    locations='State Code',
    locationmode='USA-states',
    color='Completions',
    scope='usa',
    title=f'Mining/Petroleum/Engineering Completions by State ({latest_year})',
    color_continuous_scale='Viridis',
    labels={'Completions': 'Completions'},
    hover_data={'State Code': True, 'Completions': True}
)

fig.update_layout(
    geo=dict(scope='usa'),
    height=700,
    width=1200
)

fig.write_html(f'map_completions_by_state_{latest_year}.html')
print(f"✓ Saved: map_completions_by_state_{latest_year}.html")
fig.show()

# ===== MAP 3: By CIP Code (Total) =====
for cip in master_df['CIP_Code'].unique():
    cip_title = master_df[master_df['CIP_Code'] == cip]['CIP_Title'].iloc[0]

    cip_state = master_df[master_df['CIP_Code'] == cip].groupby('State')['Completions'].sum().reset_index()
    cip_state = cip_state.rename(columns={'State': 'State Code'})

    fig = px.choropleth(
        cip_state,
        locations='State Code',
        locationmode='USA-states',
        color='Completions',
        scope='usa',
        title=f'{cip} - {cip_title} Completions by State (2021-2025)',
        color_continuous_scale='Blues',
        labels={'Completions': 'Completions'},
        hover_data={'State Code': True, 'Completions': True}
    )

    fig.update_layout(
        geo=dict(scope='usa'),
        height=700,
        width=1200
    )

    filename = f'map_completions_{cip}.html'
    fig.write_html(filename)
    print(f"✓ Saved: {filename}")
    fig.show()

# ===== MAP 4: Animation Over Years =====
state_by_year = master_df.groupby(['Year', 'State'])['Completions'].sum().reset_index()
state_by_year = state_by_year.rename(columns={'State': 'State Code'})

fig = px.choropleth(
    state_by_year,
    locations='State Code',
    locationmode='USA-states',
    color='Completions',
    scope='usa',
    animation_frame='Year',
    title='Mining/Petroleum/Engineering Completions by State (2021-2025)',
    color_continuous_scale='RdYlGn',
    labels={'Completions': 'Completions'},
    hover_data={'State Code': True, 'Completions': True}
)

fig.update_layout(
    geo=dict(scope='usa'),
    height=700,
    width=1200
)

fig.write_html('map_completions_animated.html')
print("✓ Saved: map_completions_animated.html (INTERACTIVE - Play button to animate years!)")
fig.show()

# ===== MAP 5: By Award Level (Latest Year) =====
latest_award = master_df[master_df['Year'] == latest_year].groupby(['State', 'Award_Level'])['Completions'].sum().reset_index()

for award in latest_award['Award_Level'].unique():
    award_state = latest_award[latest_award['Award_Level'] == award].copy()
    award_state = award_state.rename(columns={'State': 'State Code'})

    fig = px.choropleth(
        award_state,
        locations='State Code',
        locationmode='USA-states',
        color='Completions',
        scope='usa',
        title=f'{award} Completions by State ({latest_year})',
        color_continuous_scale='Purples',
        labels={'Completions': 'Completions'},
        hover_data={'State Code': True, 'Completions': True}
    )

    fig.update_layout(
        geo=dict(scope='usa'),
        height=700,
        width=1200
    )

    safe_award = award.replace('/', '_').replace(' ', '_')[:30]
    filename = f'map_{safe_award}_{latest_year}.html'
    fig.write_html(filename)
    print(f"✓ Saved: {filename}")

print("\n✓ All geographic maps complete!")
print("\nMaps created:")
print("  - map_completions_by_state.html")
print("  - map_completions_by_state_2025.html")
print("  - map_completions_[CIP].html (one per CIP code)")
print("  - map_completions_animated.html ← INTERACTIVE! Play to see 2021-2025")
print("  - map_[Award_Level]_2025.html (one per award type)")
