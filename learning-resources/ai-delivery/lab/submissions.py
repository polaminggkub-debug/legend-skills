"""Original teaching fixture: sequential in-memory behavior, not production storage."""
class NaiveService:
    def __init__(self):
        self.records = []

    def submit(self, customer, key, amount):
        record = {'id': len(self.records) + 1, 'customer': customer,
                  'key': key, 'amount': amount}
        self.records.append(record)
        return dict(record)


class ContractService:
    def __init__(self):
        self.records = []
        self.requests = {}

    def submit(self, customer, key, amount):
        if amount <= 0:
            raise ValueError('amount must be positive')
        identity = (customer, key)
        if identity in self.requests:
            existing = self.requests[identity]
            if existing['amount'] != amount:
                raise ValueError('key reused with different payload')
            return dict(existing)
        record = {'id': len(self.records) + 1, 'customer': customer,
                  'key': key, 'amount': amount}
        self.records.append(record)
        self.requests[identity] = record
        return dict(record)
