package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class LoadRowReferenceCalleeA636f0200Calls {
    private LoadRowReferenceCalleeA636f0200Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls delegate) {
        return new Adapter(imageBaseBits, memory, delegate);
    }

    private static final long TARGET_A636F0 = 0xA636F0L;
    private static final long CALL_SITE_337B8ED = 0x337B8EDL;
    private static final long CALL_SITE_337BA8B = 0x337BA8BL;
    private static final long CALL_SITE_337BAE2 = 0x337BAE2L;

    private static final class Adapter implements GovernmentCrtBoundary185Api.Calls {
        private final long imageBaseBits;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls delegate;

        Adapter(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls delegate) {
            this.imageBaseBits = imageBaseBits;
            this.memory = memory;
            this.delegate = delegate;
        }

        @Override
        public VolatileBits invoke(Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.targetBits() == TARGET_A636F0
                    && (call.callSiteRva() == CALL_SITE_337B8ED
                        || call.callSiteRva() == CALL_SITE_337BA8B
                        || call.callSiteRva() == CALL_SITE_337BAE2)) {

                long originalRspBits = call.rspBits();

                // Construct real target Entry for the frozen producer
                // rspBits is BEFORE the owned push, so target entry rsp is originalRspBits - 8
                GovernmentCrtBoundary185Api.Entry targetEntry = new GovernmentCrtBoundary185Api.Entry(
                    imageBaseBits,
                    originalRspBits - 8L,
                    call.volatileBits(),
                    call.nonvolatileBits()
                );

                // Call the frozen producer using exactly same Memory and delegate
                GovernmentCrtBoundary185Api.NormalReturn result = LoadRowReferenceCalleeA636f0200.execute(
                    targetEntry,
                    this.memory,
                    this.delegate
                );

                // Validate producer actual NormalReturn
                long expectedReturnRipBits = imageBaseBits + call.callSiteRva() + 5L;
                if (result.returnRipBits() != expectedReturnRipBits) {
                    throw new IllegalStateException("Malformed returnRipBits");
                }
                if (result.callerRspBits() != originalRspBits) {
                    throw new IllegalStateException("Malformed callerRspBits");
                }
                if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("Malformed restoredNonvolatile");
                }

                // Return exact actual volatileBits after checks
                return result.volatileBits();
            }

            // All unmatched Call objects pass through delegate.invoke with original identity
            return delegate.invoke(call);
        }

        @Override
        public NormalReturn tail(Tail transfer) {
            return delegate.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return delegate.readGsQword58();
        }
    }
}