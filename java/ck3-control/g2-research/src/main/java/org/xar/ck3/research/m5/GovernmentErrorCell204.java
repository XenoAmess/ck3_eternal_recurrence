package org.xar.ck3.research.m5;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m4.error32.Error32Candidate;
import org.xar.ck3.study.m4.error32.Error32Inputs;

public final class GovernmentErrorCell204 {
    private GovernmentErrorCell204() { }

    public static GovernmentCrtBoundary185Api.NormalReturn execute(
            GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.Memory memory,
            GovernmentCrtBoundary185Api.Calls calls) {
        Objects.requireNonNull(entry);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);

        Registers r = GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));

        r.rsp -= 0x28L;

        long legacyRax = Error32Candidate.execute(
                new Error32Inputs.CallInput(entry.imageBaseBits()),
                new Error32Inputs.Calls() {
                    @Override public long call424FC74() {
                        long preSP = r.rsp;
                        memory.writeQword(preSP - 8L, entry.imageBaseBits() + 0x423B195L);
                        VolatileBits v = calls.invoke(new GovernmentCrtBoundary185Api.Call(
                                0x423B190L,
                                GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                                0x424FC74L,
                                preSP,
                                r.volatileBits(),
                                r.nonvolatileBits()));
                        r.apply(v);
                        return r.rax;
                    }
                });

        r.rax = legacyRax;
        r.rsp += 0x28L;

        long actualRip = memory.readQword(r.rsp);

        return new GovernmentCrtBoundary185Api.NormalReturn(
                r.volatileBits(),
                actualRip,
                r.rsp + 8L,
                r.nonvolatileBits());
    }
}
