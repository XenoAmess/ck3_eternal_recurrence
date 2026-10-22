package org.xar.ck3.control.finance.feastvalue;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** Source-compatible, side-effect-free generic feast value/budget leaf. */
public final class FeastStage5ValuePolicy {
    public static final String POLICY = "g2-feast-stage5-value-policy-v1";
    public static final int SCALE = 100_000;
    public static final List<String> RESOURCE_KEYS = List.of("gold", "treasury", "piety", "barter_goods");
    public static final String BENEFIT = "scripted_prestige_and_reveler_progress_or_xp";

    private FeastStage5ValuePolicy() { }

    public enum ObservedBoolean { TRUE, FALSE, UNKNOWN }
    public enum Decision { START, HOLD }
    public enum Status { READY, MISSING_INPUT, NOT_ACTIONABLE }
    public enum Reason {
        UNSUPPORTED_ACTIVITY_OR_TYPE, NOT_FINAL_PLANNING_STAGE,
        NATIVE_FINAL_START_UNAVAILABLE, GUEST_ROUTE_UNPROVEN,
        CONFIGURED_COST_UNOBSERVED, PEACEFUL_SPEND_UNAPPROVED,
        GOLD_BALANCE_UNOBSERVED, TREASURY_BALANCE_UNOBSERVED,
        PIETY_BALANCE_UNOBSERVED, BARTER_GOODS_BALANCE_UNOBSERVED,
        GOLD_RESERVE_UNOBSERVED, WAR_CASH_RESERVE_UNOBSERVED,
        GOLD_BUDGET_EXCEEDED, TREASURY_BUDGET_EXCEEDED,
        PIETY_BUDGET_EXCEEDED, BARTER_GOODS_BUDGET_EXCEEDED,
        POSITIVE_FEAST_WITHIN_OBSERVED_BUDGET
    }

    public record Amounts(BigInteger gold, BigInteger treasury, BigInteger piety, BigInteger barterGoods) {
        public Amounts {
            nonnegative(gold, "gold"); nonnegative(treasury, "treasury");
            nonnegative(piety, "piety"); nonnegative(barterGoods, "barter_goods");
        }
        public BigInteger at(int index) {
            return switch (index) {
                case 0 -> gold; case 1 -> treasury; case 2 -> piety; case 3 -> barterGoods;
                default -> throw new IndexOutOfBoundsException(index);
            };
        }
        public Amounts withGold(BigInteger replacement) { return new Amounts(replacement, treasury, piety, barterGoods); }
    }

    public record Costs(Optional<BigInteger> gold, Optional<BigInteger> treasury,
                        Optional<BigInteger> piety, Optional<BigInteger> barterGoods) {
        public Costs {
            optionalNonnegative(gold, "gold"); optionalNonnegative(treasury, "treasury");
            optionalNonnegative(piety, "piety"); optionalNonnegative(barterGoods, "barter_goods");
        }
        public Optional<BigInteger> at(int index) {
            return switch (index) {
                case 0 -> gold; case 1 -> treasury; case 2 -> piety; case 3 -> barterGoods;
                default -> throw new IndexOutOfBoundsException(index);
            };
        }
        public boolean complete() { return gold.isPresent() && treasury.isPresent() && piety.isPresent() && barterGoods.isPresent(); }
        public Amounts observed() {
            return new Amounts(gold.orElseThrow(), treasury.orElseThrow(), piety.orElseThrow(), barterGoods.orElseThrow());
        }
    }

    public record Availability(boolean gold, boolean treasury, boolean piety, boolean barterGoods) {
        public boolean at(int index) {
            return switch (index) {
                case 0 -> gold; case 1 -> treasury; case 2 -> piety; case 3 -> barterGoods;
                default -> throw new IndexOutOfBoundsException(index);
            };
        }
    }

    public record Request(String activityKey, String selectedOptionKey, BigInteger planningStage,
                          ObservedBoolean finalCanStart, Costs configuredCostRaw,
                          Availability balanceAvailable, Amounts balanceRaw, Amounts reservedRaw,
                          Optional<BigInteger> expectedNonhostGuestCount, ObservedBoolean peacefulSpendAllowed,
                          Optional<BigInteger> goldFloorRaw, Optional<BigInteger> activeWarCount,
                          Optional<BigInteger> warCashReserveRaw) {
        public Request {
            Objects.requireNonNull(activityKey, "activity_key");
            Objects.requireNonNull(selectedOptionKey, "selected_option_key");
            Objects.requireNonNull(planningStage, "planning_stage");
            Objects.requireNonNull(finalCanStart, "final_can_start");
            Objects.requireNonNull(configuredCostRaw, "configured_cost_raw");
            Objects.requireNonNull(balanceAvailable, "balance_available");
            Objects.requireNonNull(balanceRaw, "balance_raw");
            Objects.requireNonNull(reservedRaw, "reserved_raw");
            Objects.requireNonNull(peacefulSpendAllowed, "peaceful_spend_allowed");
            optionalNonnegative(expectedNonhostGuestCount, "expected_nonhost_guest_count");
            optionalNonnegative(goldFloorRaw, "gold_floor_raw");
            optionalNonnegative(activeWarCount, "active_war_count");
            optionalNonnegative(warCashReserveRaw, "war_cash_reserve_raw");
        }
    }

