package org.xar.ck3.study.m6.provider222;

import org.xar.ck3.study.m6.vtable221.VirtualForward221Api.Memory;

public final class ObjectProvider86e140 {
    private ObjectProvider86e140() { }

    public static long readReturnedObject(long rcxRaw64, Memory memory) {
        return memory.read64(rcxRaw64 + 0x408);
    }
}