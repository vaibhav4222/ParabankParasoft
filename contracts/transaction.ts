/** Exact REST transaction response; JSON Schema provides runtime enforcement. */
export interface Transaction {
  id: number;
  accountId: number;
  type: 'Credit' | 'Debit';
  /** Unix timestamp in milliseconds, as emitted by ParaBank REST JSON. */
  date: number;
  amount: number;
  description: string;
}
export type TransactionHistory = Transaction[];
