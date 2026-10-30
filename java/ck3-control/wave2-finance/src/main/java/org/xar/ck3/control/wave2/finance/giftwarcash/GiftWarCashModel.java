package org.xar.ck3.control.wave2.finance.giftwarcash;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Immutable consumed projections; native observations and spending authority remain external. */
public final class GiftWarCashModel {
    private GiftWarCashModel() { }
    public enum Presence { MISSING, NULL, VALUE }
    public record Read<T>(Presence presence, T value) {
        public Read {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) {
                throw new IllegalArgumentException("only a known read has a non-null value");
            }
        }
        public static <T> Read<T> missing() { return new Read<>(Presence.MISSING, null); }
        public static <T> Read<T> nil() { return new Read<>(Presence.NULL, null); }
        public static <T> Read<T> of(T value) { return new Read<>(Presence.VALUE, Objects.requireNonNull(value)); }
        public boolean known() { return presence == Presence.VALUE; }
    }
    public record SourceFrame(BigInteger playedCharacterId, BigInteger nativeRevision, BigInteger dateRaw,
            String snapshotId, BigInteger revision, String episodeRunId) {
        public SourceFrame {
            Objects.requireNonNull(playedCharacterId); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(snapshotId);
            Objects.requireNonNull(revision); Objects.requireNonNull(episodeRunId);
            NativeCharacterId.of(playedCharacterId);
            if (nativeRevision.signum() <= 0 || dateRaw.signum() < 0
                    || revision.signum() <= 0 || snapshotId.isEmpty() || episodeRunId.isEmpty()) {
                throw new IllegalArgumentException("M5 observed frame identity is incomplete");
            }
        }
    }
    public record FrameRead(Read<BigInteger> playedCharacterId, Read<BigInteger> nativeRevision,
            Read<BigInteger> dateRaw, Read<String> snapshotId, Read<BigInteger> revision,
            Read<String> episodeRunId, boolean exactFields) {
        public FrameRead {
            Objects.requireNonNull(playedCharacterId); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(snapshotId);
            Objects.requireNonNull(revision); Objects.requireNonNull(episodeRunId);
        }
    }
    public record BudgetFrame(Read<BigInteger> actorCharacterId, Read<BigInteger> nativeRevision,
            Read<BigInteger> dateRaw, Read<String> snapshotId, boolean exactFields) {
        public BudgetFrame {
            Objects.requireNonNull(actorCharacterId); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(snapshotId);
        }
    }
    public record War(Read<BigInteger> warId, List<Read<BigInteger>> enemyProvinces) {
        public War { Objects.requireNonNull(warId); enemyProvinces = List.copyOf(enemyProvinces); }
    }
    public record Snapshot(SourceFrame frame, Read<BigInteger> actor, Read<BigInteger> walletRaw,
            Read<BigInteger> walletScale, Read<List<War>> wars) {
        public Snapshot {
            Objects.requireNonNull(frame); Objects.requireNonNull(actor); Objects.requireNonNull(walletRaw);
            Objects.requireNonNull(walletScale); Objects.requireNonNull(wars);
            if (wars.known()) { wars = Read.of(List.copyOf(wars.value())); }
        }
    }
    public record Choice(Read<BigInteger> playerCharacterId, Read<BigInteger> nativeRevision,
            Read<BigInteger> dateRaw, Read<BigInteger> giftCostRaw) {
        public Choice {
            Objects.requireNonNull(playerCharacterId); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(giftCostRaw);
        }
    }
    public record GiftObservation(Read<BigInteger> playerCharacterId, Read<BigInteger> nativeRevision,
            Read<BigInteger> observedDateRaw, Read<BigInteger> playerGoldRaw, Read<BigInteger> playerGoldScale,
            Read<BigInteger> previewGoldCostRaw) {
        public GiftObservation {
            Objects.requireNonNull(playerCharacterId); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(observedDateRaw); Objects.requireNonNull(playerGoldRaw);
            Objects.requireNonNull(playerGoldScale); Objects.requireNonNull(previewGoldCostRaw);
        }
    }
    public record Candidate(Read<Choice> choice, Read<GiftObservation> observation) {
        public Candidate { Objects.requireNonNull(choice); Objects.requireNonNull(observation); }
    }
    public record Root(Read<String> status, Read<BigInteger> playerCharacterId, Read<BigInteger> snapshotRevision,
            Read<BigInteger> dateRaw, Read<String> maximumStatus, Read<BigInteger> maintenanceRaw,
            Read<BigInteger> maintenanceScale) {
        public Root {
            Objects.requireNonNull(status); Objects.requireNonNull(playerCharacterId);
            Objects.requireNonNull(snapshotRevision); Objects.requireNonNull(dateRaw);
            Objects.requireNonNull(maximumStatus); Objects.requireNonNull(maintenanceRaw);
            Objects.requireNonNull(maintenanceScale);
        }
    }
    public record Spending(Read<String> status, Read<BudgetFrame> frame, Read<BigInteger> reservedGoldRaw,
            Read<BigInteger> activeWarCount) {
        public Spending {
            Objects.requireNonNull(status); Objects.requireNonNull(frame);
            Objects.requireNonNull(reservedGoldRaw); Objects.requireNonNull(activeWarCount);
        }
    }
    public record QuoteRow(Read<BigInteger> companyId, Presence employer, Read<List<BigInteger>> costs,
            Read<BigInteger> resourceScale, Read<Boolean> available, Read<Boolean> canHire,
            Read<Boolean> canAfford, Read<Boolean> hireReady, Read<Boolean> troopsAvailable,
            Read<BigInteger> currentSoldiers, Read<BigInteger> spawnProvince,
            Read<Boolean> positionReady, Read<Boolean> attemptedInActiveWar) {
        public QuoteRow {
            Objects.requireNonNull(companyId); Objects.requireNonNull(employer); Objects.requireNonNull(costs);
            Objects.requireNonNull(resourceScale); Objects.requireNonNull(available); Objects.requireNonNull(canHire);
            Objects.requireNonNull(canAfford); Objects.requireNonNull(hireReady); Objects.requireNonNull(troopsAvailable);
            Objects.requireNonNull(currentSoldiers); Objects.requireNonNull(spawnProvince);
            Objects.requireNonNull(positionReady); Objects.requireNonNull(attemptedInActiveWar);
            if (costs.known()) { costs = Read.of(List.copyOf(costs.value())); }
        }
    }
    public record Market(Read<Boolean> available, Read<BigInteger> actorCharacterId, Read<BigInteger> dateRaw,
            Read<List<QuoteRow>> rows) {
        public Market {
            Objects.requireNonNull(available); Objects.requireNonNull(actorCharacterId);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(rows);
            if (rows.known()) { rows = Read.of(List.copyOf(rows.value())); }
        }
    }
    public record Request(Snapshot snapshot, Read<Candidate> candidate, Read<Root> root,
            Read<Spending> spending, Read<Market> market, Read<FrameRead> marketSourceFrame,
            Read<Presence> mercenaryPending) {
        public Request {
            Objects.requireNonNull(snapshot); Objects.requireNonNull(candidate); Objects.requireNonNull(root);
            Objects.requireNonNull(spending); Objects.requireNonNull(market); Objects.requireNonNull(marketSourceFrame);
            Objects.requireNonNull(mercenaryPending);
        }
    }
    /** Shared existing financial observations, with no synthetic gift or candidate field. */
    public record CashContext(Snapshot snapshot, Read<Root> root, Read<Spending> spending,
            Read<Market> market, Read<FrameRead> marketSourceFrame, Read<Presence> mercenaryPending) {
        public CashContext {
            Objects.requireNonNull(snapshot); Objects.requireNonNull(root); Objects.requireNonNull(spending);
            Objects.requireNonNull(market); Objects.requireNonNull(marketSourceFrame); Objects.requireNonNull(mercenaryPending);
        }
    }
    public enum Status { OUTSIDE_WARTIME, DEFER_NEW_GIFT, WAR_CASH_RETAINED }
    public enum Reason {
        WAR_SCOPE("current_war_scope_unobserved"),
        GIFT_QUOTE("same_frame_gift_quote_and_treasury_unobserved"),
        MILITARY_FLOOR("wartime_gift_would_breach_military_cash_floor"),
        MAINTENANCE("same_frame_maximum_military_maintenance_unobserved"),
        SPENDING("same_frame_existing_spending_commitments_unobserved"),
        MERCENARY("mercenary_commitment_unknown_or_pending"),
        MARKET("same_frame_native_emergency_quotes_unobserved"),
        NO_USABLE_QUOTE("no_current_native_usable_emergency_contract_quote"),
        RETAIN_RESERVE("retain_current_military_commitments_and_emergency_contract");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Treasury(BigInteger observedRaw, BigInteger giftCostRaw, BigInteger afterGiftRaw) {
        public Treasury {
            Objects.requireNonNull(observedRaw); Objects.requireNonNull(giftCostRaw); Objects.requireNonNull(afterGiftRaw);
            if (giftCostRaw.signum() < 0 || !observedRaw.subtract(giftCostRaw).equals(afterGiftRaw)) {
                throw new IllegalArgumentException("treasury arithmetic does not bind quote");
            }
        }
    }
    public record EmergencyQuote(BigInteger companyId, BigInteger completeContractGoldRaw) {
        public EmergencyQuote {
            Objects.requireNonNull(companyId); Objects.requireNonNull(completeContractGoldRaw);
            if (companyId.signum() < 0 || completeContractGoldRaw.signum() < 0) {
                throw new IllegalArgumentException("nonnegative company and cost required");
            }
        }
    }
    public record Reserve(BigInteger militaryBufferRaw, BigInteger existingCommitmentsRaw,
            EmergencyQuote emergencyQuote, int qualifiedQuoteCount) {
        public Reserve {
            Objects.requireNonNull(militaryBufferRaw); Objects.requireNonNull(existingCommitmentsRaw);
            Objects.requireNonNull(emergencyQuote);
            if (militaryBufferRaw.compareTo(GiftWarCashPolicy.MILITARY_FLOOR_RAW) < 0
                    || existingCommitmentsRaw.signum() < 0 || qualifiedQuoteCount < 1) {
                throw new IllegalArgumentException("invalid qualified reserve");
            }
        }
        public BigInteger requiredRaw() {
            return militaryBufferRaw.add(existingCommitmentsRaw).add(emergencyQuote.completeContractGoldRaw());
        }
    }
    public record Decision(SourceFrame sourceFrame, Status status, Reason reason, Treasury treasury, Reserve reserve) {
        public Decision {
            Objects.requireNonNull(sourceFrame); Objects.requireNonNull(status);
            if (status == Status.OUTSIDE_WARTIME) {
                if (reason != null || treasury != null || reserve != null) { throw new IllegalArgumentException("peaceful branch shape"); }
            } else {
                Objects.requireNonNull(reason);
                if ((reason == Reason.RETAIN_RESERVE) != (reserve != null)
                        || (reserve != null && treasury == null)
                        || (status == Status.WAR_CASH_RETAINED && reserve == null)) {
                    throw new IllegalArgumentException("reserve branch shape");
                }
                if ((reason == Reason.WAR_SCOPE || reason == Reason.GIFT_QUOTE) != (treasury == null)) {
                    throw new IllegalArgumentException("treasury branch shape");
                }
                if (reserve != null && (status == Status.WAR_CASH_RETAINED)
                        != (treasury.afterGiftRaw().compareTo(reserve.requiredRaw()) >= 0)) {
                    throw new IllegalArgumentException("reserve comparison does not match status");
                }
            }
        }
        public boolean newGiftSpendingAllowed() { return status != Status.DEFER_NEW_GIFT; }
    }
}
