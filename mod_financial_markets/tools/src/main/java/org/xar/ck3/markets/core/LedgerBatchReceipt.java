package org.xar.ck3.markets.core;

public record LedgerBatchReceipt(String id, boolean applied, int transferCount, long feeCents) {
}
