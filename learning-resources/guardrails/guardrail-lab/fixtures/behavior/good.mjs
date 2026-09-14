export function findOrder(orders, tenantId, orderId) {
  return orders.find(order => order.id === orderId && order.tenantId === tenantId);
}
