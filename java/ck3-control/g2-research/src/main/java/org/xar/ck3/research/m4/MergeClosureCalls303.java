package org.xar.ck3.research.m4;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/**
 * M4-303: Exact recursive port router.
 * Composes mature298 and mature302 with THIS router as their fallback.
 * Delegates ONLY three exact ports to the mature factories.
 * All other ports go directly to the original unknown fallback once.
 * No eligibility memory work, no new algorithm, no game/hardware claims.
 */
public final class MergeClosureCalls303 {
    private MergeClosureCalls303() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            long imageBaseBits,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls originalUnknown,
            GovernmentCrtBoundary185Api.LoopBudget budget) {

        return new RouterCalls(imageBaseBits, memory, originalUnknown, budget);
    }

    private static final class RouterCalls implements GovernmentCrtBoundary185Api.Calls {
        private final GovernmentCrtBoundary185Api.Calls originalUnknown;
        private final GovernmentCrtBoundary185Api.Calls mature298;
        private final GovernmentCrtBoundary185Api.Calls mature302;

        RouterCalls(long imageBaseBits,
                    GovernmentCrtBoundary185Api.Memory memory,
                    GovernmentCrtBoundary185Api.Calls originalUnknown,
                    GovernmentCrtBoundary185Api.LoopBudget budget) {
            this.originalUnknown = originalUnknown;
            // Both mature factories only capture this reference; neither invokes it here.
            this.mature298 = BridgeMergeCalls298.bind(imageBaseBits, memory, this, budget);
            this.mature302 = ScratchMergeCalls302.bind(memory, this, budget);
        }

        @Override
        public VolatileBits invoke(Call call) {
            // Delegate ONLY exact Call DIRECT_RVA/site 0x1A8335D/target 0x1A81AB0 to mature298.
            if (call.kind() == TargetKind.DIRECT_RVA
                    && call.callSiteRva() == 0x1A8335DL
                    && call.targetBits() == 0x1A81AB0L) {
                return mature298.invoke(call);
            }
            // ALL other invoke go directly to ORIGINALUNKNOWN once.
            return originalUnknown.invoke(call);
        }

        @Override
        public NormalReturn tail(Tail transfer) {
            // Delegate ONLY exact Tail DIRECT/site 0x1A833A2/target 0x1A81AB0 to mature298.
            if (transfer.kind() == TargetKind.DIRECT_RVA
                    && transfer.jumpSiteRva() == 0x1A833A2L
                    && transfer.targetBits() == 0x1A81AB0L) {
                return mature298.tail(transfer);
            }
            // Delegate ONLY exact Tail DIRECT/site 0x1A81B9C/target 0x1A82450 to mature302.
            if (transfer.kind() == TargetKind.DIRECT_RVA
                    && transfer.jumpSiteRva() == 0x1A81B9CL
                    && transfer.targetBits() == 0x1A82450L) {
                return mature302.tail(transfer);
            }
            // ALL other tail go directly to ORIGINALUNKNOWN once.
            return originalUnknown.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            // GS goes directly to originalUnknown once.
            return originalUnknown.readGsQword58();
        }
    }
}