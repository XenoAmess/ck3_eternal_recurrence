package org.xar.ck3.control.nativebridge.capabilities.army;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Native identities retain their full generation. A public CUnit is a different domain from a CArmy/component ID. */
public final class ArmyTypes {
    private ArmyTypes() { }
    public record PublicUnitId(int value) { public PublicUnitId { require(value >= 0, "public CUnit must be 0..INT32_MAX; zero is valid"); } }
    public record FullId(int value) { public FullId { require(value != -1, "invalid full-generation component sentinel"); } }
    public record PositiveId(int value) { public PositiveId { require(value > 0, "positive complete native ID required"); } }
    public record HireId(long value) { public HireId { require(value >= 0 && value < 4_294_967_295L, "complete uint32 reference required; zero is valid"); } }
    public record UInt64(BigInteger value) {
        public UInt64 { Objects.requireNonNull(value); require(value.signum() >= 0 && value.bitLength() <= 64, "uint64 required"); }
        public static UInt64 positive(BigInteger value) { UInt64 result = new UInt64(value); require(value.signum() > 0, "positive uint64 required"); return result; }
        public String decimal() { return value.toString(); }
    }
    public record DeclarationId(PositiveId target, int casusBelliIndex, int configurationIndex) {
        public DeclarationId { Objects.requireNonNull(target); require(casusBelliIndex >= 0 && configurationIndex >= -1, "observed native declaration indices required"); }
        public String wire() { return target.value() + "-" + casusBelliIndex + "-" + configurationIndex; }
        public static DeclarationId parse(String wire) {
            require(wire != null && wire.matches("[1-9][0-9]*-(?:0|[1-9][0-9]*)-(?:-1|0|[1-9][0-9]*)"), "canonical declaration identity required");
            int first = wire.indexOf('-'), second = wire.indexOf('-', first + 1);
            DeclarationId value = new DeclarationId(new PositiveId(Integer.parseInt(wire.substring(0, first))), Integer.parseInt(wire.substring(first + 1, second)), Integer.parseInt(wire.substring(second + 1)));
            require(value.wire().equals(wire), "declaration identity spelling changed"); return value;
        }
    }
    public enum Side { ATTACKER, DEFENDER }
    public enum Scope { FULL_SIDE, OWNER_SUBSET }
    public enum Phase { MANEUVER, MAIN, PURSUIT, DONE }
    public enum Winner { NONE, ATTACKER, DEFENDER }
    public enum Availability { AVAILABLE, PARTIAL, UNAVAILABLE, ABSENT }
    /** Missing, explicit null and a present value are separate contract states. */
    public sealed interface Field<T> permits Missing, NullValue, Present { }
    public record Missing<T>() implements Field<T> { }
    public record NullValue<T>() implements Field<T> { }
    public record Present<T>(T value) implements Field<T> { public Present { Objects.requireNonNull(value); } }
    public record Context(ObservationIdentity before, G2Source source, String sessionId, Instant deadline) {
        public Context { Objects.requireNonNull(before); Objects.requireNonNull(source); StrictJson.text(sessionId); Objects.requireNonNull(deadline); require(before.machineId().equals(source.machineId()), "source machine mismatch"); }
        public BigInteger nativeRevision() { return before.frame().identity().nativeRevision(); }
        public BigInteger dateRaw() { return before.frame().identity().dateRaw(); }
        public BigInteger playerId() { return before.frame().identity().player(); }
    }
    public record Frame(UInt64 nativeRevision, long dateRaw, Field<UInt64> querySequence) {
        public Frame { Objects.requireNonNull(nativeRevision); Objects.requireNonNull(querySequence); require(nativeRevision.value().signum() > 0, "native frame must be positive"); if (querySequence instanceof Present<UInt64> present) require(present.value().value().signum() > 0, "observed query sequence must be positive"); }
    }
    public static <T> List<T> distinct(List<T> input, int minimum, int maximum, String name) {
        List<T> result = List.copyOf(input); require(result.size() >= minimum && result.size() <= maximum && result.stream().distinct().count() == result.size(), name + " must have bounded unique IDs"); return result;
    }
    static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}
