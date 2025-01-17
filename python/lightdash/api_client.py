import json
from urllib.parse import urljoin
import requests


class LightdashApiClient:
    def __init__(self, base_url, api_key, project_id):
        session = requests.Session()
        session.headers.update({
            'Authorization': f'ApiKey {api_key}',
            'Content-Type': 'application/json',
        })
        self.session = session
        self.base_url = base_url
        self.project_id = project_id

    def _url(self, path):
        return urljoin(self.base_url, path.lstrip('/'))

    def _api_call(self, method, path, **kwargs):
        request = requests.Request(method, self._url(path), **kwargs)
        response = self.session.send(self.session.prepare_request(request))
        if not response.ok:
            raise ValueError(f'{response.status_code}: {json.dumps(response.json(), indent=2)}')
        try:
            j = response.json()
        except json.decoder.JSONDecodeError as e:
            print(response.text)
            raise e
        if j['status'] == 'ok':
            return j.get('results')
        return j['error']

    def health(self):
        return self._api_call('GET', '/health')

    def space_summary_to_detail(self, space_summary):
        space_detail = {
            **space_summary,
            'queries': [
                self.saved_chart(query['uuid'])
                for query
                in space_summary['queries']
            ],
            'dashboards': [
                self.dashboard(dashboard['uuid'])
                for dashboard
                in space_summary['dashboards']
            ]
        }
        return space_detail

    def space(self, space_uuid, summary=True):
        space_summary = self._api_call('GET', f'/projects/{self.project_id}/spaces/{space_uuid}')
        return space_summary if summary else self.space_summary_to_detail(space_summary)

    def spaces(self, summary=True):
        spaces_summary = self._api_call('GET', f'/projects/{self.project_id}/spaces')
        if summary:
            return spaces_summary
        return [
            self.space_summary_to_detail(s)
            for s
            in spaces_summary
        ]

    def dashboard(self, dashboard_uuid):
        return self._api_call('GET', f'/dashboards/{dashboard_uuid}')

    def saved_chart(self, chart_uuid):
        return self._api_call('GET', f'/saved/{chart_uuid}')

    def create_empty_space(self, space):
        return self._api_call('POST', f'/projects/{self.project_id}/spaces', json=space)

    def create_saved_chart(self, saved_chart):
        return self._api_call('POST', f'/projects/{self.project_id}/saved', json=saved_chart)

    def create_dashboard(self, dashboard):
        return self._api_call('POST', f'/projects/{self.project_id}/dashboards', json=dashboard)

    def create_space(self, space):
        empty_space = self.create_empty_space({
            key: space[key] for key in space if key not in ['queries', 'dashboards']
        })
        for idx, saved_chart in enumerate(space['queries']):
            print(f'Coping chart {idx+1} of {len(space["queries"])}: {saved_chart["name"]}')
            self.create_saved_chart({**saved_chart, 'spaceUuid': empty_space['uuid']})
        for idx, dashboard in enumerate(space['dashboards']):
            print(f'Coping dashboard {idx+1} of {len(space["dashboards"])}: {dashboard["name"]}')
            self.create_dashboard({**dashboard, 'spaceUuid': empty_space['uuid']})

    def delete_space(self, space_uuid):
        return self._api_call('DELETE', f'/projects/{self.project_id}/spaces/{space_uuid}')