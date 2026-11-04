package org.xar.ck3.research.m3.hashwholefp309;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m3.assign855db0fp291.Assign855DB0Fp291Api;
import org.xar.ck3.research.m3.hash188.HashInsert188Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

/**
 * Pure source-scoped protocol for [C39C60,C39F8E).
 * No memory, instruction, callback, budget, or hardware exception effects.
 */
public final class HashWholeFp309Api {
    private HashWholeFp309Api() { }

    public record Input(QueueFp604Api.Input base, long originCallSiteRva) {
        public Input { Objects.requireNonNull(base); }

        public GovernmentCrtBoundary185Api.Entry entry() { return base.base().entry(); }
        public GovernmentCrtBoundary185Api.LoopBudget budget() { return base.base().budget(); }
        public boolean directionFlagSet() { return base.base().directionFlagSet(); }
        public QueueFp604Api.Mxcsr preMxcsr() { return base.mxcsr(); }
        public long bodyRspBits() { return entry().rspBits() - 0xA8L; }

        /** RET bits must have been freshly observed by the producer; saved N may alias. */
        public void checkNormalReturn(QueueFp604Api.Normal actual, long observedReturnRipBits) {
            Objects.requireNonNull(actual);
            var normal = actual.base().normalReturn();
            require(normal.returnRipBits() == observedReturnRipBits, "Whole RIP mismatch");
            require(normal.callerRspBits() == entry().rspBits() + 8L, "Whole SP mismatch");
            require(normal.volatileBits().raxBits() == entry().volatileBits().rdxBits(),
                    "Whole RAX mismatch");
        }
    }

    public record CallFrame(Input ownerInput, GovernmentCrtBoundary185Api.Call original,
                            QueueFp604Api.Input childInput) {
        public CallFrame {
            Objects.requireNonNull(ownerInput);
            Objects.requireNonNull(original);
            Objects.requireNonNull(childInput);
            require(original.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && validRoute(original.callSiteRva(), original.targetBits()), "Invalid source CALL");
            var child = childInput.base().entry();
            require(original.rspBits() == ownerInput.bodyRspBits(), "Source body SP mismatch");
            require(child.imageBaseBits() == ownerInput.entry().imageBaseBits(), "Image mismatch");
            require(child.rspBits() == original.rspBits() - 8L, "Child SP mismatch");
            require(child.volatileBits().equals(original.volatileBits()), "Child V mismatch");
            require(child.nonvolatileBits().equals(original.nonvolatileBits()), "Child N mismatch");
            require(childInput.base().budget() == ownerInput.budget(), "Budget identity mismatch");
        }

        public GovernmentCrtBoundary185Api.Entry childEntry() { return childInput.base().entry(); }
        public boolean directionFlagSet() { return childInput.base().directionFlagSet(); }
        public QueueFp604Api.Mxcsr preMxcsr() { return childInput.mxcsr(); }
        public GovernmentCrtBoundary185Api.LoopBudget budget() { return childInput.base().budget(); }
        public long originCallSiteRva() { return ownerInput.originCallSiteRva(); }
        public int instructionLength() { return 5; }
        public long returnRipBits() { return childEntry().imageBaseBits() + original.callSiteRva() + 5L; }

        public void checkNormalReturn(QueueFp604Api.Normal actual) {
            Objects.requireNonNull(actual);
            var normal = actual.base().normalReturn();
            require(normal.returnRipBits() == returnRipBits(), "CALL RIP mismatch");
            require(normal.callerRspBits() == original.rspBits(), "CALL SP mismatch");
            require(normal.nonvolatileBits().equals(original.nonvolatileBits()), "CALL N mismatch");
        }

        /** Validate a callback result before adopting state; Stopped has no RET guard. */
        public void checkResult(Result actual) {
            Objects.requireNonNull(actual);
            if (actual instanceof Forwarded forwarded) {
                if (forwarded.actual() instanceof QueueFp604Api.Normal normal) checkNormalReturn(normal);
            } else if (actual instanceof AssignBoundary boundary) {
                require(boundary.assignmentFrame() == this, "Assignment frame identity mismatch");
            } else if (actual instanceof RecursiveBoundary boundary) {
                require(boundary.recursiveFrame() == this, "Recursive frame identity mismatch");
            } else {
                throw new IllegalArgumentException("Own INT3 is not a direct callback result");
            }
        }
    }

    @FunctionalInterface
    public interface Calls {
        Result invoke(CallFrame frame, FullCopy437Api.Memory sameMemory);
    }

    public sealed interface Result permits Forwarded, AssignBoundary, Int3Boundary, RecursiveBoundary { }

    /** Exact actual604 object, including the original Stopped identity. */
    public record Forwarded(QueueFp604Api.Outcome actual) implements Result {
        public Forwarded { Objects.requireNonNull(actual); }
    }