    public record Assessment(Decision decision, Status status, Reason reason, boolean positiveValueSupported,
                             Costs configuredCostRaw, Optional<Amounts> resourceCommitmentRaw,
                             Optional<Amounts> submitReserveRaw) {
        public Assessment {
            Objects.requireNonNull(decision); Objects.requireNonNull(status); Objects.requireNonNull(reason);
            Objects.requireNonNull(configuredCostRaw); Objects.requireNonNull(resourceCommitmentRaw);
            Objects.requireNonNull(submitReserveRaw);
            if ((decision == Decision.START) != (status == Status.READY)
                    || (decision == Decision.START) != resourceCommitmentRaw.isPresent()
                    || (decision == Decision.START) != submitReserveRaw.isPresent()
                    || (decision == Decision.START) != (reason == Reason.POSITIVE_FEAST_WITHIN_OBSERVED_BUDGET)
                    || (decision == Decision.START && (!positiveValueSupported || !configuredCostRaw.complete()
                        || !resourceCommitmentRaw.orElseThrow().equals(configuredCostRaw.observed())))) {
                throw new IllegalArgumentException("decision/status/commitment branch mismatch");
            }
        }
    }

    public static Assessment assess(Request request) {
        Objects.requireNonNull(request, "request");
        if (!supportedActivity(request)) return hold(request, Reason.UNSUPPORTED_ACTIVITY_OR_TYPE, false);
        if (!request.planningStage().equals(BigInteger.valueOf(5))) return hold(request, Reason.NOT_FINAL_PLANNING_STAGE, false);
        if (request.finalCanStart() != ObservedBoolean.TRUE) {
            return hold(request, Reason.NATIVE_FINAL_START_UNAVAILABLE, request.finalCanStart() == ObservedBoolean.UNKNOWN);
        }
        if (request.expectedNonhostGuestCount().isEmpty() || request.expectedNonhostGuestCount().orElseThrow().signum() == 0) {
            return hold(request, Reason.GUEST_ROUTE_UNPROVEN, request.expectedNonhostGuestCount().isEmpty());
        }
        if (!request.configuredCostRaw().complete()) return hold(request, Reason.CONFIGURED_COST_UNOBSERVED, true);
        if (request.peacefulSpendAllowed() != ObservedBoolean.TRUE) {
            return hold(request, Reason.PEACEFUL_SPEND_UNAPPROVED, request.peacefulSpendAllowed() == ObservedBoolean.UNKNOWN);
        }
        Amounts costs = request.configuredCostRaw().observed();
        for (int index = 0; index < 4; index++) {
            BigInteger cost = costs.at(index);
            if (cost.signum() == 0) continue;
            if (!request.balanceAvailable().at(index)) return hold(request, balanceMissing(index), true);
            BigInteger needed = cost.add(request.reservedRaw().at(index));
            if (index == 0) {
                if (request.goldFloorRaw().isEmpty() || request.activeWarCount().isEmpty()) {
                    return hold(request, Reason.GOLD_RESERVE_UNOBSERVED, true);
                }
                needed = needed.add(request.goldFloorRaw().orElseThrow());
                if (request.activeWarCount().orElseThrow().signum() != 0) {
                    if (request.warCashReserveRaw().isEmpty()) return hold(request, Reason.WAR_CASH_RESERVE_UNOBSERVED, true);
                    needed = needed.add(request.warCashReserveRaw().orElseThrow());
                }
            }
            if (needed.compareTo(request.balanceRaw().at(index)) > 0) return hold(request, budgetExceeded(index), false);
        }
        Amounts submitReserve = request.reservedRaw();
        if (costs.gold().signum() != 0) {
            BigInteger gold = submitReserve.gold().add(request.goldFloorRaw().orElseThrow());
            if (request.activeWarCount().orElseThrow().signum() != 0) gold = gold.add(request.warCashReserveRaw().orElseThrow());
            submitReserve = submitReserve.withGold(gold);
        }
        return new Assessment(Decision.START, Status.READY, Reason.POSITIVE_FEAST_WITHIN_OBSERVED_BUDGET,
                valueSupported(request), request.configuredCostRaw(), Optional.of(costs), Optional.of(submitReserve));
    }

    private static Assessment hold(Request request, Reason reason, boolean missing) {
        return new Assessment(Decision.HOLD, missing ? Status.MISSING_INPUT : Status.NOT_ACTIONABLE,
                reason, valueSupported(request), request.configuredCostRaw(), Optional.empty(), Optional.empty());
    }
    private static boolean supportedActivity(Request request) {
        return request.activityKey().equals("activity_feast") && request.selectedOptionKey().equals("feast_type_generic");
    }
    private static boolean valueSupported(Request request) {
        return supportedActivity(request) && request.expectedNonhostGuestCount().isPresent()
                && request.expectedNonhostGuestCount().orElseThrow().signum() > 0;
    }
    private static Reason balanceMissing(int index) {
        return switch (index) {
            case 0 -> Reason.GOLD_BALANCE_UNOBSERVED; case 1 -> Reason.TREASURY_BALANCE_UNOBSERVED;
            case 2 -> Reason.PIETY_BALANCE_UNOBSERVED; case 3 -> Reason.BARTER_GOODS_BALANCE_UNOBSERVED;
            default -> throw new IndexOutOfBoundsException(index);
        };
    }
    private static Reason budgetExceeded(int index) {
        return switch (index) {
            case 0 -> Reason.GOLD_BUDGET_EXCEEDED; case 1 -> Reason.TREASURY_BUDGET_EXCEEDED;
            case 2 -> Reason.PIETY_BUDGET_EXCEEDED; case 3 -> Reason.BARTER_GOODS_BUDGET_EXCEEDED;
            default -> throw new IndexOutOfBoundsException(index);
        };
    }
    private static void nonnegative(BigInteger value, String name) {
        if (Objects.requireNonNull(value, name).signum() < 0) throw new IllegalArgumentException(name + " must be nonnegative");
    }
    private static void optionalNonnegative(Optional<BigInteger> value, String name) {
        Objects.requireNonNull(value, name).ifPresent(item -> nonnegative(item, name));
    }
}
