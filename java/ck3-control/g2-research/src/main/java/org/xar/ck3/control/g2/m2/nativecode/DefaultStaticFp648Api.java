package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;

/** Draft pure contract for only held8571D0/8571C0. No producer algorithm or tests. */
public final class DefaultStaticFp648Api {
    private DefaultStaticFp648Api() { }

    /** These leaf entries have no loop; no fabricated budget or new Memory interface is needed. */
    public record Input(GovernmentCrtBoundary185Api.Entry entry,
            boolean directionFlagSet, QueueFp604Api.Mxcsr mxcsr) {
        public Input { Objects.requireNonNull(entry); Objects.requireNonNull(mxcsr); }
    }

    /** Source8571D7 CALL pre-SP precedes its owned push; child owns its own complete Normal. */
    public record CallFrame(GovernmentCrtBoundary185Api.Call call,
            GovernmentCrtBoundary185Api.Entry childEntry, boolean directionFlagSet,
            QueueFp604Api.Mxcsr preMxcsr, int instructionLength, long returnRipBits) {
        public CallFrame {
            Objects.requireNonNull(call); Objects.requireNonNull(childEntry);
            Objects.requireNonNull(preMxcsr);
            if (call.callSiteRva() != 0x8571D7L
                    || call.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    || call.targetBits() != 0x4223B94L || instructionLength != 5)
                throw new IllegalArgumentException("Invalid held8571D0 child CALL");
            if (childEntry.rspBits() != call.rspBits() - 8
                    || !childEntry.volatileBits().equals(call.volatileBits())
                    || !childEntry.nonvolatileBits().equals(call.nonvolatileBits()))
                throw new IllegalArgumentException("Child entry mismatch");
            if (returnRipBits != childEntry.imageBaseBits() + 0x8571DCL)
                throw new IllegalArgumentException("Source continuation mismatch");
        }
        /** Guard before accepting DF/MXCSR or downconverting to old185 volatile-only invoke. */
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

    /** Tail owns its complete result. This frame invents no local return RIP/SP/N guard or RET read. */
    public record TailFrame(GovernmentCrtBoundary185Api.Tail transfer,
            boolean directionFlagSet, QueueFp604Api.Mxcsr preMxcsr) {
        public TailFrame {
            Objects.requireNonNull(transfer); Objects.requireNonNull(preMxcsr);
            if (transfer.jumpSiteRva() != 0x8571C8L
                    || transfer.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    || transfer.targetBits() != 0x40EC530L)
                throw new IllegalArgumentException("Invalid held8571C0 tail");
            if (transfer.entry().volatileBits().rdxBits() == 0
                    || transfer.entry().volatileBits().rcxBits()
                        != transfer.entry().volatileBits().rdxBits())
                throw new IllegalArgumentException("Nonzero MOV RCX,RDX tail state required");
        }
    }

    public interface Calls {
        QueueFp604Api.Outcome invoke(CallFrame frame);
        QueueFp604Api.Outcome tail(TailFrame frame);
    }
}
