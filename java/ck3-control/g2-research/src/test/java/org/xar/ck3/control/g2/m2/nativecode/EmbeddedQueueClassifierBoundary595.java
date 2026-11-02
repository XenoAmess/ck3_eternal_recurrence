package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner newactual103->81 integration fullstatecases; fixed originalsource literals. */
public final class EmbeddedQueueClassifierBoundary595 {
    private EmbeddedQueueClassifierBoundary595() { }
    private static final long I=0x140000000L,E=0x9000L,D=0x18000L,L=I+0x5C9FF68L,RET=0xAABBCCDD11223344L;
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
        {{0x8L,0x9000L,0xaabbccdd11223344L},{0x1L,0x1804eL,0x0L},{0x4L,0x1801cL,0xffffffffL},{0x8L,0x18010L,0x22334455667788efL},{0x4L,0x22334455667788bbL,0x0L},{0x4L,0x18048L,0x9L}},
        {{0x8L,0x9000L,0xaabbccdd11223344L},{0x1L,0x1804eL,0x0L},{0x4L,0x1801cL,0x0L},{0x8L,0x18030L,0x0L},{0x4L,0x1803cL,0x1L},{0x1L,0x44L,0x7fL},{0x4L,0x18048L,0xffffffffL}},
        {{0x8L,0x9000L,0xaabbccdd11223344L},{0x1L,0x1804eL,0x0L},{0x4L,0x1801cL,0x0L},{0x8L,0x18030L,0x55000L},{0x4L,0x1803cL,0x2L},{0x1L,0x55044L,0x0L},{0x1L,0x5508cL,0x0L},{0x4L,0x18048L,0x4L},{0x4L,0x145c9ff68L,0x0L}}
    };
    private static final String[][] EVENTS={
        {"W8@8ff8=111","R1@1804e=0","W8@8fd0=143727ed4","R4@1801c=ffffffff","R4@1801c=ffffffff","R8@18010=22334455667788ef","R4@22334455667788bb=0","R8@8fd0=143727ed4","R4@18048=9","R8@8ff8=111","R8@9000=aabbccdd11223344"},
        {"W8@8ff8=111","R1@1804e=0","W8@8fd0=143727ed4","R4@1801c=0","R8@18030=0","R4@1803c=1","B@37275b0:0","R1@44=7f","R8@8fd0=143727ed4","R4@18048=ffffffff","R8@8ff8=111","R8@9000=aabbccdd11223344"},
        {"W8@8ff8=111","R1@1804e=0","W8@8fd0=143727ed4","R4@1801c=0","R8@18030=55000","R4@1803c=2","B@37275b0:55000","R1@55044=0","B@37275b0:55048","R1@5508c=0","R8@8fd0=143727ed4","R4@18048=4","B@3727ee4:145c9ff68","R4@145c9ff68=0","CAS@145c9ff68:0:1:0","W8@9010=18000","W8@8fd0=143727f12","C","W8@8ff8=abcd","W8@9000=1020304050607080","W1@1804e=1","W4@145c9ff68=0","R8@8ff8=abcd","R8@9000=1020304050607080"}
    };
    private static final long[][] ACD={{0x2233445566778801L,0x18000L,0xffffffffffffff01L},{0x0L,0x48L,0x0L},{}};
    private static VolatileBits input(){return change(v(0x1000),0x1001,D,0x1003);}
    private static Map<Long,Byte> expected(Ram ram,String[] events){
        Map<Long,Byte> result=new HashMap<>(ram.bytes);
        for(String s:events)if(s.startsWith("W")){int at=s.indexOf('@'),eq=s.indexOf('=');Ram.put(result,Integer.parseInt(s.substring(1,at)),Long.parseUnsignedLong(s.substring(at+1,eq),16),Long.parseUnsignedLong(s.substring(eq+1),16));}
        else if(s.startsWith("CAS@")){String[] p=s.substring(4).split(":");if(p[1].equals(p[3]))Ram.put(result,4,Long.parseUnsignedLong(p[0],16),Long.parseUnsignedLong(p[2],16));}
        return result;
    }
    private static void whole(int index){
        Ram ram=new Ram(EVENTS[index]);for(long[] c:INITIAL[index])ram.seed((int)c[0],c[1],c[2]);Map<Long,Byte> bytes=expected(ram,EVENTS[index]);
        int[] opaque={0};boolean df=index!=1;
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{need(h==0x37275B0||(index==2&&h==0x3727EE4),"real leaf orqueue sourceheader");ram.event("B@"+Long.toHexString(h)+":"+Long.toHexString(g));};
        var actual=EmbeddedQueueWithKnownClassifier595.execute(new FullCopy437Api.Input(entry(input()),df,budget),ram,f->{
            need(index==2&&opaque[0]++==0,"only one actualenqueue opaque, no classifierfallback");ram.event("C");
            var before=change(input(),0,I+0x5468A68,E+0x10);var offeredN=n(D);
            need(f.call().equals(new GovernmentCrtBoundary185Api.Call(0x3727F0D,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x880340,E-0x28,before,offeredN)),"fullactual enqueueframe and inherited V/N");
            need(f.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(I,E-0x30,before,offeredN))&&f.directionFlagSet()&&f.instructionLength()==5&&f.returnRipBits()==I+0x3727F12,"enqueueactual child/fullDF/5B/RET");
            need(ram.raw(8,E-0x30)==I+0x3727F12&&ram.raw(8,E+0x10)==D,"sharedRAM realCALL anddatum");
            ram.writeQword(E-8,0xABCD);ram.writeQword(E,0x1020304050607080L);
            return result(v(0x5000),offeredN,f.returnRipBits(),f.call().rspBits(),false);
        });
        var expectedV=index==2?v(0x5000):change(input(),ACD[index][0],ACD[index][1],ACD[index][2]);
        long finalRBX=index==2?0xABCD:N.rbxBits(),rip=index==2?0x1020304050607080L:RET;
        need(actual.equals(result(expectedV,n(finalRBX),rip,E+8,index==2?false:df)),"whole103/81 actualAL-fullRDX/N/XMM/DF/freshparenthomesRET case"+index);
        need(opaque[0]==(index==2?1:0),"no spurious fallback/enqueue");ram.end();need(ram.bytes.equals(bytes),"complete fixed ownedbytes"+index);
    }
    private static FullCopy437Api.Input wrongTop(GovernmentCrtBoundary185Api.LoopBudget budget){return new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I+0x70000,0x700000,v(0x7000),N),false,budget);}
    private static EmbeddedQueue591Api.CallFrame frame(long site,long target,long image,long childSP,VolatileBits v,NonvolatileBits n,boolean df){
        var call=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,childSP+8,v,n);
        return new EmbeddedQueue591Api.CallFrame(call,new GovernmentCrtBoundary185Api.Entry(image,childSP,v,n),df,5,image+site+5);
    }
    private static void actualChildDF(){
        long image=I+0x90000,sp=0x9A00,a=0x22000,base=0xA0000,rip=image+0x3727ED4;
        var offered=change(v(0x9000),0x9001,a,0x9003);var offeredN=n(0xAAA);
        Ram ram=new Ram(mem("R",4,a+0x1C,0),mem("R",8,a+0x30,base),mem("R",4,a+0x3C,0),mem("R",8,sp,rip));
        ram.seed(4,a+0x1C,0);ram.seed(8,a+0x30,base);ram.seed(4,a+0x3C,0);ram.seed(8,sp,rip);Map<Long,Byte> before=new HashMap<>(ram.bytes);
        var bound=EmbeddedQueueWithKnownClassifier595.bindClassifier(wrongTop((h,g)->{throw new AssertionError("empty leaf no budget");}),ram,f->{throw new AssertionError("knownleaf cannotfallback");});
        var actual=bound.invoke(frame(0x3727ECF,0x3727580,image,sp,offered,offeredN,true));
        need(actual.equals(result(change(offered,0,base,0),offeredN,rip,sp+8,true)),"actual frame V/N/SP/DF over wrongtop defaults");ram.end();need(ram.bytes.equals(before),"leafno Memorywrites or fakepush");
    }
    private static void originalBudget(){
        long image=I+0xA0000,sp=0xA800,a=0x24000,base=0x88000;var offered=change(v(0xA000),0xA001,a,0xA003);var offeredN=n(0xBBB);
        Ram ram=new Ram(mem("R",4,a+0x1C,0),mem("R",8,a+0x30,base),mem("R",4,a+0x3C,1),"B");ram.seed(4,a+0x1C,0);ram.seed(8,a+0x30,base);ram.seed(4,a+0x3C,1);Map<Long,Byte> before=new HashMap<>(ram.bytes);
        var marker=new UnsupportedOperationException("original595budget");
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{need(h==0x37275B0&&g==base,"actualchild sourceheader andguard");ram.event("B");throw marker;};
        var bound=EmbeddedQueueWithKnownClassifier595.bindClassifier(wrongTop(budget),ram,f->{throw new AssertionError();});
        try{bound.invoke(frame(0x3727ECF,0x3727580,image,sp,offered,offeredN,true));throw new AssertionError("must stop");}
        catch(UnsupportedOperationException ex){need(ex==marker,"originalexception identity no wrap/fallback");}ram.end();need(ram.bytes.equals(before),"beforeflag/RET Memory, no fakeCALLpush");
    }
    private static void foreignIdentity(){
        Ram ram=new Ram();var offered=frame(0x3727F0D,0x880340,I+0xB0000,0xB800,v(0xB000),n(0xCCC),true);
        var reply=result(v(0xC000),N,0x1234,0x5678,false);int[] count={0};
        var bound=EmbeddedQueueWithKnownClassifier595.bindClassifier(wrongTop((h,g)->{throw new AssertionError();}),ram,f->{need(f==offered,"same foreignframe");count[0]++;return reply;});
        need(ram.bytes.isEmpty()&&ram.cursor==0,"no eagerexecute/bind effects");need(bound.invoke(offered)==reply&&count[0]==1,"same result/no addedforeignNRguard");ram.end();
    }
    public static int verify(){whole(0);whole(1);whole(2);actualChildDF();originalBudget();foreignIdentity();return 6;}
    public static void main(String[] args){System.out.println(verify());}
}
