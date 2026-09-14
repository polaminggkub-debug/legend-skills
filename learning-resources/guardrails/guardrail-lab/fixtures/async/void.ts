declare function storeInvoice(): Promise<void>;
export function finishInvoice(): void {
  void storeInvoice();
}
