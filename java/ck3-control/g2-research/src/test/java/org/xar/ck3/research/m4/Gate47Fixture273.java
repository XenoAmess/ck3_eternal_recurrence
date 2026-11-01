package org.xar.ck3.research.m4;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Owner mechanical test-only byte storage and register constructors; no target algorithm/expected trace. */
final class Gate47Fixture273 {
    private Gate47Fixture273() { }
    record Write(long address, int bytes, long bits) { }
    static void qword(Map<Long,Byte> map,long address,long bits) {
        for(int i=0;i<8;i++) map.put(address+i,(byte)(bits >>> (8*i)));
    }
    static void dword(Map<Long,Byte> map,long address,int bits) {
        for(int i=0;i<4;i++) map.put(address+i,(byte)(bits >>> (8*i)));
    }
    static final class Memory implements GovernmentCrtBoundary185Api.Memory {
        final Map<Long,Byte> data=new LinkedHashMap<>();
        final List<Write> writes=new ArrayList<>();
        final List<Long> qwordReads=new ArrayList<>();
        Map<Long,Byte> snapshot(){ return Map.copyOf(data); }
        void put(long address,long bits){qword(data,address,bits);}
        @Override public int readUnsignedByte(long address){
            Byte b=data.get(address);if(b==null)throw new UnsupportedOperationException("unmapped byte "+Long.toHexString(address));return Byte.toUnsignedInt(b);
        }
        @Override public long readQword(long address){
            qwordReads.add(address);long n=0;for(int i=0;i<8;i++)n|=(long)readUnsignedByte(address+i)<<(8*i);return n;
        }
        @Override public int readDword(long address){int n=0;for(int i=0;i<4;i++)n|=readUnsignedByte(address+i)<<(8*i);return n;}
        @Override public void writeQword(long address,long bits){writes.add(new Write(address,8,bits));qword(data,address,bits);}
        @Override public void writeDword(long address,int bits){writes.add(new Write(address,4,Integer.toUnsignedLong(bits)));dword(data,address,bits);}
        @Override public void writeByte(long address,int bits){writes.add(new Write(address,1,bits&255));data.put(address,(byte)bits);}
        @Override public Bits128 read128(long address){return new Bits128(readQword(address),readQword(address+8));}
        @Override public void write128(long address,Bits128 bits){writeQword(address,bits.lowBits());writeQword(address+8,bits.highBits());}
        @Override public int lockedXaddDword(long address,int addend){throw new UnsupportedOperationException("unused atomic port");}
    }
    static VolatileBits v(long seed,long rax,long rcx,long rdx){
        return new VolatileBits(rax,rcx,rdx,seed+3,seed+4,seed+5,seed+6,
            new Bits128(seed+10,seed+11),new Bits128(seed+12,seed+13),new Bits128(seed+14,seed+15),
            new Bits128(seed+16,seed+17),new Bits128(seed+18,seed+19),new Bits128(seed+20,seed+21));
    }
    static VolatileBits rax(VolatileBits v,long rax){return new VolatileBits(rax,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    static VolatileBits rcx(VolatileBits v,long rcx){return new VolatileBits(v.raxBits(),rcx,v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    static NonvolatileBits n(long seed){return new NonvolatileBits(seed,seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,seed+7,new Bits128(seed+8,seed+9));}
    static NonvolatileBits rbx(NonvolatileBits n,long rbx){return new NonvolatileBits(rbx,n.rbpBits(),n.rsiBits(),n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    static NonvolatileBits rdi(NonvolatileBits n,long rdi){return new NonvolatileBits(n.rbxBits(),n.rbpBits(),n.rsiBits(),rdi,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    abstract static class Calls implements GovernmentCrtBoundary185Api.Calls {
        @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail t){throw new AssertionError("unexpected tail");}
        @Override public long readGsQword58(){throw new AssertionError("unexpected GS");}
    }
}
