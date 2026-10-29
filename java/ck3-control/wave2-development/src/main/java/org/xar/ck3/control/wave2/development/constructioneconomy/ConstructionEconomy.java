package org.xar.ck3.control.wave2.development.constructioneconomy;

import java.math.BigInteger;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

import static org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.*;

/** Pure material, aggregate-flow and wallet classification. An ACK grants no completion or ROI. */
public final class ConstructionEconomy {
    private ConstructionEconomy() { }

    public static Outcome classify(OutcomeRequest request) {
        Receipt r = request.receipt();
        boolean mismatch = r.status() == ReceiptStatus.MISMATCHED;
        boolean completed = r.status() == ReceiptStatus.APPLIED && r.verified()
                && r.completion() == CompletionStatus.COMPLETED;
        Phase phase = mismatch ? Phase.MISMATCHED
                : r.status() == ReceiptStatus.RESTORED_BEFORE_ACTION ? Phase.RESTORED
                : completed ? Phase.COMPLETED
                : r.status() == ReceiptStatus.APPLIED && r.verified()
                        && r.completion() == CompletionStatus.IN_PROGRESS ? Phase.ACTIVE : Phase.PENDING;
        boolean qualified = qualifiedIncomeBuild(request.exactBuild());
        boolean grossReady = completed && qualified && r.preGross().isPresent() && r.postGross().isPresent()
                && r.completionDate().isPresent() && r.incomeDate().isPresent()
                && r.incomeDate().orElseThrow().compareTo(r.completionDate().orElseThrow()) >= 0;
        String grossReason = grossReady ? null : !completed ? "construction_not_completed"
                : !qualified ? "player_income_semantics_not_qualified"
                : r.preGross().isEmpty() ? "pre_submit_player_income_unavailable"
                : "post_completion_player_income_unavailable";
        Optional<BigInteger> provincePre = province(r.preProvince(), r, false);
        Optional<BigInteger> provincePost = province(r.postProvince(), r, true);
        boolean provinceReady = completed && provincePre.isPresent() && provincePost.isPresent();
        String provinceReason = provinceReady ? null : !completed ? "construction_not_completed"
                : provincePre.isEmpty() ? "pre_submit_province_income_unavailable"
                : "post_completion_province_income_unavailable";
        String next = null;
        if (mismatch) {
            if (r.completion() != CompletionStatus.COMPLETED) next = "scheduled_completion_watch";
        } else if (phase == Phase.PENDING) next = "independent_construction_material_receipt";
        else if (phase == Phase.ACTIVE) next = "scheduled_completion_watch";
        else if (completed && r.preGross().isPresent() && !grossReady)
            next = qualified ? "existing_player_root_then_material_receipt" : "income_source_qualification";
        else if (completed && provincePre.isPresent() && !provinceReady)
            next = "scheduled_province_income_receipt_retry";
        return new Outcome(phase, r, request.exactBuild(), completed,
                new AggregateChange(change(r.preGross(), r.postGross(), grossReady), Optional.ofNullable(grossReason)),
                new AggregateChange(change(provincePre, provincePost, provinceReady), Optional.ofNullable(provinceReason)),
                Optional.ofNullable(next), cashChange(request, completed, qualified));
    }

    private static Optional<BigInteger> province(Optional<ProvinceObservation> observation, Receipt r, boolean post) {
        if (observation.isEmpty()) return Optional.empty();
        ProvinceObservation value = observation.orElseThrow();
        if (!value.observed() || !value.barony().equals(r.candidate().barony())
                || !value.province().equals(r.candidate().province()) || value.monthlyIncomeRaw().isEmpty())
            return Optional.empty();
        if (post && (r.completionDate().isEmpty() || value.date().isEmpty()
                || value.date().orElseThrow().compareTo(r.completionDate().orElseThrow()) < 0)) return Optional.empty();
        return value.monthlyIncomeRaw();
    }

    private static Change change(Optional<BigInteger> before, Optional<BigInteger> after, boolean ready) {
        return new Change(ready, before, after,
                ready ? Optional.of(after.orElseThrow().subtract(before.orElseThrow())) : Optional.empty());
    }

