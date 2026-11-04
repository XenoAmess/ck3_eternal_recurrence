package org.xar.ck3.research.m3.assign855db0fp291;

import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import java.util.Objects;

/**
 * Pure metadata for the six source CALLs in complete855DB0.
 * Constructors perform no memory, callback or instruction effects.
 */
public final class Assign855DB0Fp291Api {
    private Assign855DB0Fp291Api() { }

    public interface Memory extends FullCopy437Api.Memory {
    }

    public record Input(QueueFp604Api.Input base, long originCallSiteRva) {
        public Input {
            Objects.requireNonNull(base);
        }
    }

    public record CallFrame(GovernmentCrtBoundary185Api.Call original, QueueFp604Api.Input childInput) {
        public CallFrame {
            Objects.requireNonNull(original);
            Objects.requireNonNull(childInput);

            GovernmentCrtBoundary185Api.Entry childEntry = childInput.base().entry();

            if (childEntry.rspBits() != original.rspBits() - 8) {
                throw new IllegalArgumentException("Child RSP mismatch");
            }
            if (!childEntry.volatileBits().equals(original.volatileBits())) {
                throw new IllegalArgumentException("Child V mismatch");
            }
            if (!childEntry.nonvolatileBits().equals(original.nonvolatileBits())) {
                throw new IllegalArgumentException("Child N mismatch");
            }

            if (original.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                throw new IllegalArgumentException("Invalid kind");
            }

            long site = original.callSiteRva();
            long target = original.targetBits();

            if (site == 0x855DE7L && target == 0x4226860L) {
                // Valid
            } else if (site == 0x855E3CL && target == 0x856DB0L) {
                // Valid
            } else if (site == 0x855E55L && target == 0x4226860L) {
                // Valid
            } else if (site == 0x855E8DL && target == 0x4223F44L) {
                // Valid
            } else if (site == 0x855EB0L && target == 0x8523A0L) {
                // Valid
            } else if (site == 0x855EB6L && target == 0x4232A70L) {
                // Valid
            } else {
                throw new IllegalArgumentException("Invalid call site/target pair");
            }
        }

        public GovernmentCrtBoundary185Api.Entry childEntry() {
            return childInput.base().entry();
        }

        public boolean directionFlagSet() {
            return childInput.base().directionFlagSet();
        }

        public QueueFp604Api.Mxcsr preMxcsr() {
            return childInput.mxcsr();
        }

        public GovernmentCrtBoundary185Api.LoopBudget budget() {
            return childInput.base().budget();
        }

        public int instructionLength() {
            return 5;
        }

        public long returnRipBits() {
            return childEntry().imageBaseBits() + original.callSiteRva() + 5L;
        }

        public void checkNormalReturn(QueueFp604Api.Normal actual) {
            Objects.requireNonNull(actual);
            GovernmentCrtBoundary185Api.NormalReturn nr = actual.base().normalReturn();
            if (nr.returnRipBits() != returnRipBits()) {
                throw new IllegalArgumentException("RIP mismatch");
            }
            if (nr.callerRspBits() != original.rspBits()) {
                throw new IllegalArgumentException("SP mismatch");
            }
            if (!nr.nonvolatileBits().equals(original.nonvolatileBits())) {
                throw new IllegalArgumentException("N mismatch");
            }
        }
    }

    @FunctionalInterface
    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame, FullCopy437Api.Memory sameMemory);
    }

    public sealed interface Result permits Forwarded, Int3Boundary { }

    /** Retains the exact offered604 Normal or Stopped object; never reconstructs it. */
    public record Forwarded(QueueFp604Api.Outcome actual) implements Result {
        public Forwarded {
            Objects.requireNonNull(actual);
        }
    }

    /** Software boundary at unexecuted INT3 after an explicit validated helper Normal. */
    public record Int3Boundary(CallFrame helperFrame, QueueFp604Api.Normal helperNormal, QueueFp604Api.Snapshot snapshot, long originCallSiteRva) implements Result {
        public Int3Boundary {
            Objects.requireNonNull(helperFrame);
            Objects.requireNonNull(helperNormal);
            Objects.requireNonNull(snapshot);

            long site = helperFrame.original().callSiteRva();
            if (site != 0x855EB0L && site != 0x855EB6L) {
                throw new IllegalArgumentException("Helper must be EB0 or EB6");
            }

            helperFrame.checkNormalReturn(helperNormal);

            if (snapshot.instructionRva() != site + 5) {
                throw new IllegalArgumentException("Snapshot instruction RVA mismatch");
            }

            GovernmentCrtBoundary185Api.Entry childEntry = helperFrame.childEntry();
            if (snapshot.currentState().imageBaseBits() != childEntry.imageBaseBits()) {
                throw new IllegalArgumentException("Snapshot image mismatch");
            }

            GovernmentCrtBoundary185Api.NormalReturn nr = helperNormal.base().normalReturn();
            if (snapshot.currentState().rspBits() != nr.callerRspBits()) {
                throw new IllegalArgumentException("Snapshot RSP mismatch");
            }
            if (!snapshot.currentState().volatileBits().equals(nr.volatileBits())) {
                throw new IllegalArgumentException("Snapshot V mismatch");
            }
            if (!snapshot.currentState().nonvolatileBits().equals(nr.nonvolatileBits())) {
                throw new IllegalArgumentException("Snapshot N mismatch");
            }

            if (snapshot.directionFlagSet() != helperNormal.base().postDirectionFlagSet()) {
                throw new IllegalArgumentException("Snapshot DF mismatch");
            }

            if (snapshot.mxcsr() != helperNormal.postMxcsr()) {
                throw new IllegalArgumentException("Snapshot MXCSR reference mismatch");
            }
        }
    }
}
