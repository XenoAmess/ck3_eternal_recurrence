package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Owner contract for the complete normal source hull [DBDB80,DBDBFA); opaque callees. */
public final class Dbdb80Fp656Api {
    private Dbdb80Fp656Api() { }

    public interface Memory extends FullCopy437Api.Memory { }

    /**
     * The producer consumes QueueFp604Api.Input and returns QueueFp604Api.Outcome.
     * CALL rspBits precedes its one owned push; childEntry starts after that push.
     * directionFlagSet and preMxcsr are the actual current state at this CALL.
     * targetBits is the freshly resolved absolute Memory target: [RAX] at DBDBB8,
     * [RAX+0x10] at DBDBD9. This pure frame performs no Memory read or push.
     */
    public record CallFrame(GovernmentCrtBoundary185Api.Call call,
            GovernmentCrtBoundary185Api.Entry childEntry, boolean directionFlagSet,
            QueueFp604Api.Mxcsr preMxcsr, int instructionLength, long returnRipBits) {
        public CallFrame {
            Objects.requireNonNull(call); Objects.requireNonNull(childEntry);
            Objects.requireNonNull(preMxcsr);
            if (childEntry.rspBits() != call.rspBits() - 8)
                throw new IllegalArgumentException("Child RSP mismatch");
            if (!childEntry.volatileBits().equals(call.volatileBits()))
                throw new IllegalArgumentException("Child V mismatch");
            if (!childEntry.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Child N mismatch");
            long expectedReturn;
            int expectedLength;
            if (call.callSiteRva() == 0xDBDBB8L) {
                expectedLength = 2;
                expectedReturn = childEntry.imageBaseBits() + 0xDBDBBAL;
            } else if (call.callSiteRva() == 0xDBDBD9L) {
                expectedLength = 3;
                expectedReturn = childEntry.imageBaseBits() + 0xDBDBDCL;
            } else {
                throw new IllegalArgumentException("Unknown DBDB80 call site");
            }
            if (call.kind() != GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE
                    || instructionLength != expectedLength)
                throw new IllegalArgumentException("Invalid DBDB80 indirect call");
            if (returnRipBits != expectedReturn)
                throw new IllegalArgumentException("Return RIP mismatch");
        }

        /** Validate RIP, SP and all represented N before adopting any offered post-state. */
        public void checkNormalReturn(QueueFp604Api.Normal actual) {
            Objects.requireNonNull(actual);
            GovernmentCrtBoundary185Api.NormalReturn nr = actual.base().normalReturn();
            if (nr.returnRipBits() != returnRipBits)
                throw new IllegalArgumentException("Return RIP mismatch");
            if (nr.callerRspBits() != call.rspBits())
                throw new IllegalArgumentException("Caller RSP mismatch");
            if (!nr.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Nonvolatile mismatch");
        }
    }

    /**
     * Every offer is nonnull and complete. A Normal is guarded before its V/DF/MXCSR
     * are adopted. A Stopped is returned unchanged without executing a suffix.
     * Memory, budget, callback and guard exceptions retain the completed prefix.
     */
    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }
}
