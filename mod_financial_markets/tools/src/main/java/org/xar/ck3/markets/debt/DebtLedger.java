package org.xar.ck3.markets.debt;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import org.xar.ck3.markets.core.AccountId;

/** Claim authority. Cash plans must be committed through the shared wallet before publication. */
public final class DebtLedger {
    public static final long MAX_SINGLE_FUND_PAYMENT_CENTS = 100_000_000L;
    public static final long MAX_CLAIM_CENTS = 1_000_000_000_000L;
    public enum SettlementKind { VARIATION, FUNDING, LIQUIDATION, EXPIRY }
    public record SettlementKey(String sourceId, long day, SettlementKind kind) {
        public SettlementKey {
            if (sourceId == null || sourceId.isBlank() || day < 0 || kind == null)
                throw new IllegalArgumentException("invalid settlement identity");
        }
    }
    public record Payment(AccountId from, AccountId to, long cents) {
        public Payment {
            Objects.requireNonNull(from); Objects.requireNonNull(to);
            if (from.equals(to) || cents <= 0) throw new IllegalArgumentException("invalid payment");
        }
    }
    public record DebtView(SettlementKey key, AccountId debtor, AccountId winner, AccountId fund,
                           long originalShortfallCents, long fundPaidCents,
                           long winnerUnpaidCents, long fundRecourseCents,
                           long repaidCents, long writtenOffCents, long revision) {
        public DebtView {
            Objects.requireNonNull(key); Objects.requireNonNull(debtor);
            Objects.requireNonNull(winner); Objects.requireNonNull(fund);
            if (debtor.equals(winner) || debtor.equals(fund) || winner.equals(fund))
                throw new IllegalArgumentException("economic parties must differ");
            if (originalShortfallCents <= 0 || originalShortfallCents > MAX_CLAIM_CENTS
                    || fundPaidCents < 0 || fundPaidCents > originalShortfallCents
                    || winnerUnpaidCents < 0 || fundRecourseCents < 0 || fundRecourseCents > fundPaidCents
                    || repaidCents < 0 || writtenOffCents < 0 || revision < 0)
                throw new IllegalArgumentException("negative or invalid claim");
            long outstanding = Math.addExact(winnerUnpaidCents, fundRecourseCents);
            if (Math.addExact(outstanding, Math.addExact(repaidCents, writtenOffCents)) != originalShortfallCents)
                throw new IllegalArgumentException("claim does not reconcile");
        }
        public long outstandingCents() { return Math.addExact(winnerUnpaidCents, fundRecourseCents); }
    }
    public record CoverPlan(SettlementKey key, AccountId debtor, AccountId winner, AccountId fund,
                            long shortfallCents, boolean insured, List<Payment> transfers, DebtView debt, boolean replay) {
        public CoverPlan { transfers = List.copyOf(transfers); }
    }
    public record RepaymentPlan(String operationId, SettlementKey key, AccountId payer,
                                long requestedCents, List<Payment> transfers, DebtView debt, boolean replay) {
        public RepaymentPlan { transfers = List.copyOf(transfers); }
        public long paidCents() { return transfers.stream().mapToLong(Payment::cents).reduce(0, Math::addExact); }
    }
    public record WriteDown(String operationId, SettlementKey key, long winnerReductionCents,
                            long fundReductionCents, long previousRevision, DebtView debt, boolean replay) { }
    public record Snapshot(List<DebtView> debts, List<CoverPlan> covers,
                           List<RepaymentPlan> repayments, List<WriteDown> writeDowns) {
        public Snapshot {
            debts = List.copyOf(debts); covers = List.copyOf(covers);
            repayments = List.copyOf(repayments); writeDowns = List.copyOf(writeDowns);
        }
    }

    private final Map<SettlementKey, DebtView> debts = new LinkedHashMap<>();
    private final Map<SettlementKey, CoverPlan> covers = new LinkedHashMap<>();
    private final Map<String, RepaymentPlan> repayments = new LinkedHashMap<>();
    private final Map<String, WriteDown> writeDowns = new LinkedHashMap<>();
    private final Map<SettlementKey, CoverPlan> pendingCovers = new LinkedHashMap<>();
    private final Map<SettlementKey, RepaymentPlan> pendingRepayments = new LinkedHashMap<>();
    private sealed interface DebtHistory permits RepaymentHistory, WriteDownHistory { }
    private record RepaymentHistory(RepaymentPlan payment) implements DebtHistory { }
    private record WriteDownHistory(WriteDown reduction) implements DebtHistory { }

