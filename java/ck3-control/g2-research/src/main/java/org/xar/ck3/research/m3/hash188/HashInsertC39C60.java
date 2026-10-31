package org.xar.ck3.research.m3.hash188;

import org.xar.ck3.research.m3.hash188.HashInsert188Api.Bytes16;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.Input;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.Memory;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.Ports;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.Scratch;
import org.xar.ck3.research.m3.hash188.HashInsert188Api.UnprojectedInt3;

/** Owner normal projection of all814 original bytes; opaque bodies/CPU state/EH remain unclaimed. */
public final class HashInsertC39C60 {
    private HashInsertC39C60() { }

    public static long execute(Input in, Memory m, Ports p) {
        long map=in.map(), output=in.output(), descriptor=in.descriptor();
        long rbp=in.scratch().bodyRsp()+0x70L;
        int mask=m.readInt32(map+0x14L);
        long index=((long)mask)&((long)in.hash());
        long data=m.readPointer(map+8L);
        long bucket=data+(index+index*4L)*8L;
        int probe=1;
        int first=m.readUnsigned8(bucket+4L);
        if(first>=probe) {
            long descriptorCapacity=m.readPointer(descriptor+0x18L);
            while(true) {
                long bucketCapacity=m.readPointer(bucket+0x20L);
                long right=bucket+8L;
                if(Long.compareUnsigned(bucketCapacity,0x10L)>=0) right=m.readPointer(right);
                long left=descriptor;
                if(Long.compareUnsigned(descriptorCapacity,0x10L)>=0) left=m.readPointer(descriptor);
                if((p.equal3f6d2b0(m,0xC39CCAL,left,right)&0xFF)!=0) {
                    m.writeInt64(output,bucket);
                    m.write8(output+8L,0);
                    return output;
                }
                bucket+=0x28L;
                probe=(probe+1)&0xFF;
                int next=m.readUnsigned8(bucket+4L);
                if(probe>next) break;
            }
            mask=m.readInt32(map+0x14L);
        }
        int maximum=m.readUnsigned8(map+0x18L);
        if(probe>maximum) return grow(in,m,p,mask,rbp);
        int nextCount=m.readInt32(map+0x10L)+1;
        float ratio=((float)nextCount)/((float)mask);
        float limit=Float.intBitsToFloat(m.readInt32(map+0x1CL));
        if(ratio>limit) return grow(in,m,p,mask,rbp);

        int occupied=m.readUnsigned8(bucket+4L);
        long destination=bucket+8L;
        if(occupied==0) {
            m.writeInt32(bucket,in.hash());
            m.write8(bucket+4L,probe);
            p.copy855f00(m,0xC39D27L,destination,descriptor);
            return inserted(in,m,bucket);
        }
        int oldHash=m.readInt32(bucket);
        int displacedProbe=(occupied+1)&0xFF;
        int nextOccupied=m.readUnsigned8(bucket+0x2CL);
        if(nextOccupied==0) {
            m.writeInt32(bucket+0x28L,oldHash);
            m.write8(bucket+0x2CL,displacedProbe);
            m.writeInt64(bucket+0x30L,0);
            m.writeInt64(bucket+0x40L,0);
            m.writeInt64(bucket+0x48L,0);
            Bytes16 firstHalf=m.read128(destination);
            m.write128(bucket+0x30L,firstHalf);
            Bytes16 secondHalf=m.read128(destination+0x10L);
            m.write128(bucket+0x40L,secondHalf);
            m.writeInt64(destination+0x10L,0);
            m.writeInt64(destination+0x18L,0x0FL);
            m.write8(destination,0);
            m.writeInt32(bucket,in.hash());
            m.write8(bucket+4L,probe);
            assignIfDifferent(m,p,0xC39DA4L,destination,descriptor);
            return inserted(in,m,bucket);
        }

        long scratchHash=rbp-0x30L, scratchProbe=rbp-0x2CL;
        long scratchLow=rbp-0x28L, scratchHigh=rbp-0x18L;
        m.writeInt32(scratchHash,oldHash);
        m.write8(scratchProbe,displacedProbe);
        Bytes16 firstHalf=m.read128(destination);
        m.write128(scratchLow,firstHalf);
        Bytes16 secondHalf=m.read128(destination+0x10L);
        m.write128(scratchHigh,secondHalf);
        m.writeInt64(destination+0x10L,0);
        m.writeInt64(destination+0x18L,0x0FL);
        m.write8(destination,0);
        m.writeInt32(bucket,in.hash());
        m.write8(bucket+4L,probe);
        assignIfDifferent(m,p,0xC39DFBL,destination,descriptor);

        int carriedProbe=m.readUnsigned8(scratchProbe);
        long originalBucket=bucket;
        while(true) {
            int nextProbe=m.readUnsigned8(bucket+0x2CL);
            bucket+=0x28L;
            if(nextProbe==0) {
                int carriedHash=m.readInt32(scratchHash);
                m.write8(bucket+4L,carriedProbe);
                m.writeInt32(bucket,carriedHash);
                m.writeInt64(bucket+8L,0);
                m.writeInt64(bucket+0x18L,0);
                m.writeInt64(bucket+0x20L,0);
                Bytes16 low=m.read128(scratchLow);
                m.write128(bucket+8L,low);
                Bytes16 high=m.read128(scratchHigh);
                Bytes16 empty=m.read128(in.moduleBase()+0x49F6EE0L);
                m.write128(bucket+0x18L,high);
                m.write8(scratchLow,0);
                m.write128(scratchHigh,empty);
                p.destroy856050(m,0xC39F15L,scratchLow);
                return inserted(in,m,originalBucket);
            }
            if(nextProbe<carriedProbe) {
                swap(m,bucket,scratchHash,scratchProbe,scratchLow,scratchHigh);
                carriedProbe=(m.readUnsigned8(scratchProbe)+1)&0xFF;
                m.write8(scratchProbe,carriedProbe);
                continue;
            }
            carriedProbe=(carriedProbe+1)&0xFF;
            m.write8(scratchProbe,carriedProbe);
            int currentMaximum=m.readUnsigned8(map+0x18L);
            if(carriedProbe<=currentMaximum) continue;

            swap(m,originalBucket,scratchHash,scratchProbe,scratchLow,scratchHigh);
            p.rehashC3a400(m,0xC39EADL,map);
            int reinsertHash=m.readInt32(scratchHash);
            long result=rbp-0x40L;
            p.insertC3b960(m,0xC39EC1L,map,result,reinsertHash,scratchLow);
            p.destroy856050(m,0xC39ECAL,scratchLow);
            Bytes16 copiedResult=m.read128(result);
            m.write128(output,copiedResult);
            return output;
        }
    }

