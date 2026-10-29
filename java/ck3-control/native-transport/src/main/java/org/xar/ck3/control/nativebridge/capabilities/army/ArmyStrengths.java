package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Reader-owned values: none of these observations grants action, restore or next-episode authority. */
public final class ArmyStrengths {
    private ArmyStrengths() { }
    public static final String STEP = "query-army-strengths-v1";
    public static final String CAPABILITY = "game.command.query-army-strengths-v1";
    public static final String SCOPED_CAPABILITY = "game.command.query-army-strengths-scoped-v1";
    public static final int SCALE = 100_000;
    public enum Profile {
        ORDINARY_CORE_V1("ordinary_core_v1", "not_requested"), OBSERVED_HISTORY_FULL_V1("observed_history_full_v1", "exported_retained");
        private final String wire; private final String coverage;
        Profile(String wire, String coverage) { this.wire = wire; this.coverage = coverage; }
        public String wire() { return wire; } public String coverage() { return coverage; }
    }
    public enum Mode { EXPLICIT_RICH, AUTO_CORE, PRIVATE_AUTO_SCALAR }
    public enum Status { AVAILABLE, PARTIAL, UNAVAILABLE }
    public enum Role { PLAYER, ACTIVE_WAR_ALLY, ACTIVE_WAR_ENEMY }
    public enum EntryMode { OBSERVED_PREPARED, FIXED_CHUNK0_PREPARE }
    public record ScopeArmy(PublicUnitId army, Role role, List<PositiveId> wars) {
        public ScopeArmy { Objects.requireNonNull(army); Objects.requireNonNull(role); wars = distinct(wars, 0, 65536, "scope wars"); }
    }
    /** The seven original cache fields, plus actual machine/Game/session binding. */
    public record Binding(String machineId, GameGeneration game, String sessionId, BigInteger connectionGeneration,
            String snapshotId, BigInteger publicRevision, BigInteger nativeRevision, BigInteger dateRaw,
            Optional<String> episodeRunId, int actorCharacterId) {
        public Binding {
            Objects.requireNonNull(machineId); Objects.requireNonNull(game); Objects.requireNonNull(sessionId);
            Objects.requireNonNull(connectionGeneration); Objects.requireNonNull(snapshotId); Objects.requireNonNull(publicRevision);
            Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(episodeRunId);
            new NativeCharacterId(actorCharacterId);
            require(connectionGeneration.signum() > 0 && connectionGeneration.bitLength() <= 64
                    && publicRevision.signum() >= 0 && nativeRevision.signum() >= 0, "exact published query binding required");
        }
    }
    public record Snapshot(Context context, Binding binding, List<ScopeArmy> scope, RawJson original) {
        public Snapshot { Objects.requireNonNull(context); Objects.requireNonNull(binding); scope = List.copyOf(scope); Objects.requireNonNull(original); }
    }
    public record Query(Profile profile, Mode mode, Field<List<PublicUnitId>> requestedArmies,
            EntryMode refillEntryMode, EntryMode besiegingEntryMode) {
        public Query {
            Objects.requireNonNull(profile); Objects.requireNonNull(mode); Objects.requireNonNull(requestedArmies);
            Objects.requireNonNull(refillEntryMode); Objects.requireNonNull(besiegingEntryMode);
            require(!(requestedArmies instanceof NullValue<?>), "requested Army scope cannot be explicit null");
            if (requestedArmies instanceof Present<List<PublicUnitId>> present)
                requestedArmies = new Present<>(distinct(present.value(), 1, 64, "Army request"));
            require(mode == Mode.EXPLICIT_RICH || profile == Profile.ORDINARY_CORE_V1 && requestedArmies instanceof Missing<?>,
                    "auto scalar projection requires the complete ordinary scope");
        }
    }
    public record Core(Status status, PublicUnitId army, Field<FullId> nativeArmy, Role role, List<PositiveId> wars,
            Field<Integer> regimentCount, Field<Integer> currentSoldiers, Field<Integer> maximumSoldiers,
            Field<Long> aiBasePowerRaw, Field<String> unavailableReason) {
        public Core {
            Objects.requireNonNull(status); Objects.requireNonNull(army); Objects.requireNonNull(nativeArmy); Objects.requireNonNull(role);
            wars = distinct(wars, 0, 65536, "strength wars"); Objects.requireNonNull(regimentCount); Objects.requireNonNull(currentSoldiers);
            Objects.requireNonNull(maximumSoldiers); Objects.requireNonNull(aiBasePowerRaw); Objects.requireNonNull(unavailableReason);
            require(status != Status.PARTIAL, "individual strength rows are available or unavailable");
            boolean all = regimentCount instanceof Present<?> && currentSoldiers instanceof Present<?> && maximumSoldiers instanceof Present<?> && aiBasePowerRaw instanceof Present<?>;
            boolean none = regimentCount instanceof NullValue<?> && currentSoldiers instanceof NullValue<?> && maximumSoldiers instanceof NullValue<?> && aiBasePowerRaw instanceof NullValue<?>;
            require(status == Status.AVAILABLE ? nativeArmy instanceof Present<?> && all && unavailableReason instanceof NullValue<?>
                    : none && unavailableReason instanceof Present<?>, "row aggregates and availability must be atomic");
        }
        public ScopeArmy scope() { return new ScopeArmy(army, role, wars); }
    }
    public enum SupplyKey {
        CURRENT_SUPPLY("current_supply"), MERGE_SUPPLY_DESTINATION_WEIGHT("merge_supply_destination_weight"),
        CURRENT_SUPPLY_CAPACITY("current_supply_capacity"), CURRENT_ATTRITION_FRACTION("current_attrition_fraction"),
        CURRENT_SUPPLY_CHANGE_MONTHLY("current_supply_change_monthly");
        private final String prefix; SupplyKey(String prefix) { this.prefix = prefix; }
        public String rawKey() { return prefix + "_raw"; } public String scaleKey() { return prefix + "_scale"; }
    }
    public record Supply(SupplyKey key, Field<Long> raw) { public Supply { Objects.requireNonNull(key); Objects.requireNonNull(raw); require(!(raw instanceof Missing<?>), "present scalar must be value or null"); } }
    public enum GatheringStatus { AVAILABLE, NOT_GATHERING, UNAVAILABLE }
    public record Gathering(Field<Integer> daysLeft, GatheringStatus status, boolean ready) {
        public Gathering { Objects.requireNonNull(daysLeft); Objects.requireNonNull(status); require((status == GatheringStatus.AVAILABLE) == (daysLeft instanceof Present<?>) && ready == (status != GatheringStatus.UNAVAILABLE), "gathering status mismatch"); }
    }
    public enum MaaStatus { AVAILABLE, ABSENT, UNAVAILABLE }
    public record Composition(MaaStatus status, Field<String> key, Field<Integer> siegeTier, boolean siegeTierObservable, Field<String> reason) {
        public Composition { Objects.requireNonNull(status); Objects.requireNonNull(key); Objects.requireNonNull(siegeTier); Objects.requireNonNull(reason); require((status == MaaStatus.AVAILABLE) == (key instanceof Present<?>) && siegeTierObservable == (siegeTier instanceof Present<?>), "regiment composition mismatch"); }
    }
    public record SupplyEligibility(Field<Boolean> eligible, Field<String> reason) {
        public SupplyEligibility { Objects.requireNonNull(eligible); Objects.requireNonNull(reason); require(eligible instanceof NullValue<?> ? reason instanceof Present<?> : eligible instanceof Present<?> && reason instanceof NullValue<?>, "regiment eligibility reason mismatch"); }
    }
    public record Regiment(int armyRegimentId, int currentSoldiers, int maximumSoldiers,
            Field<Composition> composition, Field<SupplyEligibility> supplyEligibility) {
        public Regiment { require(armyRegimentId >= 0 && currentSoldiers >= 0 && maximumSoldiers >= 0, "regiment nonnegative int32 values required"); Objects.requireNonNull(composition); Objects.requireNonNull(supplyEligibility); }
    }
    public record RowContext(Core core, Field<List<Regiment>> regiments) {
        public RowContext { Objects.requireNonNull(core); Objects.requireNonNull(regiments); if (regiments instanceof Present<List<Regiment>> p) regiments = new Present<>(List.copyOf(p.value())); }
    }
    public record FamilyValue<T>(ArmyStrengthsFamilies.Key key, Class<T> valueType, Field<T> value, RawJson normalizedJson, RawJson publicV2Json) {
        public FamilyValue { Objects.requireNonNull(key); Objects.requireNonNull(valueType); Objects.requireNonNull(value); Objects.requireNonNull(normalizedJson); Objects.requireNonNull(publicV2Json); if (value instanceof Present<T> p) valueType.cast(p.value()); }
        public FamilyValue(ArmyStrengthsFamilies.Key key, Class<T> valueType, Field<T> value, RawJson normalizedJson) {
            this(key, valueType, value, normalizedJson, normalizedJson);
        }
    }
    public record Row(Core core, List<Supply> supply, Field<Gathering> gathering, Field<List<Regiment>> regiments,
            List<FamilyValue<?>> families) {
        public Row { Objects.requireNonNull(core); supply = List.copyOf(supply); Objects.requireNonNull(gathering); Objects.requireNonNull(regiments); if (regiments instanceof Present<List<Regiment>> p) regiments = new Present<>(List.copyOf(p.value())); families = List.copyOf(families); }
    }
    public record NativeTiming(BigInteger readTotalNs, BigInteger ownerQueryNs, BigInteger baselineReadNs, BigInteger richAttachNs, BigInteger serializeNs) {
        public NativeTiming { for (BigInteger n : List.of(readTotalNs, ownerQueryNs, baselineReadNs, richAttachNs, serializeNs)) require(n.signum() >= 0, "timings must be nonnegative integers"); require(baselineReadNs.compareTo(ownerQueryNs) <= 0 && richAttachNs.compareTo(ownerQueryNs) <= 0 && ownerQueryNs.compareTo(readTotalNs) <= 0, "native timing interval mismatch"); }
    }
    public record Read(Profile profile, Status status, BigInteger sequence, String backendId, List<Row> rows,
            Field<NativeTiming> timing, Field<Status> publishedScopeStatus, PlanningReadReceipt original) implements ArmyStrengthsReadValue {
        public Read { Objects.requireNonNull(profile); Objects.requireNonNull(status); Objects.requireNonNull(sequence); Objects.requireNonNull(backendId); rows = List.copyOf(rows); Objects.requireNonNull(timing); Objects.requireNonNull(publishedScopeStatus); Objects.requireNonNull(original); require(sequence.signum() > 0 && sequence.bitLength() <= 64 && status != Status.UNAVAILABLE, "positive exact query sequence and aggregate status required"); }
        @Override public ArmyStrengthsReadValue.CoreProjection coreSemanticProjection() {
            require(!(publishedScopeStatus instanceof NullValue<?>), "Core scope cannot be an invented null");
            var values = rows.stream().map(row -> org.xar.ck3.control.application.driver.DriverJson.fromNode(
                    ArmyStrengthsCodec.coreJson(row.core()))).map(value -> org.xar.ck3.control.planning.opportunity.OpportunityJson.object(value, "Core row")).toList();
            return new ArmyStrengthsReadValue.CoreProjection(ArmyRequests.StrengthProfile.valueOf(profile.name()),
                    publishedScopeStatus instanceof Missing<?> ? ArmyStrengthsReadValue.Scope.FULL_PUBLISHED : ArmyStrengthsReadValue.Scope.SUBSET,
                    ArmyTypes.Availability.valueOf(status.name()), sequence, values);
        }
    }
    public record SnapshotProjection(Binding binding, Profile profile, Status status, BigInteger sequence, List<Core> rows) {
        public SnapshotProjection { Objects.requireNonNull(binding); Objects.requireNonNull(profile); Objects.requireNonNull(status); Objects.requireNonNull(sequence); rows = List.copyOf(rows); }
    }
    public static Status status(List<Row> rows) { return rows.stream().allMatch(row -> row.core().status() == Status.AVAILABLE) ? Status.AVAILABLE : Status.PARTIAL; }
}