    public synchronized CoverPlan prepareCover(SettlementKey key, AccountId debtor, AccountId winner,
                                               AccountId fund, long shortfallCents, long fundAvailableCents) {
        return prepareCover(key, debtor, winner, fund, shortfallCents, fundAvailableCents,
                key.kind() != SettlementKind.FUNDING);
    }

    public synchronized CoverPlan prepareCover(SettlementKey key, AccountId debtor, AccountId winner,
                                               AccountId fund, long shortfallCents, long fundAvailableCents, boolean insured) {
        Objects.requireNonNull(key); Objects.requireNonNull(debtor);
        Objects.requireNonNull(winner); Objects.requireNonNull(fund);
        if (shortfallCents <= 0 || shortfallCents > MAX_CLAIM_CENTS || fundAvailableCents < 0)
            throw new IllegalArgumentException("invalid funding");
        insured = insured && key.kind() != SettlementKind.FUNDING;
        CoverPlan prior = covers.get(key);
        if (prior != null) {
            requireSameCover(prior, debtor, winner, fund, shortfallCents);
            if (prior.insured() != insured) throw new IllegalArgumentException("coverage identity conflict");
            return new CoverPlan(key, debtor, winner, fund, shortfallCents, insured, List.of(), debts.get(key), true);
        }
        CoverPlan pending = pendingCovers.get(key);
        if (pending != null) {
            requireSameCover(pending, debtor, winner, fund, shortfallCents);
            if (pending.insured() != insured) throw new IllegalArgumentException("coverage identity conflict");
            return pending;
        }
        long reserved = pendingCovers.values().stream().filter(plan -> plan.fund().equals(fund))
                .mapToLong(plan -> plan.debt().fundPaidCents()).reduce(0, Math::addExact);
        if (insured && reserved > fundAvailableCents) throw new IllegalStateException("fund changed while plans are outstanding");
        long paid = insured ? Math.min(MAX_SINGLE_FUND_PAYMENT_CENTS, Math.min(shortfallCents, fundAvailableCents - reserved)) : 0;
        DebtView debt = new DebtView(key, debtor, winner, fund, shortfallCents, paid,
                shortfallCents - paid, paid, 0, 0, 0);
        List<Payment> payments = paid == 0 ? List.of() : List.of(new Payment(fund, winner, paid));
        CoverPlan plan = new CoverPlan(key, debtor, winner, fund, shortfallCents, insured, payments, debt, false);
        pendingCovers.put(key, plan);
        return plan;
    }

    /** Caller owns the wallet batch and must not execute another cash batch between prepare and commit. */
    public synchronized void commitCover(CoverPlan plan) {
        Objects.requireNonNull(plan);
        if (plan.replay()) {
            CoverPlan old = covers.get(plan.key());
            if (old == null) throw new IllegalArgumentException("unknown replay");
            requireSameCover(old, plan.debtor(), plan.winner(), plan.fund(), plan.shortfallCents());
            if (old.insured() != plan.insured()) throw new IllegalArgumentException("coverage identity conflict");
            return;
        }
        if (!plan.equals(pendingCovers.get(plan.key()))) throw new IllegalArgumentException("unprepared cover");
        debts.put(plan.key(), plan.debt()); covers.put(plan.key(), plan); pendingCovers.remove(plan.key());
    }

    public synchronized void abortCover(CoverPlan plan) {
        if (plan.equals(pendingCovers.get(plan.key()))) pendingCovers.remove(plan.key());
    }

    /** A relative, estate, guarantor or debtor may pay, only after its own wallet authority authorizes it. */
    public synchronized RepaymentPlan prepareRepayment(String operationId, SettlementKey key, AccountId payer,
                                                        long requestedCents, long availableCents) {
        requireOperation(operationId); Objects.requireNonNull(payer);
        if (requestedCents <= 0 || availableCents < 0) throw new IllegalArgumentException("invalid repayment");
        RepaymentPlan previous = repayments.get(operationId);
        if (previous != null) {
            requireSameRepayment(previous, key, payer, requestedCents);
            return new RepaymentPlan(operationId, key, payer, requestedCents, List.of(), debts.get(key), true);
        }
        if (writeDowns.containsKey(operationId)) throw new IllegalArgumentException("operation identity conflict");
        for (RepaymentPlan active : pendingRepayments.values()) {
            if (active.operationId().equals(operationId) && !active.key().equals(key))
                throw new IllegalArgumentException("repayment identity conflict");
        }
        RepaymentPlan pending = pendingRepayments.get(key);
        if (pending != null) {
            requireSameRepayment(pending, key, payer, requestedCents);
            if (!pending.operationId().equals(operationId)) throw new IllegalStateException("claim is reserved");
            return pending;
        }
        DebtView old = debt(key);
        long payment = Math.min(requestedCents, old.outstandingCents());
        if (payment > availableCents) throw new IllegalArgumentException("payer has insufficient authorized money");
        long winnerPayment = Math.min(payment, old.winnerUnpaidCents());
        long fundPayment = payment - winnerPayment;
        if ((winnerPayment > 0 && payer.equals(old.winner())) || (fundPayment > 0 && payer.equals(old.fund())))
            throw new IllegalArgumentException("self payment requires explicit creditor write down");
        List<Payment> transfers = new ArrayList<>();
        if (winnerPayment > 0) transfers.add(new Payment(payer, old.winner(), winnerPayment));
        if (fundPayment > 0) transfers.add(new Payment(payer, old.fund(), fundPayment));
        DebtView updated = new DebtView(key, old.debtor(), old.winner(), old.fund(), old.originalShortfallCents(),
                old.fundPaidCents(), old.winnerUnpaidCents() - winnerPayment, old.fundRecourseCents() - fundPayment,
                Math.addExact(old.repaidCents(), payment), old.writtenOffCents(), Math.addExact(old.revision(), 1));
        RepaymentPlan plan = new RepaymentPlan(operationId, key, payer, requestedCents, transfers, updated, false);
        pendingRepayments.put(key, plan);
        return plan;
    }

