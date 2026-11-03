package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.control.g2.m2.nativecode.Element172Fp636Api;
import org.xar.ck3.control.g2.m2.nativecode.Range16Fp638Api;
import org.xar.ck3.control.g2.m2.nativecode.Add4Fp639Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.Range16FullState638;
import org.xar.ck3.control.g2.m2.nativecode.Add4FullState639;

/**
 * Model integration of actual172 entry636 with complete full-state callees 638 and 639.
 * Binds the two direct call sites in Element172FullState636 to their respective full-state executors.
 * No algorithm implementation, no state repair, no additional memory effects.
 */
public final class Element172KnownLower640 {
    private Element172KnownLower640() { }

    /**
     * Nominal strong union of memory interfaces for the three components.
     */
    public interface Memory extends Element172Fp636Api.Memory, Range16Fp638Api.Memory, Add4Fp639Api.Memory {
    }

    /**
     * Binds the actual172 call sites to the full-state callees.
     * @param memory Shared memory view.
     * @param budget Loop budget for range16.
     * @param rangeCalls Calls interface for range16.
     * @param addCalls Calls interface for add4.
     * @return Element172Fp636Api.Calls implementation.
     */
    public static Element172Fp636Api.Calls bind(Memory memory, GovernmentCrtBoundary185Api.LoopBudget budget,
            Range16Fp638Api.Calls rangeCalls, Add4Fp639Api.Calls addCalls) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(rangeCalls);
        Objects.requireNonNull(addCalls);

        return new Element172Fp636Api.Calls() {
            @Override
            public QueueFp604Api.Outcome invoke(Element172Fp636Api.CallFrame frame) {
                Objects.requireNonNull(frame);

                GovernmentCrtBoundary185Api.Call call = frame.call();
                long site = call.callSiteRva();
                GovernmentCrtBoundary185Api.TargetKind kind = call.kind();
                long target = call.targetBits();

                // Exact selection for first call site 3729846 -> 8C70B0
                if (site == 0x3729846L && kind == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && target == 0x8C70B0L) {
                    // Construct input for Range16FullState638
                    // Input: QueueFp604Api.Input(FullCopy437Api.Input(entry, df, budget), mxcsr)
                    FullCopy437Api.Input baseInput = new FullCopy437Api.Input(frame.childEntry(), frame.directionFlagSet(), budget);
                    QueueFp604Api.Input fpInput = new QueueFp604Api.Input(baseInput, frame.preMxcsr());

                    // Execute Range16FullState638
                    // Signature: execute(QueueFp604Api.Input input, Range16Fp638Api.Memory memory, Range16Fp638Api.Calls calls, long originCallSiteRva)
                    QueueFp604Api.Outcome offered = Range16FullState638.execute(fpInput, memory, rangeCalls, site);

                    if (offered == null) {
                        throw new IllegalArgumentException("Null callee outcome");
                    }

                    if (offered instanceof QueueFp604Api.Normal normal) {
                        // Validate normal return against original frame
                        frame.checkNormalReturn(normal);
                    }

                    return offered;
                }

                // Exact selection for second call site 3729877 -> ADD0D0
                if (site == 0x3729877L && kind == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && target == 0xADD0D0L) {
                    // Construct input for Add4FullState639
                    // Input: QueueFp604Api.Input(FullCopy437Api.Input(entry, df, budget), mxcsr)
                    FullCopy437Api.Input baseInput = new FullCopy437Api.Input(frame.childEntry(), frame.directionFlagSet(), budget);
                    QueueFp604Api.Input fpInput = new QueueFp604Api.Input(baseInput, frame.preMxcsr());

                    // Execute Add4FullState639
                    // Signature: execute(QueueFp604Api.Input input, Add4Fp639Api.Memory memory, Add4Fp639Api.Calls calls, long originCallSiteRva)
                    QueueFp604Api.Outcome offered = Add4FullState639.execute(fpInput, memory, addCalls, site);

                    if (offered == null) {
                        throw new IllegalArgumentException("Null callee outcome");
                    }

                    if (offered instanceof QueueFp604Api.Normal normal) {
                        // Validate normal return against original frame
                        frame.checkNormalReturn(normal);
                    }

                    return offered;
                }

                // Reject any other frame identity
                throw new IllegalArgumentException("Unknown or invalid call frame identity");
            }
        };
    }
}