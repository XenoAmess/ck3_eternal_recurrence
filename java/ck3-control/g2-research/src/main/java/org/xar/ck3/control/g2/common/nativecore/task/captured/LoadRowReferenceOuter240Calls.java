package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api;

public final class LoadRowReferenceOuter240Calls {
    private LoadRowReferenceOuter240Calls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(
            long image,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls originalFallback,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
        return new Dispatcher(image, memory, originalFallback, budget, floating);
    }

    private static final class Dispatcher implements GovernmentCrtBoundary185Api.Calls {
        private final long image;
        private final GovernmentCrtBoundary185Api.Memory memory;
        private final GovernmentCrtBoundary185Api.Calls originalFallback;
        private final GovernmentCrtBoundary185Api.LoopBudget budget;
        private final LoadRowReferenceCallee337b7e0199Api.Float32 floating;

        private final GovernmentCrtBoundary185Api.Calls closure239;
        private final GovernmentCrtBoundary185Api.Calls outer201;
        private final GovernmentCrtBoundary185Api.Calls outer202;
        private final GovernmentCrtBoundary185Api.Calls outer200;
        private final GovernmentCrtBoundary185Api.Calls outer199;

        Dispatcher(long image, GovernmentCrtBoundary185Api.Memory memory,
                   GovernmentCrtBoundary185Api.Calls originalFallback,
                   GovernmentCrtBoundary185Api.LoopBudget budget,
                   LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
            this.image = image;
            this.memory = memory;
            this.originalFallback = originalFallback;
            this.budget = budget;
            this.floating = floating;

            // Construct mature 239 closure with 'this' as fallback for internal mutual reachability
            this.closure239 = LoadRowReferenceClosure239Calls.bind(image, memory, this, budget, floating);

            // Construct outer adapters with 'this' as fallback for internal mutual reachability
            this.outer201 = LoadRowReferenceCallee87c9b0201Calls.bind(image, memory, this);
            this.outer202 = LoadRowReferenceCalleeE23ea0202Calls.bind(image, memory, this);
            this.outer200 = LoadRowReferenceCalleeA636f0200Calls.bind(image, memory, this);
            this.outer199 = LoadRowReferenceCallee337b7e0199Calls.bind(image, memory, this, budget, floating);
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                long site = call.callSiteRva();
                long target = call.targetBits();

                // Mature 239 scope: 18 DIRECT pairs + 1 Tail
                // These are handled by closure239 which internally routes to its own adapters
                if (isMature239Scope(site, target)) {
                    return closure239.invoke(call);
                }

                // Outer 201: 3 pairs targeting 0x87C9B0
                if (target == 0x87C9B0L && (site == 0x337B93EL || site == 0x337B9CEL || site == 0x337BB4AL)) {
                    return outer201.invoke(call);
                }

                // Outer 202: 2 pairs targeting 0xE23EA0
                if (target == 0xE23EA0L && (site == 0x337B987L || site == 0x337BA17L)) {
                    return outer202.invoke(call);
                }

                // Outer 200: 3 pairs targeting 0xA636F0
                if (target == 0xA636F0L && (site == 0x337B8EDL || site == 0x337BA8BL || site == 0x337BAE2L)) {
                    return outer200.invoke(call);
                }

                // Outer 199: 1 pair targeting 0x337B7E0 from site 0x34EF8C5
                if (target == 0x337B7E0L && site == 0x34EF8C5L) {
                    return outer199.invoke(call);
                }
            }

            // Foreign calls go directly to original fallback
            return originalFallback.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            // Mature 239 Tail: site 0x337C064, target 0x337C0C0
            if (transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && transfer.targetBits() == 0x337C0C0L
                    && transfer.jumpSiteRva() == 0x337C064L) {
                return closure239.tail(transfer);
            }

            // Foreign tails go directly to original fallback
            return originalFallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return originalFallback.readGsQword58();
        }

        private boolean isMature239Scope(long site, long target) {
            // 18 DIRECT pairs in mature 239
            // Sites: 0x337BAEA, 0x337BB00, 0x337C882, 0x337BB8B, 0x337C198, 0x337C7F8, 0x337C8A0, 0x337C7D7, 0x337C6EA, 0x337C71D, 0x337C843, 0x337C6FC, 0x337C72F, 0x337C784, 0x337C7CF, 0x337BB7C, 0x337C051, 0x337C873
            // Targets: 0x337C040, 0x337C5D0, 0x337C0C0, 0x87C9B0, 0xE23EA0, 0xA636F0, 0x86E160

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
                return site == 0x337C6EAL || site == 0x337C71DL || site == 0x337C843L;
            }
            if (target == 0xE23EA0L) {
                return site == 0x337C6FCL || site == 0x337C72FL;
            }
            if (target == 0xA636F0L) {
                return site == 0x337C784L || site == 0x337C7CFL;
            }
            if (target == 0x86E160L) {
                return site == 0x337BB7CL || site == 0x337C051L || site == 0x337C873L;
            }
            return false;
        }
    }
}