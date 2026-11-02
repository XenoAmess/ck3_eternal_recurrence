package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner fixed original103 cases; no target-derived oracle or algorithm simulator. */
public final class EmbeddedQueueBoundary591 {
    private EmbeddedQueueBoundary591() { }
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
    private static void frame(EmbeddedQueue591Api.CallFrame f,long site,long target,VolatileBits v,boolean df){
        var c=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,E-0x28,v,n(D));
        need(f.call().equals(c),"whole call bank");
        need(f.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(I,E-0x30,v,n(D))),"whole child bank");
        need(f.directionFlagSet()==df&&f.instructionLength()==5&&f.returnRipBits()==I+site+5,"DF/5B/ret");
    }
    private static FullCopy437Api.CallResult reply(EmbeddedQueue591Api.CallFrame f,VolatileBits v,boolean df){return result(v,f.call().nonvolatileBits(),f.returnRipBits(),f.call().rspBits(),df);}
    private static void flagAliasesPush(){
        long receiver=E-0x56;VolatileBits input=change(v(0x1000),0x1001,receiver,0x1003);
        Ram ram=new Ram(mem("W",8,E-8,N.rbxBits()),mem("R",1,E-8,0x11),mem("R",8,E-8,N.rbxBits()),mem("R",8,E,RET));
        ram.seed(8,E,RET);Map<Long,Byte> expected=new HashMap<>(ram.bytes);Ram.put(expected,8,E-8,N.rbxBits());
        var actual=EmbeddedQueueFullState3727EC0.execute(new FullCopy437Api.Input(entry(input),true,(h,g)->{throw new AssertionError("no loop");}),ram,f->{throw new AssertionError("no calls");});
        need(actual.equals(result(input,N,RET,E+8,true)),"flag push alias fullreturn");ram.end();need(ram.bytes.equals(expected),"flag completeRAM");
    }
    private static void exactEqualAL(){
        VolatileBits input=change(v(0x1000),0x1001,D,0x1003),post=change(v(0x2000),0xAABBCCDD00000001L,0x2002,0x1234567890ABCDEFL);
        Ram ram=new Ram(mem("W",8,E-8,N.rbxBits()),mem("R",1,D+0x4E,0),mem("W",8,E-0x30,I+0x3727ED4),"IN1",mem("R",4,D+0x48,5),mem("R",8,E-8,N.rbxBits()),mem("R",8,E,RET));
        ram.seed(8,E,RET);ram.seed(1,D+0x4E,0);ram.seed(4,D+0x48,5);Map<Long,Byte> expected=new HashMap<>(ram.bytes);Ram.put(expected,8,E-8,N.rbxBits());Ram.put(expected,8,E-0x30,I+0x3727ED4);
        var actual=EmbeddedQueueFullState3727EC0.execute(new FullCopy437Api.Input(entry(input),true,(h,g)->{throw new AssertionError("no loop");}),ram,f->{ram.event("IN1");frame(f,0x3727ECF,0x3727580,input,true);return reply(f,post,false);});
        need(actual.equals(result(change(post,post.raxBits(),post.rcxBits(),0x1234567890ABCD01L),N,RET,E+8,false)),"SETNE DL preserves upper56 and exactAL return");ram.end();need(ram.bytes.equals(expected),"equal completeRAM");
    }
    private static void enqueueAL2AndFreshHomes(){
        VolatileBits input=change(v(0x1000),0x1001,D,0x1003),p1=change(v(0x2000),0xABCDEF0000000002L,0x2002,0x1234567890ABCDEFL),p2=v(0x3000);
        long restored=0x999,ret2=0x8877665544332211L;
        Ram ram=new Ram(mem("W",8,E-8,N.rbxBits()),mem("R",1,D+0x4E,0),mem("W",8,E-0x30,I+0x3727ED4),"IN1",mem("R",4,D+0x48,5),"B",mem("R",4,L,0),"CAS@"+Long.toHexString(L)+":0:1:0",mem("W",8,E+0x10,D),mem("W",8,E-0x30,I+0x3727F12),"IN2",mem("W",8,E-8,restored),mem("W",8,E,ret2),mem("W",1,D+0x4E,1),mem("W",4,L,0),mem("R",8,E-8,restored),mem("R",8,E,ret2));
        ram.seed(8,E,RET);ram.seed(1,D+0x4E,0);ram.seed(4,D+0x48,5);ram.seed(4,L,0);Map<Long,Byte> expected=new HashMap<>(ram.bytes);
        Ram.put(expected,8,E-8,restored);Ram.put(expected,8,E,ret2);Ram.put(expected,8,E-0x30,I+0x3727F12);Ram.put(expected,8,E+0x10,D);Ram.put(expected,1,D+0x4E,1);
        int[] count={0};var actual=EmbeddedQueueFullState3727EC0.execute(new FullCopy437Api.Input(entry(input),true,(h,g)->{need(h==0x3727EE4&&g==L,"budgetheader/guard");ram.event("B");}),ram,f->{
            if(count[0]++==0){ram.event("IN1");frame(f,0x3727ECF,0x3727580,input,true);return reply(f,p1,false);}
            ram.event("IN2");frame(f,0x3727F0D,0x880340,change(p1,0,I+0x5468A68,E+0x10),false);
            need(ram.raw(8,E+0x10)==D&&ram.raw(8,E-0x30)==I+0x3727F12,"physical queuehome/CALL");ram.writeQword(E-8,restored);ram.writeQword(E,ret2);return reply(f,p2,true);
        });
        need(count[0]==2&&actual.equals(result(p2,n(restored),ret2,E+8,true)),"AL2 is mismatch / full secondpost / fresh savedRBX andRET");ram.end();need(ram.bytes.equals(expected),"enqueue completeRAM");
    }
    private static void finiteAtomicRace(){
        // Fixed competing-agent observations, not a simulated target loop: busy7, load0/CASrace2, load0/CASsuccess0.
        Ram ram=new Ram("B",mem("R",4,L,7),"B",mem("R",4,L,0),"CAS@"+Long.toHexString(L)+":0:1:2","B",mem("R",4,L,0),"CAS@"+Long.toHexString(L)+":0:1:0"){
            int reads,cas;
            public int readDword(long a){need(a==L,"lock address");seed(4,L,reads++==0?7:0);return super.readDword(a);}
            public int compareExchangeDword(long a,int e,int d){if(cas++==0)seed(4,L,2);return super.compareExchangeDword(a,e,d);}
        };
        var initial=change(v(0x4000),0xDEADBEEFL,1,0x4003);var r=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,E,initial,N));
        EmbeddedQueueLock591.acquire(r,ram,(h,g)->{need(h==0x3727EE4&&g==L,"same budget");ram.event("B");},L);
        ram.end();need(r.volatileBits().equals(change(initial,0,1,0x4003))&&r.nonvolatileBits().equals(N)&&r.rsp==E,"only EAX changed in lock block");need(ram.bytes.size()==4&&ram.raw(4,L)==1,"single current RAM atomic success");
    }
    private static void originalBudgetBeforeMemory(){
        VolatileBits input=change(v(0x1000),0x1001,D,0x1003),post=change(v(0x2000),2,0x2002,0x2003);
        Ram ram=new Ram(mem("W",8,E-8,N.rbxBits()),mem("R",1,D+0x4E,0),mem("W",8,E-0x30,I+0x3727ED4),"IN1",mem("R",4,D+0x48,5),"B");
        ram.seed(8,E,RET);ram.seed(1,D+0x4E,0);ram.seed(4,D+0x48,5);
        var marker=new UnsupportedOperationException("original591budget");int[] count={0};
        try{EmbeddedQueueFullState3727EC0.execute(new FullCopy437Api.Input(entry(input),true,(h,g)->{need(h==0x3727EE4&&g==L,"header before lock");ram.event("B");throw marker;}),ram,f->{need(count[0]++==0,"one classify only");ram.event("IN1");frame(f,0x3727ECF,0x3727580,input,true);return reply(f,post,false);});throw new AssertionError("missing marker");}
        catch(UnsupportedOperationException actual){need(actual==marker&&count[0]==1,"same marker / no enqueue");}ram.end();need(!ram.bytes.containsKey(L),"unseeded lock untouched");
    }
    public static int verify(){flagAliasesPush();exactEqualAL();enqueueAL2AndFreshHomes();finiteAtomicRace();originalBudgetBeforeMemory();return 5;}
    public static void main(String[] args){System.out.println(verify());}
}
