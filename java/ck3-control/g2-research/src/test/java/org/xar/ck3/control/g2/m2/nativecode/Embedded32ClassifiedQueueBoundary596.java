package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner newactual394->103->81 wholecases; fixed independent originalsource literals. */
public final class Embedded32ClassifiedQueueBoundary596 {
    private Embedded32ClassifiedQueueBoundary596() { }
    private static final long I=0x140000000L,E=0xB000L,D=0x28000L,L=I+0x5C9FF68L,RET=0xAABBCCDD11223344L;
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
    private static class Ram implements EmbeddedQueue591Api.Memory {
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
        public int compareExchangeDword(long a,int expected,int desired){
            int old=(int)raw(4,a);event("CAS@"+Long.toHexString(a)+":"+Integer.toUnsignedString(expected,16)+":"+Integer.toUnsignedString(desired,16)+":"+Integer.toUnsignedString(old,16));
            if(old==expected)seed(4,a,Integer.toUnsignedLong(desired));return old;
        }
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
        {{0x8L,0xb000L,0xaabbccdd11223344L},{0x4L,0x28028L,0x3L},{0x1L,0x2804eL,0x0L},{0x4L,0x2801cL,0xffffffffL},{0x8L,0x28010L,0x22334455667788efL},{0x4L,0x22334455667788bbL,0x0L},{0x4L,0x28048L,0x9L}},
        {{0x8L,0xb000L,0xaabbccdd11223344L},{0x4L,0x28028L,0x3L},{0x1L,0x2804eL,0x0L},{0x4L,0x2801cL,0x0L},{0x8L,0x28030L,0x55000L},{0x4L,0x2803cL,0x2L},{0x1L,0x55044L,0x0L},{0x1L,0x5508cL,0x0L},{0x4L,0x28048L,0x5L},{0x4L,0x145c9ff68L,0x0L}},
        {{0x8L,0xb000L,0xaabbccdd11223344L},{0x4L,0x28028L,0x3L},{0x1L,0x2804eL,0x0L},{0x4L,0x2801cL,0x0L},{0x8L,0x28030L,0x0L},{0x4L,0x2803cL,0x1L},{0x1L,0x44L,0x80L},{0x4L,0x28048L,0xffffffffL}},
        {{0x8L,0xb000L,0xaabbccdd11223344L},{0x4L,0x28028L,0x3L},{0x1L,0x2804eL,0x0L},{0x4L,0x2801cL,0x0L},{0x8L,0x28030L,0x0L},{0x4L,0x2803cL,0x1L},{0x1L,0x44L,0x80L}}
    };
    private static final String[][] EVENTS={
        {"W8@aff8=333","W8@aff0=777","W8@afe8=888","R4@28028=3","W4@28028=3","W8@afb0=1437272f5","F0","W8@afb0=1437272fd","W8@afa8=111","R1@2804e=0","W8@af80=143727ed4","R4@2801c=ffffffff","R4@2801c=ffffffff","R8@28010=22334455667788ef","R4@22334455667788bb=0","R8@af80=143727ed4","R4@28048=9","R8@afa8=111","R8@afb0=1437272fd","R8@afe8=888","R8@aff0=777","R8@aff8=333","R8@b000=aabbccdd11223344"},
        {"W8@aff8=333","W8@aff0=777","W8@afe8=888","R4@28028=3","W4@28028=3","W8@afb0=1437272f5","F0","W8@afb0=1437272fd","W8@afa8=111","R1@2804e=0","W8@af80=143727ed4","R4@2801c=0","R8@28030=55000","R4@2803c=2","B@37275b0:55000","R1@55044=0","B@37275b0:55048","R1@5508c=0","R8@af80=143727ed4","R4@28048=5","B@3727ee4:145c9ff68","R4@145c9ff68=0","CAS@145c9ff68:0:1:0","W8@afc0=28000","W8@af80=143727f12","ENQUEUE","W8@aff8=7777","W8@b000=1020304050607080","W1@2804e=1","W4@145c9ff68=0","R8@afa8=111","R8@afb0=1437272fd","R8@afe8=888","R8@aff0=777","R8@aff8=7777","R8@b000=1020304050607080"},
        {"W8@aff8=333","W8@aff0=777","W8@afe8=888","R4@28028=3","W4@28028=3","W8@afb0=1437272f5","F0","W8@afb0=1437272fd","W8@afa8=111","R1@2804e=0","W8@af80=143727ed4","R4@2801c=0","R8@28030=0","R4@2803c=1","B@37275b0:0","R1@44=80","R8@af80=143727ed4","R4@28048=ffffffff","R8@afa8=111","R8@afb0=1437272fd","R8@afe8=888","R8@aff0=777","R8@aff8=333","R8@b000=aabbccdd11223344"},
        {"W8@aff8=333","W8@aff0=777","W8@afe8=888","R4@28028=3","W4@28028=3","W8@afb0=1437272f5","F0","W8@afb0=1437272fd","W8@afa8=111","R1@2804e=0","W8@af80=143727ed4","R4@2801c=0","R8@28030=0","R4@2803c=1","B@37275b0:0","W8@af80=deadbeef11223344","R1@44=80","R8@af80=deadbeef11223344"}
    };
    private static final long[][] FINAL={
        {0x3000L,0x28000L,0x28000L,0xffffffffffffff01L,0x333L,0xaabbccdd11223344L ,1L},
        {0x7000L,0x28000L,0x7002L,0x7003L,0x7777L,0x1020304050607080L ,0L},
        {0x3000L,0x28000L,0x48L,0x0L,0x333L,0xaabbccdd11223344L ,1L}
    };
    private static Map<Long,Byte> expected(Ram ram,String[] events){
        Map<Long,Byte> result=new HashMap<>(ram.bytes);
        for(String s:events)if(s.startsWith("W")){int at=s.indexOf('@'),eq=s.indexOf('=');Ram.put(result,Integer.parseInt(s.substring(1,at)),Long.parseUnsignedLong(s.substring(at+1,eq),16),Long.parseUnsignedLong(s.substring(eq+1),16));}
        else if(s.startsWith("CAS@")){String[] p=s.substring(4).split(":");if(p[1].equals(p[3]))Ram.put(result,4,Long.parseUnsignedLong(p[0],16),Long.parseUnsignedLong(p[2],16));}
        return result;
    }