    public synchronized void commitRepayment(RepaymentPlan plan) {
        Objects.requireNonNull(plan);
        if (plan.replay()) {
            RepaymentPlan previous = repayments.get(plan.operationId());
            if (previous == null) throw new IllegalArgumentException("unknown replay");
            requireSameRepayment(previous, plan.key(), plan.payer(), plan.requestedCents()); return;
        }
        if (!plan.equals(pendingRepayments.get(plan.key()))) throw new IllegalArgumentException("unprepared repayment");
        debts.put(plan.key(), plan.debt()); repayments.put(plan.operationId(), plan); pendingRepayments.remove(plan.key());
    }

    public synchronized void abortRepayment(RepaymentPlan plan) {
        if (plan.equals(pendingRepayments.get(plan.key()))) pendingRepayments.remove(plan.key());
    }

    /** Only each actual creditor's consent can remove its claim. No money or compensation is minted. */
    public synchronized WriteDown writeDown(String operationId, SettlementKey key, long winnerReductionCents,
                                             long fundReductionCents, boolean winnerConsents, boolean fundConsents) {
        requireOperation(operationId);
        if (winnerReductionCents < 0 || fundReductionCents < 0
                || (winnerReductionCents > 0 && !winnerConsents) || (fundReductionCents > 0 && !fundConsents))
            throw new IllegalArgumentException("creditor consent required");
        WriteDown previous = writeDowns.get(operationId);
        if (previous != null) {
            if (!previous.key().equals(key) || previous.winnerReductionCents() != winnerReductionCents
                    || previous.fundReductionCents() != fundReductionCents) throw new IllegalArgumentException("operation conflict");
            return new WriteDown(operationId, key, winnerReductionCents, fundReductionCents,
                    previous.previousRevision(), debts.get(key), true);
        }
        if (repayments.containsKey(operationId) || pendingRepayments.containsKey(key))
            throw new IllegalStateException("operation conflict or claim reserved");
        if (pendingRepayments.values().stream().anyMatch(plan -> plan.operationId().equals(operationId)))
            throw new IllegalStateException("operation identity is reserved");
        DebtView old = debt(key);
        if (winnerReductionCents > old.winnerUnpaidCents() || fundReductionCents > old.fundRecourseCents())
            throw new IllegalArgumentException("write down exceeds creditor claim");
        DebtView updated = new DebtView(key, old.debtor(), old.winner(), old.fund(), old.originalShortfallCents(),
                old.fundPaidCents(), old.winnerUnpaidCents() - winnerReductionCents,
                old.fundRecourseCents() - fundReductionCents, old.repaidCents(),
                Math.addExact(old.writtenOffCents(), Math.addExact(winnerReductionCents, fundReductionCents)),
                Math.addExact(old.revision(), 1));
        WriteDown result = new WriteDown(operationId, key, winnerReductionCents, fundReductionCents, old.revision(), updated, false);
        debts.put(key, updated); writeDowns.put(operationId, result); return result;
    }

    public synchronized DebtView debt(SettlementKey key) {
        DebtView result = debts.get(key);
        if (result == null) throw new IllegalArgumentException("unknown debt");
        return result;
    }

    public synchronized Snapshot snapshot() {
        if (!pendingCovers.isEmpty() || !pendingRepayments.isEmpty()) throw new IllegalStateException("cannot save uncommitted cash plans");
        return new Snapshot(new ArrayList<>(debts.values()), new ArrayList<>(covers.values()),
                new ArrayList<>(repayments.values()), new ArrayList<>(writeDowns.values()));
    }

