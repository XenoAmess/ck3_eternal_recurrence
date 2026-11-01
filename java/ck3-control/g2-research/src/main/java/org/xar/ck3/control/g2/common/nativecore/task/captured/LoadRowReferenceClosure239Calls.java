package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199Api;

public final class LoadRowReferenceClosure239Calls {
    private LoadRowReferenceClosure239Calls() { }

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

        private final GovernmentCrtBoundary185Api.Calls a204;
        private final GovernmentCrtBoundary185Api.Calls a205;
        private final GovernmentCrtBoundary185Api.Calls a234;
        private final GovernmentCrtBoundary185Api.Calls a235;
        private final GovernmentCrtBoundary185Api.Calls a236;
        private final GovernmentCrtBoundary185Api.Calls a237;
        private final GovernmentCrtBoundary185Api.Calls a238;
        private final GovernmentCrtBoundary185Api.Calls a203;
        private final GovernmentCrtBoundary185Api.Calls a204cap;

        Dispatcher(long image, GovernmentCrtBoundary185Api.Memory memory,
                   GovernmentCrtBoundary185Api.Calls originalFallback,
                   GovernmentCrtBoundary185Api.LoopBudget budget,
                   LoadRowReferenceCallee337b7e0199Api.Float32 floating) {
            this.image = image;
            this.memory = memory;
            this.originalFallback = originalFallback;
            this.budget = budget;
            this.floating = floating;

            // Construct adapters with 'this' as fallback to ensure mutual reachability.
            // Construction does not invoke methods, only stores references.
            this.a204 = LoadRowReferenceCallee337c0c0204Calls.bind(image, memory, this, budget);
            this.a205 = LoadRowReferenceCallee337c5d0FromC0c0205Calls.bind(image, memory, this, budget, floating);
            this.a234 = LoadRowReferenceSelf337c5d0234Calls.bind(image, memory, this, budget, floating);
            this.a235 = LoadRowReferenceMutual235Calls.bind(image, memory, this, budget, floating);
            this.a236 = LoadRowReferenceRebuild236Calls.bind(image, memory, this, budget, floating);
            this.a237 = LoadRowReferenceTransfer237Calls.bind(image, memory, this);
            this.a238 = LoadRowReferenceSwap238Calls.bind(image, memory, this);
            this.a203 = LoadRowReferenceCallees337c203Calls.bind(image, memory, this, budget, floating);
            this.a204cap = CapacityIndex86e160204Calls.bind(image, memory, this);
        }

        @Override
        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
            if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA) {
                long site = call.callSiteRva();
                long target = call.targetBits();

                // 199 Caller Routes (C5/C0 normal callees)
                if (target == 0x337C5D0L) {
                    if (site == 0x337C198L) return a205.invoke(call);
                    if (site == 0x337C7F8L || site == 0x337C8A0L) return a234.invoke(call);
                    if (site == 0x337BB00L) return a203.invoke(call);
                }
                if (target == 0x337C0C0L) {
                    if (site == 0x337C882L || site == 0x337BB8BL) return a204.invoke(call);
                }
                if (target == 0x337C040L) {
                    if (site == 0x337BAEAL) return a203.invoke(call);
                    if (site == 0x337C7D7L) return a236.invoke(call);
                }

                // 235 Mutual/Self Routes
                if (target == 0x337C5D0L && (site == 0x337C7F8L || site == 0x337C8A0L)) return a235.invoke(call);
                if (target == 0x337C0C0L && (site == 0x337C882L || site == 0x337BB8BL)) return a235.invoke(call);
                if (target == 0x337C5D0L && site == 0x337C198L) return a235.invoke(call);

                // 236 Rebuild
                if (target == 0x337C040L && site == 0x337C7D7L) return a236.invoke(call);

                // 237 Transfer
                if (target == 0x87C9B0L && (site == 0x337C6EAL || site == 0x337C71DL || site == 0x337C843L)) return a237.invoke(call);
                if (target == 0xE23EA0L && (site == 0x337C6FCL || site == 0x337C72FL)) return a237.invoke(call);

                // 238 Swap
                if (target == 0xA636F0L && (site == 0x337C784L || site == 0x337C7CFL)) return a238.invoke(call);

                // 203 Parent Direct Routes
                if (target == 0x337C040L && site == 0x337BAEAL) return a203.invoke(call);
                if (target == 0x337C5D0L && site == 0x337BB00L) return a203.invoke(call);

                // 204 Capacity Three Direct Sites
                if (target == 0x86E160L && (site == 0x337BB7CL || site == 0x337C051L || site == 0x337C873L)) return a204cap.invoke(call);


            }
            return originalFallback.invoke(call);
        }

        @Override
        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
            if (transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && transfer.targetBits() == 0x337C0C0L
                    && transfer.jumpSiteRva() == 0x337C064L) {
                return a204.tail(transfer);
            }
            return originalFallback.tail(transfer);
        }

        @Override
        public long readGsQword58() {
            return originalFallback.readGsQword58();
        }
    }
}