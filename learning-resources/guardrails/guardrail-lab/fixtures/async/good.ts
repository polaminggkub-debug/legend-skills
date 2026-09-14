declare function storeInvoice(): Promise<void>;
export async function finishInvoice(): Promise<void> {
  await storeInvoice();
}
