package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownAllocateErrorFp625;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.study.m6.fc226.Fc74FullState226;
import org.xar.ck3.research.m3.fc74238.Fc74Target424FC74;
import org.xar.ck3.research.m3.fc74238.Fc74Api238;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

/**
 * FP/DF carrier for actual error cell CALL 423B190 -> normal FC74 424FC74.
 * Reuses existing Fc74FullState226 and Fc74Target424FC74 algorithms once.
 * No new algorithm, no state repair, no Game/native proof.
 */
public final class KnownErrorFc74Fp626 {
    private KnownErrorFc74Fp626() { }

    /**
     * Private exception used to propagate the Stopped outcome from a callback back to execute.
     */
    private static final class StoppedOutcomeException extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Stopped outcome;

        StoppedOutcomeException(QueueFp604Api.Stopped outcome) {
            this.outcome = outcome;
        }
    }

    /**
     * Binds a KnownAllocateErrorFp625.ErrorCalls handler that routes the specific error edge to the known binder
     * and delegates all other calls to the foreign handler.
     */
    public static KnownAllocateErrorFp625.ErrorCalls bind(
            GovernmentCrtBoundary185Api.Memory memory,
            Fc74Fp626Api.Calls inner,
            KnownAllocateErrorFp625.ErrorCalls foreign) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(inner);
        Objects.requireNonNull(foreign);

        return new KnownAllocateErrorFp625.ErrorCalls() {
            @Override
            public QueueFp604Api.Outcome invoke(KnownAllocateErrorFp625.ErrorCall frame) {
                Objects.requireNonNull(frame);
                GovernmentCrtBoundary185Api.Call original = frame.original();
                QueueFp604Api.Mxcsr preMxcsr = frame.preMxcsr();
                boolean directionFlagSet = frame.directionFlagSet();

                // Match ONLY original ErrorCall site 423B190 / kind DIRECT_RVA / target 424FC74
                if (original.callSiteRva() == 0x423B190L
                        && original.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && original.targetBits() == 0x424FC74L) {

                    // Isolated local MXCSR holder for EACH invoke, initialized to the SAME preMxcsr object.
                    final QueueFp604Api.Mxcsr[] currentMxcsrHolder = new QueueFp604Api.Mxcsr[1];
                    currentMxcsrHolder[0] = preMxcsr;
                    final boolean[] currentDfHolder = new boolean[1];
                    currentDfHolder[0] = directionFlagSet;

                    // Narrow 185.Calls implementation for the FC74 body.
                    GovernmentCrtBoundary185Api.Calls narrowCalls = new GovernmentCrtBoundary185Api.Calls() {
                        @Override
                        public long readGsQword58() {
                            throw new UnsupportedOperationException("GS read not expected in FC74");
                        }

                        @Override
                        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                            // Construct Fc74Fp626Api.CallFrame with EXACT originalCall, new 185.Entry, currentDF/SAME currentFP
                            Fc74Fp626Api.CallFrame fc74Frame = new Fc74Fp626Api.CallFrame(
                                    call,
                                    new GovernmentCrtBoundary185Api.Entry(
                                            frame.childEntry().imageBaseBits(),
                                            call.rspBits() - 8,
                                            call.volatileBits(),
                                            call.nonvolatileBits()),
                                    currentDfHolder[0],
                                    currentMxcsrHolder[0]);

                            // Call inner.invoke ONCE
                            QueueFp604Api.Outcome outcome = inner.invoke(fc74Frame);

                            if (outcome instanceof QueueFp604Api.Normal normal) {
                                // Validate against the Fc74Fp626Api.CallFrame BEFORE current state update
                                fc74Frame.checkNormalReturn(normal.base());
                                // Retain SAME postMxcsr
                                currentMxcsrHolder[0] = normal.postMxcsr();
                                // Update currentDF from actual postDirectionFlagSet
                                currentDfHolder[0] = normal.base().postDirectionFlagSet();
                                // Return SAME normal.base() with actual full NR/postDF
                                return normal.base().normalReturn().volatileBits();
                            } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                                // Abort immediately to execute's outer boundary.
                                throw new StoppedOutcomeException(stopped);
                            } else {
                                throw new NullPointerException("Null outcome from inner");
                            }
                        }

                        @Override
                        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                            throw new UnsupportedOperationException("Tail not expected in FC74");
                        }
                    };

                    try {
                        // Execute Fc74FullState226.execute ONCE with exact child entry, same memory, narrow calls.
                        GovernmentCrtBoundary185Api.NormalReturn nr = Fc74FullState226.execute(
                                frame.childEntry(),
                                memory,
                                narrowCalls);

                        // Wrap in Normal with SAME currentMxcsr and current direction flag
                        FullCopy437Api.CallResult baseResult = new FullCopy437Api.CallResult(
                                nr,
                                currentDfHolder[0]);

                        // Validate against the original outer ErrorCall frame
                        frame.checkNormalReturn(baseResult);

                        return new QueueFp604Api.Normal(baseResult, currentMxcsrHolder[0]);
                    } catch (StoppedOutcomeException e) {
                        // Return the EXACT offered Stopped object.
                        return e.outcome;
                    }
                }

                // All legal nonmatches go ONCE to foreign.invoke(EXACT SAME ErrorCall frame)
                QueueFp604Api.Outcome outcome = foreign.invoke(frame);
                if (outcome == null) {
                    throw new NullPointerException("Null outcome from foreign");
                }
                return outcome;
            }
        };
    }
}