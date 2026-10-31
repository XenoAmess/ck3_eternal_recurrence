package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

/** Complete394 normal3727180, actual233 CALL373ADBD, explicitcalleeports. */
public final class PendingEmbedded32Copy3727180 {
    private PendingEmbedded32Copy3727180() { }
    public interface Memory {
        int read32(long address);
        long read64(long address);
        Bits128 read128(long address);
        void write32(long address,int value);
        void write64(long address,long value);
        void write128(long address,Bits128 value);
    }
    public interface Calls {
        void prepare889660(Memory memory,long rcx);
        long allocate(Memory memory,long target,long rcx,long rdx,int r8d);
        void replace8874D0(Memory memory,long rcx,long rdx,int r8d,int r9d);
        void virtualDestroy(Memory memory,long target,long rcx,long rdx);
        void copy37282B0(Memory memory,long rcx,long rdx);
        void finalize3727EC0(Memory memory,long rcx);
    }
    public static long copy(Memory memory,Calls calls,long destination,long source,long moduleBase) {
        long destinationHeader=destination+0x10;
        long sourceHeader=source+0x10;
        if (destinationHeader!=sourceHeader) {
            int sourceCount=memory.read32(sourceHeader+0xC);
            long sourceBuffer=memory.read64(sourceHeader);
            calls.prepare889660(memory,destinationHeader);
            int currentCount=memory.read32(destinationHeader+0xC);
            long token=moduleBase+0x448D230L;
            if (sourceCount>currentCount) {
                if (sourceCount>memory.read32(destinationHeader+8)) {
                    long allocator=memory.read64(destinationHeader+0x10);
                    long target=memory.read64(memory.read64(allocator)+8);
                    long replacement=calls.allocate(memory,target,allocator,Integer.toUnsignedLong(sourceCount)<<5,8);
                    int oldCount=memory.read32(destinationHeader+0xC);
                    if (oldCount>0) {
                        long oldBuffer=memory.read64(destinationHeader);
                        long from=oldBuffer,to=replacement;
                        for (int remaining=oldCount;remaining>0;remaining--) {
                            transfer32(memory,to,from,token);
                            from+=0x20;to+=0x20;
                        }
                        oldCount=memory.read32(destinationHeader+0xC);
                    }
                    calls.replace8874D0(memory,destinationHeader,replacement,oldCount,sourceCount);
                }
            } else {
                long end=((long)currentCount<<5)+memory.read64(destinationHeader);
                long at=((long)sourceCount<<5)+memory.read64(destinationHeader);
                while (at!=end) {
                    long target=memory.read64(memory.read64(at));
                    calls.virtualDestroy(memory,target,at,0);
                    at+=0x20;
                }
            }
            memory.write32(destinationHeader+0xC,sourceCount);
            if (sourceCount>0) {
                long to=memory.read64(destinationHeader),from=sourceBuffer;
                for (int remaining=sourceCount;remaining>0;remaining--) {
                    transfer32(memory,to,from,token);
                    from+=0x20;to+=0x20;
                }
            }
        }
        int tail=memory.read32(source+0x28);
        memory.write32(destination+0x28,tail);
        calls.copy37282B0(memory,destination+0x30,source+0x30);
        calls.finalize3727EC0(memory,destination);
        return destination;
    }
    private static void transfer32(Memory memory,long destination,long source,long token) {
        memory.write64(destination,token);
        int first=memory.read32(source+8);
        memory.write32(destination+8,first);
        int second=memory.read32(source+0xC);
        memory.write32(destination+0xC,second);
        Bits128 pair=memory.read128(source+0x10);
        memory.write128(destination+0x10,pair);
    }
}