    private static final long BAD=0xDEADBEEF11223344L;
    private static NonvolatileBits fields(long b,long si,long r14,long r15) {
        return new NonvolatileBits(b,N.rbpBits(),si,N.rdiBits(),N.r12Bits(),N.r13Bits(),r14,r15,N.xmm6());
    }
    private static NonvolatileBits parentN(){return fields(N.rbxBits(),D+0x10,D,D);}
    private static NonvolatileBits queueN(){return fields(D,D+0x10,D,D);}
    private static VolatileBits input(){return change(v(0x1000),0x1001,D,D);}
    private static void whole(int index) {
        Ram ram=new Ram(EVENTS[index]);
        for(long[] cell:INITIAL[index])ram.seed((int)cell[0],cell[1],cell[2]);
        Map<Long,Byte> bytes=expected(ram,EVENTS[index]);
        int[] parentCalls={0},enqueues={0};
        GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{
            ram.event("B@"+Long.toHexString(header)+":"+Long.toHexString(guard));
            if(index==3){need(header==0x37275B0L&&guard==0,"originalnestedbudget sourceheader");ram.writeQword(E-0x80,BAD);}
        };
        var top=new FullCopy437Api.Input(entry(input()),false,budget);
        Embedded32Copy581Api.Calls foreign=f->{
            need(parentCalls[0]++==0,"oneforeign322call only");ram.event("F0");
            var before=change(input(),3,D+0x30,D+0x30);var offered=parentN();
            need(f.call().equals(new GovernmentCrtBoundary185Api.Call(0x37272F0L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x37282B0L,E-0x48,before,offered)),"complete394foreignframe currentV/N");
            need(f.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(I,E-0x50,before,offered))&&!f.directionFlagSet()&&f.instructionLength()==5&&f.returnRipBits()==I+0x37272F5L,"foreignactualchild SP/DF/RF");
            need(ram.raw(8,E-0x50)==I+0x37272F5L,"one physicalouterpush");
            return result(v(0x3000),offered,f.returnRipBits(),f.call().rspBits(),true);
        };
        EmbeddedQueue591Api.Calls enqueue=f->{
            need(index==1&&enqueues[0]++==0,"onlyoneopaqueenqueue, classifierisactual");ram.event("ENQUEUE");
            var before=change(v(0x3000),0,I+0x5468A68L,E-0x40);var offered=queueN();
            need(f.call().equals(new GovernmentCrtBoundary185Api.Call(0x3727F0DL,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x880340L,E-0x78,before,offered)),"fullnested enqueueframe currentN andV");
            need(f.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(I,E-0x80,before,offered))&&f.directionFlagSet()&&f.instructionLength()==5&&f.returnRipBits()==I+0x3727F12L,"enqueueactualSP/DF/RET");
            need(ram.raw(8,E-0x80)==I+0x3727F12L&&ram.raw(8,E-0x40)==D,"sameRAM nestedCALL andargument");
            ram.writeQword(E-8,0x7777);ram.writeQword(E,0x1020304050607080L);
            return result(v(0x7000),offered,f.returnRipBits(),f.call().rspBits(),false);
        };
        if(index==3){
            try{Embedded32WithKnownClassifiedQueue596.execute(top,ram,foreign,enqueue);throw new AssertionError("badfreshRET mustreject");}
            catch(IllegalArgumentException ex){need("Return RIP mismatch".equals(ex.getMessage()),"actual591normalreturnguard sourcefailure");}
        }else{
            var actual=Embedded32WithKnownClassifiedQueue596.execute(top,ram,foreign,enqueue);
            long[] finalBits=FINAL[index];
            var finalV=change(v(finalBits[0]),finalBits[1],finalBits[2],finalBits[3]);
            var finalN=fields(N.rbxBits(),finalBits[4],N.r14Bits(),N.r15Bits());
            need(actual.equals(result(finalV,finalN,finalBits[5],E+8,finalBits[6]!=0)),"complete394/103/81 finalV/N/XMM/DF/freshhomes/RET case"+index);
        }
        need(parentCalls[0]==1&&enqueues[0]==(index==1?1:0),"no hiddenfallback or spuriouscallback");
        ram.end();need(ram.bytes.equals(bytes),"allownedRAM bytes case"+index);
    }
    private static void foreignIdentity(){
        long image=I+0x70000,sp=0x8C00;var offered=v(0x6000);var offeredN=n(0xAAA);
        var call=new GovernmentCrtBoundary185Api.Call(0x37272F0L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x37282B0L,sp+8,offered,offeredN);
        var frame=new Embedded32Copy581Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(image,sp,offered,offeredN),true,5,image+0x37272F5L);
        var marker=result(v(0x9000),N,0x1234,0x5678,false);Ram ram=new Ram();int[] count={0};
        var wrongTop=new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I+0x90000,0x900000,v(0xA000),N),false,(h,g)->{throw new AssertionError("foreignnobudget");});
        var bound=Embedded32WithKnownClassifiedQueue596.bindKnown(wrongTop,ram,f->{need(f==frame,"sameforeign581frame");count[0]++;return marker;},f->{throw new AssertionError("foreignnotqueue");});
        need(ram.bytes.isEmpty()&&ram.cursor==0,"no eagerfactoryeffects");
        need(bound.invoke(frame)==marker&&count[0]==1,"foreignresultidentity/noaddedNRguard");ram.end();
    }
    public static int verify(){whole(0);whole(1);whole(2);whole(3);foreignIdentity();return 5;}
    public static void main(String[] args){System.out.println(verify());}
}
