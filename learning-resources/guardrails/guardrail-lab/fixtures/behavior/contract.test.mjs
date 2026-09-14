import test from 'node:test';
import assert from 'node:assert/strict';

const variant = process.env.LAB_VARIANT;
if (!['bad', 'good'].includes(variant)) throw new Error('LAB_VARIANT must be bad or good');
const { findOrder } = await import(`./${variant}.mjs`);
const orders = [{ id: 'order-1', tenantId: 'shop-a' }];

test('another tenant cannot retrieve this order', () => {
  assert.equal(findOrder(orders, 'shop-b', 'order-1'), undefined);
});
test('the owning tenant can retrieve this order', () => {
  assert.deepEqual(findOrder(orders, 'shop-a', 'order-1'), orders[0]);
});
test('a missing order returns undefined', () => {
  assert.equal(findOrder(orders, 'shop-a', 'missing'), undefined);
});
