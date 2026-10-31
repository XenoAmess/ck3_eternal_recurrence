package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class LoadRowReferenceCallee87c9b0201Calls {
    private LoadRowReferenceCallee87c9b0201Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls delegate) {
        return new Adapter(imageBaseBits, memory, delegate);
    }

    private static final long TARGET_87C9B0 = 0x87C9B0L;
    private static final long CALL_SITE_1 = 0x337B93EL;
    private static final long CALL_SITE_2 = 0x337B9CEL;
    private static final long CALL_SITE_3 = 0x337BB4AL;

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
                    && call.targetBits() == TARGET_87C9B0
                    && (call.callSiteRva() == CALL_SITE_1 || call.callSiteRva() == CALL_SITE_2 || call.callSiteRva() == CALL_SITE_3)) {

                // Construct real target Entry
                // rspBits is BEFORE the owned push in the Call record.
                // The callee prologue does: mov [rsp+8], rbx; push rdi; sub rsp, 0x20.
                // Actual parent CALL already owns the return slot; target Entry is pre-CALL RSP minus8.

                GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                    imageBaseBits,
                    call.rspBits() - 8L,
                    call.volatileBits(),
                    call.nonvolatileBits()
                );

                // Call the frozen producer
                GovernmentCrtBoundary185Api.NormalReturn result = LoadRowReferenceCallee87c9b0201.execute(entry, memory, delegate);

                // Validate producer actual NormalReturn
                // returnRipBits = imageBaseBits + call.callSiteRva() + 5
                long expectedReturnRip = imageBaseBits + call.callSiteRva() + 5L;
                if (result.returnRipBits() != expectedReturnRip) {
                    throw new IllegalArgumentException("Malformed return RIP");
                }

                // callerRspBits = original pre-CALL rspBits
                if (result.callerRspBits() != call.rspBits()) {
                    throw new IllegalArgumentException("Malformed caller RSP");
                }

                // restored full nonvolatile equals original call.nonvolatileBits
                if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalArgumentException("Malformed nonvolatile restoration");
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