package com.xenoamess.kaishek.runtime;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/** Append-only transaction receipts with conservation and refund upper bounds. */
public final class ReceiptJournal {
    private final Map<String, Long> balances = new ConcurrentHashMap<>();
    private final Map<String, Receipt> receipts = new ConcurrentHashMap<>();
    private final List<Receipt> journal = Collections.synchronizedList(new ArrayList<>());

    public ReceiptJournal() { }
    public ReceiptJournal(Map<String, Long> initialBalances) {
        if (initialBalances != null) for (var e : initialBalances.entrySet()) setBalanceKey(e.getKey(), e.getValue());
    }
    private static String key(String account, String resource) {
        requireIdentifier(account, "account");
        requireIdentifier(resource, "resource");
        return account + "\u0000" + resource;
    }
    private static void requireIdentifier(String value, String label) {
        if (value == null || value.isBlank()) throw new IllegalArgumentException(label + " is blank");
    }
    private void setBalanceKey(String k, long value) { if (value < 0) throw new IllegalArgumentException("negative balance"); balances.put(k, value); }
    public long balance(String account, String resource) { return balances.getOrDefault(key(account, resource), 0L); }
    public synchronized void credit(String account, String resource, long amount) {
        if (amount < 0) throw new IllegalArgumentException("negative credit");
        balances.merge(key(account, resource), amount, Math::addExact);
    }
    public synchronized Receipt debit(String transactionId, String account, String resource, long amount) {
        requireIdentifier(transactionId, "transaction id");
        // Validate all identifiers before changing the balance. Receipt's own
        // constructor also validates them, but doing it here prevents a failed
        // debit from leaving a partially-applied balance mutation.
        String balanceKey = key(account, resource);
        if (amount < 0) throw new IllegalArgumentException("negative debit");
        Receipt old = receipts.get(transactionId); if (old != null) {
            if (!old.account().equals(account) || !old.resource().equals(resource) || old.charged() != amount) throw new IllegalStateException("transaction id conflict");
            return old;
        }
        long before = balance(account, resource); if (before < amount) throw new IllegalStateException("insufficient resource");
        setBalanceKey(balanceKey, before - amount);
        Receipt receipt = new Receipt(transactionId, account, resource, amount, 0); receipts.put(transactionId, receipt); journal.add(receipt); return receipt;
    }
    public synchronized Receipt refund(String transactionId, long amount) {
        requireIdentifier(transactionId, "transaction id");
        Receipt old = receipts.get(transactionId); if (old == null) throw new IllegalArgumentException("unknown transaction");
        if (amount < 0 || amount > old.net()) throw new IllegalArgumentException("refund exceeds charged amount");
        if (amount == 0) return old;
        String balanceKey = key(old.account(), old.resource());
        // Compute every fallible value before publishing either side of the
        // receipt. In particular, Math.addExact may overflow at Long.MAX_VALUE;
        // an overflow must leave both balance and receipt unchanged.
        long nextBalance = Math.addExact(balance(old.account(), old.resource()), amount);
        Receipt next = new Receipt(old.transactionId(), old.account(), old.resource(), old.charged(), old.refunded() + amount);
        setBalanceKey(balanceKey, nextBalance);
        receipts.put(transactionId, next);
        journal.add(next);
        return next;
    }
    /** Alias accepting an explicit receipt id; receipt ids are transaction ids in Phase 0. */
    public Receipt refund(String transactionId, String receiptId, long amount) {
        if (!Objects.equals(transactionId, receiptId)) throw new IllegalArgumentException("receipt id does not match transaction");
        return refund(transactionId, amount);
    }
    public Receipt get(String transactionId) { return receipts.get(transactionId); }
    public List<Receipt> entries() { synchronized (journal) { return List.copyOf(journal); } }
    public long totalCharged(String resource) { return receipts.values().stream().filter(r -> r.resource().equals(resource)).mapToLong(Receipt::charged).sum(); }
    public long totalRefunded(String resource) { return receipts.values().stream().filter(r -> r.resource().equals(resource)).mapToLong(Receipt::refunded).sum(); }
}