    private static CashChange unavailable(String reason) {
        return new CashChange(false, Optional.of(reason), List.of(), Optional.empty(), Map.of(),
                Optional.empty(), Optional.empty(), Optional.empty());
    }

    private static CashChange cashChange(OutcomeRequest request, boolean completed, boolean qualified) {
        if (!completed) return unavailable("construction_not_completed");
        Receipt r = request.receipt();
        Optional<CashPacket> pre = request.preCashOverride().or(r::preCash);
        Optional<CashPacket> post = request.postCashOverride().or(r::postCash);
        if (pre.isEmpty()) return unavailable("pre_submit_cash_v2_unavailable");
        if (post.isEmpty()) return unavailable("post_completion_cash_v2_unavailable");
        CashPacket before = pre.orElseThrow(), after = post.orElseThrow();
        for (CashPacket cash : List.of(before, after)) {
            if (!cash.frame().gameVersion().equals(request.exactBuild()))
                throw new ProjectionDomainRejection("construction cash interval crossed its exact build");
        }
        Optional<BigInteger> beforeDate = before.frame().date(), afterDate = after.frame().date();
        boolean bound = qualified && r.actor().isPresent() && before.frame().actor().equals(r.actor())
                && after.frame().actor().equals(r.actor()) && before.sameFrameReady() && after.sameFrameReady()
                && beforeDate.isPresent() && afterDate.isPresent() && beforeDate.equals(r.preDate())
                && r.completionDate().isPresent()
                && afterDate.orElseThrow().compareTo(r.completionDate().orElseThrow()) >= 0
                && afterDate.orElseThrow().compareTo(beforeDate.orElseThrow()) >= 0;
        if (!bound) return unavailable("cash_interval_actor_or_dates_not_bound");
        Map<CashField, Change> monthly = new EnumMap<>(CashField.class);
        Change wallet = null;
        int observed = 0;
        for (CashField field : CashField.values()) {
            FixedObservation a = before.value(field), b = after.value(field);
            boolean ready = a.raw().isPresent() && b.raw().isPresent() && a.ready() && b.ready();
            Change value = ready ? change(a.raw(), b.raw(), true)
                    : new Change(false, Optional.empty(), Optional.empty(), Optional.empty());
            if (field == CashField.TREASURY) wallet = value; else monthly.put(field, value);
            if (ready) observed++;
        }
        Optional<BigInteger> debit = Optional.empty(), residual = Optional.empty();
        if (r.start().isPresent()) {
            StartReceipt start = r.start().orElseThrow();
            Candidate c = r.candidate();
            if (start.status() == ReceiptStatus.APPLIED && start.postconditionVerified()
                    && r.actionRequestId().isPresent() && start.actionRequestId().equals(r.actionRequestId())
                    && c.cost().isPresent() && c.cost().orElseThrow().signum() > 0 && c.goldBefore().isPresent()
                    && start.postPlayerGold().equals(Optional.of(c.goldBefore().orElseThrow().subtract(c.cost().orElseThrow())))) {
                debit = c.cost();
                if (wallet != null && wallet.ready()) residual = Optional.of(wallet.delta().orElseThrow().add(debit.orElseThrow()));
            }
        }
        return new CashChange(observed > 0, observed > 0 ? Optional.empty() : Optional.of("cash_interval_values_unavailable"),
                List.of(before.frame(), after.frame()), Optional.of(afterDate.orElseThrow().subtract(beforeDate.orElseThrow())),
                monthly, Optional.ofNullable(wallet), debit, residual);
    }

