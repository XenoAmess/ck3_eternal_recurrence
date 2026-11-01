package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api;

public final class LoadRowReferenceGrowth244Calls {
    private LoadRowReferenceGrowth244Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            long image,
            GovernmentCrtBoundary185Api.Memory sameMemory,
            GovernmentCrtBoundary185Api.Calls ORIGINALfallback,
            GovernmentCrtBoundary185Api.LoopBudget sameBudget,
            LoadRowReferenceCallee337b7e0199Api.Float32 sameFloating) {
        return new Dispatcher(image, sameMemory, ORIGINALfallback, sameBudget, sameFloating);
    }

    private static final class Dispatcher implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls originalFallback;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;
        private final LoadRowReferenceCallee337b7e0199Api.Float32 floating;

        private final GovernmentCrtBoundary185Api.Calls outer240;
        private final GovernmentCrtBoundary185Api.Calls child207;
        private final GovernmentCrtBoundary185Api.Calls lazy205;

        Dispatcher(long image, GovernmentCrtBoundary185Api.Memory memory,
                   GovernmentCrtBoundary185Api.Calls originalFallback,
                   GovernmentCrtBoundary185Api.LoopBudget budget,
                   LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
            this.image = image;
            this.memory = memory;
            this.originalFallback = originalFallback;
            this.budget = budget;
            this.floating = floating;

            // Construct mature 240 with 'this' as fallback for internal mutual reachability
            this.outer240 = LoadRowReferenceOuter240Calls.bind(image, memory, this, budget, floating);

            // Construct child 207 with 'this' as fallback
            this.child207 = LoadRowReferenceCallee337c200207Calls.bind(image, memory, this, budget, floating);

            // Construct lazy 205 with 'this' as fallback
            this.lazy205 = LoadRowReferenceCallee8ceeb0205Calls.bind(image, memory, this);
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                long site = call.callSiteRva();
                long target = call.targetBits();

                // New exact pairs added by this composition
                if (site == 0x337BBA6L && target == 0x337C200L) {
                    return child207.invoke(call);
                }
                if (site == 0x337C161L && target == 0x8CEEB0L) {
                    return lazy205.invoke(call);
                }
                if (site == 0x337C1C3L && target == 0x8CEEB0L) {
                    return lazy205.invoke(call);
                }

                // Preserve all actual current240 27 DIRECT pairs via outer240
                if (isMature240Scope(site, target)) {
                    return outer240.invoke(call);
                }
            }

            // Foreign calls go directly to original fallback
            return originalFallback.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            // Preserve the one DIRECT_RVA Tail(0x337C064, 0x337C0C0) via outer240
            if (transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && transfer.targetBits() == 0x337C0C0L
                    && transfer.jumpSiteRva() == 0x337C064L) {
                return outer240.tail(transfer);
            }

            // Foreign tails go directly to original fallback
            return originalFallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return originalFallback.readGsQword58();
        }

        private boolean isMature240Scope(long site, long target) {
            // 18 DIRECT pairs in mature 239 scope (handled by outer240's closure239)
            if (target == 0x337C040L) {
                return site == 0x337BAEAL || site == 0x337C7D7L;
            }
            if (target == 0x337C5D0L) {
                return site == 0x337BB00L || site == 0x337C198L || site == 0x337C7F8L || site == 0x337C8A0L;
            }
            if (target == 0x337C0C0L) {
                return site == 0x337C882L || site == 0x337BB8BL;
            }
            if (target == 0x87C9B0L) {
                return site == 0x337C6EAL || site == 0x337C71DL || site == 0x337C843L
                    || site == 0x337B93EL || site == 0x337B9CEL || site == 0x337BB4AL;
            }
            if (target == 0xE23EA0L) {
                return site == 0x337C6FCL || site == 0x337C72FL
                    || site == 0x337B987L || site == 0x337BA17L;
            }
            if (target == 0xA636F0L) {
                return site == 0x337C784L || site == 0x337C7CFL
                    || site == 0x337B8EDL || site == 0x337BA8BL || site == 0x337BAE2L;
            }
            if (target == 0x86E160L) {
                return site == 0x337BB7CL || site == 0x337C051L || site == 0x337C873L;
            }
            if (target == 0x337B7E0L) {
                return site == 0x34EF8C5L;
            }

            return false;
        }
    }
}