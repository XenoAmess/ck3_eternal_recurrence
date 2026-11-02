package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner fixedsource new227 nongrowthblock andpure3CALLAPI boundaries; no full227 execution. */
public final class QueueAppendPartsBoundary597 {
    private QueueAppendPartsBoundary597() { }
    private static final long I=0x140000000L,E=0xC000L,D=0x30000L,L=I+0x5C9FF68L,RET=0xAABBCCDD11223344L;
    private static final Bits128 X6=new Bits128(0x61,0x62);
    private static final NonvolatileBits N=new NonvolatileBits(0x111,0x222,0x333,0x444,0x555,0x666,0x777,0x888,X6);
    private static void need(boolean ok,String why) { if(!ok)throw new AssertionError(why); }
    private static VolatileBits v(long seed) {
        return new VolatileBits(seed+1,seed+2,seed+3,seed+4,seed+5,seed+6,seed+7,
            new Bits128(seed+0x10,seed+0x11),new Bits128(seed+0x20,seed+0x21),new Bits128(seed+0x30,seed+0x31),
            new Bits128(seed+0x40,seed+0x41),new Bits128(seed+0x50,seed+0x51),new Bits128(seed+0x60,seed+0x61));
    }
    private static VolatileBits change(VolatileBits v,long a,long c,long d) {
        return new VolatileBits(a,c,d,v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static NonvolatileBits n(long b) {return new NonvolatileBits(b,N.rbpBits(),N.rsiBits(),N.rdiBits(),N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());}
    private static GovernmentCrtBoundary185Api.Entry entry(VolatileBits v) {return new GovernmentCrtBoundary185Api.Entry(I,E,v,N);}
    private static FullCopy437Api.CallResult result(VolatileBits v,NonvolatileBits n,long rip,long sp,boolean df) {
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,rip,sp,n),df);
    }
    private static String mem(String op,int width,long address,long value) {return op+width+"@"+Long.toHexString(address)+"="+Long.toHexString(value);}
    private static class Ram implements QueueAppend597Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<String> trace;int cursor;
        Ram(String...events){trace=List.of(events);}
        void event(String value){need(cursor<trace.size()&&trace.get(cursor).equals(value),"event"+cursor+" got"+value+" expected"+(cursor<trace.size()?trace.get(cursor):"END"));cursor++;}
        static void put(Map<Long,Byte> map,int width,long a,long x){for(int j=0;j<width;j++)map.put(a+j,(byte)(x>>>(8*j)));}
        void seed(int w,long a,long x){put(bytes,w,a,x);}
        long raw(int w,long a){long x=0;for(int j=0;j<w;j++){Byte b=bytes.get(a+j);need(b!=null,"unseeded"+Long.toHexString(a+j));x|=Byte.toUnsignedLong(b)<<(8*j);}return x;}
        long read(int w,long a){long x=raw(w,a);event(mem("R",w,a,x));return x;}
        void write(int w,long a,long x){if(w<8)x&=(1L<<(w*8))-1;event(mem("W",w,a,x));seed(w,a,x);}
        public int readUnsignedByte(long a){return (int)read(1,a);}
        public int readDword(long a){return (int)read(4,a);}
        public long readQword(long a){return read(8,a);}
        public void writeByte(long a,int x){write(1,a,x&0xFFL);}
        public void writeDword(long a,int x){write(4,a,Integer.toUnsignedLong(x));}
        public void writeQword(long a,long x){write(8,a,x);}
        void end(){need(cursor==trace.size(),"all events consumed");}
        public int readUnsignedWord(long a){throw new AssertionError("unusedWORD");}
        public void writeWord(long a,int x){throw new AssertionError("unusedWORD");}
        public Bits128 read128(long a){throw new AssertionError("unused128");}
        public void write128(long a,Bits128 x){throw new AssertionError("unused128");}
        public int lockedXaddDword(long a,int x){throw new AssertionError("unusedXADD");}
        public void write128NonTemporal(long a,Bits128 x){throw new AssertionError("unusedNT");}
        public FullCopy437Api.Bits256 read256(long a){throw new AssertionError("unused256");}
        public void write256(long a,FullCopy437Api.Bits256 x){throw new AssertionError("unused256");}
        public void write256NonTemporal(long a,FullCopy437Api.Bits256 x){throw new AssertionError("unused256");}
        public void sfence(){throw new AssertionError("unusedFENCE");}
    }
    private static final long[][][] INITIAL={
        {{0x8L,0x30000L,0x50000L},{0x4L,0x3000cL,0x1L},{0x8L,0x41000L,0xf0e0d0c0b0a09080L}},
        {{0x8L,0x30000L,0x2fff8L},{0x4L,0x3000cL,0x1L},{0x8L,0x41000L,0x22334455667788efL}},
        {{0x8L,0x30000L,0x30014L},{0x4L,0x3000cL,0xffffffffL},{0x8L,0x41000L,0x11223344ffffffffL}},
        {{0x8L,0x110000030000L,0x330000050000L},{0x4L,0x11000003000cL,0x1L},{0x8L,0x220000041000L,0x123456789abcdef0L}}
    };
    private static final String[][] EVENTS={
        {"R8@30000=50000","R8@41000=f0e0d0c0b0a09080","W8@50008=f0e0d0c0b0a09080","R4@3000c=1","W4@3000c=2","R4@3000c=2","R8@30000=50000"},
        {"R8@30000=2fff8","R8@41000=22334455667788ef","W8@30000=22334455667788ef","R4@3000c=1","W4@3000c=2","R4@3000c=2","R8@30000=22334455667788ef"},
        {"R8@30000=30014","R8@41000=11223344ffffffff","W8@3000c=11223344ffffffff","R4@3000c=ffffffff","W4@3000c=0","R4@3000c=0","R8@30000=30014"},
        {"R8@110000030000=330000050000","R8@220000041000=123456789abcdef0","W8@330000050008=123456789abcdef0","R4@11000003000c=1","W4@11000003000c=2","R4@11000003000c=2","R8@110000030000=330000050000"}
    };
    private static final long[][] BANKS={
        {0x30000L,0x41000L,0x1L,0xf0e0d0c0b0a09080L,0x50000L,0x1L,0x2L,0x50000L},
        {0x30000L,0x41000L,0x1L,0x22334455667788efL,0x2fff8L,0x1L,0x2L,0x22334455667788efL},
        {0x30000L,0x41000L,0xffffffffffffffffL,0x11223344ffffffffL,0x30014L,0xffffffffffffffffL,0x0L,0x30014L},
        {0x110000030000L,0x220000041000L,0x1L,0x123456789abcdef0L,0x330000050000L,0x1L,0x2L,0x330000050000L}
    };
    private static Map<Long,Byte> expected(Ram ram,String[] events){
        Map<Long,Byte> result=new HashMap<>(ram.bytes);
        for(String s:events)if(s.startsWith("W")){int at=s.indexOf('@'),eq=s.indexOf('=');Ram.put(result,Integer.parseInt(s.substring(1,at)),Long.parseUnsignedLong(s.substring(at+1,eq),16),Long.parseUnsignedLong(s.substring(eq+1),16));}
        else if(s.startsWith("CAS@")){String[] p=s.substring(4).split(":");if(p[1].equals(p[3]))Ram.put(result,4,Long.parseUnsignedLong(p[0],16),Long.parseUnsignedLong(p[2],16));}
        return result;
    }

    private static NonvolatileBits bank(long c,long p,long si,long di) {
        return new NonvolatileBits(c,N.rbpBits(),si,di,N.r12Bits(),N.r13Bits(),p,N.r15Bits(),N.xmm6());
    }
    private static void block(int index) {
        Ram ram=new Ram(EVENTS[index]);for(long[] c:INITIAL[index])ram.seed((int)c[0],c[1],c[2]);
        Map<Long,Byte> bytes=expected(ram,EVENTS[index]);long[] bits=BANKS[index];
        // Current blockSP is E; the whole native entry would have been E+28.
        // RCX is a different capacity and RDX remains the entry elementPointer before this block.
        var before=change(v(0x1000),bits[2],0x1002,bits[1]);var beforeN=bank(bits[0],bits[1],0x333,0x444);
        var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,E,before,beforeN));
        QueueAppendNonGrowthBlock597.append(r,ram);
        need(r.volatileBits().equals(change(v(0x1000),bits[3],bits[4],bits[5])),"actual7instruction fullvolatilebank"+index);
        need(r.nonvolatileBits().equals(bank(bits[0],bits[1],bits[6],bits[7]))&&r.rsp==E,"intermediateRSI/RDI plusotherN/XMM/SP"+index);
        ram.end();need(ram.bytes.equals(bytes),"allfixedRAM bytes"+index);
    }
    private static QueueAppend597Api.CallFrame frame(long site,GovernmentCrtBoundary185Api.TargetKind kind,long target,int len,long sp,VolatileBits v,NonvolatileBits n,long rip) {
        var call=new GovernmentCrtBoundary185Api.Call(site,kind,target,E-0x28,v,n);
        return new QueueAppend597Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,sp,v,n),true,len,rip);
    }
    private static void legalFrames(){
        long[] sites={0x88039F,0x8803C5,0x8803DA},targets={0xABCD0000L,0x4226860L,0xBCDE0000L};int[] lengths={3,5,3};
        for(int index=0;index<3;index++){
            long site=sites[index],rip=I+site+lengths[index];var kind=index==1?GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA:GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE;
            var offered=v(0x2000+index*0x100);var f=frame(site,kind,targets[index],lengths[index],E-0x30,offered,N,rip);
            need(f.call().targetBits()==targets[index]&&f.childEntry().volatileBits().equals(offered)&&f.directionFlagSet(),"fullsource Frame values carried");
            var actual=result(v(0x9000),N,rip,E-0x28,false);f.checkNormalReturn(actual);
            QueueAppend597Api.Calls calls=got->{need(got==f,"sameAPIframe");return actual;};
            need(calls.invoke(f)==actual&&!actual.postDirectionFlagSet(),"unchangedactualresult allowedpostDFchange");
        }
    }
    private static void reject(Runnable operation){
        try{operation.run();}catch(IllegalArgumentException expected){return;}
        throw new AssertionError("malformedsourceframe mustreject");
    }
    private static void invalidFrames(){
        long site=0x8803C5,rip=I+0x8803CA;var offered=v(0x2000);var direct=GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
        reject(()->frame(site,direct,0x4226861,5,E-0x30,offered,N,rip));
        reject(()->frame(0x88039F,direct,0xABCD0000L,3,E-0x30,offered,N,I+0x8803A2));
        reject(()->frame(site,direct,0x4226860,3,E-0x30,offered,N,rip));
        reject(()->frame(site,direct,0x4226860,5,E-0x28,offered,N,rip));
        reject(()->frame(0x8803D9,direct,0x4226860,5,E-0x30,offered,N,I+0x8803DE));
        var call=new GovernmentCrtBoundary185Api.Call(site,direct,0x4226860,E-0x28,offered,N);
        reject(()->new QueueAppend597Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,E-0x30,v(0x3000),N),true,5,rip));
        reject(()->new QueueAppend597Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(I,E-0x30,offered,n(0xAAA)),true,5,rip));
        var f=frame(site,direct,0x4226860,5,E-0x30,offered,N,rip);
        reject(()->f.checkNormalReturn(result(v(0x9000),N,rip+1,E-0x28,false)));
        reject(()->f.checkNormalReturn(result(v(0x9000),N,rip,E-0x20,false)));
        reject(()->f.checkNormalReturn(result(v(0x9000),n(0xAAA),rip,E-0x28,false)));
    }
    public static int verify(){block(0);block(1);block(2);block(3);legalFrames();invalidFrames();return 6;}
    public static void main(String[] args){System.out.println(verify());}
}
