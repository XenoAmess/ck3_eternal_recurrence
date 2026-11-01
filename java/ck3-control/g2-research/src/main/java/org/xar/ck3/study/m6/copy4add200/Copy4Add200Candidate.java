package org.xar.ck3.study.m6.copy4add200;

import org.xar.ck3.study.m6.element172.Element172Inputs;

public final class Copy4Add200Candidate {
    private Copy4Add200Candidate() { }

    public static void apply(Copy4Add200Inputs.Input input, Element172Inputs.Memory memory,
                             Copy4Add200Inputs.Calls calls) {
        long header=input.headerRaw64(), begin=input.beginRaw64(), end=input.endRaw64();
        if (begin==end) return;
        long oldSize=memory.read32(header+12);
        long bytes=end-begin;
        long index=(int)input.indexRaw64();
        int capacity=memory.read32(header+8);
        long count=bytes>>2;
        int newSize=(int)(oldSize+count);
        if (newSize<=capacity) {
            long base=memory.read64(header);
            calls.copy4226860(base+oldSize*4,begin,bytes);
            long currentSize=memory.read32(header+12);
            long currentBase=memory.read64(header);
            int updatedSize=(int)(currentSize+count);
            memory.write32(header+12,updatedSize);
            calls.range9d0950(currentBase+index*4,currentBase+currentSize*4,
                    currentBase+(long)updatedSize*4,currentBase);
            return;
        }

        float grown=(float)capacity*1.5f;
        int converted;
        if (Float.isNaN(grown) || grown>=2147483648.0f || grown< -2147483648.0f) {
            converted=Integer.MIN_VALUE;
        } else {
            converted=(int)grown;
        }
        long allocator=memory.read64(header+16);
        int newCapacity=newSize<converted ? converted : newSize;
        long vtable=memory.read64(allocator);
        long allocationBytes=Integer.toUnsignedLong(newCapacity)<<2;
        long allocationTarget=memory.read64(vtable+8);
        long newBase=calls.virtual8(allocationTarget,allocator,allocationBytes,4,end);

        long oldBase=memory.read64(header);
        long indexBytes=index*4;
        calls.copy4226860(newBase,oldBase,indexBytes);
        calls.copy4226860(newBase+indexBytes,begin,bytes);

        long currentBase=memory.read64(header);
        long currentSize=memory.read32(header+12);
        long sourceTail=currentBase+indexBytes;
        long tailBytes=(currentSize<<2)-sourceTail+currentBase;
        long destinationTail=newBase+((long)(int)count+index)*4;
        calls.copy4226860(destinationTail,sourceTail,tailBytes);

        long currentAllocator=memory.read64(header+16);
        long releasedBase=memory.read64(header);
        long currentVtable=memory.read64(currentAllocator);
        long releaseTarget=memory.read64(currentVtable+16);
        calls.virtual16(releaseTarget,currentAllocator,releasedBase,4);
        memory.write64(header,newBase);
        memory.write32(header+8,newCapacity);
        memory.write32(header+12,newSize);
    }
}
