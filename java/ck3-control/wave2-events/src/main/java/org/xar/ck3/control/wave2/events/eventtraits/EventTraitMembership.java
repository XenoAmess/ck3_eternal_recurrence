package org.xar.ck3.control.wave2.events.eventtraits;

import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.semantic.NativePlayerEventTraitMembership;

/** Detached two-trait fact already produced by the exact-build C++ snapshot reader. */
public final class EventTraitMembership {
    public static final String SCHEMA = NativePlayerEventTraitMembership.SCHEMA;
    public static final String GAME_VERSION = NativePlayerEventTraitMembership.GAME_VERSION;
    public static final String EXECUTABLE_SHA256 = NativePlayerEventTraitMembership.EXECUTABLE_SHA256;
    private static final BigInteger UINT64_MAX = new BigInteger("18446744073709551615");
    private EventTraitMembership() { }

    public enum Trait {
        LIFESTYLE_POET("lifestyle_poet"), JOURNALLER("journaller");
        private final String wire;
        Trait(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** This is a native publication revision, never the independent public revision. */
    public record Frame(BigInteger nativeRevision, int dateRaw, int playedCharacterId) {
        public Frame {
            Objects.requireNonNull(nativeRevision, "nativeRevision");
            if (nativeRevision.signum() <= 0 || nativeRevision.compareTo(UINT64_MAX) > 0 || playedCharacterId <= 0) {
                throw new IllegalArgumentException("positive uint64 native revision and positive int32 player required");
            }
        }
    }
    public record Traits(boolean lifestylePoet, boolean journaller) {
        public boolean contains(Trait trait) {
            return switch (Objects.requireNonNull(trait, "trait")) {
                case LIFESTYLE_POET -> lifestylePoet;
                case JOURNALLER -> journaller;
            };
        }
    }
    public sealed interface Observation permits Available, Unavailable { Frame frame(); }
    public record Available(Frame frame, Traits traits) implements Observation {
        public Available { Objects.requireNonNull(frame, "frame"); Objects.requireNonNull(traits, "traits"); }
    }
    public record Unavailable(Frame frame, String reason) implements Observation {
        public Unavailable {
            Objects.requireNonNull(frame, "frame");
            if (reason == null || reason.isEmpty() || reason.length() > 1024) {
                throw new IllegalArgumentException("bounded nonempty native unavailable reason required");
            }
        }
    }
}
