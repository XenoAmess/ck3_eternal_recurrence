package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;

/**
 * Binder for the actual 638 consumer to the two new 648 producer signatures.
 * Selects only the exact indirect call sites 8C7131 (->8571D0) and 8C71D7 (->8571C0).
 * All other frames delegate to the foreign calls.
 */
public final class Range16KnownDefault648 {
    private Range16KnownDefault648() { }

    public static Range16Fp638Api.Calls bind(Range16Fp638Api.Memory memory,
            DefaultStaticFp648Api.Calls defaultCalls, Range16Fp638Api.Calls foreignCalls) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(defaultCalls);
        Objects.requireNonNull(foreignCalls);

        return new Range16Fp638Api.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(Range16Fp638Api.CallFrame frame) {
                Objects.requireNonNull(frame);

                GovernmentCrtBoundary185Api.Call call = frame.call();
                GovernmentCrtBoundary185Api.Entry childEntry = frame.childEntry();
                boolean df = frame.directionFlagSet();
                QueueFp604Api.Mxcsr preMxcsr = frame.preMxcsr();
                long site = call.callSiteRva();
                GovernmentCrtBoundary185Api.TargetKind kind = call.kind();
                long target = call.targetBits();
                int len = frame.instructionLength();
                long image = childEntry.imageBaseBits();

                // Check for Allocate: site 8C7131, INDIRECT_ABSOLUTE, target image+8571D0, len 3
                if (site == 0x8C7131L
                        && kind == GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                        && target == image + 0x8571D0L
                        && len == 3) {
                    DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(
                            childEntry, df, preMxcsr);
                    QueueFp604Api.Outcome outcome = DefaultAllocateWithFp648.fromSlot08(
                            input, memory, defaultCalls);

                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        frame.checkNormalReturn(normal);
                    }
                    return outcome;
                }

                // Check for Release: site 8C71D7, INDIRECT_ABSOLUTE, target image+8571C0, len 3
                if (site == 0x8C71D7L
                        && kind == GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                        && target == image + 0x8571C0L
                        && len == 3) {
                    DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(
                            childEntry, df, preMxcsr);
                    QueueFp604Api.Outcome outcome = DefaultReleaseWithFp648.fromSlot10(
                            input, memory, defaultCalls);

                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        frame.checkNormalReturn(normal);
                    }
                    return outcome;
                }

                // All other frames delegate to foreign calls
                QueueFp604Api.Outcome outcome = foreignCalls.invoke(frame);
                Objects.requireNonNull(outcome);
                return outcome;
            }
        };
    }
}