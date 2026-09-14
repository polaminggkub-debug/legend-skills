"""Acceptance checks use observable records/results, not private implementation."""
import os
import unittest
from submissions import NaiveService, ContractService

Service = {'naive': NaiveService, 'contract': ContractService}[os.environ.get('LAB_VARIANT', 'naive')]

class Smoke(unittest.TestCase):
    def test_first_submission_returns_id(self):
        self.assertGreater(Service().submit('alice', 'retry-1', 100)['id'], 0)

class Acceptance(unittest.TestCase):
    def test_same_customer_retry_returns_same_id_and_one_record(self):
        service = Service()
        first = service.submit('alice', 'retry-1', 100)
        retry = service.submit('alice', 'retry-1', 100)
        self.assertEqual(first['id'], retry['id'])
        self.assertEqual(len(service.records), 1)

    def test_reused_key_with_different_amount_rejected_without_write(self):
        service = Service()
        service.submit('alice', 'retry-1', 100)
        with self.assertRaisesRegex(ValueError, 'different payload'):
            service.submit('alice', 'retry-1', 200)
        self.assertEqual(len(service.records), 1)
        self.assertEqual(service.records[0]['amount'], 100)

    def test_other_customer_can_use_same_key_independently(self):
        service = Service()
        first = service.submit('alice', 'retry-1', 100)
        second = service.submit('bob', 'retry-1', 100)
        self.assertNotEqual(first['id'], second['id'])
        self.assertEqual(len(service.records), 2)

    def test_non_positive_amount_rejected_without_write(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):
                service = Service()
                with self.assertRaisesRegex(ValueError, 'positive'):
                    service.submit('alice', 'retry-1', amount)
                self.assertEqual(service.records, [])
