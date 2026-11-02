package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.EmbeddedQueue591Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueAppend597Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/**
 * Source-scoped carrier for MXCSR knowledge in the queue/append context.
 * No FP implementation, no native proof, no old file rewrite.
 */
public final class QueueFp604Api {
    private QueueFp604Api() { }

    /**
     * Represents MXCSR bits with a known mask.
     * valueBits must be subset of knownMaskBits.
     */
    public record Mxcsr(int valueBits, int knownMaskBits) {
        public Mxcsr {
            if (valueBits < 0 || valueBits > 0xFFFF) throw new IllegalArgumentException("valueBits out of range");
            if (knownMaskBits < 0 || knownMaskBits > 0xFFFF) throw new IllegalArgumentException("knownMaskBits out of range");
            if ((valueBits & ~knownMaskBits) != 0) throw new IllegalArgumentException("valueBits outside knownMask");
        }

        public static Mxcsr unknown() {
            return new Mxcsr(0, 0);
        }

        public static Mxcsr exact(int bits) {
            return new Mxcsr(bits, 0xFFFF);
        }

        public boolean isExact() {
            return knownMaskBits == 0xFFFF;
        }

        public int requireExactBits() {
            if (!isExact()) throw new IllegalStateException("MXCSR not exact");
            return valueBits;
        }
    }

    /**
     * Input wrapper carrying base 437 Input and explicit MXCSR.
     */
    public record Input(FullCopy437Api.Input base, Mxcsr mxcsr) {
        public Input {
            Objects.requireNonNull(base);
            Objects.requireNonNull(mxcsr);
        }
    }

    /**
     * Sealed outcome interface for queue/append operations.
     */
    public sealed interface Outcome permits Normal, Stopped { }

    /**
     * Normal completion with post-state MXCSR.
     */
    public record Normal(FullCopy437Api.CallResult base, Mxcsr postMxcsr) implements Outcome {
        public Normal {
            Objects.requireNonNull(base);
            Objects.requireNonNull(postMxcsr);
        }
    }

    /**
     * Snapshot of state at a stop point.
     */
    public record Snapshot(GovernmentCrtBoundary185Api.Entry currentState, long instructionRva, boolean directionFlagSet, Mxcsr mxcsr) {
        public Snapshot {
            Objects.requireNonNull(currentState);
            Objects.requireNonNull(mxcsr);
        }
    }

    /**
     * Reasons for stopping execution.
     */
    public enum StopReason {
        MISSING_FP_INPUT,
        UNSUPPORTED_FP_DOMAIN,
        ARCHITECTURAL_FP_CONDITION,
        MISSING_POST_STATE
    }

    /**
     * Stopped outcome with reason, snapshot, and condition bits.
     */
    public record Stopped(StopReason reason, Snapshot snapshot, int raisedConditionBits, long originCallSiteRva) implements Outcome {
        public Stopped {
            Objects.requireNonNull(reason);
            Objects.requireNonNull(snapshot);
            if (raisedConditionBits < 0 || raisedConditionBits > 0x3F) throw new IllegalArgumentException("raisedConditionBits out of range");
            if (reason != StopReason.ARCHITECTURAL_FP_CONDITION && raisedConditionBits != 0) throw new IllegalArgumentException("Non-architectural reason must have 0 raisedConditionBits");
        }
    }

    /**
     * Queue call frame wrapper.
     */
    public record QueueCallFrame(EmbeddedQueue591Api.CallFrame base, Mxcsr preMxcsr) {
        public QueueCallFrame {
            Objects.requireNonNull(base);
            Objects.requireNonNull(preMxcsr);
        }

        public void checkNormalReturn(Normal actual) {
            Objects.requireNonNull(actual);
            base.checkNormalReturn(actual.base());
        }
    }

    /**
     * Append call frame wrapper.
     */
    public record AppendCallFrame(QueueAppend597Api.CallFrame base, Mxcsr preMxcsr) {
        public AppendCallFrame {
            Objects.requireNonNull(base);
            Objects.requireNonNull(preMxcsr);
        }

        public void checkNormalReturn(Normal actual) {
            Objects.requireNonNull(actual);
            base.checkNormalReturn(actual.base());
        }
    }

    /**
     * Interface for queue calls.
     */
    public interface QueueCalls {
        Outcome invoke(QueueCallFrame frame);
    }

    /**
     * Interface for append calls.
     */
    public interface AppendCalls {
        Outcome invoke(AppendCallFrame frame);
    }

    /**
     * Helper to verify Win64 controls preservation if explicitly qualified.
     */
    public static void requireKnownControlsPreserved(Mxcsr before, Mxcsr after) {
        Objects.requireNonNull(before);
        Objects.requireNonNull(after);
        if ((before.knownMaskBits() & 0xFFC0) != 0xFFC0) throw new IllegalStateException("Before MXCSR does not cover controls");
        if ((after.knownMaskBits() & 0xFFC0) != 0xFFC0) throw new IllegalStateException("After MXCSR does not cover controls");
        if ((before.valueBits() & 0xFFC0) != (after.valueBits() & 0xFFC0)) throw new IllegalArgumentException("Controls mismatch");
    }
}