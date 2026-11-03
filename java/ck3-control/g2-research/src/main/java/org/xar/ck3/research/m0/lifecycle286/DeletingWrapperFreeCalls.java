package org.xar.ck3.research.m0.lifecycle286;

import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.study.m6.full224.DefaultFreeThunks185224;

/**
 * Thin binding for the two exact wrapper CALL sites to 0x4223F44.
 * Intercepts only the specific direct calls from PlayerInfo and Manager wrappers.
 * The held front JMP has no effects; the mature helper owns the subsequent 40EC530 chain.
 */
public final class DeletingWrapperFreeCalls {
    private DeletingWrapperFreeCalls() { }

    public static GovernmentCrtBoundary185Api.Calls bind(long imageBaseBits, Memory memory, Calls fallback) {
        return new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(Call call) {
                // Intercept only the two exact wrapper sites calling 0x4223F44
                if (call.kind() == TargetKind.DIRECT_RVA && call.targetBits() == 0x4223F44L) {
                    if (call.callSiteRva() == 0x23DA6A1L || call.callSiteRva() == 0x28EE5F1L) {
                        // Verify existing return slot written by caller
                        long expectedRip = imageBaseBits + call.callSiteRva() + 5L;
                        long entryRsp = call.rspBits() - 8L;
                        if (memory.readQword(entryRsp) != expectedRip) {
                            throw new IllegalStateException("existing CALL return slot mismatch");
                        }

                        // Construct entry for the mature helper
                        Entry helperEntry = new Entry(imageBaseBits, entryRsp, call.volatileBits(), call.nonvolatileBits());

                        // Execute the mature helper (DefaultFreeThunks185224)
                        NormalReturn result = DefaultFreeThunks185224.execute(helperEntry, memory, fallback);

                        // Verify boundary conditions
                        if (result.returnRipBits() != expectedRip
                                || result.callerRspBits() != call.rspBits()
                                || !result.nonvolatileBits().equals(call.nonvolatileBits())) {
                            throw new IllegalStateException("normal return boundary mismatch");
                        }

                        return result.volatileBits();
                    }
                }
                return fallback.invoke(call);
            }

            @Override public NormalReturn tail(Tail transfer) {
                return fallback.tail(transfer);
            }

            @Override public long readGsQword58() {
                return fallback.readGsQword58();
            }
        };
    }
}
