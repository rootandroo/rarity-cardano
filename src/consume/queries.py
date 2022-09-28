from gql import gql

metadata = gql(
    """
query metadataByPolicy($policy_id: Hash28Hex, $offset: Int) {
  transactions(where: {mint: {asset: {policyId: {_eq: $policy_id}}}},
  limit: 2500,
  offset: $offset) {
    metadata {
      value
    }
  }
}
    """
)

asset_count = gql(
    """
query assetCount($policy_id: Hash28Hex) {
  assets_aggregate(where: { policyId: { _eq: $policy_id } }) {
    aggregate {
      count
    }
  }
}     
    """
)
