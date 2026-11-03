package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Owner source contract for held150 [37295B0,3729646); both lower outcomes stay explicit. */
public final class Element150Fp643Api {
    private Element150Fp643Api() { }

    public interface Memory extends GovernmentCrtBoundary185Api.Memory { }

    public record Input(GovernmentCrtBoundary185Api.Entry entry,
            boolean directionFlagSet, QueueFp604Api.Mxcsr mxcsr) {
        public Input { Objects.requireNonNull(entry); Objects.requireNonNull(mxcsr); }
    }

    /** CALL rspBits precedes the owned push; childEntry starts after that push. */
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
            long expectedTarget;
            long expectedReturn;
            if (call.callSiteRva() == 0x37295FBL) {
                expectedTarget = 0x21A5050L;
                expectedReturn = childEntry.imageBaseBits() + 0x3729600L;
            } else if (call.callSiteRva() == 0x3729620L) {
                expectedTarget = 0xB2EEE0L;
                expectedReturn = childEntry.imageBaseBits() + 0x3729625L;
            } else {
                throw new IllegalArgumentException("Unknown held150 call site");
            }
            if (call.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    || call.targetBits() != expectedTarget || instructionLength != 5)
                throw new IllegalArgumentException("Invalid held150 direct call");
            if (returnRipBits != expectedReturn)
                throw new IllegalArgumentException("Return RIP mismatch");
        }

        /** Validate the offered Normal before applying any post-state. No repair or rollback. */
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

    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
    }
}