    /** Actual lower855DB0 software boundary; no outer RET or invented FP stop. */
    public record AssignBoundary(CallFrame assignmentFrame,
                                 Assign855DB0Fp291Api.Int3Boundary actual) implements Result {
        public AssignBoundary {
            Objects.requireNonNull(assignmentFrame);
            Objects.requireNonNull(actual);
            long site = assignmentFrame.original().callSiteRva();
            require(site == 0xC39DA4L || site == 0xC39DFBL, "Not an assignment CALL");
            var helper = actual.helperFrame();
            require(helper.childEntry().imageBaseBits() == assignmentFrame.childEntry().imageBaseBits(),
                    "Assignment helper image mismatch");
            require(helper.original().rspBits() == assignmentFrame.childEntry().rspBits() - 0x38L,
                    "Assignment helper SP mismatch");
            require(helper.budget() == assignmentFrame.budget(), "Assignment helper budget mismatch");
        }
    }

    /** This Hash's unexecuted F8D INT3, after the second fatal CALL really returned Normal. */
    public record Int3Boundary(CallFrame terminalFrame, QueueFp604Api.Normal terminalNormal,
                               QueueFp604Api.Snapshot snapshot) implements Result {
        public Int3Boundary {
            Objects.requireNonNull(terminalFrame);
            Objects.requireNonNull(terminalNormal);
            Objects.requireNonNull(snapshot);
            require(terminalFrame.original().callSiteRva() == 0xC39F88L, "Not the terminal CALL");
            terminalFrame.checkNormalReturn(terminalNormal);
            require(snapshot.instructionRva() == 0xC39F8DL, "INT3 PC mismatch");
            require(snapshot.currentState().imageBaseBits() == terminalFrame.childEntry().imageBaseBits(),
                    "INT3 image mismatch");
            var normal = terminalNormal.base().normalReturn();
            require(snapshot.currentState().rspBits() == normal.callerRspBits(), "INT3 SP mismatch");
            require(snapshot.currentState().volatileBits().equals(normal.volatileBits()), "INT3 V mismatch");
            require(snapshot.currentState().nonvolatileBits().equals(normal.nonvolatileBits()), "INT3 N mismatch");
            require(snapshot.directionFlagSet() == terminalNormal.base().postDirectionFlagSet(), "INT3 DF mismatch");
            require(snapshot.mxcsr() == terminalNormal.postMxcsr(), "INT3 MXCSR reference mismatch");
        }
    }

    /** One source F5C edge of a typed nonreturn chain; never invokes recursion. */
    public record RecursiveBoundary(CallFrame recursiveFrame, Result actual) implements Result {
        public RecursiveBoundary {
            Objects.requireNonNull(recursiveFrame);
            Objects.requireNonNull(actual);
            require(recursiveFrame.original().callSiteRva() == 0xC39F5CL, "Not the recursive CALL");
            Input childOwner;
            if (actual instanceof AssignBoundary boundary) {
                childOwner = boundary.assignmentFrame().ownerInput();
            } else if (actual instanceof Int3Boundary boundary) {
                childOwner = boundary.terminalFrame().ownerInput();
            } else if (actual instanceof RecursiveBoundary boundary) {
                childOwner = boundary.recursiveFrame().ownerInput();
            } else {
                throw new IllegalArgumentException("Recursive boundary needs a nonreturn child");
            }
            require(sameInputState(childOwner.base(), recursiveFrame.childInput()),
                    "Recursive child input mismatch");
        }
    }

    public static HashInsert188Api.Bytes16 toBusinessBytes16(Bits128 value) {
        Objects.requireNonNull(value);
        return new HashInsert188Api.Bytes16(value.lowBits(), value.highBits());
    }

    public static Bits128 fromBusinessBytes16(HashInsert188Api.Bytes16 value) {
        Objects.requireNonNull(value);
        return new Bits128(value.low(), value.high());
    }

    private static boolean sameInputState(QueueFp604Api.Input a, QueueFp604Api.Input b) {
        return a.base().entry().equals(b.base().entry())
                && a.base().directionFlagSet() == b.base().directionFlagSet()
                && a.mxcsr().equals(b.mxcsr())
                && a.base().budget() == b.base().budget();
    }

    private static boolean validRoute(long site, long target) {
        return (site == 0xC39CCAL && target == 0x3F6D2B0L)
                || (site == 0xC39D27L && target == 0x855F00L)
                || (site == 0xC39DA4L && target == 0x855DB0L)
                || (site == 0xC39DFBL && target == 0x855DB0L)
                || (site == 0xC39EADL && target == 0xC3A400L)
                || (site == 0xC39EC1L && target == 0xC3B960L)
                || (site == 0xC39ECAL && target == 0x856050L)
                || (site == 0xC39F15L && target == 0x856050L)
                || (site == 0xC39F2FL && target == 0x86E160L)
                || (site == 0xC39F3EL && target == 0xC3B700L)
                || (site == 0xC39F5CL && target == 0xC39C60L)
                || (site == 0xC39F83L && target == 0x86F210L)
                || (site == 0xC39F88L && target == 0x4232CF4L);
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
