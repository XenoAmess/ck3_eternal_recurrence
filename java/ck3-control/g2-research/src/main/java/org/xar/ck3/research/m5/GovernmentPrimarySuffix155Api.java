package org.xar.ck3.research.m5;
import java.util.Objects;
/** Shared795B suffix composition boundaries. Nothing here captures original Game registers. */
public final class GovernmentPrimarySuffix155Api {
    private GovernmentPrimarySuffix155Api() { }
    public record Entry(long imageBaseBits, long governmentBits, int savedTlsOffsetDwordBits,
            long savedRsiBits, long savedR15Bits, long frameRbpBits, long frameRspBits,
            long incomingR13Bits, long incomingR14Bits, GovernmentPrimaryTail155Api.Bits128 incomingXmm6) {
        public Entry { Objects.requireNonNull(incomingXmm6); }
    }
    public interface Memory extends GovernmentPrimaryTail155Api.Memory, InternedLookup155Api.Memory { }
    public sealed interface VolatileObservation permits AvailableVolatile, UnavailableVolatile { }
    public record AvailableVolatile(GovernmentPrimaryTail155Api.VolatileBits bits) implements VolatileObservation {
        public AvailableVolatile { Objects.requireNonNull(bits); }
    }
    public record UnavailableVolatile(String reason) implements VolatileObservation {
        public UnavailableVolatile { Objects.requireNonNull(reason); }
    }
    /**
     * Mandatory external OWNED post-prefix observation. Existing153 only returns Outcome and does not
     * represent opaque callee volatile outputs. This port observes supplied post-prefix bits without
     * mutating shared Memory. It is an explicit software boundary, not an original Native CALL or a
     * proven Game capture producer. Missing represented state must return UnavailableVolatile.
     */
    public interface VolatileBoundary {
        VolatileObservation afterPrefix(Entry entry, GovernmentCaller153Api.Outcome prefixOutcome,
                                       long observedPostPrefixR14Bits);
    }
    public static final class BoundaryUnavailableException extends UnsupportedOperationException {
        private static final long serialVersionUID = 1L;
        public BoundaryUnavailableException(String reason) { super(reason); }
    }
    public record Result(GovernmentCaller153Api.Outcome prefixOutcome,
                         GovernmentPrimaryTail155Api.NormalReturn normalReturn) { }
}
