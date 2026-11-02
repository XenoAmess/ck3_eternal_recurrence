package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner new combined394->322->93 +103 boundary cases; fixed original-source literal oracle. */
public final class Embedded32ClearQueueBoundary593 {
    private Embedded32ClearQueueBoundary593() { }
    private static final long I=0x140000000L,E=0x8000L,D=0x10000L,L=I+0x5C9FF68L,RET=0xAABBCCDD11223344L;
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
    private static final String[][] EVENTS={
        new String[]{
            "W8@7ff8=333",
            "W8@7ff0=777",
            "W8@7fe8=888",
            "W8@8018=444",
            "R4@2001c=0",
            "W8@7fe0=555",
            "W8@7fd8=666",
            "R8@20010=60000",
            "W8@7fb0=1437271bf",
            "C0",
            "R4@1001c=0",
            "W8@8008=111",
            "W8@8010=222",
            "R8@10010=70000",
            "R8@10010=70000",
            "R8@8010=222",
            "R8@8008=111",
            "W4@1001c=0",
            "R8@8018=444",
            "R8@7fe0=555",
            "R8@7fd8=666",
            "R4@20028=13579bdf",
            "W4@10028=13579bdf",
            "W8@7fb0=1437272f5",
            "W8@7fb8=111",
            "W8@7fc0=222",
            "W8@7fc8=10010",
            "W8@7fd0=444",
            "W8@7fa8=555",
            "W8@7fa0=10000",
            "W8@7f98=20000",
            "R4@2003c=0",
            "R8@20030=90000",
            "W8@7f60=1437282e6",
            "W8@7f70=10030",
            "W8@7f58=444",
            "R4@1003c=1",
            "W8@7f68=0",
            "R8@10030=30000",
            "B@8897a0:30000",
            "R8@30000=40000",
            "R8@40000=50000",
            "W8@7f30=1408897aa",
            "C1",
            "W8@7ff8=abcd",
            "W8@8000=8877665544332211",
            "R8@7f68=0",
            "W4@1003c=0",
            "R8@7f70=10030",
            "R8@7f58=444",
            "R8@7f60=1437282e6",
            "R4@1003c=0",
            "R8@10030=30000",
            "W4@1003c=0",
            "R8@7fb8=111",
            "R8@7fc0=222",
            "R8@7fc8=10010",
            "R8@7fd0=444",
            "R8@7f98=20000",
            "R8@7fa0=10000",
            "R8@7fa8=555",
            "R8@7fb0=1437272f5",
            "W8@7fb0=1437272fd",
            "W8@7fa8=111",
            "R1@1004e=0",
            "W8@7f80=143727ed4",
            "C2",
            "R4@10048=7",
            "B@3727ee4:145c9ff68",
            "R4@145c9ff68=0",
            "CAS@145c9ff68:0:1:0",
            "W8@7fc0=10000",
            "W8@7f80=143727f12",
            "C3",
            "W8@7ff8=beef",
            "W8@8000=1020304050607080",
            "W1@1004e=1",
            "W4@145c9ff68=0",
            "R8@7fa8=111",
            "R8@7fb0=1437272fd",
            "R8@7fe8=888",
            "R8@7ff0=777",
            "R8@7ff8=beef",
            "R8@8000=1020304050607080"
        },
        new String[]{
            "W8@7ff8=333",
            "W8@7ff0=777",
            "W8@7fe8=888",
            "W8@8018=444",
            "R4@2001c=0",
            "W8@7fe0=555",
            "W8@7fd8=666",
            "R8@20010=60000",
            "W8@7fb0=1437271bf",
            "C0",
            "R4@1001c=0",
            "W8@8008=111",
            "W8@8010=222",
            "R8@10010=70000",
            "R8@10010=70000",
            "R8@8010=222",
            "R8@8008=111",
            "W4@1001c=0",
            "R8@8018=444",
            "R8@7fe0=555",
            "R8@7fd8=666",
            "R4@20028=13579bdf",
            "W4@10028=13579bdf",
            "W8@7fb0=1437272f5",
            "W8@7fb8=111",
            "W8@7fc0=222",
            "W8@7fc8=10010",
            "W8@7fd0=444",
            "W8@7fa8=555",
            "W8@7fa0=10000",
            "W8@7f98=20000",
            "R4@2003c=0",
            "R8@20030=90000",
            "W8@7f60=1437282e6",
            "W8@7f70=10030",
            "W8@7f58=444",
            "R4@1003c=1",
            "W8@7f68=0",
            "R8@10030=30000",
            "B@8897a0:30000",
            "R8@30000=40000",
            "R8@40000=50000",
            "W8@7f30=1408897aa",
            "C1",
            "W8@7ff8=abcd",
            "W8@8000=8877665544332211",
            "W8@7fb8=999",
            "R8@7f68=0",
            "W4@1003c=0",
            "R8@7f70=10030",
            "R8@7f58=444",
            "R8@7f60=1437282e6",
            "R4@1003c=0",
            "R8@10030=30000",
            "W4@1003c=0",
            "R8@7fb8=999",
            "R8@7fc0=222",
            "R8@7fc8=10010",
            "R8@7fd0=444",
            "R8@7f98=20000",
            "R8@7fa0=10000",
            "R8@7fa8=555",
            "R8@7fb0=1437272f5"
        },
        new String[]{
            "W8@7ff8=333",
            "W8@7ff0=777",
            "W8@7fe8=888",
            "W8@8018=444",
            "R4@2001c=0",
            "W8@7fe0=555",
            "W8@7fd8=666",
            "R8@20010=60000",
            "W8@7fb0=1437271bf",
            "C0",
            "R4@1001c=0",
            "W8@8008=111",
            "W8@8010=222",
            "R8@10010=70000",
            "R8@10010=70000",
            "R8@8010=222",
            "R8@8008=111",
            "W4@1001c=0",
            "R8@8018=444",
            "R8@7fe0=555",
            "R8@7fd8=666",
            "R4@20028=13579bdf",
            "W4@10028=13579bdf",
            "W8@7fb0=1437272f5",
            "W8@7fb8=111",
            "W8@7fc0=222",
            "W8@7fc8=10010",
            "W8@7fd0=444",
            "W8@7fa8=555",
            "W8@7fa0=10000",
            "W8@7f98=20000",
            "R4@2003c=0",
            "R8@20030=90000",
            "W8@7f60=1437282e6",
            "W8@7f70=10030",
            "W8@7f58=444",
            "R4@1003c=1",
            "W8@7f68=0",
            "R8@10030=30000",
            "B@8897a0:30000",
            "R8@30000=40000",
            "R8@40000=50000",
            "W8@7f30=1408897aa",
            "C1",
            "W8@7ff8=abcd",
            "W8@8000=8877665544332211",
            "R8@7f68=0",
            "W4@1003c=0",
            "R8@7f70=10030",
            "R8@7f58=444",
            "R8@7f60=1437282e6",
            "R4@1003c=0",
            "R8@10030=30000",
            "W4@1003c=0",
            "R8@7fb8=111",
            "R8@7fc0=222",
            "R8@7fc8=10010",
            "R8@7fd0=444",
            "R8@7f98=20000",
            "R8@7fa0=10000",
            "R8@7fa8=555",
            "R8@7fb0=1437272f5",
            "W8@7fb0=1437272fd",
            "W8@7fa8=111",
            "R1@1004e=0",
            "W8@7f80=143727ed4",
            "C2",
            "R4@10048=7",
            "B@3727ee4:145c9ff68"
        }
    };
    private static final long[][] INITIAL={{0x8L,0x8000L,0xaabbccdd11223344L},{0x4L,0x2001cL,0x0L},{0x8L,0x20010L,0x60000L},{0x4L,0x1001cL,0x0L},{0x8L,0x10010L,0x70000L},{0x4L,0x20028L,0x13579bdfL},{0x4L,0x2003cL,0x0L},{0x8L,0x20030L,0x90000L},{0x4L,0x1003cL,0x1L},{0x8L,0x10030L,0x30000L},{0x8L,0x30000L,0x40000L},{0x8L,0x40000L,0x50000L},{0x1L,0x1004eL,0x0L},{0x4L,0x10048L,0x7L},{0x4L,0x145c9ff68L,0x0L}};
    private static final VolatileBits INPUT=new VolatileBits(0x1001L,0x10000L,0x20000L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L));
    private static final VolatileBits[] POSTS={new VolatileBits(0x2001L,0x2002L,0x2003L,0x2004L,0x2005L,0x2006L,0x2007L,new Bits128(0x2010L,0x2011L),new Bits128(0x2020L,0x2021L),new Bits128(0x2030L,0x2031L),new Bits128(0x2040L,0x2041L),new Bits128(0x2050L,0x2051L),new Bits128(0x2060L,0x2061L)),new VolatileBits(0x3001L,0x3002L,0x3003L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),new VolatileBits(0x2L,0x4002L,0x1234567890abcdefL,0x4004L,0x4005L,0x4006L,0x4007L,new Bits128(0x4010L,0x4011L),new Bits128(0x4020L,0x4021L),new Bits128(0x4030L,0x4031L),new Bits128(0x4040L,0x4041L),new Bits128(0x4050L,0x4051L),new Bits128(0x4060L,0x4061L)),new VolatileBits(0x5001L,0x5002L,0x5003L,0x5004L,0x5005L,0x5006L,0x5007L,new Bits128(0x5010L,0x5011L),new Bits128(0x5020L,0x5021L),new Bits128(0x5030L,0x5031L),new Bits128(0x5040L,0x5041L),new Bits128(0x5050L,0x5051L),new Bits128(0x5060L,0x5061L))};
    private static final boolean[] POST_DF={false,true,false,false};
    private static void offered(int index,GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,boolean df,int length,long rip) {
        GovernmentCrtBoundary185Api.Call expected;
        boolean expectedDF;int expectedLength;
        switch(index) {
            case 0 -> { expected=new GovernmentCrtBoundary185Api.Call(0x37271baL,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x889660L,0x7fb8L,new VolatileBits(0x20010L,0x10010L,0x20000L,0x1004L,0x1005L,0x1006L,0x1007L,new Bits128(0x1010L,0x1011L),new Bits128(0x1020L,0x1021L),new Bits128(0x1030L,0x1031L),new Bits128(0x1040L,0x1041L),new Bits128(0x1050L,0x1051L),new Bits128(0x1060L,0x1061L)),new NonvolatileBits(0x111L,0x222L,0x10010L,0x0L,0x555L,0x60000L,0x10000L,0x20000L,new Bits128(0x61L,0x62L)));expectedDF=true;expectedLength=5;}
            case 1 -> { expected=new GovernmentCrtBoundary185Api.Call(0x8897a8L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x50000L,0x7f38L,new VolatileBits(0x40000L,0x30000L,0x0L,0x2004L,0x2005L,0x2006L,0x2007L,new Bits128(0x2010L,0x2011L),new Bits128(0x2020L,0x2021L),new Bits128(0x2030L,0x2031L),new Bits128(0x2040L,0x2041L),new Bits128(0x2050L,0x2051L),new Bits128(0x2060L,0x2061L)),new NonvolatileBits(0x30000L,0x90000L,0x10030L,0x1L,0x555L,0x666L,0x10000L,0x20000L,new Bits128(0x61L,0x62L)));expectedDF=false;expectedLength=2;}
            case 2 -> { expected=new GovernmentCrtBoundary185Api.Call(0x3727ecfL,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x3727580L,0x7f88L,new VolatileBits(0x10030L,0x10000L,0x30000L,0x3004L,0x3005L,0x3006L,0x3007L,new Bits128(0x3010L,0x3011L),new Bits128(0x3020L,0x3021L),new Bits128(0x3030L,0x3031L),new Bits128(0x3040L,0x3041L),new Bits128(0x3050L,0x3051L),new Bits128(0x3060L,0x3061L)),new NonvolatileBits(0x10000L,0x222L,0x10010L,0x444L,0x555L,0x666L,0x10000L,0x20000L,new Bits128(0x61L,0x62L)));expectedDF=true;expectedLength=5;}
            case 3 -> { expected=new GovernmentCrtBoundary185Api.Call(0x3727f0dL,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x880340L,0x7f88L,new VolatileBits(0x0L,0x145468a68L,0x7fc0L,0x4004L,0x4005L,0x4006L,0x4007L,new Bits128(0x4010L,0x4011L),new Bits128(0x4020L,0x4021L),new Bits128(0x4030L,0x4031L),new Bits128(0x4040L,0x4041L),new Bits128(0x4050L,0x4051L),new Bits128(0x4060L,0x4061L)),new NonvolatileBits(0x10000L,0x222L,0x10010L,0x444L,0x555L,0x666L,0x10000L,0x20000L,new Bits128(0x61L,0x62L)));expectedDF=false;expectedLength=5;}
            default -> throw new AssertionError("unexpected callback index");
        }
        need(call.equals(expected),"full call bank"+index+" got"+call+" expected"+expected);
        need(child.equals(new GovernmentCrtBoundary185Api.Entry(I,expected.rspBits()-8,expected.volatileBits(),expected.nonvolatileBits())),"actual child bank"+index);
        need(df==expectedDF&&length==expectedLength&&rip==I+expected.callSiteRva()+expectedLength,"DF/length/return"+index);
    }
    private static FullCopy437Api.CallResult callback(Ram ram,int mode,int[] calls,int index,
            GovernmentCrtBoundary185Api.Call call,GovernmentCrtBoundary185Api.Entry child,boolean df,int length,long rip) {
        ram.event("C"+index);need(calls[0]++==index,"callback order/once");offered(index,call,child,df,length,rip);
        need(ram.raw(8,child.rspBits())==rip,"one physical CALL push"+index);
        if(index==1){ram.writeQword(E-8,0xABCD);ram.writeQword(E,0x8877665544332211L);if(mode==1)ram.writeQword(E-0x48,0x999);}
        if(index==3){ram.writeQword(E-8,0xBEEF);ram.writeQword(E,0x1020304050607080L);}
        return result(POSTS[index],call.nonvolatileBits(),rip,call.rspBits(),POST_DF[index]);
    }
    private static void scenario(int mode){
        Ram ram=new Ram(EVENTS[mode]);
        for(long[] cell:INITIAL)if(mode!=2||cell[1]!=L)ram.seed((int)cell[0],cell[1],cell[2]);
        int[] calls={0},budgets={0};var marker=new UnsupportedOperationException("original593budget");
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{
            int n=budgets[0]++;need((n==0&&h==0x8897A0&&g==0x30000)||(n==1&&h==0x3727EE4&&g==L),"same original budget exact header/guard");
            ram.event("B@"+Long.toHexString(h)+":"+Long.toHexString(g));if(mode==2&&n==1)throw marker;
        };
        FullCopy437Api.CallResult actual=null;
        try{
            actual=Embedded32WithKnownClearQueue593.execute(new FullCopy437Api.Input(entry(INPUT),true,budget),ram,
                f->callback(ram,mode,calls,0,f.call(),f.childEntry(),f.directionFlagSet(),f.instructionLength(),f.returnRipBits()),
                f->{throw new AssertionError("all newscene 322 calls resolved; unsupportedlower untouched");},
                f->callback(ram,mode,calls,1,f.call(),f.childEntry(),f.directionFlagSet(),f.instructionLength(),f.returnRipBits()),
                f->{int index=f.call().callSiteRva()==0x3727ECF?2:3;return callback(ram,mode,calls,index,f.call(),f.childEntry(),f.directionFlagSet(),f.instructionLength(),f.returnRipBits());});
            need(mode==0,"negative must reject");
        }catch(IllegalArgumentException ex){need(mode==1&&calls[0]==2&&budgets[0]==1,"outer581 rejects fresh322 savedRBX, not callbackN");need(ram.raw(8,E-0x48)==0x999,"no state repair");}
        catch(UnsupportedOperationException ex){need(mode==2&&ex==marker&&calls[0]==3&&budgets[0]==2,"exact original marker before lock read");need(!ram.bytes.containsKey(L),"no premature lockMemory");}
        if(mode==0){need(actual!=null&&actual.equals(result(new VolatileBits(0x10000L,0x5002L,0x5003L,0x5004L,0x5005L,0x5006L,0x5007L,new Bits128(0x5010L,0x5011L),new Bits128(0x5020L,0x5021L),new Bits128(0x5030L,0x5031L),new Bits128(0x5040L,0x5041L),new Bits128(0x5050L,0x5051L),new Bits128(0x5060L,0x5061L)),new NonvolatileBits(0x111L,0x222L,0xbeefL,0x444L,0x555L,0x666L,0x777L,0x888L,new Bits128(0x61L,0x62L)),0x1020304050607080L,E+8,false)),"whole combined final fullV/N/XMM/DF/freshRET");need(calls[0]==4&&budgets[0]==2,"two realcallee branches and all lower callbacks");}
        ram.end();Map<Long,Byte> expected=new HashMap<>();
        for(long[] cell:INITIAL)if(mode!=2||cell[1]!=L)Ram.put(expected,(int)cell[0],cell[1],cell[2]);
        // Mechanical literal-write overlay, independent of target execution/results.
        for(String event:EVENTS[mode])if(event.startsWith("W")){
            int at=event.indexOf('@'),eq=event.indexOf('=');Ram.put(expected,Integer.parseInt(event.substring(1,at)),Long.parseUnsignedLong(event.substring(at+1,eq),16),Long.parseUnsignedLong(event.substring(eq+1),16));
        }else if(event.startsWith("CAS@")){
            String[] p=event.substring(4).split(":");if(p[1].equals(p[3]))Ram.put(expected,4,Long.parseUnsignedLong(p[0],16),Long.parseUnsignedLong(p[2],16));
        }
        need(ram.bytes.equals(expected),"all owned byteRAM exact"+mode);
    }
    private static void foreignIdentity(){
        Ram ram=new Ram();var input=new FullCopy437Api.Input(entry(INPUT),false,(h,g)->{throw new AssertionError("no eager budget");});
        var call=new GovernmentCrtBoundary185Api.Call(0x37271BA,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x889660,E+8,INPUT,N);
        var frame=new Embedded32Copy581Api.CallFrame(call,entry(INPUT),true,5,I+0x37271BF);
        var reply=result(v(0x9000),N,0x1234,0x5678,false);int[] calls={0};
        var bound=Embedded32WithKnownClearQueue593.bindKnown(input,ram,f->{need(f==frame,"same foreignframe through both outer factories");calls[0]++;return reply;},f->{throw new AssertionError();},f->{throw new AssertionError();},f->{throw new AssertionError();});
        need(ram.cursor==0&&ram.bytes.isEmpty(),"no execution/effects during bind");need(bound.invoke(frame)==reply&&calls[0]==1,"same result no foreign NRvalidation");ram.end();
    }
    public static int verify(){scenario(0);scenario(1);scenario(2);foreignIdentity();return 4;}
    public static void main(String[] args){System.out.println(verify());}
}
