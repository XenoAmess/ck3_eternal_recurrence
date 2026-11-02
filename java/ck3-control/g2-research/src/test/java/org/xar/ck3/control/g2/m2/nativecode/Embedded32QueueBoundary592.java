package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner new394-to103 binding cases; fixed source expectations, no target-derived oracle. */
public final class Embedded32QueueBoundary592 {
    private Embedded32QueueBoundary592() { }
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
    private static FullCopy437Api.Input wrongTop(GovernmentCrtBoundary185Api.LoopBudget budget){
        return new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I+0x70000,0x700000,v(0x7000),N),false,budget);
    }
    private static Embedded32Copy581Api.CallFrame outer(long site,long target,VolatileBits v,boolean df){
        var c=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,E+8,v,N);
        return new Embedded32Copy581Api.CallFrame(c,entry(v),df,5,I+site+5);
    }
    private static void lower(EmbeddedQueue591Api.CallFrame f,long sp,VolatileBits v,NonvolatileBits n,boolean df){
        need(f.call().equals(new GovernmentCrtBoundary185Api.Call(0x3727ECF,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x3727580,sp,v,n)),"whole actual103classify frame");
        need(f.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(I,sp-8,v,n)),"whole actualchild");
        need(f.directionFlagSet()==df&&f.instructionLength()==5&&f.returnRipBits()==I+0x3727ED4,"child DF/5B/continuation");
    }
    private static FullCopy437Api.CallResult reply(EmbeddedQueue591Api.CallFrame f,VolatileBits v,boolean df){return result(v,f.call().nonvolatileBits(),f.returnRipBits(),f.call().rspBits(),df);}
    private static void aliasCallbackWhole(){
        long a=E-0x56,ret2=0x8877665544332211L,count=0x13579BDF;
        VolatileBits input=change(v(0x1000),0x1001,a,a),p1=v(0x2000),p2=change(v(0x3000),0xBBBBBBBB00000001L,0x3002,0x1234567890ABCDEFL);
        Ram ram=new Ram(mem("W",8,E-8,N.rsiBits()),mem("W",8,E-0x10,N.r14Bits()),mem("W",8,E-0x18,N.r15Bits()),mem("R",4,a+0x28,count),mem("W",4,a+0x28,count),mem("W",8,E-0x50,I+0x37272F5),"F0",mem("W",1,E-8,0),mem("W",8,E-0x50,I+0x37272FD),mem("W",8,E-0x58,N.rbxBits()),mem("R",1,E-8,0),mem("W",8,E-0x80,I+0x3727ED4),"C",mem("W",8,E-8,0x5555),mem("W",8,E,ret2),mem("R",4,a+0x48,0),mem("R",8,E-0x58,N.rbxBits()),mem("R",8,E-0x50,I+0x37272FD),mem("R",8,E-0x18,N.r15Bits()),mem("R",8,E-0x10,N.r14Bits()),mem("R",8,E-8,0x5555),mem("R",8,E,ret2));
        ram.seed(8,E,RET);ram.seed(4,a+0x28,count);Map<Long,Byte> expected=new HashMap<>(ram.bytes);
        long[][] cells={{8,E-8,0x5555},{8,E-0x10,N.r14Bits()},{8,E-0x18,N.r15Bits()},{8,E-0x50,I+0x37272FD},{8,E-0x58,N.rbxBits()},{8,E-0x80,I+0x3727ED4},{8,E,ret2}};
        for(long[] c:cells)Ram.put(expected,(int)c[0],c[1],c[2]);
        NonvolatileBits parentN=new NonvolatileBits(N.rbxBits(),N.rbpBits(),a+0x10,N.rdiBits(),N.r12Bits(),N.r13Bits(),a,a,X6);
        NonvolatileBits innerN=new NonvolatileBits(a,N.rbpBits(),a+0x10,N.rdiBits(),N.r12Bits(),N.r13Bits(),a,a,X6);
        int[] fallback={0},classify={0};
        var actual=Embedded32WithKnownQueue592.execute(new FullCopy437Api.Input(entry(input),true,(h,g)->{throw new AssertionError("no budget in new alias branch");}),ram,f->{
            ram.event("F0");need(fallback[0]++==0,"one foreign37282B0 opaque callback");
            var before=change(input,count,a+0x30,a+0x30);
            need(f.call().equals(new GovernmentCrtBoundary185Api.Call(0x37272F0,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x37282B0,E-0x48,before,parentN)),"whole parent fallback frame");
            need(f.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(I,E-0x50,before,parentN))&&f.directionFlagSet()&&f.instructionLength()==5&&f.returnRipBits()==I+0x37272F5,"parent child/DF/ret");
            need(ram.raw(8,E-0x50)==I+0x37272F5,"parent actual physical CALL");
            ram.writeByte(E-8,0);return result(p1,parentN,f.returnRipBits(),f.call().rspBits(),false);
        },f->{
            ram.event("C");need(classify[0]++==0,"one actual103 classify after fallback alias effect");
            lower(f,E-0x78,change(p1,p1.raxBits(),a,p1.rdxBits()),innerN,false);
            need(ram.raw(8,E-0x50)==I+0x37272FD&&ram.raw(8,E-0x80)==I+0x3727ED4,"two nested physicalCALLs oneRAM");
            ram.writeQword(E-8,0x5555);ram.writeQword(E,ret2);return reply(f,p2,true);
        });
        NonvolatileBits restored=new NonvolatileBits(N.rbxBits(),N.rbpBits(),0x5555,N.rdiBits(),N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),X6);
        VolatileBits finalV=change(p2,a,p2.rcxBits(),0x1234567890ABCD01L);
        need(actual.equals(result(finalV,restored,ret2,E+8,true)),"whole394->actual103 full V/N/XMM/DF and freshparent RET/homes");
        need(fallback[0]==1&&classify[0]==1,"exact opaque callbacks");ram.end();need(ram.bytes.equals(expected),"complete new alias ownedbyteRAM");
    }
    private static void foreignIdentity(){
        Ram ram=new Ram();var f=outer(0x37272F0,0x37282B0,change(v(0x1000),0x1001,D,0x1003),true);
        var value=result(v(0x8000),N,0x1234,0x5678,false);int[] calls={0};
        var bound=Embedded32WithKnownQueue592.bindQueue(wrongTop((h,g)->{throw new AssertionError();}),ram,offered->{need(offered==f,"same foreignframe");calls[0]++;return value;},q->{throw new AssertionError();});
        need(bound.invoke(f)==value&&calls[0]==1&&ram.bytes.isEmpty(),"foreign frame/result identity noRAM/validation");ram.end();
    }
    private static void actualChildAndDF(){
        VolatileBits input=change(v(0x1000),0x1001,D,0x1003);
        Ram ram=new Ram(mem("W",8,E-8,N.rbxBits()),mem("R",1,D+0x4E,1),mem("R",8,E-8,N.rbxBits()),mem("R",8,E,I+0x37272FD));
        ram.seed(8,E,I+0x37272FD);ram.seed(1,D+0x4E,1);
        var bound=Embedded32WithKnownQueue592.bindQueue(wrongTop((h,g)->{throw new AssertionError();}),ram,f->{throw new AssertionError();},f->{throw new AssertionError("no classify forflag1");});
        var actual=bound.invoke(outer(0x37272F8,0x3727EC0,input,true));
        need(actual.equals(result(input,N,I+0x37272FD,E+8,true)),"actual framechild andDF, not wrongtopentry");ram.end();
    }
    private static void callbackBreaksOuterN(){
        VolatileBits input=change(v(0x1000),0x1001,D,0x1003),post=change(v(0x3000),1,0x3002,0x3003);long bad=0x999;
        Ram ram=new Ram(mem("W",8,E-8,N.rbxBits()),mem("R",1,D+0x4E,0),mem("W",8,E-0x30,I+0x3727ED4),"C",mem("W",8,E-8,bad),mem("R",4,D+0x48,5),mem("R",8,E-8,bad),mem("R",8,E,I+0x37272FD));
        ram.seed(8,E,I+0x37272FD);ram.seed(1,D+0x4E,0);ram.seed(4,D+0x48,5);int[] count={0};
        var bound=Embedded32WithKnownQueue592.bindQueue(wrongTop((h,g)->{throw new AssertionError();}),ram,f->{throw new AssertionError("no fallback on actualqueue NR failure");},f->{
            ram.event("C");need(count[0]++==0,"one classify");lower(f,E-0x28,input,n(D),true);ram.writeQword(E-8,bad);return reply(f,post,false);
        });
        try{bound.invoke(outer(0x37272F8,0x3727EC0,input,true));throw new AssertionError("outer581guard missing");}
        catch(IllegalArgumentException expected){need(count[0]==1,"callee ran before outer guard");ram.end();need(ram.raw(8,E-8)==bad,"actual freshsavedRBX not repaired");}
    }
    private static void originalBudgetMarker(){
        VolatileBits input=change(v(0x1000),0x1001,D,0x1003),post=change(v(0x3000),2,0x3002,0x3003);
        Ram ram=new Ram(mem("W",8,E-8,N.rbxBits()),mem("R",1,D+0x4E,0),mem("W",8,E-0x30,I+0x3727ED4),"C",mem("R",4,D+0x48,5),"B");
        ram.seed(8,E,I+0x37272FD);ram.seed(1,D+0x4E,0);ram.seed(4,D+0x48,5);int[] calls={0},steps={0};var marker=new UnsupportedOperationException("original592budget");
        GovernmentCrtBoundary185Api.LoopBudget budget=(h,g)->{need(h==0x3727EE4&&g==L,"original innerheader/guard");ram.event("B");steps[0]++;throw marker;};
        var bound=Embedded32WithKnownQueue592.bindQueue(wrongTop(budget),ram,f->{throw new AssertionError();},f->{ram.event("C");need(calls[0]++==0,"one classify only");lower(f,E-0x28,input,n(D),true);return reply(f,post,false);});
        try{bound.invoke(outer(0x37272F8,0x3727EC0,input,true));throw new AssertionError("missing marker");}
        catch(UnsupportedOperationException actual){need(actual==marker&&calls[0]==1&&steps[0]==1,"same original budget marker");}ram.end();need(!ram.bytes.containsKey(L),"before unseeded loopMemory");
    }
    public static int verify(){aliasCallbackWhole();foreignIdentity();actualChildAndDF();callbackBreaksOuterN();originalBudgetMarker();return 5;}
    public static void main(String[] args){System.out.println(verify());}
}
