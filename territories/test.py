import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
}

# Get totals
state_totals = master_df.groupby('State')['Completions'].sum().reset_index()
state_totals['State_Abbr'] = state_totals['State'].map(STATE_NAME_TO_ABBR)

print("States in data:")
print(state_totals[['State', 'State_Abbr', 'Completions']])

# Split states and territories
vi_data = state_totals[state_totals['State'] == 'Virgin Islands']
states_data = state_totals[state_totals['State'] != 'Virgin Islands']

print(f"\nVI Data: {len(vi_data)} rows")
print(vi_data)

print(f"\nStates Data: {len(states_data)} rows")

# Create base map
fig = px.choropleth(
    states_data,
    locations='State_Abbr',
    locationmode='USA-states',
    color='Completions',
    scope='usa',
    title='Test Map',
    color_continuous_scale='YlOrRd',
)

# Add VI manually
if len(vi_data) > 0:
    vi_value = vi_data['Completions'].values[0]
    print(f"\nAdding VI with value: {vi_value}")

    fig.add_trace(go.Scattergeo(
        lon=[-64.896],
        lat=[18.335],
        mode='markers+text',
        marker=dict(size=25, color='darkred', line=dict(width=2, color='white')),
        text=['VI<br>' + str(int(vi_value))],
        textposition='top center',
        hovertemplate='Virgin Islands: ' + str(int(vi_value)),
        showlegend=False
    ))

fig.update_layout(
    geo=dict(
        scope='usa',
        projection_type='albers usa',
        # Add these lines to show Caribbean:
        lonaxis=dict(range=[-180, -40]),
        lataxis=dict(range=[10, 50]),
    ),
    height=700,
    width=1200
)
fig.write_html('test_map.html')
fig.show()

# fig.update_layout(geo=dict(scope='usa'), height=700, width=1200)
# fig.write_html('test_map.html')
# print("\n✓ Saved: test_map.html")
# fig.show()
