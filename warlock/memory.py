# memory.py

import json
from datetime import datetime


class Memory:
    # creates the store and the log
    def __init__(self):
        self._store = {}
        self._log = []

    # stores a value in store and logs it
    def write(self, key, value):
        self._store[key] = value
        self._log.append(
            {
                "ts": datetime.utcnow().isoformat(),
                "key": key,
                "value": value,
            }
        )

    def patch(self, key, sub_key, value):
        if key not in self._store:
            self._store[key] = {}
        self._store[key][sub_key] = value
        self._log.append(
            {
                "ts": datetime.utcnow().isoformat(),
                "key": f"{key}.{sub_key}",
                "value": value,
            }
        )

    # retrieves one value from store
    def read(self, key):
        return self._store.get(key, None)

    # shows full current state
    def dump(self):
        return self._store

    # shows raw log history
    def log(self):
        return self._log

    def print_log(self):
        separator = "─" * 60
        for entry in self._log:
            print(f"\n{separator}")
            print(f"  {entry['ts']}  │  {entry['key']}")
            print(separator)
            value = entry["value"]
            if isinstance(value, dict) and all(
                isinstance(v, str) for v in value.values()
            ):
                for k, v in value.items():
                    print(f"[{k}]\n{v}")
            elif isinstance(value, (dict, list)):
                print(json.dumps(value, indent=2))
            else:
                print(value)
        print(f"\n{separator}")

    def print_run_summary(self):
        token_spend = self._store.get("token_spend", {})
        timing = self._store.get("timing", {})
        separator = "─" * 60
        print(f"\n{separator}")
        print("Run Summary")
        print(separator)
        total_cost = 0.0000
        for agent, spend in token_spend.items():
            input_cost = spend["input_tokens"] * 0.80 / 1_000_000
            output_cost = spend["output_tokens"] * 4.00 / 1_000_000
            cost = input_cost + output_cost
            total_cost += cost
            seconds = timing.get(agent, "─")
            print(f"{agent:<20} ${cost:.4f} {seconds}s")
        print(f"{separator}")
        print(f"Total Cost: ${total_cost:.4f}")
        print(separator)
