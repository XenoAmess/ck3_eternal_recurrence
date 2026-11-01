package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api;

public final class LoadRowReferenceRebuild236Calls {
    private LoadRowReferenceRebuild236Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls originalFallback, GovernmentCrtBoundary185Api.LoopBudget budget, LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        Link link = new Link(image, memory, originalFallback, budget, floating);
        return link.dispatcher;
    }

    private static final class Link implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls originalFallback;
        private final GovernmentCrtBoundary185Api.Calls dispatcher;

        Link(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls originalFallback, GovernmentCrtBoundary185Api.LoopBudget budget, LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
            this.image = image;
            this.memory = memory;
            this.originalFallback = originalFallback;
            this.dispatcher = LoadRowReferenceMutual235Calls.bind(image, memory, this, budget, floating);
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.callSiteRva() == 0x337C7D7L
                    && call.targetBits() == 0x337C040L) {
                GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                        image,
                        call.rspBits() - 8L,
                        call.volatileBits(),
                        call.nonvolatileBits());
                GovernmentCrtBoundary185Api.NormalReturn result = LoadRowReferenceCallee337c040203.execute(childEntry, memory, dispatcher);
                if (result.returnRipBits() != image + 0x337C7DCL) {
                    throw new IllegalStateException("Malformed return RIP");
                }
                if (result.callerRspBits() != call.rspBits()) {
                    throw new IllegalStateException("Malformed caller RSP");
                }
                if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("Malformed nonvolatile restoration");
                }
                return result.volatileBits();
            }
            return originalFallback.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            return originalFallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return originalFallback.readGsQword58();
        }
    }
}