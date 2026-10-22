package org.xar.ck3.control.finance.feastbudget;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Pure observed allocation. It does not grant Start, read ledgers, or submit actions. */
public final class FeastBudgetPolicy {
    public static final BigInteger PEACEFUL_GOLD_FLOOR_RAW = BigInteger.valueOf(20_000_000);
    public static final int MAINTENANCE_RESERVATION_MONTHS = 18;
    public static final String MAINTENANCE_POLICY = "robert-feast-discretionary-maintenance-allocation-v1";
    public static final BigInteger SCALE = BigInteger.valueOf(100_000);

    private FeastBudgetPolicy() { }

    public enum Presence { MISSING, NULL, VALUE }
    public record Field<T>(Presence presence, T value) {
        public Field {
            Objects.requireNonNull(presence);
            if ((presence == Presence.VALUE) != (value != null)) {
                throw new IllegalArgumentException("only VALUE has a non-null value");
            }
        }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, null); }
        public static <T> Field<T> nil() { return new Field<>(Presence.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.VALUE, Objects.requireNonNull(value)); }
        public boolean known() { return presence == Presence.VALUE; }
    }
    public record Actor(Field<BigInteger> characterId) {
        public Actor { Objects.requireNonNull(characterId); }
    }
    public record War(Field<BigInteger> warId) {
        public War { Objects.requireNonNull(warId); }
    }
    public record Snapshot(Field<Boolean> paused, Field<Boolean> mapReady,
            Field<Actor> playedCharacter, Field<BigInteger> nativeRevision,
            Field<BigInteger> dateRaw, Field<String> snapshotId, Field<BigInteger> revision,
            Field<List<War>> activeWars, Presence pendingInteraction) {
        public Snapshot {
            Objects.requireNonNull(paused); Objects.requireNonNull(mapReady);
            Objects.requireNonNull(playedCharacter); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(snapshotId);
            Objects.requireNonNull(revision); Objects.requireNonNull(activeWars);
            Objects.requireNonNull(pendingInteraction);
            if (activeWars.known()) { activeWars = Field.of(List.copyOf(activeWars.value())); }
        }
    }
    public record Inputs(Field<BigInteger> actorCharacterId, Field<BigInteger> snapshotRevision,
            Field<BigInteger> dateRaw, Field<String> postSnapshotId, Field<BigInteger> queriedRevision) {
        public Inputs {
            Objects.requireNonNull(actorCharacterId); Objects.requireNonNull(snapshotRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(postSnapshotId);
            Objects.requireNonNull(queriedRevision);
        }
    }
    public record Money(Field<BigInteger> raw, Field<BigInteger> scale) {
        public Money { Objects.requireNonNull(raw); Objects.requireNonNull(scale); }
    }
    public record Maintenance(Field<String> status, Field<Money> value) {
        public Maintenance { Objects.requireNonNull(status); Objects.requireNonNull(value); }
    }
    public record CampaignRoot(Field<BigInteger> playerCharacterId, Field<BigInteger> snapshotRevision,
            Field<BigInteger> dateRaw, Field<Maintenance> maximumMaintenance) {
        public CampaignRoot {
            Objects.requireNonNull(playerCharacterId); Objects.requireNonNull(snapshotRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(maximumMaintenance);
        }
    }
    /** Only validated original ledger reader outputs may be projected here; missing is not clear. */
    public enum IntentState { CLEAR, PENDING }
    public record Ledgers(IntentState construction, IntentState factionGift,
            IntentState firstHeirMarriage, IntentState childMarriage) {
        public Ledgers {
            Objects.requireNonNull(construction); Objects.requireNonNull(factionGift);
            Objects.requireNonNull(firstHeirMarriage); Objects.requireNonNull(childMarriage);
        }
    }
    public record Request(Snapshot snapshot, Inputs inputs, Ledgers ledgers, Field<CampaignRoot> campaignRoot) {
        public Request {
            Objects.requireNonNull(snapshot); Objects.requireNonNull(inputs);
            Objects.requireNonNull(ledgers); Objects.requireNonNull(campaignRoot);
            if (campaignRoot.presence() == Presence.MISSING) {
                throw new IllegalArgumentException("campaign_root is a required nullable wrapper field");
            }
        }
    }
    public enum Reason {
        BUDGET_FRAME_UNOBSERVED("budget_frame_unobserved"),
        ACTIVE_WARS_UNOBSERVED("active_wars_unobserved"),
        INTERACTION_PENDING_OR_UNOBSERVED("interaction_pending_or_unobserved"),
        CONSTRUCTION_PENDING("construction_pending"), FACTION_GIFT_PENDING("faction_gift_pending"),
        FIRST_HEIR_MARRIAGE_PENDING("first_heir_marriage_pending"), CHILD_MARRIAGE_PENDING("child_marriage_pending");
        private final String wire;
        Reason(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public sealed interface Result permits Unavailable, Observed { }
    public record Unavailable(Reason reason) implements Result {
        public Unavailable { Objects.requireNonNull(reason); }
    }
    public record Frame(BigInteger actorCharacterId, BigInteger nativeRevision,
            BigInteger dateRaw, String snapshotId) {
        public Frame {
            Objects.requireNonNull(actorCharacterId); Objects.requireNonNull(nativeRevision);
            Objects.requireNonNull(dateRaw); Objects.requireNonNull(snapshotId);
        }
    }
    /** Null is an unknown reserve, including peaceful frames; zero is an observed zero. */
    public record Observed(Frame frame, int activeWarCount, BigInteger warCashReserveRaw,
            BigInteger maximumMonthlyMaintenanceRaw) implements Result {
        public Observed {
            Objects.requireNonNull(frame);
            if (activeWarCount < 0 || (warCashReserveRaw == null) != (maximumMonthlyMaintenanceRaw == null)) {
                throw new IllegalArgumentException("reserve and supporting maintenance are paired");
            }
            if (warCashReserveRaw != null && (activeWarCount == 0 || maximumMonthlyMaintenanceRaw.signum() < 0
                    || !warCashReserveRaw.equals(maximumMonthlyMaintenanceRaw.multiply(BigInteger.valueOf(MAINTENANCE_RESERVATION_MONTHS))))) {
                throw new IllegalArgumentException("invalid maintenance allocation");
            }
        }
    }

    public static Result observe(Request request) {
        Objects.requireNonNull(request);
        Snapshot snapshot = request.snapshot(); Inputs inputs = request.inputs();
        if (!Boolean.TRUE.equals(snapshot.paused().value()) || !Boolean.TRUE.equals(snapshot.mapReady().value())
                || !snapshot.playedCharacter().known()
                || !same(snapshot.playedCharacter().value().characterId(), inputs.actorCharacterId())
                || !same(snapshot.nativeRevision(), inputs.snapshotRevision())
                || !same(snapshot.dateRaw(), inputs.dateRaw())
                || !same(snapshot.snapshotId(), inputs.postSnapshotId())
                || !same(snapshot.revision(), inputs.queriedRevision())) {
            return new Unavailable(Reason.BUDGET_FRAME_UNOBSERVED);
        }
        if (!snapshot.activeWars().known() || snapshot.activeWars().value().stream()
                .anyMatch(war -> !war.warId().known() || war.warId().value().signum() <= 0)) {
            return new Unavailable(Reason.ACTIVE_WARS_UNOBSERVED);
        }
        if (snapshot.pendingInteraction() != Presence.NULL) {
            return new Unavailable(Reason.INTERACTION_PENDING_OR_UNOBSERVED);
        }
        Ledgers ledgers = request.ledgers();
        if (ledgers.construction() == IntentState.PENDING) { return new Unavailable(Reason.CONSTRUCTION_PENDING); }
        if (ledgers.factionGift() == IntentState.PENDING) { return new Unavailable(Reason.FACTION_GIFT_PENDING); }
        if (ledgers.firstHeirMarriage() == IntentState.PENDING) { return new Unavailable(Reason.FIRST_HEIR_MARRIAGE_PENDING); }
        if (ledgers.childMarriage() == IntentState.PENDING) { return new Unavailable(Reason.CHILD_MARRIAGE_PENDING); }
        BigInteger rate = maintenance(request);
        return new Observed(new Frame(inputs.actorCharacterId().value(), inputs.snapshotRevision().value(),
                inputs.dateRaw().value(), snapshot.snapshotId().value()), snapshot.activeWars().value().size(),
                rate == null ? null : rate.multiply(BigInteger.valueOf(MAINTENANCE_RESERVATION_MONTHS)), rate);
    }

    private static BigInteger maintenance(Request request) {
        if (request.snapshot().activeWars().value().isEmpty() || !request.campaignRoot().known()) { return null; }
        CampaignRoot root = request.campaignRoot().value(); Inputs inputs = request.inputs();
        if (!same(root.playerCharacterId(), inputs.actorCharacterId())
                || !same(root.snapshotRevision(), inputs.snapshotRevision())
                || !same(root.dateRaw(), inputs.dateRaw()) || !root.maximumMaintenance().known()) { return null; }
        Maintenance maintenance = root.maximumMaintenance().value();
        if (!"available".equals(maintenance.status().value()) || !maintenance.value().known()) { return null; }
        Money value = maintenance.value().value();
        return value.raw().known() && value.raw().value().signum() >= 0 && SCALE.equals(value.scale().value())
                ? value.raw().value() : null;
    }

    private static <T> boolean same(Field<T> left, Field<T> right) {
        // Missing/null do not provide a frame identity, even if both are absent.
        return left.known() && right.known() && left.value().equals(right.value());
    }
}
