package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api;

public final class LoadRowReferenceMigration246Calls {
    private LoadRowReferenceMigration246Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            long image,
            GovernmentCrtBoundary185Api.Memory sameMemory,
            GovernmentCrtBoundary185Api.Calls ORIGINALfallback,
            GovernmentCrtBoundary185Api.LoopBudget sameBudget,
            LoadRowReferenceCallee337b7e0199Api.Float32 sameFloating) {

        // Create the single-site bridge which acts as the fallback for the 244 graph
        GovernmentCrtBoundary185Api.Calls bridge = new Bridge(image, sameMemory, ORIGINALfallback);

        // Construct the actual 244 graph using the bridge as its original fallback
        return LoadRowReferenceGrowth244Calls.bind(image, sameMemory, bridge, sameBudget, sameFloating);
    }

    private static final class Bridge implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls fallback;

        Bridge(long image, GovernmentCrtBoundary185Api.Memory memory, GovernmentCrtBoundary185Api.Calls fallback) {
            this.image = image;
            this.memory = memory;
            this.fallback = fallback;
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && call.callSiteRva() == 0x337C68BL
                    && call.targetBits() == 0x87C9B0L) {

                // Construct real target Entry for the frozen producer
                // rspBits is BEFORE the owned push, so target entry rsp is originalRspBits - 8
                GovernmentCrtBoundary185Api.Entry entry = new GovernmentCrtBoundary185Api.Entry(
                    image,
                    call.rspBits() - 8L,
                    call.volatileBits(),
                    call.nonvolatileBits()
                );

                // Call the frozen producer using exactly same Memory and delegate
                GovernmentCrtBoundary185Api.NormalReturn result = LoadRowReferenceCallee87c9b0201.execute(
                    entry,
                    this.memory,
                    this.fallback
                );

                // Validate producer actual NormalReturn
                // returnRipBits = imageBaseBits + call.callSiteRva() + 5
                long expectedReturnRip = image + 0x337C690L;
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
            return fallback.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            return fallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }
    }
}