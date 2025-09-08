from database import Database
import requests
import json


class Results:
    def get_results(self):
        db = Database()
        outcome_ids = db.get_outcome_ids()
        results = self.api_results(outcome_ids)
        if results:
            db.bulk_update_results(results)

    def api_results(self, ids):
        url = "https://gql.novig.us/v1/graphql"

        payload = json.dumps({
            "query": "query ($ids: [uuid!]!) {\n  outcome(where: { id: { _in: $ids } }) {\n    id\n    description\n    status\n    last\n    available\n  }\n}",
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
            (outcome.get("id"), outcome.get("status"))
            for outcome in raw_results.get("data", {}).get("outcome", [])
            if outcome.get("status") != "TBD"
        ]


if __name__ == "__main__":
    results = Results()
    results.get_results()