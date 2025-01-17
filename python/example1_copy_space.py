from lightdash.api_client import LightdashApiClient

# Lightdash space to copy
SOURCE_URL = 'https://app.lightdash.cloud/api/v1/'
SOURCE_API_KEY = ''
SOURCE_PROJECT_ID = ''

# Lightdash project to create new space
TARGET_URL = 'https://eu1.lightdash.cloud/api/v1/'
TARGET_API_KEY = ''
TARGET_PROJECT_ID = ''

if __name__ == '__main__':
    source_client = LightdashApiClient(SOURCE_URL, SOURCE_API_KEY, SOURCE_PROJECT_ID)
    target_client = LightdashApiClient(TARGET_URL, TARGET_API_KEY, TARGET_PROJECT_ID)

    # Get all spaces
    print('Getting all spaces')
    all_spaces = source_client.spaces(summary=True)
    SPACE_UUID_MAP = {}
    for idx, s in enumerate(all_spaces):
        new_space = {'name': s['name'], 'isPrivate': s['isPrivate']}
        print(f'Coping space {idx+1} of {len(all_spaces)}: {new_space["name"]}')
        new_space = target_client.create_empty_space(new_space)
        SPACE_UUID_MAP[s["uuid"]] = new_space["uuid"]

    print('Getting all spaces and content')
    full_spaces = [source_client.space(s["uuid"], summary=False) for s in all_spaces]
    all_charts = [chart for space in full_spaces for chart in space["queries"]]
    all_dashboards = [dashboard for space in full_spaces for dashboard in space["dashboards"]]

    CHART_UUID_MAP = {}
    for idx, chart in enumerate(all_charts):
        print(f'Copying chart {idx+1} of {len(all_charts)}: {chart["name"]}')
        new_chart = target_client.create_saved_chart({**chart, 'spaceUuid': SPACE_UUID_MAP[chart["spaceUuid"]]})
        CHART_UUID_MAP[chart["uuid"]] = new_chart["uuid"]

    for idx, dashboard in enumerate(all_dashboards):
        print(f'Copying dashboard {idx+1} of {len(all_dashboards)}: {dashboard["name"]}')
        new_dashboard = {
            'name': dashboard['name'],
            'description': dashboard.get('description', ''),
            'spaceUuid': SPACE_UUID_MAP[dashboard["spaceUuid"]]
        }
        if dashboard.get('tiles'):
            new_dashboard['tiles'] = [
                {
                    **tile,
                    'properties': {
                        **tile['properties'],
                        # try to get the new id but if it was already a broken reference, use the old id
                        'savedChartUuid': CHART_UUID_MAP.get(tile['properties']['savedChartUuid'], tile['properties']['savedChartUuid'])
                    }
                } 
                if tile['type'] == 'saved_chart' else tile 
                for tile in dashboard.get('tiles', [])
            ]
        else:
            new_dashboard['tiles'] = []
        if dashboard.get('filters'):
            new_dashboard['filters'] = dashboard['filters']
        target_client.create_dashboard(new_dashboard)
