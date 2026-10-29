package org.xar.ck3.control.wave2.planning.playerrisk;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;

/** Pure same-frame risk evidence. Neither readiness nor a signal grants action authority. */
public final class PlayerRiskContext {
    public static final String SCHEMA = "xar.ck3.ordinary-player-risk-context/v1";
    static final String INVALID = "same_frame_player_risk_inputs_invalid";
    static final String MISSING = "same_frame_campaign_root_result_unavailable";
    private PlayerRiskContext() { }

    public enum Status { PARTIAL, UNAVAILABLE }
    public enum Band { DYING_OR_WORSE, BELOW_FINE, FINE_OR_BETTER }
    public enum Priority { CRITICAL, ELEVATED, NORMAL }

    public sealed interface Component<T> permits Known, Unknown, NotApplicable { }
    public record Known<T>(T value) implements Component<T> {
        public Known { Objects.requireNonNull(value); }
    }
    public record Unknown<T>(String reason) implements Component<T> {
        public Unknown { requireReason(reason); }
    }
    public record NotApplicable<T>(String reason) implements Component<T> {
        public NotApplicable { requireReason(reason); }
    }
    public record Binding(String snapshotId, BigInteger revision, BigInteger nativeRevision,
                          int dateRaw, int characterId) { }
    public record Source(BigInteger querySequence, String backendId) { }
    /** Current diagnostics are not a response-generation witness. */
    public record CurrentScope(BigInteger connectionGeneration, boolean responseGenerationObserved) { }
    public record Health(long raw, Band band, boolean belowFine, boolean dyingOrWorse) { }
    public record Stress(int points, boolean firstBreakThreshold) { }
    public record Alerts(Component<Boolean> belowFine, Component<Boolean> highStress,
                         Component<Boolean> noHeir, Component<Boolean> partitionSplit) { }
    public record Signals(Component<Priority> successionPriority, Component<Boolean> avoidStressGain,
                          Component<Boolean> protectLegitimacyFloor) { }
    public record Readiness(boolean healthReady, boolean stressReady,
                            boolean successionPriorityReady, boolean legitimacyProtectionReady) { }
    public record Context(Status status, Binding binding, Source source, CurrentScope currentScope,
                          Component<Health> health, Component<Stress> stress, Alerts alerts,
                          Signals signals, Readiness readiness, String unavailableReason) {
        public Context {
            Objects.requireNonNull(status); Objects.requireNonNull(health); Objects.requireNonNull(stress);
            Objects.requireNonNull(alerts); Objects.requireNonNull(signals); Objects.requireNonNull(readiness);
            if (status == Status.UNAVAILABLE) {
                requireReason(unavailableReason);
                if (binding != null || source != null || currentScope != null
                        || readiness.healthReady || readiness.stressReady
                        || readiness.successionPriorityReady || readiness.legitimacyProtectionReady) {
                    throw new IllegalArgumentException("unavailable risk cannot retain frame or readiness");
                }
            } else {
                Objects.requireNonNull(binding); Objects.requireNonNull(source); Objects.requireNonNull(currentScope);
                if (unavailableReason != null) { throw new IllegalArgumentException("observed risk cannot carry failure"); }
            }
        }
    }

    sealed interface Input permits Rejected, RootUnavailable, Observation { }
    record Rejected(String reason) implements Input { }
    record RootUnavailable(String reason) implements Input { }
    record HeldTitle(int titleId, int tier, Integer firstHeir, Integer capital, boolean primary,
                     boolean familyNoProvince) { }
    record Observation(Binding binding, Source source, CurrentScope scope, long healthRaw,
                       Component<Stress> stress, Integer primaryTier, List<Integer> successors,
                       List<HeldTitle> heldTitles) implements Input {
        Observation { successors = List.copyOf(successors); heldTitles = List.copyOf(heldTitles); }
    }

    static Context project(Input input) {
        if (input instanceof Rejected rejected) { return unavailable(rejected.reason); }
        if (input instanceof RootUnavailable unavailable) { return unavailable(unavailable.reason); }
        Observation observed = (Observation) input;
        long raw = observed.healthRaw;
        Band band = raw <= 150_000 ? Band.DYING_OR_WORSE : raw < 300_000 ? Band.BELOW_FINE : Band.FINE_OR_BETTER;
        Health health = new Health(raw, band, raw < 300_000, raw <= 150_000);
        boolean landed = observed.primaryTier != null;
        boolean hasHeir = !observed.successors.isEmpty();
        boolean partitionApplicable = landed && observed.primaryTier != 1;
        Integer heir = hasHeir ? observed.successors.getFirst() : null;
        boolean split = partitionApplicable && hasHeir && observed.heldTitles.stream()
                .anyMatch(row -> row.firstHeir != null && !row.firstHeir.equals(heir));
        Component<Boolean> noHeir = landed ? new Known<>(!hasHeir) : new NotApplicable<>("no_primary_landed_title");
        Component<Boolean> splitAlert = partitionApplicable ? new Known<>(split)
                : new NotApplicable<>(landed ? "primary_title_below_county" : "no_primary_landed_title");
        boolean successionRisk = landed && !hasHeir || split;
        Priority priority = band == Band.DYING_OR_WORSE && successionRisk ? Priority.CRITICAL
                : band == Band.BELOW_FINE && successionRisk ? Priority.ELEVATED : Priority.NORMAL;
        Component<Boolean> highStress = observed.stress instanceof Known<Stress> known
                ? new Known<>(known.value.firstBreakThreshold) : new Unknown<>("played_character_stress_unavailable");
        Signals signals = new Signals(new Known<>(priority), highStress,
                new Unknown<>("player_legitimacy_state_unavailable"));
        return new Context(Status.PARTIAL, observed.binding, observed.source, observed.scope,
                new Known<>(health), observed.stress, new Alerts(new Known<>(health.belowFine), highStress, noHeir, splitAlert),
                signals, new Readiness(true, observed.stress instanceof Known<?>, true, false), null);
    }

    public static Context unavailable(String reason) {
        return new Context(Status.UNAVAILABLE, null, null, null, new Unknown<>(reason), new Unknown<>(reason),
                new Alerts(new Unknown<>(reason), new Unknown<>(reason), new Unknown<>(reason), new Unknown<>(reason)),
                new Signals(new Unknown<>(reason), new Unknown<>(reason), new Unknown<>(reason)),
                new Readiness(false, false, false, false), reason);
    }
    private static void requireReason(String reason) {
        if (reason == null || reason.isEmpty()) { throw new IllegalArgumentException("nonempty reason required"); }
    }
}
