declare function storeInvoice(): Promise<void>;
export function finishInvoice(): void {
  storeInvoice();
}
