from gql import Client
from gql.transport.requests import RequestsHTTPTransport

from . import queries
import conf


class GQLClient:
    def __init__(self):
        transport = RequestsHTTPTransport(url=conf.ENDPOINT)
        self._client = Client(transport=transport)

    # Determine number of assets onchain for a given policy_id
    def get_asset_count(self, policy_id):
        params = {"policy_id": policy_id}
        resp = self._client.execute(queries.asset_count, variable_values=params)
        return resp["assets_aggregate"]["aggregate"]["count"]

    # Obtain onchain assets for a given policy_id
    def get_assets(self, policy_id, offset):
        params = {"policy_id": policy_id, "offset": offset}
        resp = self._client.execute(queries.metadata, variable_values=params)
        return resp["transactions"]


