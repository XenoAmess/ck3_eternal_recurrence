package org.xar.ck3.research.m3.index183;

import org.xar.ck3.research.m3.index183.RegistrationIndex183Api.*;

/** Complete original normal397B storage and EAX projection; comparator remains an explicit port. */
public final class RegistrationIndex3F542C0 {
    private RegistrationIndex3F542C0() { }
    public static int find(Memory memory,Ports ports,Input input) {
        long stack=input.scratch().bodyRsp();
        long key=input.keyDescriptor();
        memory.writeInt64(stack+0x88L,key);
        long originalBase=memory.readPointer(input.receiver());
        long remaining=memory.readInt32(input.receiver()+0xCL);
        long end=originalBase+(remaining<<6);
        long candidate=originalBase;
        memory.writeInt64(stack+0x90L,end);
        if(remaining>0) {
            Bytes16 snapshot=memory.read128(key);
            memory.write128(stack+0x20L,snapshot);
            int capturedLength=memory.readInt32(stack+0x28L);
            long capturedData=memory.readPointer(stack+0x20L);
            do {
                long half=remaining>>>1;
                long record=candidate+(half<<6);
                long successor=candidate+((remaining-half)<<6);
                remaining=half;
                long capacity=memory.readPointer(record+0x18L);
                int recordLength=memory.readInt32(record+0x10L);
                long recordData=record;
                if(Long.compareUnsigned(capacity,0x10L)>=0)recordData=memory.readPointer(record);
                int minimum=capturedLength<recordLength?capturedLength:recordLength;
                int compared=ports.compare42270b0(memory,0x3F5436AL,recordData,capturedData,(long)minimum);
                if(compared==0)compared=Integer.compare(recordLength,capturedLength);
                if(compared<0)candidate=successor;
            }while(remaining!=0);
            end=memory.readPointer(stack+0x90L);
            key=memory.readPointer(stack+0x88L);
        }
        if(candidate==end)return -1;
        long capacity=memory.readPointer(candidate+0x18L);
        int recordLength=memory.readInt32(candidate+0x10L);
        long recordData=candidate;
        if(Long.compareUnsigned(capacity,0x10L)>=0)recordData=memory.readPointer(candidate);
        Bytes16 freshKey=memory.read128(key);
        memory.writeInt64(stack+0x20L,recordData);
        memory.writeInt32(stack+0x28L,recordLength);
        memory.write8(stack+0x2CL,0);
        Bytes16 recordSnapshot=memory.read128(stack+0x20L);
        memory.write128(stack+0x20L,recordSnapshot);
        int freshKeyLength=(int)freshKey.high();
        memory.write128(stack+0x30L,freshKey);
        long minimumAddress=recordLength<freshKeyLength?stack+0x28L:stack+0x38L;
        long signedLength=memory.readInt32(minimumAddress);
        int compared=ports.compare42270b0(memory,0x3F5441CL,freshKey.low(),recordData,signedLength);
        if(compared<0||(compared==0&&freshKeyLength<recordLength))return -1;
        return (int)((candidate-originalBase)>>6);
    }
}
