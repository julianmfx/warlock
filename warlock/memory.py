# memory.py

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

    # prints logs in human readable format
    def print_log(self):
        for entry in self._log:
            print(f"[{entry['ts']}] {entry['key']} = {entry['value']}")
