package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;
import java.util.Objects;

public final class FullCopy437Api {
    private FullCopy437Api() { }

    public record Bits256(GovernmentPrimaryTail155Api.Bits128 low, GovernmentPrimaryTail155Api.Bits128 high) {
        public Bits256 { Objects.requireNonNull(low); Objects.requireNonNull(high); }
    }

    public interface Memory extends GovernmentMemoryFill206Api.Memory, GovernmentCrtBoundary185Api.Memory {
        /** Exact two-byte MOVZX snapshot, returned as unsigned 0..65535. */
        int readUnsignedWord(long addressBits);
        Bits256 read256(long addressBits);
        void write256(long addressBits, Bits256 valueBits);
        void write256NonTemporal(long addressBits, Bits256 valueBits);
    }

    public record Input(
        GovernmentCrtBoundary185Api.Entry entry,
        boolean directionFlagSet,
        GovernmentCrtBoundary185Api.LoopBudget budget
    ) {
        public Input { Objects.requireNonNull(entry); Objects.requireNonNull(budget); }
    }

    public record CallResult(
        GovernmentCrtBoundary185Api.NormalReturn normalReturn,
        boolean postDirectionFlagSet
    ) {
        public CallResult { Objects.requireNonNull(normalReturn); }
    }

    public record CallFrame(
        GovernmentCrtBoundary185Api.Call call,
        GovernmentCrtBoundary185Api.Entry childEntry,
        boolean directionFlagSet,
        int instructionLength,
        long returnRipBits
    ) {
        public CallFrame {
            Objects.requireNonNull(call);
            Objects.requireNonNull(childEntry);
            if (childEntry.rspBits() != call.rspBits() - 8) throw new IllegalArgumentException("RSP mismatch");
            if (!childEntry.volatileBits().equals(call.volatileBits())) throw new IllegalArgumentException("V mismatch");
            if (!childEntry.nonvolatileBits().equals(call.nonvolatileBits())) throw new IllegalArgumentException("N mismatch");
            if (call.callSiteRva() != 0x1ACE4FCL || call.kind() != GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA || call.targetBits() != 0x4226860L || instructionLength != 5) {
                throw new IllegalArgumentException("Invalid call site");
            }
            if (returnRipBits != childEntry.imageBaseBits() + 0x1ACE501L) throw new IllegalArgumentException("Invalid return RIP");
        }
        public void checkNormalReturn(CallResult result) {
            if (result.normalReturn().returnRipBits() != this.returnRipBits()) throw new IllegalArgumentException("RIP mismatch");
            if (result.normalReturn().callerRspBits() != this.call().rspBits()) throw new IllegalArgumentException("SP mismatch");
            if (!result.normalReturn().nonvolatileBits().equals(this.call().nonvolatileBits())) throw new IllegalArgumentException("N mismatch");
        }
    }

    public record TailFrame(
        GovernmentCrtBoundary185Api.Tail transfer,
        boolean directionFlagSet
    ) {
        public TailFrame { Objects.requireNonNull(transfer); }
    }

    public interface Calls {
        CallResult invoke(CallFrame frame);
        CallResult tail(TailFrame frame);
        long readGsQword58();
    }
}