    public static DebtLedger restore(Snapshot snapshot) {
        Objects.requireNonNull(snapshot);
        DebtLedger ledger = new DebtLedger();
        for (CoverPlan cover : snapshot.covers()) {
            if (cover.replay() || ledger.covers.containsKey(cover.key()))
                throw new IllegalArgumentException("duplicate or replay cover in snapshot");
            CoverPlan rebuilt = ledger.prepareCover(cover.key(), cover.debtor(), cover.winner(), cover.fund(),
                    cover.shortfallCents(), cover.debt().fundPaidCents(), cover.insured());
            if (!rebuilt.equals(cover)) throw new IllegalArgumentException("initial claim or payment does not reconcile");
            ledger.commitCover(rebuilt);
        }
        Map<SettlementKey, DebtView> expected = new LinkedHashMap<>();
        for (DebtView debt : snapshot.debts()) {
            CoverPlan cover = ledger.covers.get(debt.key());
            if (cover == null || expected.putIfAbsent(debt.key(), debt) != null)
                throw new IllegalArgumentException("orphan or duplicate debt");
            requireSameCover(cover, debt.debtor(), debt.winner(), debt.fund(), debt.originalShortfallCents());
            if (cover.debt().fundPaidCents() != debt.fundPaidCents()) throw new IllegalArgumentException("changed fund payment");
        }
        if (ledger.covers.size() != expected.size()) throw new IllegalArgumentException("missing current debt");
        Map<SettlementKey, TreeMap<Long, DebtHistory>> history = new LinkedHashMap<>();
        for (RepaymentPlan plan : snapshot.repayments()) {
            if (plan.replay() || !ledger.debts.containsKey(plan.key()))
                throw new IllegalArgumentException("invalid repayment history");
            if (history.computeIfAbsent(plan.key(), ignored -> new TreeMap<>()).putIfAbsent(plan.debt().revision(), new RepaymentHistory(plan)) != null)
                throw new IllegalArgumentException("duplicate claim revision");
        }
        for (WriteDown writeDown : snapshot.writeDowns()) {
            if (writeDown.replay() || !ledger.debts.containsKey(writeDown.key()))
                throw new IllegalArgumentException("invalid write down history");
            if (history.computeIfAbsent(writeDown.key(), ignored -> new TreeMap<>()).putIfAbsent(writeDown.debt().revision(), new WriteDownHistory(writeDown)) != null)
                throw new IllegalArgumentException("duplicate claim revision");
        }
        for (var claimHistory : history.entrySet()) {
            long revision = 1;
            for (var event : claimHistory.getValue().entrySet()) {
                if (event.getKey() != revision++) throw new IllegalArgumentException("missing claim revision");
                if (event.getValue() instanceof RepaymentHistory repaymentHistory) {
                    RepaymentPlan payment = repaymentHistory.payment();
                    RepaymentPlan rebuilt = ledger.prepareRepayment(payment.operationId(), payment.key(), payment.payer(),
                            payment.requestedCents(), payment.paidCents());
                    if (!rebuilt.equals(payment)) throw new IllegalArgumentException("repayment history does not reconcile");
                    ledger.commitRepayment(rebuilt);
                } else if (event.getValue() instanceof WriteDownHistory writeDownHistory) {
                    WriteDown reduction = writeDownHistory.reduction();
                    WriteDown rebuilt = ledger.writeDown(reduction.operationId(), reduction.key(), reduction.winnerReductionCents(),
                            reduction.fundReductionCents(), true, true);
                    if (!rebuilt.equals(reduction)) throw new IllegalArgumentException("write down history does not reconcile");
                } else throw new IllegalArgumentException("unknown claim history");
            }
        }
        if (!ledger.debts.equals(expected)) throw new IllegalArgumentException("current debt disagrees with payment history");
        return ledger;
    }

    private static void requireSameCover(CoverPlan plan, AccountId debtor, AccountId winner, AccountId fund, long cents) {
        if (!plan.debtor().equals(debtor) || !plan.winner().equals(winner) || !plan.fund().equals(fund)
                || plan.shortfallCents() != cents) throw new IllegalArgumentException("settlement identity conflict");
    }
    private static void requireSameRepayment(RepaymentPlan plan, SettlementKey key, AccountId payer, long cents) {
        if (!plan.key().equals(key) || !plan.payer().equals(payer) || plan.requestedCents() != cents)
            throw new IllegalArgumentException("repayment identity conflict");
    }
    private static void requireOperation(String operationId) {
        if (operationId == null || operationId.isBlank()) throw new IllegalArgumentException("missing operation identity");
    }
}
