package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api.IatCall;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;
import org.xar.ck3.research.m1.GovernmentThreadHeader178Api;

/**
 * Direct-call consumer for the actual Header178 wait loop CALL to Wait179.
 * Intercepts only OpaqueCall with callSiteRva 0x4223AA9 and targetRva 0x4223B30.
 * All other calls delegate unchanged.
 */
public final class GovernmentThreadWait179Calls {
    private GovernmentThreadWait179Calls() { }

    public static GovernmentThreadHeader178Api.Ports bind(
            long imageBase,
            GovernmentSharedManager167Api.Memory memory,
            GovernmentThreadHeader178Api.Ports delegate) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(delegate);

        return new GovernmentThreadHeader178Api.Ports() {
            @Override
            public long readGsQword58() {
                return delegate.readGsQword58();
            }

            @Override
            public VolatileBits invoke(OpaqueCall call) {
                Objects.requireNonNull(call);
                if (call.callSiteRva() == 0x4223AA9L && call.targetRva() == 0x4223B30L) {
                    // Construct the callee entry for Wait179.
                    // frameRspBits is after CALL pushed its return address.
                    // The caller (Header178) already wrote the return address at callSiteRsp-8.
                    // We do NOT write it again.
                    GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                            imageBase,
                            call.rspBits() - 8,
                            call.volatileBits(),
                            call.nonvolatileBits()
                    );

                    // Execute the Wait179 body.
                    GovernmentCallee164Api.NormalReturn ret = GovernmentThreadWait179.execute(
                            entry,
                            memory,
                            delegate
                    );

                    // Validate the actual return state matches expectations.
                    // 1. Return RIP must be the address pushed by the caller (imageBase + 0x4223AAE).
                    if (ret.returnRipBits() != imageBase + 0x4223AAEL) {
                        throw new IllegalStateException("Return RIP mismatch");
                    }
                    // 2. Caller RSP must match the original call site RSP (after RET pop).
                    if (ret.callerRspBits() != call.rspBits()) {
                        throw new IllegalStateException("Caller RSP mismatch");
                    }
                    // 3. Nonvolatile state must be preserved exactly.
                    if (!ret.nonvolatileBits().equals(call.nonvolatileBits())) {
                        throw new IllegalStateException("Nonvolatile state mismatch");
                    }

                    return ret.volatileBits();
                }
                return delegate.invoke(call);
            }

            @Override
            public VolatileBits invokeIat(IatCall call) {
                return delegate.invokeIat(call);
            }
        };
    }
}