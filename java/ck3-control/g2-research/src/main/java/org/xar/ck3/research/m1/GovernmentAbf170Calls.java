package org.xar.ck3.research.m1;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentResult168Api;
import org.xar.ck3.research.m5.GovernmentResult168;

/**
 * Thin consumer binding for the ABF7E0 target.
 * Intercepts calls to 0xABF7E0 and executes the frozen shared core method.
 */
public final class GovernmentAbf170Calls {

    private GovernmentAbf170Calls() { }

    public static GovernmentPrimaryTail155Api.Calls bind(
            long imageBaseBits,
            GovernmentPrimaryTail155Api.Memory memory,
            GovernmentPrimaryTail155Api.Calls delegate,
            GovernmentResult168Api.WorkBudget budget) {

        return new GovernmentPrimaryTail155Api.Calls() {
            @Override
            public long readGsQword58() {
                return delegate.readGsQword58();
            }

            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentPrimaryTail155Api.OpaqueCall call) {
                if (call.targetRva() == 0xABF7E0L) {
                    // Simulate normal actual CALL5 push(image+callSiteRva+5) at call.rspBits()-8
                    long calleeRsp = call.rspBits() - 8L;
                    long returnRip = imageBaseBits + call.callSiteRva() + 5L;
                    memory.writeQword(calleeRsp, returnRip);

                    // Construct real GovernmentCallee164Api.Entry
                    GovernmentCallee164Api.Entry entry = new GovernmentCallee164Api.Entry(
                            imageBaseBits,
                            calleeRsp,
                            call.volatileBits(),
                            call.nonvolatileBits());

                    // Invoke the frozen ACTUAL shared method signature
                    GovernmentCallee164Api.NormalReturn result = GovernmentResult168.execute(
                            GovernmentResult168Api.Instance.RESULT_ABF7E0,
                            entry,
                            memory,
                            budget);

                    // Validate actual returned state against expected ABI continuation.
                    long expectedReturnRip = imageBaseBits + call.callSiteRva() + 5L;
                    long expectedCallerRsp = call.rspBits();

                    if (result.returnRipBits() != expectedReturnRip) {
                        throw new UnsupportedOperationException("NormalReturn.returnRipBits mismatch");
                    }
                    if (result.callerRspBits() != expectedCallerRsp) {
                        throw new UnsupportedOperationException("NormalReturn.callerRspBits mismatch");
                    }

                    NonvolatileBits expectedNV = call.nonvolatileBits();
                    NonvolatileBits actualNV = result.nonvolatileBits();

                    if (actualNV.rbxBits() != expectedNV.rbxBits()) {
                        throw new UnsupportedOperationException("NormalReturn.nonvolatileBits.rbxBits mismatch");
                    }
                    if (actualNV.rbpBits() != expectedNV.rbpBits()) {
                        throw new UnsupportedOperationException("NormalReturn.nonvolatileBits.rbpBits mismatch");
                    }
                    if (actualNV.rsiBits() != expectedNV.rsiBits()) {
                        throw new UnsupportedOperationException("NormalReturn.nonvolatileBits.rsiBits mismatch");
                    }
                    if (actualNV.rdiBits() != expectedNV.rdiBits()) {
                        throw new UnsupportedOperationException("NormalReturn.nonvolatileBits.rdiBits mismatch");
                    }
                    if (actualNV.r12Bits() != expectedNV.r12Bits()) {
                        throw new UnsupportedOperationException("NormalReturn.nonvolatileBits.r12Bits mismatch");
                    }
                    if (actualNV.r13Bits() != expectedNV.r13Bits()) {
                        throw new UnsupportedOperationException("NormalReturn.nonvolatileBits.r13Bits mismatch");
                    }
                    if (actualNV.r14Bits() != expectedNV.r14Bits()) {
                        throw new UnsupportedOperationException("NormalReturn.nonvolatileBits.r14Bits mismatch");
                    }
                    if (actualNV.r15Bits() != expectedNV.r15Bits()) {
                        throw new UnsupportedOperationException("NormalReturn.nonvolatileBits.r15Bits mismatch");
                    }
                    if (!Objects.equals(actualNV.xmm6(), expectedNV.xmm6())) {
                        throw new UnsupportedOperationException("NormalReturn.nonvolatileBits.xmm6 mismatch");
                    }

                    return result.volatileBits();
                } else {
                    return delegate.invoke(call);
                }
            }
        };
    }
}