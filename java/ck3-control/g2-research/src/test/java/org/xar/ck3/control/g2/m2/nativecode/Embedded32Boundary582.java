package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

/** Owner fixed original-source cases, not an implementation used to generate expectations. */
public final class Embedded32Boundary582 {
    private Embedded32Boundary582() { }
    private static final long I=0x140000000L,E=0x8000,D=0x10000,S=0x20000,RET=0x12345678,RET2=0x87654321L;
    private static final long TOKEN=I+0x448D230,TAIL=0xF1234567L,PAIR=0x1F1E1D1C1B1A1918L;
    private static final Bits128 X=new Bits128(0x101,0x102),P=new Bits128(0x901,0x902),A=new Bits128(TOKEN,PAIR);
    private static final NonvolatileBits N=new NonvolatileBits(0xB1,0xB2,0xB3,0xB4,0xB5,0xB6,0xB7,0xB8,new Bits128(0x701,0x702));
    private static VolatileBits v(long ax,long cx,long dx,long r8,long r9,long r10,long r11,Bits128 x0,boolean post) {
        long k=post?0x900:0x100;
        return new VolatileBits(ax,cx,dx,r8,r9,r10,r11,x0,new Bits128(k+3,k+4),new Bits128(k+5,k+6),
            new Bits128(k+7,k+8),new Bits128(k+9,k+10),new Bits128(k+11,k+12));
    }
    private static VolatileBits initial(long s) { return v(0x11,D,s,0x44,0x55,0x66,0x77,X,false); }
    private static VolatileBits post() { return v(0xCC,0xDD,0xEE,0x88,0x99,0xAA,0xBB,P,true); }
    private static NonvolatileBits offered(long count,long buffer,boolean token) {
        return new NonvolatileBits(0xB1,0xB2,D+0x10,count,token?TOKEN:0xB5,buffer,D,S,N.xmm6());
    }
    private static NonvolatileBits tailN(long s) { return new NonvolatileBits(0xB1,0xB2,D+0x10,0xB4,0xB5,0xB6,D,s,N.xmm6()); }
    private static void need(boolean condition,String label) { if(!condition) throw new AssertionError(label); }
    private static FullCopy437Api.CallResult result(VolatileBits bits,NonvolatileBits n,long rip,long sp,boolean df) {
        return new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(bits,rip,sp,n),df);
    }
    private record Expect(Embedded32Copy581Api.CallFrame frame,VolatileBits post,boolean df,Consumer<Ram> effect) { }
    private static Expect call(long site,long target,int length,boolean indirect,VolatileBits bits,NonvolatileBits n,
            boolean df,VolatileBits returned,boolean returnedDF,Consumer<Ram> effect) {
        var call=new GovernmentCrtBoundary185Api.Call(site,indirect?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:
            GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,E-0x48,bits,n);
        return new Expect(new Embedded32Copy581Api.CallFrame(call,
            new GovernmentCrtBoundary185Api.Entry(I,E-0x50,bits,n),df,length,I+site+length),returned,returnedDF,effect);
    }
    private static final Consumer<Ram> NONE=r->{ };
    private static final List<String> ALIAS=List.of("W8@1008:14448d230:0","R4@1008:4448d230:0","W4@1010:4448d230:0",
        "R4@100c:1:0","W4@1014:1:0","R16@1010:14448d230:1f1e1d1c1b1a1918","W16@1018:14448d230:1f1e1d1c1b1a1918");
    private static final class Ram implements FullCopy437Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<String> events=new ArrayList<>();
        static void put(Map<Long,Byte> map,int width,long address,long value) {
            for(int j=0;j<width;j++) map.put(address+j,(byte)(value>>>(8*j)));
        }
        void seed(int width,long address,long value) { put(bytes,width,address,value); }
        long raw(int width,long address) {
            long value=0;
            for(int j=0;j<width;j++) { Byte x=bytes.get(address+j);if(x==null) throw new AssertionError("unseeded "+Long.toHexString(address+j));
                value|=Byte.toUnsignedLong(x)<<(8*j); }
            return value;
        }
        void event(String op,int width,long address,long low,long high) {
            if(address>=0x1000 && address<0x1028) events.add(op+width+"@"+Long.toHexString(address)+":"+Long.toHexString(low)+":"+Long.toHexString(high));
        }
        void write(int width,long address,long value) {
            need((address>=E-0x100 && address+width<=E+0x30)||(address>=D && address+width<=D+0x80)||
                (address>=0x1000 && address+width<=0x1028),"owned write bounds");
            event("W",width,address,value,0);seed(width,address,value);
        }
        public int readDword(long a) { long v=raw(4,a);event("R",4,a,v,0);return (int)v; }
        public long readQword(long a) { long v=raw(8,a);event("R",8,a,v,0);return v; }
        public Bits128 read128(long a) { var v=new Bits128(raw(8,a),raw(8,a+8));event("R",16,a,v.lowBits(),v.highBits());return v; }
        public void writeDword(long a,int v) { write(4,a,Integer.toUnsignedLong(v)); }
        public void writeQword(long a,long v) { write(8,a,v); }
        public void write128(long a,Bits128 v) {
            need(a>=0x1000 && a+16<=0x1028,"owned W128 bounds");event("W",16,a,v.lowBits(),v.highBits());
            seed(8,a,v.lowBits());seed(8,a+8,v.highBits());
        }
        public int readUnsignedByte(long a) { throw new UnsupportedOperationException(); }
        public int readUnsignedWord(long a) { throw new UnsupportedOperationException(); }
        public int lockedXaddDword(long a,int v) { throw new UnsupportedOperationException(); }
        public void writeByte(long a,int v) { throw new UnsupportedOperationException(); }
        public void writeWord(long a,int v) { throw new UnsupportedOperationException(); }
        public void write128NonTemporal(long a,Bits128 v) { throw new UnsupportedOperationException(); }
        public FullCopy437Api.Bits256 read256(long a) { throw new UnsupportedOperationException(); }
        public void write256(long a,FullCopy437Api.Bits256 v) { throw new UnsupportedOperationException(); }
        public void write256NonTemporal(long a,FullCopy437Api.Bits256 v) { throw new UnsupportedOperationException(); }
        public void sfence() { throw new UnsupportedOperationException(); }
    }
    private static Ram memory(int count,int old,int capacity,long sourceBuffer,long destinationBuffer) {
        Ram r=new Ram();r.seed(8,E,RET);r.seed(8,S+0x10,sourceBuffer);r.seed(4,S+0x1C,Integer.toUnsignedLong(count));
        r.seed(8,D+0x10,destinationBuffer);r.seed(4,D+0x1C,Integer.toUnsignedLong(old));r.seed(4,D+0x18,Integer.toUnsignedLong(capacity));
        r.seed(4,S+0x28,TAIL);return r;
    }
    private static void data(Ram r) { for(int j=0;j<40;j++) r.seed(1,0x1000+j,j); }
    private static FullCopy437Api.CallResult run(Ram ram,long s,List<Expect> expected,
            GovernmentCrtBoundary185Api.LoopBudget budget,int[] cursor) {
        return Embedded32FullState3727180.execute(new FullCopy437Api.Input(
            new GovernmentCrtBoundary185Api.Entry(I,E,initial(s),N),true,budget),ram,f->{
                need(cursor[0]<expected.size(),"extra opaque call");Expect x=expected.get(cursor[0]++);
                need(f.equals(x.frame()),"complete frame "+(cursor[0]-1));
                x.effect().accept(ram);
                return result(x.post(),f.call().nonvolatileBits(),f.returnRipBits(),f.call().rspBits(),x.df());
            });
    }
    private static void finalWrites(Map<Long,Byte> map,boolean self,long count) {
        long[][] writes={{8,E-8,0xB3},{8,E-0x10,0xB7},{8,E-0x18,0xB8},{8,E-0x50,I+0x37272FD},{4,D+0x28,TAIL}};
        for(long[] c:writes) Ram.put(map,(int)c[0],c[1],c[2]);
        if(!self) {
            long[][] extra={{8,E+0x18,0xB4},{8,E-0x20,0xB5},{8,E-0x28,0xB6},{8,E+8,0xB1},{8,E+0x10,0xB2},{4,D+0x1C,count}};
            for(long[] c:extra) Ram.put(map,(int)c[0],c[1],c[2]);
        }
    }
    private static void normal(int mode) {
        boolean self=mode==0,alias=mode==2;long s=self?D:S;
        Ram r=self?new Ram():memory(alias?1:-1,alias?1:-1,0,alias?0x1000:0x50000,alias?0x1008:0x60000);
        if(self) { r.seed(8,E,RET);r.seed(4,D+0x28,TAIL); }
        if(alias) data(r);Map<Long,Byte> expected=new HashMap<>(r.bytes);finalWrites(expected,self,alias?1:0xFFFFFFFFL);
        List<Expect> calls=new ArrayList<>();
        if(!self) calls.add(call(0x37271BA,0x889660,5,false,v(S+0x10,D+0x10,S,0x44,0x55,0x66,0x77,X,false),
            offered(alias?1:-1,alias?0x1000:0x50000,false),true,post(),false,NONE));
        Bits128 current=alias?A:P;
        VolatileBits tail=self?v(TAIL,D+0x30,D+0x30,0x44,0x55,0x66,0x77,X,false):v(TAIL,D+0x30,S+0x30,0x88,0x99,0xAA,0xBB,current,true);
        VolatileBits last=self?v(0xCC,D,0xEE,0x88,0x99,0xAA,0xBB,P,true):v(TAIL,D,S+0x30,0x88,0x99,0xAA,0xBB,current,true);
        calls.add(call(0x37272F0,0x37282B0,5,false,tail,tailN(s),self,self?post():tail,self?false:true,
            self?mem->{mem.writeQword(E-8,0xA3);mem.writeQword(E,RET2);}:NONE));
        calls.add(call(0x37272F8,0x3727EC0,5,false,last,tailN(s),!self,last,true,NONE));
        if(self) { Ram.put(expected,8,E-8,0xA3);Ram.put(expected,8,E,RET2); }
        if(alias) { Ram.put(expected,8,0x1008,TOKEN);Ram.put(expected,8,0x1010,TOKEN);Ram.put(expected,8,0x1018,TOKEN);Ram.put(expected,8,0x1020,PAIR); }
        int[] steps={0},cursor={0};
        var actual=run(r,s,calls,(header,guard)->{
            need(alias && steps[0]++==0 && header==0x37272A0 && guard==0x100C,"new alias budget firststep");
        },cursor);
        NonvolatileBits finalN=self?new NonvolatileBits(0xB1,0xB2,0xA3,0xB4,0xB5,0xB6,0xB7,0xB8,N.xmm6()):N;
        VolatileBits finalV=self?v(D,D,0xEE,0x88,0x99,0xAA,0xBB,P,true):v(D,D,S+0x30,0x88,0x99,0xAA,0xBB,current,true);
        need(actual.equals(result(finalV,finalN,self?RET2:RET,E+8,true)),"whole NR/DF");
        need(r.bytes.equals(expected),"complete owned RAM final map");need(cursor[0]==calls.size(),"missing call");
        need(steps[0]==(alias?1:0),"budget count");need(r.events.equals(alias?ALIAS:List.of()),"seven live alias events");
    }
    private static void oldCopy(boolean stopOld) {
        Ram r=memory(2,1,0,0x1000,0x1000);data(r);r.seed(8,D+0x20,0x7000);r.seed(8,0x7000,0x7100);r.seed(8,0x7108,0xAA77);
        List<Expect> calls=new ArrayList<>();calls.add(call(0x37271BA,0x889660,5,false,v(S+0x10,D+0x10,S,0x44,0x55,0x66,0x77,X,false),offered(2,0x1000,false),true,post(),false,NONE));
        VolatileBits allocated=v(0x1008,0x7000,0x40,8,0x99,0xFA,0xFB,P,true);
        calls.add(call(0x37271EE,0xAA77,3,true,v(0x7100,0x7000,0x40,8,0x99,0xAA,0xBB,P,true),offered(2,0x1000,true),false,allocated,true,NONE));
        if(!stopOld) { var replaced=v(1,D+0x10,0x1008,1,2,0x1008,0xFB,A,true);
            calls.add(call(0x3727249,0x8874D0,5,false,replaced,offered(2,0x1000,true),true,replaced,false,mem->mem.writeQword(D+0x10,0x60000))); }
        var marker=new UnsupportedOperationException("old/new originalbudget582");int[] steps={0},cursor={0};
        try {
            run(r,S,calls,(header,guard)->{
                if(steps[0]++==0) { need(header==0x3727210 && guard==0x100C && cursor[0]==2,"old budget before firstwrite");if(stopOld) throw marker; }
                else { need(header==0x37272A0 && guard==0x100C && cursor[0]==3,"new budget after actualreplace");throw marker; }
            },cursor);throw new AssertionError("missing old/new budget stop");
        } catch(UnsupportedOperationException actual) { need(actual==marker,"original exception identity"); }
        need(cursor[0]==calls.size() && steps[0]==(stopOld?1:2),"old/new callbacks/headers");
        need(r.events.equals(stopOld?List.of():ALIAS),"old loop seven actual memory events");
        if(!stopOld) need(r.raw(8,0x1018)==TOKEN && r.raw(8,0x1020)==PAIR,"old alias final bytes");
    }
    private static void firstStop(boolean destroy) {
        int count=destroy?0:1,old=destroy?1:0;Ram r=memory(count,old,1,0x50000,0x60000);
        var e=call(0x37271BA,0x889660,5,false,v(S+0x10,D+0x10,S,0x44,0x55,0x66,0x77,X,false),offered(count,0x50000,false),true,post(),false,NONE);
        var marker=new UnsupportedOperationException("firstmemory marker582");int[] steps={0},cursor={0};
        try { run(r,S,List.of(e),(header,guard)->{
            need(steps[0]++==0 && cursor[0]==1 && header==(destroy?0x3727273:0x37272A0) && guard==(destroy?0x60000:0x5000C),"first memory hook");throw marker;
        },cursor);throw new AssertionError("missing first memory stop"); }
        catch(UnsupportedOperationException actual) { need(actual==marker,"exact first memory exception"); }
        need(steps[0]==1 && cursor[0]==1 && r.events.isEmpty(),"no extra effects after stop");
    }
    public static int verify() { normal(0);normal(1);normal(2);oldCopy(false);oldCopy(true);firstStop(true);firstStop(false);return 7; }
    public static void main(String[] args) { System.out.println(verify()); }
}
