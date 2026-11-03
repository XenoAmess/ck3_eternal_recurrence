package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownPageAllocateFp622;

/**
 * Binder for the actual 648 consumer to the new 649 retry producer.
 * Selects only the exact direct call site 8571D7 (->4223B94).
 * All other frames delegate to the foreign calls.
 */
public final class DefaultAllocateKnownRetry649 {
    private DefaultAllocateKnownRetry649() { }

    public static DefaultStaticFp648Api.Calls bind(
            GovernmentCrtBoundary185Api.Memory memory,
            KnownPageAllocateFp622.RetryCalls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            DefaultStaticFp648Api.Calls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(foreign);

        return new DefaultStaticFp648Api.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
                Objects.requireNonNull(frame);

                GovernmentCrtBoundary185Api.Call call = frame.call();
                GovernmentCrtBoundary185Api.Entry childEntry = frame.childEntry();
                boolean df = frame.directionFlagSet();
                QueueFp604Api.Mxcsr preMxcsr = frame.preMxcsr();
                long site = call.callSiteRva();
                GovernmentCrtBoundary185Api.TargetKind kind = call.kind();
                long target = call.targetBits();
                int len = frame.instructionLength();

                // Check for Allocate: site 8571D7, DIRECT_RVA, target 4223B94, len 5
                if (site == 0x8571D7L
                        && kind == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && target == 0x4223B94L
                        && len == 5) {
                    DefaultStaticFp648Api.Input input = new DefaultStaticFp648Api.Input(
                            childEntry, df, preMxcsr);
                    QueueFp604Api.Outcome outcome = Retry60EntryFp649.execute(
                            input, memory, calls, budget);

                    Objects.requireNonNull(outcome);
                    if (outcome instanceof QueueFp604Api.Normal normal) {
                        frame.checkNormalReturn(normal);
                    }
                    return outcome;
                }

                // All other frames delegate to foreign calls
                QueueFp604Api.Outcome outcome = foreign.invoke(frame);
                Objects.requireNonNull(outcome);
                return outcome;
            }

            @Override
            public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                Objects.requireNonNull(frame);
                QueueFp604Api.Outcome outcome = foreign.tail(frame);
                Objects.requireNonNull(outcome);
                return outcome;
            }
        };
    }
}