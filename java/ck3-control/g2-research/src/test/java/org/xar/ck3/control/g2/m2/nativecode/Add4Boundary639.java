package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Owner independent literal protocol fixtures; COPY/virtual/reverse remain explicit ports. */
public final class Add4Boundary639 {
    private Add4Boundary639() { }
    private static final long I=0x140000000L,P=0x70001008L,H=0x8000000000001100L,S=0xf000000000002200L;
    private static final long OLD=0x8000,ALT=0x8100,ALT2=0x8200,NEW=0x9000,A=0xa000,A2=0xa100,T=0xb000,T2=0xb100;
    private static final long TARGET1=0x800000000000c001L,TARGET2=0xf00000000000c002L,RIP=0x140123456L,RIP2=0x140abcdefL,ORIGIN=0x3729877;
    private static final long B=0x9988776655443322L,R12=0x7766554433221100L,SI=0x8877665544332211L,DI=0x1234567887654321L;
    private static final QueueFp604Api.Mxcsr F0=new QueueFp604Api.Mxcsr(0,0),F1=new QueueFp604Api.Mxcsr(0x20,0x20),F2=new QueueFp604Api.Mxcsr(4,12),F3=new QueueFp604Api.Mxcsr(1,1),F4=new QueueFp604Api.Mxcsr(2,3),F5=new QueueFp604Api.Mxcsr(8,8);
    private record E(String k,long a,long v) { }
    private static void a(List<E> z,String k,long p,long v) { z.add(new E(k,p,v)); }
    private static Bits128 x(long n) { return new Bits128(n,~n); }
    private static VolatileBits bank(long b,long ax,long cx,long dx,long r8,long r9,Bits128 x0) { return new VolatileBits(ax,cx,dx,r8,r9,b+10,b+11,x0,x(b+1),x(b+2),x(b+3),x(b+4),x(b+5)); }
    private static VolatileBits in(int count,long index) { return bank(0x1000,0x111,H,index,S,S+4L*count,x(0x1000)); }
    private static VolatileBits offer(int n) { long b=0x2000L+n*0x1000L;return bank(b,n==1?NEW:b+1,b+2,b+3,b+4,b+5,x(b)); }
    private static VolatileBits change(VolatileBits v,long ax,long cx,long dx,long r8,long r9) { return new VolatileBits(ax,cx,dx,r8,r9,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5()); }
    private static NonvolatileBits n() { return new NonvolatileBits(0x101,0x102,0x103,0x104,0x105,0x106,0x107,0x108,x(0x109)); }
    private static void same(boolean yes,String text) { if(!yes)throw new AssertionError(text); }
    private static final class Ram implements Add4Fp639Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<E> events=new ArrayList<>();Registers observer;
        void seed(long p,int w,long v) { for(int j=0;j<w;j++)bytes.put(p+j,(byte)(v>>>(8*j))); }
        long peek(long p,int w) { long v=0;for(int j=0;j<w;j++)v|=(bytes.getOrDefault(p+j,(byte)0)&255L)<<(8*j);return v; }
        @Override public int readDword(long p) { int v=(int)peek(p,4);a(events,"R32",p,v);return v; }
        @Override public long readQword(long p) { long v=peek(p,8);a(events,"R64",p,v);if(observer!=null&&p==P+0x20)a(events,"PUBLIC-EAX",p,observer.rax);return v; }
        @Override public void writeDword(long p,int v) { a(events,"W32",p,v);seed(p,4,v); }
        @Override public void writeQword(long p,long v) { a(events,"W64",p,v);seed(p,8,v); }
        @Override public void writeByte(long p,int v) { a(events,"W8",p,v&255);seed(p,1,v); }
        @Override public int readUnsignedByte(long p) { throw new AssertionError("unexpected byte read"); }
        @Override public Bits128 read128(long p) { throw new AssertionError("no implicit COPY algorithm"); }
        @Override public void write128(long p,Bits128 v) { throw new AssertionError("no implicit COPY algorithm"); }
        @Override public int lockedXaddDword(long p,int v) { throw new AssertionError("unexpected atomic"); }
        @Override public void writeWord(long p,int v) { throw new AssertionError("unexpected word"); }
        @Override public void write128NonTemporal(long p,Bits128 v) { throw new AssertionError("unexpected NT"); }
        @Override public void sfence() { throw new AssertionError("unexpected fence"); }
        @Override public int readUnsignedWord(long p) { throw new AssertionError("unexpected R16"); }
        @Override public FullCopy437Api.Bits256 read256(long p) { throw new AssertionError("unexpected R256"); }
        @Override public void write256(long p,FullCopy437Api.Bits256 v) { throw new AssertionError("unexpected W256"); }
        @Override public void write256NonTemporal(long p,FullCopy437Api.Bits256 v) { throw new AssertionError("unexpected NT256"); }
    }
    private static Ram initial(int mode) {
        Ram r=new Ram();r.seed(P,8,RIP);r.seed(H,8,OLD);r.seed(H+8,4,mode==0?4:mode==1?16777217:1);r.seed(H+0xc,4,mode==0?1:mode==1?16777217:0);
        r.seed(H+0x10,8,A);r.seed(A,8,T);r.seed(T+8,8,TARGET1);r.seed(A2,8,T2);r.seed(T2+0x10,8,TARGET2);r.seed(I+0x49f64f0,4,0x3fc00000);r.seed(S,8,0x1122334455667788L);r.seed(0x7770,1,0xcc);return r;
    }
    private static QueueFp604Api.Input input(int count,long index,QueueFp604Api.Mxcsr fp) { return new QueueFp604Api.Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,P,in(count,index),n()),true,(pc,p)->{throw new AssertionError("no implicit lower loop");}),fp); }
    private static void compare(Ram r,Ram want,List<E> z) {
        for(E e:z)switch(e.k()) {case "W64"->want.seed(e.a(),8,e.v());case "W32"->want.seed(e.a(),4,e.v());case "W8"->want.seed(e.a(),1,e.v());default->{}}
        if(!r.events.equals(z)) {int j=0;while(j<r.events.size()&&j<z.size()&&r.events.get(j).equals(z.get(j)))j++;throw new AssertionError("639 event "+j+" actual="+(j<r.events.size()?r.events.get(j):"END")+" expected="+(j<z.size()?z.get(j):"END"));}same(r.bytes.equals(want.bytes),"complete byteRAM");
    }
    private static void prologue(List<E> z,int size,int cap,int newsize) {
        a(z,"W64",P-8,n().rbxBits());a(z,"W64",P-0x10,n().r13Bits());a(z,"W64",P-0x18,n().r14Bits());a(z,"W64",P-0x20,n().r15Bits());
        a(z,"R32",H+0xc,size);a(z,"W64",P-0x28,n().r12Bits());a(z,"R32",H+8,cap);a(z,"W32",P+8,newsize);
    }
    private static void pops(List<E> z,long rip) {a(z,"R64",P-0x20,n().r15Bits());a(z,"R64",P-0x18,n().r14Bits());a(z,"R64",P-0x10,n().r13Bits());a(z,"R64",P-8,n().rbxBits());a(z,"R64",P,rip);}
    private static void frame(Add4Fp639Api.CallFrame f,long site,long target,int len,VolatileBits v,NonvolatileBits nv,boolean df,QueueFp604Api.Mxcsr fp) {
        var kind=len==3?GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE:GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA;
        same(f.call().equals(new GovernmentCrtBoundary185Api.Call(site,kind,target,P-0x48,v,nv)),"full call state "+site);same(f.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(I,P-0x50,v,nv)),"child state");same(f.returnRipBits()==I+site+len&&f.instructionLength()==len&&f.directionFlagSet()==df&&f.preMxcsr()==fp,"frame metadata/currentFP");
    }
    private static QueueFp604Api.Normal normal(Add4Fp639Api.CallFrame f,VolatileBits v,boolean df,QueueFp604Api.Mxcsr fp,long wrong) {return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,f.returnRipBits()+wrong,P-0x48,f.call().nonvolatileBits()),df),fp);}
    private static void empty() {
        Ram r=initial(0),w=initial(0);var out=Add4FullState639.execute(input(0,0,F0),r,f->{throw new AssertionError("empty call");},ORIGIN);same(out instanceof QueueFp604Api.Normal,"empty normal");var q=(QueueFp604Api.Normal)out;same(q.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(in(0,0),RIP,P+8,n()))&&q.base().postDirectionFlagSet()&&q.postMxcsr()==F0,"empty full state");List<E> z=new ArrayList<>();a(z,"R64",P,RIP);compare(r,w,z);
    }
    private static void nongrowth(int mode) {
        Ram r=initial(0),w=initial(0);int[] calls={0};QueueFp604Api.Stopped[] stopped={null};QueueFp604Api.Outcome out=null;boolean reject=false;
        try {out=Add4FullState639.execute(input(1,1,F0),r,f->{int j=calls[0]++;var nv=new NonvolatileBits(1,n().rbpBits(),n().rsiBits(),n().rdiBits(),1,S,H,4,n().xmm6());
            if(j==0) {frame(f,0xadd1f7,0x4226860,5,change(in(1,1),OLD,OLD+4,S,4,S+4),nv,true,F0);a(r.events,"CALL",0xadd1f7,0x4226860);r.writeQword(H,ALT);r.writeDword(H+0xc,-2);r.writeByte(0x7770,0x77);return normal(f,offer(1),false,F1,mode==2?1:0);}
            same(j==1,"onlytwo nongrowth calls");frame(f,0xadd219,0x9d0950,5,change(offer(1),-1,ALT+4,ALT-8,ALT-4,ALT),nv,false,F1);a(r.events,"CALL",0xadd219,0x9d0950);r.writeQword(P-0x28,R12);r.writeQword(P,RIP2);
            if(mode==1) {stopped[0]=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(f.childEntry(),0xadd219,false,F1),0,ORIGIN);return stopped[0];}return normal(f,offer(2),true,F2,0);
        },ORIGIN);}catch(IllegalArgumentException ex){if(mode!=2)throw ex;reject=true;}
        same(reject==(mode==2)&&calls[0]==(mode==2?1:2),"nongrowth calls/rejection");if(mode==1)same(out==stopped[0],"exact Stopped identity");if(mode==0){same(out instanceof QueueFp604Api.Normal,"normal");var q=(QueueFp604Api.Normal)out;var nv=new NonvolatileBits(n().rbxBits(),n().rbpBits(),n().rsiBits(),n().rdiBits(),R12,n().r13Bits(),n().r14Bits(),n().r15Bits(),n().xmm6());same(q.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(offer(2),RIP2,P+8,nv))&&q.base().postDirectionFlagSet()&&q.postMxcsr()==F2,"nongrowth fullpost/alias/FP");}
        List<E> z=new ArrayList<>();prologue(z,1,4,2);a(z,"R64",H,OLD);a(z,"W64",P-0x50,I+0xadd1fc);a(z,"CALL",0xadd1f7,0x4226860);a(z,"W64",H,ALT);a(z,"W32",H+0xc,-2);a(z,"W8",0x7770,0x77);
        if(mode!=2){a(z,"R32",H+0xc,-2);a(z,"R64",H,ALT);a(z,"W32",H+0xc,-1);a(z,"W64",P-0x50,I+0xadd21e);a(z,"CALL",0xadd219,0x9d0950);a(z,"W64",P-0x28,R12);a(z,"W64",P,RIP2);if(mode==0){a(z,"R64",P-0x28,R12);pops(z,RIP2);}}compare(r,w,z);
    }
    private static void cvtStop() {
        Ram r=initial(1),w=initial(1);var out=Add4FullState639.execute(input(1,0,F0),r,f->{throw new AssertionError("CVTstop call");},ORIGIN);same(out instanceof QueueFp604Api.Stopped,"CVTstop");var q=(QueueFp604Api.Stopped)out;
        var vv=new VolatileBits(16777217,16777218,16777217,4,S+4,in(1,0).r10Bits(),in(1,0).r11Bits(),new Bits128(16777217,0),in(1,0).xmm1(),in(1,0).xmm2(),in(1,0).xmm3(),in(1,0).xmm4(),in(1,0).xmm5());var nv=new NonvolatileBits(0,16777218,n().rsiBits(),n().rdiBits(),1,S,H,4,n().xmm6());
        same(q.reason()==QueueFp604Api.StopReason.MISSING_FP_INPUT&&q.snapshot().currentState().equals(new GovernmentCrtBoundary185Api.Entry(I,P-0x48,vv,nv))&&q.snapshot().instructionRva()==0xadd128&&q.snapshot().directionFlagSet()&&q.snapshot().mxcsr()==F0&&q.raisedConditionBits()==0&&q.originCallSiteRva()==ORIGIN,"CVT local fullprefix/origin");List<E> z=new ArrayList<>();prologue(z,16777217,16777217,16777218);a(z,"W64",P+0x10,n().rbpBits());compare(r,w,z);
    }
    private static NonvolatileBits gn(int at) {return new NonvolatileBits(0,2,at==0?n().rsiBits():NEW,at==0?n().rdiBits():0,2,S,H,8,n().xmm6());}
    private static void growth() {
        Ram r=initial(2),w=initial(2);int[] count={0};var out=Add4FullState639.execute(input(2,0,QueueFp604Api.Mxcsr.exact(0x1f80)),r,f->{int j=count[0]++;
            if(j==0){same(f.preMxcsr().isExact()&&f.preMxcsr().requireExactBits()==0x1fa0,"prior precision flag");var v=change(in(2,0),T,A,8,4,S+8);v=new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),new Bits128(0x3fc00000,0),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());frame(f,0xadd153,TARGET1,3,v,gn(0),true,f.preMxcsr());a(r.events,"CALL",0xadd153,TARGET1);r.writeQword(H,ALT);r.writeQword(H+0x10,A2);return normal(f,offer(1),false,F1,0);}
            if(j==1){frame(f,0xadd16d,0x4226860,5,change(offer(1),NEW,NEW,ALT,0,offer(1).r9Bits()),gn(1),false,F1);a(r.events,"CALL",0xadd16d,0x4226860);r.writeByte(0x7770,0x11);return normal(f,offer(2),true,F2,0);}
            if(j==2){frame(f,0xadd17c,0x4226860,5,change(offer(2),offer(2).raxBits(),NEW,S,8,offer(2).r9Bits()),gn(1),true,F2);a(r.events,"CALL",0xadd17c,0x4226860);r.writeDword(NEW,0x11223344);r.writeDword(NEW+4,0x55667788);return normal(f,offer(3),false,F3,0);}
            if(j==3){frame(f,0xadd1a0,0x4226860,5,change(offer(3),2,NEW+8,ALT,0,offer(3).r9Bits()),gn(1),false,F3);a(r.events,"CALL",0xadd1a0,0x4226860);r.writeQword(H,ALT2);r.writeDword(P+8,0x80000001);r.writeQword(P-0x28,R12);r.writeQword(P+0x10,B);r.writeQword(P+0x18,SI);r.writeQword(P+0x20,DI);return normal(f,offer(4),true,F4,0);}
            same(j==4,"five growth calls");frame(f,0xadd1b5,TARGET2,3,change(offer(4),T2,A2,ALT2,4,offer(4).r9Bits()),gn(1),true,F4);a(r.events,"CALL",0xadd1b5,TARGET2);r.writeQword(P,RIP2);return normal(f,offer(5),false,F5,0);
        },ORIGIN);
        same(count[0]==5&&out instanceof QueueFp604Api.Normal,"allfive calls including twozerobyteCOPY");var q=(QueueFp604Api.Normal)out;var nv=new NonvolatileBits(n().rbxBits(),B,SI,DI,R12,n().r13Bits(),n().r14Bits(),n().r15Bits(),n().xmm6());same(q.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(change(offer(5),0x80000001L,offer(5).rcxBits(),offer(5).rdxBits(),offer(5).r8Bits(),offer(5).r9Bits()),RIP2,P+8,nv))&&!q.base().postDirectionFlagSet()&&q.postMxcsr()==F5,"growth currentfullstate/freshalias/z32");
        List<E> z=new ArrayList<>();prologue(z,0,1,2);a(z,"W64",P+0x10,n().rbpBits());a(z,"W64",P+0x18,n().rsiBits());a(z,"W64",P+0x20,n().rdiBits());a(z,"R32",I+0x49f64f0,0x3fc00000);a(z,"R64",H+0x10,A);a(z,"R64",A,T);a(z,"R64",T+8,TARGET1);a(z,"W64",P-0x50,I+0xadd156);a(z,"CALL",0xadd153,TARGET1);a(z,"W64",H,ALT);a(z,"W64",H+0x10,A2);
        a(z,"R64",H,ALT);a(z,"W64",P-0x50,I+0xadd172);a(z,"CALL",0xadd16d,0x4226860);a(z,"W8",0x7770,0x11);a(z,"W64",P-0x50,I+0xadd181);a(z,"CALL",0xadd17c,0x4226860);a(z,"W32",NEW,0x11223344);a(z,"W32",NEW+4,0x55667788);a(z,"R64",H,ALT);a(z,"R32",H+0xc,0);a(z,"W64",P-0x50,I+0xadd1a5);a(z,"CALL",0xadd1a0,0x4226860);a(z,"W64",H,ALT2);a(z,"W32",P+8,0x80000001);a(z,"W64",P-0x28,R12);a(z,"W64",P+0x10,B);a(z,"W64",P+0x18,SI);a(z,"W64",P+0x20,DI);
        a(z,"R64",H+0x10,A2);a(z,"R64",H,ALT2);a(z,"R64",A2,T2);a(z,"R64",T2+0x10,TARGET2);a(z,"W64",P-0x50,I+0xadd1b8);a(z,"CALL",0xadd1b5,TARGET2);a(z,"W64",P,RIP2);commitEvents(z,RIP2,false);compare(r,w,z);
    }
    private static void commitEvents(List<E> z,long rip,boolean probe) {a(z,"R32",P+8,0x80000001);a(z,"R64",P+0x20,DI);if(probe)a(z,"PUBLIC-EAX",P+0x20,0x80000001L);a(z,"R64",P-0x28,R12);a(z,"W64",H,NEW);a(z,"R64",P+0x18,SI);a(z,"W32",H+8,2);a(z,"R64",P+0x10,B);a(z,"W32",H+0xc,0x80000001);pops(z,rip);}
    private static void publicCommit() {
        Ram r=initial(2),w=initial(2);for(Ram m:new Ram[]{r,w}){m.seed(P+8,4,0x80000001);m.seed(P+0x20,8,DI);m.seed(P-0x28,8,R12);m.seed(P+0x18,8,SI);m.seed(P+0x10,8,B);m.seed(P-0x20,8,n().r15Bits());m.seed(P-0x18,8,n().r14Bits());m.seed(P-0x10,8,n().r13Bits());m.seed(P-8,8,n().rbxBits());}
        Registers rr=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(I,P-0x48,offer(5),n()));rr.r14=H;rr.rsi=NEW;rr.rbp=2;r.observer=rr;
        var q=Add4GrowthCommit639.finish(rr,r,true,F0);same(rr.rsp==P+8&&rr.rax==0x80000001L&&q.base().normalReturn().callerRspBits()==rr.rsp&&q.postMxcsr()==F0&&q.base().postDirectionFlagSet(),"publicRETadvancesRSP/zeroextendsEAX/currentFP");List<E> z=new ArrayList<>();commitEvents(z,RIP,true);compare(r,w,z);
    }
    public static int verify() {empty();nongrowth(0);nongrowth(1);nongrowth(2);cvtStop();growth();publicCommit();return 7;}
    public static void main(String[] args) {System.out.println(verify());}
}
