package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class GovernmentCrtBoundary185Calls {
    private GovernmentCrtBoundary185Calls() { }

    public static GovernmentCrtBoundary185BridgeApi.Calls bind(long imageBase, Memory memory, GovernmentPrimaryTail155Api.Calls fallback, Calls crtPorts, LoopBudget budget) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(fallback);
        Objects.requireNonNull(crtPorts);
        Objects.requireNonNull(budget);
        return new Bridge(imageBase, memory, fallback, crtPorts, budget);
    }

    private static final class Bridge implements GovernmentCrtBoundary185BridgeApi.Calls {
        private final long imageBase;
        private final Memory memory;
        private final GovernmentPrimaryTail155Api.Calls fallback;
        private final Calls crtPorts;
        private final LoopBudget budget;

        Bridge(long imageBase, Memory memory, GovernmentPrimaryTail155Api.Calls fallback, Calls crtPorts, LoopBudget budget) {
            this.imageBase = imageBase;
            this.memory = memory;
            this.fallback = fallback;
            this.crtPorts = crtPorts;
            this.budget = budget;
        }

        @Override
        public long readGsQword58() {
            return fallback.readGsQword58();
        }

        @Override
        public VolatileBits invoke(OpaqueCall call) {
            Objects.requireNonNull(call);
            long site = call.callSiteRva();
            long target = call.targetRva();

            if (isCrtBoundary(site, target)) {
                Entry entry = new Entry(imageBase, call.rspBits() - 8L, call.volatileBits(), call.nonvolatileBits());
                NormalReturn result;
                if (target == 0x4223A84L) {
                    result = GovernmentCrtBoundary185.execute3A84(entry, memory, crtPorts, budget);
                } else if (target == 0x4223A24L) {
                    result = GovernmentCrtBoundary185.execute3A24(entry, memory, crtPorts);
                } else if (target == 0x4223F24L) {
                    result = GovernmentCrtBoundary185.execute3F24(entry, memory, crtPorts);
                } else {
                    throw new IllegalStateException("Unknown CRT target");
                }

                long expectedRip = imageBase + site + 5L;
                if (result.returnRipBits() != expectedRip) {
                    throw new IllegalStateException("Return RIP mismatch");
                }
                if (result.callerRspBits() != call.rspBits()) {
                    throw new IllegalStateException("Caller RSP mismatch");
                }
                if (!result.nonvolatileBits().equals(call.nonvolatileBits())) {
                    throw new IllegalStateException("Nonvolatile mismatch");
                }
                return result.volatileBits();
            }

            return fallback.invoke(call);
        }

        private static boolean isCrtBoundary(long site, long target) {
            if (target == 0x4223A84L) {
                return site == 0x3F4F982L || site == 0x3F5C0C3L;
            }
            if (target == 0x4223F24L) {
                return site == 0x3F4F9E6L || site == 0x3F5C162L;
            }
            if (target == 0x4223A24L) {
                return site == 0x3F4F9F3L || site == 0x3F5C16FL;
            }
            return false;
        }
    }
}
