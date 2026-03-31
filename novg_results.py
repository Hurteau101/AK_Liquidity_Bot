from Database.database import Database
import requests
import json


class Results:
    def get_results(self):
        db = Database()
        outcome_data = db.get_outcome_ids()

        results = self.api_results(outcome_data)

        if results:
            db.bulk_update_results(results)

    def api_results(self, outcome_data: dict):
        url = "https://gql.novig.us/v1/graphql"

        payload = json.dumps({
            "query": """
                query ($ids: [uuid!]!) {
                  market(where: { outcomes: { id: { _in: $ids } } }) {
                    type
                    outcomes(where: { id: { _in: $ids } }) {
                      id
                      description
                      status
                      last
                      available
                    }
                  }
                }
            """,
            "variables": {
                "ids": list(outcome_data.keys())
            }
        })

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 200:
            return self.filter_results(response.json(), outcome_data)

    def filter_results(self, raw_results, outcome_data: dict):
        results = []

        for outcome in raw_results.get("data", {}).get("market", []):
            if outcome.get("outcomes"):
                for market in outcome.get("outcomes"):
                    if market.get("status") != "TBD":
                        side = outcome_data.get(market.get("id"), {})
                        if side is None:
                            results.append(
                                (market.get("id"), market.get("status"), outcome.get("type"), market.get("description"))
                            )

                            continue

                        if side in market.get("description", "").lower():
                            results.append(
                                (market.get("id"), market.get("status"), outcome.get("type"), market.get("description"))
                            )

        return results



if __name__ == "__main__":
    results = Results()
    results.get_results()