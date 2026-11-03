package org.xar.ck3.study.m6.poststate249;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/** Complete held8B normal body [86E140,86E148); no allocator ownership/type inference. */
public final class AllocatorGetterPostState249 implements PostState240Api.EntryExecutor {
    @Override
    public QueueFp604Api.Outcome execute(PostState240Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        var entry=input.entry();
        var before=entry.volatileBits();
        long rax=memory.readQword(before.rcxBits()+0x408L); // 86E140 MOV RAX,[RCX+408h]
        var after=new VolatileBits(rax,before.rcxBits(),before.rdxBits(),before.r8Bits(),
                before.r9Bits(),before.r10Bits(),before.r11Bits(),before.xmm0(),before.xmm1(),
                before.xmm2(),before.xmm3(),before.xmm4(),before.xmm5());
        long returnRip=memory.readQword(entry.rspBits()); // 86E147 RET: a separate fresh read
        var returned=new GovernmentCrtBoundary185Api.NormalReturn(after,returnRip,
                entry.rspBits()+8,entry.nonvolatileBits());
        // Neither held instruction modifies DF or MXCSR; retain explicit input knowledge exactly.
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(returned,
                input.directionFlagSet()),input.mxcsr());
    }
}
