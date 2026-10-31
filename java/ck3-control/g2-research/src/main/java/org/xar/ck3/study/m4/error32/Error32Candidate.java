package org.xar.ck3.study.m4.error32;

public final class Error32Candidate {
    private Error32Candidate() { }

    public static long execute(Error32Inputs.CallInput input, Error32Inputs.Calls calls) {
        long rax = calls.call424FC74();
        long target;
        if (rax == 0L) {
            target = input.moduleBaseRaw() + 0x542F210L;
        } else {
            target = rax + 0x20L;
        }
        return target;
    }
}
