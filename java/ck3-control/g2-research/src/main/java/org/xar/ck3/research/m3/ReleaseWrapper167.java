package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class ReleaseWrapper167 {
    private ReleaseWrapper167() {}
    public static long apply(NativeTaskMemory memory,ReleaseApi167.Ports ports,
        long receiver,long rows,long alignment,long incomingR9) {
        long inlineRows=receiver+8;
        if (rows==inlineRows) return inlineRows;
        long entryVptr=memory.readPointer(receiver);
        long firstTarget=memory.readPointer(entryVptr+0x38);
        long returnedReceiver=ports.slot38(memory,firstTarget,receiver,rows,alignment,incomingR9);
        long returnedVptr=memory.readPointer(returnedReceiver);
        long releaseTarget=memory.readPointer(returnedVptr+0x10);
        return ports.release10(memory,releaseTarget,returnedReceiver,rows,alignment,returnedVptr);
    }
}
