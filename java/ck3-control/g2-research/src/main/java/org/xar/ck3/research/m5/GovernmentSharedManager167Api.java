package org.xar.ck3.research.m5;

/** Only the actually missing owned-memory primitive; normal raw entry/return reuse callee164. */
public final class GovernmentSharedManager167Api {
    private GovernmentSharedManager167Api() { }
    public interface Memory extends GovernmentPrimaryTail155Api.Memory {
        /** Atomically stores low8(old+low8(addend)) and returns old unsigned8. */
        int lockedXaddByte(long addressBits, int addendBits);
    }
}
