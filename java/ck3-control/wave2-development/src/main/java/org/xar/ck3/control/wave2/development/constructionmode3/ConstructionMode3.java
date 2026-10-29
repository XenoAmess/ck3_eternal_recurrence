package org.xar.ck3.control.wave2.development.constructionmode3;

import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Independent copied mode3 source inputs. No native-call, building-attribution or realised-net claim. */
public final class ConstructionMode3 {
    public static final String FIELD = "native_mode3_inputs";
    public static final String SCHEMA = "xar.ck3.construction-owner-mode3-inputs-12004-v1";
    public static final String SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private ConstructionMode3() { }
    public record BuildIdentity(String gameVersion, String executableSha256) {
        public BuildIdentity { Objects.requireNonNull(gameVersion); Objects.requireNonNull(executableSha256); }
    }
    public record Frame(BigInteger revision, Integer dateRaw, Integer actorId) {
        public Frame { nativeInteger(revision, 64, true); }
    }
    public record Identity(Integer baronyId, Integer provinceId) { }
    public record WorldFrame(Frame frame, List<Identity> identities) {
        public WorldFrame { Objects.requireNonNull(frame); identities = List.copyOf(identities); }
    }
    public record Component(long callRva, int keyU16, boolean reached, BigInteger rawQ64, String unavailableInput) {
        public Component {
            Objects.requireNonNull(unavailableInput);
            require(callRva >= 0 && callRva <= 0xFFFF_FFFFL && keyU16 >= 0 && keyU16 <= 0xFFFF, "native component widths required");
            nativeInteger(rawQ64, 64, false);
        }
    }
    public record RawValues(BigInteger loadedPublisher718, BigInteger loadedKey3f, BigInteger factorBeforeContext,
            BigInteger contextFactor, BigInteger ownerFactor, BigInteger conditionalAggregate) {
        public RawValues {
            nativeInteger(loadedPublisher718, 64, false); nativeInteger(loadedKey3f, 64, false); nativeInteger(factorBeforeContext, 64, false);
            nativeInteger(contextFactor, 64, false); nativeInteger(ownerFactor, 64, false); nativeInteger(conditionalAggregate, 64, false);
        }
    }
    public record Keys(Integer selectedA3OrA4, Integer selectedA6OrA7, Integer contextDynamic) {
        public Keys { key(selectedA3OrA4); key(selectedA6OrA7); key(contextDynamic); }
    }
    public record Children(Integer child28be0b0, Integer child28b9300) { }
    public record Inputs(BigInteger revision, Integer provinceId, String unavailableInput, Boolean contextPredicate,
            boolean inputsObserved, boolean allReachedInputsObserved, RawValues raw, Keys keys,
            Children children, List<Component> components) {
        public Inputs {
            Objects.requireNonNull(unavailableInput); Objects.requireNonNull(raw); Objects.requireNonNull(keys); Objects.requireNonNull(children);
            nativeInteger(revision, 64, true);
            components = List.copyOf(components);
        }
    }
    public record Holding(int baronyId, int provinceId, Inputs inputs) { public Holding { Objects.requireNonNull(inputs); } }
    public enum Failure {
        NONE("none"), EXACT_BUILD("exact_build"), APPLICATION_MAIN("application_main"), PAUSED_FRAME("paused_frame"),
        PLAYER_IDENTITY("player_identity"), HELD_TITLE_SOURCE("held_title_source"), HOLDING_PROVINCE_IDENTITY("holding_province_identity"),
        DEFINITION_SOURCE("definition_source"), FRAME_CHANGED("frame_changed");
        private final String wire;
        Failure(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Packet(String schema, String sourceSha256, boolean currentFrameObserved, Failure failure,
            Frame frame, List<Holding> holdings) {
        public Packet {
            Objects.requireNonNull(schema); Objects.requireNonNull(sourceSha256); Objects.requireNonNull(failure); Objects.requireNonNull(frame);
            holdings = List.copyOf(holdings);
        }
    }
    public enum Status {
        OBSERVATION_UNAVAILABLE("observation_unavailable"), CONDITIONAL_PROJECTION_AVAILABLE("conditional_projection_available"), PARTIAL("partial"), SOURCE_RED("source_red");
        private final String wire;
        Status(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record State(Status status, String reason) { public State { Objects.requireNonNull(status); } }
    public sealed interface Normalization permits Absent, ExplicitNull, Normalized, SourceRed { }
    public record Absent() implements Normalization { }
    public record ExplicitNull() implements Normalization { }
    public record Normalized(Packet packet, State state) implements Normalization {
        public Normalized { Objects.requireNonNull(packet); Objects.requireNonNull(state); }
    }
    public record SourceRed(String reason) implements Normalization { public SourceRed { Objects.requireNonNull(reason); } }
    public record ProvinceProjection(State state, Inputs inputs, boolean includePacketIdentity) {
        public ProvinceProjection { Objects.requireNonNull(state); }
    }
    public static final class InvalidSource extends IllegalArgumentException {
        private static final long serialVersionUID = 1L;
        public InvalidSource(String message) { super(message); }
    }
    static void require(boolean condition, String reason) { if (!condition) { throw new InvalidSource(reason); } }
    private static void nativeInteger(BigInteger value, int bits, boolean unsigned) {
        if (value == null) { return; }
        BigInteger minimum = unsigned ? BigInteger.ZERO : BigInteger.ONE.shiftLeft(bits - 1).negate();
        BigInteger maximum = BigInteger.ONE.shiftLeft(unsigned ? bits : bits - 1).subtract(BigInteger.ONE);
        require(value.compareTo(minimum) >= 0 && value.compareTo(maximum) <= 0, "native integer width required");
    }
    private static void key(Integer value) { require(value == null || (value >= 0 && value <= 0xFFFF), "native unsigned16 key required"); }

    public static Normalized normalize(Packet packet, Frame source, WorldFrame world, BuildIdentity build) {
        require(build.equals(new BuildIdentity("1.20.0.4", SHA)) && packet.schema().equals(SCHEMA) && packet.sourceSha256().equals(SHA),
                FIELD + " requires its exact actual4 source identity");
        if (!packet.currentFrameObserved()) {
            require(packet.holdings().isEmpty() && packet.frame().revision() == null && packet.frame().dateRaw() == null && packet.frame().actorId() == null,
                    FIELD + " unobserved frame must retain null metadata and no holdings");
            return new Normalized(packet, new State(Status.OBSERVATION_UNAVAILABLE, packet.failure().wire()));
        }
        require(packet.frame().revision() != null && packet.frame().revision().equals(source.revision()), FIELD + ".snapshot_revision differs from this material source frame");
        require(packet.frame().dateRaw() != null && packet.frame().dateRaw().equals(source.dateRaw()), FIELD + ".date_raw differs from this material source frame");
        require(packet.frame().actorId() != null && packet.frame().actorId().equals(source.actorId()), FIELD + ".player_character_id differs from this material source frame");
        require(packet.frame().equals(world.frame()), FIELD + " differs from this native world observation");
        Set<Identity> seen = new HashSet<>();
        for (int index = 0; index < packet.holdings().size(); index++) {
            Holding holding = packet.holdings().get(index); Identity identity = new Identity(holding.baronyId(), holding.provinceId());
            String path = FIELD + ".holdings[" + index + "]";
            require(seen.add(identity) && world.identities().stream().filter(identity::equals).count() == 1,
                    path + " lacks one exact held title/province in this query");
            Inputs inputs = holding.inputs();
            require((inputs.revision() == null || inputs.revision().equals(packet.frame().revision()))
                    && (inputs.provinceId() == null || inputs.provinceId().equals(holding.provinceId())),
                    path + ".inputs differs from its copied current frame or holding");
        }
        List<State> states = packet.holdings().stream().map(row -> holdingState(row.inputs())).toList();
        Status status = !states.isEmpty() && states.stream().allMatch(state -> state.status() == Status.CONDITIONAL_PROJECTION_AVAILABLE)
                ? Status.CONDITIONAL_PROJECTION_AVAILABLE : Status.PARTIAL;
        String reason = states.stream().map(State::reason).filter(Objects::nonNull).findFirst().orElse(states.isEmpty() ? "no_held_mode3_inputs" : null);
        return new Normalized(packet, new State(status, reason));
    }

    public static State holdingState(Inputs inputs) {
        if (inputs.revision() == null || inputs.provinceId() == null) {
            return new State(Status.PARTIAL, inputs.unavailableInput().isEmpty() ? "mode3_holding_frame_metadata_unavailable" : inputs.unavailableInput());
        }
        if (inputs.inputsObserved() && inputs.allReachedInputsObserved() && inputs.raw().conditionalAggregate() != null) {
            return new State(Status.CONDITIONAL_PROJECTION_AVAILABLE, null);
        }
        return new State(Status.PARTIAL, inputs.unavailableInput().isEmpty() ? "reached_mode3_source_inputs_unavailable" : inputs.unavailableInput());
    }
    public static ProvinceProjection province(Normalization normalization, int baronyId, int provinceId) {
        return switch (normalization) {
            case Absent ignored -> throw new IllegalArgumentException("absent mode3 has no province observation");
            case ExplicitNull ignored -> new ProvinceProjection(new State(Status.OBSERVATION_UNAVAILABLE, "native_mode3_inputs_explicitly_null"), null, false);
            case SourceRed red -> new ProvinceProjection(new State(Status.SOURCE_RED, red.reason()), null, false);
            case Normalized normalized -> {
                if (!normalized.packet().currentFrameObserved()) { yield new ProvinceProjection(normalized.state(), null, true); }
                List<Holding> rows = normalized.packet().holdings().stream().filter(row -> row.baronyId() == baronyId && row.provinceId() == provinceId).toList();
                if (rows.size() != 1) {
                    yield new ProvinceProjection(new State(Status.OBSERVATION_UNAVAILABLE, "mode3_holding_missing_or_duplicate"), null, true);
                }
                yield new ProvinceProjection(holdingState(rows.getFirst().inputs()), rows.getFirst().inputs(), true);
            }
        };
    }
}