    public static Budget projectBudget(CashPacket cash, BudgetPolicy policy) {
        if (!cash.normalizedReadOnly()) throw new ProjectionDomainRejection("normalized current cash resources are required");
        Map<MissingInput, String> missing = new EnumMap<>(MissingInput.class);
        if (!cash.sameFrameReady()) missing.put(MissingInput.SAME_FRAME, "war_cash_same_frame_unavailable");
        FixedObservation treasury = cash.value(CashField.TREASURY), net = cash.value(CashField.NET);
        budgetFixed(treasury, MissingInput.TREASURY, missing);
        budgetFixed(net, MissingInput.NET, missing);
        MilitaryObservation current = cash.currentMilitary().orElseThrow(
                () -> new IllegalArgumentException("military_expenses.current normalized observation is absent"));
        MilitaryObservation raised = cash.allRaisedMilitary().orElseThrow(
                () -> new IllegalArgumentException("military_expenses.all_raised normalized observation is absent"));
        Map<MissingInput, String> raisedMissing = new EnumMap<>(MissingInput.class);
        raisedMissing.putAll(missing);
        if (current.gold().isEmpty()) raisedMissing.put(MissingInput.CURRENT_MILITARY, current.unavailableReason().orElseThrow());
        if (raised.gold().isEmpty()) raisedMissing.put(MissingInput.ALL_RAISED_MILITARY, raised.unavailableReason().orElseThrow());
        Optional<BigInteger> raisedRate = net.raw().isPresent() && current.gold().isPresent() && raised.gold().isPresent()
                ? Optional.of(net.raw().orElseThrow().add(current.gold().orElseThrow()).subtract(raised.gold().orElseThrow()))
                : Optional.empty();
        return new Budget(cash, policy, scenario(treasury.raw(), net.raw(), policy, missing),
                scenario(treasury.raw(), raisedRate, policy, raisedMissing), false);
    }

    private static void budgetFixed(FixedObservation value, MissingInput key, Map<MissingInput, String> missing) {
        if (value.raw().isEmpty()) {
            String reason = value.unavailableReason().filter(text -> !text.isEmpty()).orElseThrow(
                    () -> new IllegalArgumentException(key.wire() + " unavailable observation is malformed"));
            if (value.ready()) throw new IllegalArgumentException(key.wire() + " availability is malformed");
            missing.put(key, reason);
        } else if (!value.ready() || value.unavailableReason().isPresent()) {
            throw new IllegalArgumentException(key.wire() + " available observation is malformed");
        }
    }

    private static Scenario scenario(Optional<BigInteger> treasury, Optional<BigInteger> rate,
            BudgetPolicy policy, Map<MissingInput, String> missing) {
        Optional<BigInteger> start = treasury.isPresent() && !missing.containsKey(MissingInput.SAME_FRAME)
                ? Optional.of(treasury.orElseThrow().subtract(policy.constructionCost()).subtract(policy.commitments()))
                : Optional.empty();
        if (!missing.isEmpty()) return new Scenario(rate, start, Optional.empty(), Optional.empty(), Optional.empty(),
                Optional.empty(), Optional.empty(), Optional.empty(), missing);
        BigInteger first = start.orElseThrow(), monthly = rate.orElseThrow();
        BigInteger months = BigInteger.valueOf(policy.horizonMonths());
        BigInteger end = first.add(monthly.multiply(months));
        BigInteger burn = monthly.negate().max(BigInteger.ZERO).multiply(months);
        BigInteger minimum = first.min(end);
        Optional<Integer> breach = Optional.empty();
        if (first.compareTo(policy.reserve()) < 0) breach = Optional.of(0);
        else if (monthly.signum() < 0) {
            BigInteger crossing = first.subtract(policy.reserve()).divide(monthly.negate()).add(BigInteger.ONE);
            if (crossing.compareTo(months) <= 0) breach = Optional.of(crossing.intValueExact());
        }
        return new Scenario(rate, start, Optional.of(end), Optional.of(burn), Optional.of(minimum),
                Optional.of(minimum.compareTo(policy.reserve()) >= 0),
                Optional.of(treasury.orElseThrow().subtract(policy.commitments()).subtract(policy.reserve()).subtract(burn).max(BigInteger.ZERO)),
                breach, missing);
    }

    private static boolean qualifiedIncomeBuild(String build) { return build.equals("1.20.0.3") || build.equals("1.20.0.4"); }
}
