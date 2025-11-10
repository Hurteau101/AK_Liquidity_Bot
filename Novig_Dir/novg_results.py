from database import Database
import requests
import json


class Results:
    def get_results(self):
        db = Database()
        outcome_ids = db.get_outcome_ids()
        results = self.api_results(outcome_ids)
        if results:
            print(results)
            db.bulk_update_results(results)

    def api_results(self, ids):
        url = "https://gql.novig.us/v1/graphql"

        # payload = json.dumps({
        #     "query": "query ($ids: [uuid!]!) {\n  outcome(where: { id: { _in: $ids } }) {\n    id\n    description\n    status\n    last\n    available\n  }\n}",
        #     "variables": {
        #         "ids": ids
        #     }
        # })

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
                "ids": ids
            }
        })

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            return self.filter_results(response.json())

    def filter_results(self, raw_results):
        return [
            (market.get("id"), market.get("status"), outcome.get("type"), market.get("description"))
            for outcome in raw_results.get("data", {}).get("market", [])
            if outcome.get("outcomes")
            for market in outcome.get("outcomes")
            if market.get("status") != "TBD"
        ]


if __name__ == "__main__":
    results = Results()
    results.get_results()