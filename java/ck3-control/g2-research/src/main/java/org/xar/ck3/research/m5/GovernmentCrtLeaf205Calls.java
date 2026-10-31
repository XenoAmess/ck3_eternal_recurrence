package org.xar.ck3.research.m5;

import org.xar.ck3.research.m4.Free61FullState201;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class GovernmentCrtLeaf205Calls {
    private GovernmentCrtLeaf205Calls() { }

    public static Calls bind(long imageBaseBits, Memory memory, Calls fallback) {
        return new CallsImpl(imageBaseBits, memory, fallback);
    }

    private static final class CallsImpl implements Calls {
        private final long imageBaseBits;
        private final Memory memory;
        private final Calls fallback;
        private final Calls errorInner;

        CallsImpl(long imageBaseBits, Memory memory, Calls fallback) {
            this.imageBaseBits = imageBaseBits;
            this.memory = memory;
            this.fallback = fallback;
            this.errorInner = GovernmentErrorCell204Calls.bind(imageBaseBits, memory, fallback);
        }

        @Override
        public VolatileBits invoke(Call call) {
            if (call.kind() == TargetKind.DIRECT_RVA) {
                long site = call.callSiteRva();
                long target = call.targetBits();

                if (site == 0x4259259L && target == 0x423B18CL) {
                    return execute204(call);
                }
                if (site == 0x4251F7DL && target == 0x423B18CL) {
                    return execute204(call);
                }
                if (site == 0x4251F70L && target == 0x424E364L) {
                    return executeFree61(call);
                }
            }
            return fallback.invoke(call);
        }

        @Override
        public NormalReturn tail(Tail transfer) {
            return fallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }

        private VolatileBits execute204(Call call) {
            Entry entry = new Entry(imageBaseBits, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
            NormalReturn result = GovernmentErrorCell204.execute(entry, memory, fallback);
            validate(call, result);
            return result.volatileBits();
        }

        private VolatileBits executeFree61(Call call) {
            Entry entry = new Entry(imageBaseBits, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
            NormalReturn result = Free61FullState201.execute(entry, memory, errorInner);
            validate(call, result);
            return result.volatileBits();
        }

        private void validate(Call call, NormalReturn result) {
            long expectedRip = imageBaseBits + call.callSiteRva() + 5L;
            if (result.returnRipBits() != expectedRip) {
                throw new IllegalStateException("returnRip mismatch");
            }
            if (result.callerRspBits() != call.rspBits()) {
                throw new IllegalStateException("callerRsp mismatch");
            }
            if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                throw new IllegalStateException("nonvolatile mismatch");
            }
        }
    }
}
