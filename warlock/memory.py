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
