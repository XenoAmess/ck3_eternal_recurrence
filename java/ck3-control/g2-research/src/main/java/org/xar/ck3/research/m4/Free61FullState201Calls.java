package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class Free61FullState201Calls {
    private static final long TARGET_424E364 = 0x424E364L;
    private static final long SITE_424DC48 = 0x424DC48L;
    private static final long SITE_424DC6C = 0x424DC6CL;

    public static Calls bind(long imageBaseBits, Memory memory, Calls fallback) {
        return new CallsImpl(imageBaseBits, memory, fallback);
    }

    private static final class CallsImpl implements Calls {
        private final long imageBaseBits;
        private final Memory memory;
        private final Calls fallback;

        CallsImpl(long imageBaseBits, Memory memory, Calls fallback) {
            this.imageBaseBits = imageBaseBits;
            this.memory = memory;
            this.fallback = fallback;
        }

        @Override
        public VolatileBits invoke(Call call) {
            if (call.kind() == TargetKind.DIRECT_RVA
                    && call.targetBits() == TARGET_424E364
                    && (call.callSiteRva() == SITE_424DC48 || call.callSiteRva() == SITE_424DC6C)) {
                long site = call.callSiteRva();
                long rspBits = call.rspBits();
                long entryRspBits = rspBits - 8L;
                Entry entry = new Entry(imageBaseBits, entryRspBits, call.volatileBits(), call.nonvolatileBits());
                NormalReturn result = Free61FullState201.execute(entry, memory, fallback);
                long expectedRip = imageBaseBits + site + 5L;
                if (result.returnRipBits() != expectedRip) {
                    throw new IllegalStateException("returnRip mismatch");
                }
                if (result.callerRspBits() != rspBits) {
                    throw new IllegalStateException("callerRsp mismatch");
                }
                if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("nonvolatile mismatch");
                }
                return result.volatileBits();
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
    }
}