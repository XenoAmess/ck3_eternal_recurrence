package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.PendingSlotCapacityFullState412Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m1.GovernmentMemoryFill206;
import org.xar.ck3.research.m1.GovernmentMemoryFillRep207;
import org.xar.ck3.research.m1.GovernmentMemoryFill206Api;
import java.util.Objects;

public final class PendingSlotCapacityKnownSet412 {
    private PendingSlotCapacityKnownSet412() { }

    public static PendingSlotCapacityFullState412Api.Calls bind(
            PendingSlotCapacityFullState412Api.Memory memory,
            GovernmentCrtBoundary185Api.LoopBudget budget,
            PendingSlotCapacityFullState412Api.Calls fallback) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(budget);
        Objects.requireNonNull(fallback);

        return new PendingSlotCapacityFullState412Api.Calls() {
            @Override
            public PendingSlotCapacityFullState412Api.CallResult invoke(PendingSlotCapacityFullState412Api.CallFrame frame) {
                Objects.requireNonNull(frame);
                GovernmentCrtBoundary185Api.Call call = frame.call();
                if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                        && call.callSiteRva() == 0x1ACE015L
                        && call.targetBits() == 0x4226F10L) {
                    
                    final boolean[] dfHolder = new boolean[1];
                    dfHolder[0] = frame.directionFlagSet();
                    final PendingSlotCapacityFullState412Api.CallResult[] tailResultHolder = new PendingSlotCapacityFullState412Api.CallResult[1];

                    GovernmentCrtBoundary185Api.Calls bridge = new GovernmentCrtBoundary185Api.Calls() {
                        @Override
                        public long readGsQword58() {
                            return fallback.readGsQword58();
                        }

                        @Override
                        public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                            throw new UnsupportedOperationException("206 has no CALL instructions");
                        }

                        @Override
                        public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                            if (transfer.jumpSiteRva() == 0x4226F57L
                                    && transfer.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                                    && transfer.targetBits() == 0x4226EF0L) {
                                GovernmentCrtBoundary185Api.NormalReturn nr = GovernmentMemoryFillRep207.execute(
                                        transfer.entry(),
                                        memory,
                                        dfHolder[0],
                                        budget);
                                return nr;
                            }
                            
                            PendingSlotCapacityFullState412Api.TailFrame tf = new PendingSlotCapacityFullState412Api.TailFrame(transfer, dfHolder[0]);
                            PendingSlotCapacityFullState412Api.CallResult cr = fallback.tail(tf);
                            tailResultHolder[0] = cr;
                            dfHolder[0] = cr.postDirectionFlagSet();
                            return cr.normalReturn();
                        }
                    };

                    GovernmentCrtBoundary185Api.NormalReturn nr = GovernmentMemoryFill206.execute(
                            frame.childEntry(),
                            memory,
                            bridge,
                            budget);

                    if (tailResultHolder[0] != null) {
                        PendingSlotCapacityFullState412Api.CallResult result = tailResultHolder[0];
                        frame.checkNormalReturn(result);
                        return result;
                    }

                    PendingSlotCapacityFullState412Api.CallResult result = new PendingSlotCapacityFullState412Api.CallResult(nr, dfHolder[0]);
                    frame.checkNormalReturn(result);
                    return result;
                }
                return fallback.invoke(frame);
            }

            @Override
            public PendingSlotCapacityFullState412Api.CallResult tail(PendingSlotCapacityFullState412Api.TailFrame frame) {
                Objects.requireNonNull(frame);
                return fallback.tail(frame);
            }

            @Override
            public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };
    }
}
