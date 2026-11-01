package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.TerminalAbort4242284215.Calls60;

public final class ModuleLookup42422d0216Calls {
    public static Calls60 bind(long image, GovernmentCrtBoundary185Api.Memory memory, TerminalAbort4242284215.Calls60 fallback) {
        return new Calls60() {
            @Override public VolatileBits invoke(Call call) {
                if (call.kind() == GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA && call.targetBits() == 0x42422D0L) {
                    if (call.callSiteRva() == 0x424222AL || call.callSiteRva() == 0x42422C0L) {
                        // Intercept child call to 42422D0
                        // Construct child Entry: imageBaseBits=image, rspBits=call.rspBits()-8 (pre-push RBX location)
                        // VolatileBits and NonvolatileBits are passed through from the Call descriptor
                        GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                            image,
                            call.rspBits() - 8L,
                            call.volatileBits(),
                            call.nonvolatileBits()
                        );

                        // Execute the new child module
                        NormalReturn nr = ModuleLookup42422d0216.execute(childEntry, memory, fallback);

                        // Enforce gates: returnRip must be image + site + 5 (next instruction after CALL)
                        // callerSP must be preSP (call.rspBits())
                        // All NV must equal original call NV (normal port precondition)
                        if (nr.returnRipBits() != image + call.callSiteRva() + 5L) {
                            throw new UnsupportedOperationException("Gate violation: returnRip mismatch");
                        }
                        if (nr.callerRspBits() != call.rspBits()) {
                            throw new UnsupportedOperationException("Gate violation: callerSP mismatch");
                        }
                        if (!nr.nonvolatileBits().equals(call.nonvolatileBits())) {
                            throw new UnsupportedOperationException("Gate violation: NV mismatch");
                        }

                        return nr.volatileBits();
                    }
                }
                // Foreign invoke: delegate to fallback
                return fallback.invoke(call);
            }

            @Override public NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                // Foreign tail: delegate to fallback
                return fallback.tail(transfer);
            }

            @Override public long readGsQword58() {
                // Foreign GS58: delegate to fallback
                return fallback.readGsQword58();
            }

            @Override public long readGsQword60() {
                // Foreign GS60: delegate to fallback
                return fallback.readGsQword60();
            }
        };
    }
}