    private static void assignIfDifferent(Memory m, Ports p, long site, long destination, long descriptor) {
        if(destination==descriptor) return;
        long capacity=m.readPointer(descriptor+0x18L);
        long count=m.readPointer(descriptor+0x10L);
        long source=descriptor;
        if(Long.compareUnsigned(capacity,0x10L)>=0) source=m.readPointer(descriptor);
        p.assign855db0(m,site,destination,source,count);
    }

    private static void swap(Memory m, long bucket, long scratchHash, long scratchProbe,
                             long scratchLow, long scratchHigh) {
        int oldHash=m.readInt32(bucket);
        int carriedHash=m.readInt32(scratchHash);
        m.writeInt32(scratchHash,oldHash);
        int oldProbe=m.readUnsigned8(bucket+4L);
        m.writeInt32(bucket,carriedHash);
        int carriedProbe=m.readUnsigned8(scratchProbe);
        m.write8(scratchProbe,oldProbe);
        m.write8(bucket+4L,carriedProbe);
        Bytes16 low=m.read128(bucket+8L);
        Bytes16 carriedLow=m.read128(scratchLow);
        Bytes16 carriedHigh=m.read128(scratchHigh);
        m.write128(scratchLow,low);
        Bytes16 high=m.read128(bucket+0x18L);
        m.write128(scratchHigh,high);
        m.write128(bucket+8L,carriedLow);
        m.write128(bucket+0x18L,carriedHigh);
    }

    private static long inserted(Input in, Memory m, long bucket) {
        int count=m.readInt32(in.map()+0x10L);
        m.writeInt32(in.map()+0x10L,count+1);
        m.writeInt64(in.output(),bucket);
        m.write8(in.output()+8L,1);
        return in.output();
    }

    private static long grow(Input in, Memory m, Ports p, int currentMask, long rbp) {
        int capacity=p.capacity86e160(m,0xC39F2FL,currentMask+1,1);
        if(capacity>=0x1F) {
            p.overflow86f210(m,0xC39F83L,rbp+0x40L,in.map());
            p.terminal4232cf4(m,0xC39F88L);
            throw new UnprojectedInt3();
        }
        p.reserveC3b700(m,0xC39F3EL,in.map(),capacity);
        long fifth=rbp+0x50L;
        m.write8(fifth,0);
        m.writeInt64(in.scratch().bodyRsp()+0x20L,fifth);
        execute(new Input(in.moduleBase(),in.map(),in.output(),in.hash(),in.descriptor(),
                          new Scratch(in.scratch().bodyRsp()-0xB0L)),m,p);
        return in.output();
    }
}
