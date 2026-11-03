package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

/** Owner literal source witness; six new represented-state groups, no Native or lower algorithms. */
public final class Range16Boundary638 {
    private Range16Boundary638() { }
    private static final long I=0x140000000L,P=0x70001008L,H=0x8000000000001100L,S=0xf000000000002200L;
    private static final long NEW=0x9000,OLD=0x8000,ALT=0x8200,A=0xa000,A2=0xa100,T=0xb000,T2=0xb100;
    private static final long TARGET1=0x800000000000c001L,TARGET2=0xf00000000000c002L,RIP=0x140123456L,RIP2=0x140abcdefL,ORIGIN=0x3729846;
    private static final long SAVED_B=0x9988776655443322L,SAVED_12=0x7766554433221100L,SAVED_13=0x8877665544332211L;
    private static final Bits128 W1=new Bits128(0x1122334455667788L,0x99aabbccddeeff00L),W2=new Bits128(0x1020304050607080L,0x90a0b0c0d0e0f000L);
    private static final QueueFp604Api.Mxcsr F0=new QueueFp604Api.Mxcsr(0,0),F1=new QueueFp604Api.Mxcsr(0x20,0x20),F2=new QueueFp604Api.Mxcsr(4,12);
    private record E(String k,long a,long lo,long hi) { }
    private static void a(List<E> z,String k,long address,long value) { z.add(new E(k,address,value,0)); }
    private static void v(List<E> z,String k,long address,Bits128 value) { z.add(new E(k,address,value.lowBits(),value.highBits())); }
    private static Bits128 x(long n) { return new Bits128(n,~n); }
    private static VolatileBits bank(long b,long ax,long cx,long dx,long r8,long r9,Bits128 x0) {
        return new VolatileBits(ax,cx,dx,r8,r9,b+10,b+11,x0,x(b+1),x(b+2),x(b+3),x(b+4),x(b+5));
    }
    private static VolatileBits in(int count) { return bank(0x1000,0x111,H,0,S,S+16L*count,x(0x1000)); }
    private static VolatileBits offer1() { return bank(0x2000,NEW,0x222,0x233,0x244,0x255,x(0x2000)); }
    private static VolatileBits offer2() { return bank(0x3000,0x311,0x322,0x333,0x344,0x355,x(0x3000)); }
    private static NonvolatileBits n() { return new NonvolatileBits(0x101,0x102,0x103,0x104,0x105,0x106,0x107,0x108,x(0x109)); }
    private static final class Ram implements Range16Fp638Api.Memory {
        final Map<Long,Byte> bytes=new HashMap<>();final List<E> events=new ArrayList<>();
        void seed(long p,int width,long value) { for(int i=0;i<width;i++)bytes.put(p+i,(byte)(value>>>(8*i))); }
        void word(long p,Bits128 value) { seed(p,8,value.lowBits());seed(p+8,8,value.highBits()); }
        long peek(long p,int width) { long v=0;for(int i=0;i<width;i++)v|=(bytes.getOrDefault(p+i,(byte)0)&255L)<<(8*i);return v; }
        @Override public int readDword(long p) { int q=(int)peek(p,4);a(events,"R32",p,q);return q; }
        @Override public long readQword(long p) { long q=peek(p,8);a(events,"R64",p,q);return q; }
        @Override public void writeDword(long p,int q) { a(events,"W32",p,q);seed(p,4,q); }
        @Override public void writeQword(long p,long q) { a(events,"W64",p,q);seed(p,8,q); }
        @Override public int readUnsignedByte(long p) { throw new AssertionError("unexpected R8"); }
        @Override public void writeByte(long p,int q) { a(events,"W8",p,q&255);seed(p,1,q); }
        @Override public Bits128 read128(long p) { Bits128 q=new Bits128(peek(p,8),peek(p+8,8));v(events,"R128",p,q);return q; }
        @Override public void write128(long p,Bits128 q) { v(events,"W128",p,q);word(p,q); }
        @Override public int lockedXaddDword(long p,int q) { throw new AssertionError("unexpected atomic"); }
        @Override public void writeWord(long p,int q) { throw new AssertionError("unexpected word"); }
        @Override public void write128NonTemporal(long p,Bits128 q) { throw new AssertionError("unexpected NT"); }
        @Override public void sfence() { throw new AssertionError("unexpected fence"); }
        @Override public int readUnsignedWord(long p) { throw new AssertionError("unexpected R16"); }
        @Override public FullCopy437Api.Bits256 read256(long p) { throw new AssertionError("unexpected R256"); }
        @Override public void write256(long p,FullCopy437Api.Bits256 q) { throw new AssertionError("unexpected W256"); }
        @Override public void write256NonTemporal(long p,FullCopy437Api.Bits256 q) { throw new AssertionError("unexpected NT256"); }
    }
    private static Ram initial(int mode) {
        Ram r=new Ram();r.seed(P,8,RIP);r.seed(H,8,mode==0?S+8:OLD);r.seed(H+8,4,mode==0?4:mode==1?16777217:1);
        r.seed(H+0xc,4,mode==1?16777217:0);r.seed(H+0x10,8,A);r.seed(A,8,T);r.seed(T+8,8,TARGET1);r.seed(A2,8,T2);r.seed(T2+0x10,8,TARGET2);
        r.word(S,W1);r.word(S+16,W2);r.seed(I+0x49f64f0,4,0x3fc00000);r.seed(0x7770,1,0xcc);return r;
    }
    private static QueueFp604Api.Input input(int count,QueueFp604Api.Mxcsr fp,GovernmentCrtBoundary185Api.LoopBudget budget) {
        return new QueueFp604Api.Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(I,P,in(count),n()),true,budget),fp);
    }
    private static void same(boolean q,String msg) { if(!q)throw new AssertionError(msg); }
    private static void compare(Ram r,Ram wanted,List<E> expected) {
        for(E e:expected)switch(e.k()) {
            case "W64" -> wanted.seed(e.a(),8,e.lo());case "W32" -> wanted.seed(e.a(),4,e.lo());
            case "W8" -> wanted.seed(e.a(),1,e.lo());case "W128" -> wanted.word(e.a(),new Bits128(e.lo(),e.hi()));default -> { }
        }
        if(!r.events.equals(expected)) { int j=0;while(j<r.events.size()&&j<expected.size()&&r.events.get(j).equals(expected.get(j)))j++;
            throw new AssertionError("638 event "+j+" actual="+(j<r.events.size()?r.events.get(j):"END")+" expected="+(j<expected.size()?expected.get(j):"END")); }
        same(r.bytes.equals(wanted.bytes),"all byteRAM including padding");
    }
    private static void prologue(List<E> z,int size,int cap) {
        a(z,"W64",P-8,n().rbxBits());a(z,"W64",P-0x10,n().rsiBits());a(z,"W64",P-0x18,n().rdiBits());a(z,"W64",P-0x20,n().r14Bits());
        a(z,"R32",H+0xc,size);a(z,"W64",P+8,n().rbpBits());a(z,"R32",H+8,cap);a(z,"W64",P-0x28,n().r15Bits());
    }
    private static void epilogue(List<E> z) {
        a(z,"R64",P+8,n().rbpBits());a(z,"R64",P-0x28,n().r15Bits());a(z,"R64",P-0x20,n().r14Bits());
        a(z,"R64",P-0x18,n().rdiBits());a(z,"R64",P-0x10,n().rsiBits());a(z,"R64",P-8,n().rbxBits());a(z,"R64",P,RIP);
    }
    private static void frame(Range16Fp638Api.CallFrame f,long site,long target,int len,VolatileBits bits,NonvolatileBits nv,boolean df,QueueFp604Api.Mxcsr fp) {
        var kind=site==0x8c723f?GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA:GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE;
        same(f.call().equals(new GovernmentCrtBoundary185Api.Call(site,kind,target,P-0x48,bits,nv)),"full call state "+site);
        same(f.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(I,P-0x50,bits,nv)),"child state");
        same(f.instructionLength()==len&&f.returnRipBits()==I+site+len&&f.directionFlagSet()==df&&f.preMxcsr()==fp,"frame metadata/currentFP identity");
    }
    private static QueueFp604Api.Normal normal(Range16Fp638Api.CallFrame f,VolatileBits v,boolean df,QueueFp604Api.Mxcsr fp,long ripDelta) {
        return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(v,f.returnRipBits()+ripDelta,P-0x48,f.call().nonvolatileBits()),df),fp);
    }
    private static void empty() {
        Ram r=initial(0),want=initial(0);var e=new GovernmentCrtBoundary185Api.Entry(I,P,in(0),n());
        var out=Range16FullState638.execute(new QueueFp604Api.Input(new FullCopy437Api.Input(e,true,(pc,p)->{throw new AssertionError("empty budget");}),F0),r,f->{throw new AssertionError("empty call");},ORIGIN);
        same(out instanceof QueueFp604Api.Normal,"empty Normal");var q=(QueueFp604Api.Normal)out;
        same(q.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(in(0),RIP,P+8,n()))&&q.base().postDirectionFlagSet()&&q.postMxcsr()==F0,"empty complete preserved state");
        List<E> z=new ArrayList<>();a(z,"R64",P,RIP);compare(r,want,z);
    }
    private static void nongrowth(int mode) {
        Ram r=initial(0),want=initial(0);int[] calls={0};QueueFp604Api.Stopped[] stop={null};
        QueueFp604Api.Outcome out=null;boolean rejected=false;
        try { out=Range16FullState638.execute(input(1,F0,(pc,p)->a(r.events,"B",p,pc)),r,f->{
            calls[0]++;var vv=new VolatileBits(1,S+8,S+8,S+24,S+8,in(1).r10Bits(),in(1).r11Bits(),W1,in(1).xmm1(),in(1).xmm2(),in(1).xmm3(),in(1).xmm4(),in(1).xmm5());
            var nn=new NonvolatileBits(S+16,1,S+16,H,n().r12Bits(),n().r13Bits(),0,1,n().xmm6());frame(f,0x8c723f,0x8f8550,5,vv,nn,true,F0);
            a(r.events,"CALL",0x8c723f,0x8f8550);r.writeQword(P+8,SAVED_B);r.writeQword(P,RIP2);r.writeByte(0x7770,0x77);
            if(mode==1) { stop[0]=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(f.childEntry(),0x8c723f,true,F0),0,ORIGIN);return stop[0]; }
            return normal(f,offer2(),false,F2,mode==2?1:0);
        },ORIGIN); } catch(IllegalArgumentException ex) { if(mode!=2)throw ex;rejected=true; }
        same(calls[0]==1&&rejected==(mode==2),"nongrowth path count");
        if(mode==0) { same(out instanceof QueueFp604Api.Normal,"nongrowth Normal");var q=(QueueFp604Api.Normal)out;var nn=new NonvolatileBits(n().rbxBits(),SAVED_B,n().rsiBits(),n().rdiBits(),n().r12Bits(),n().r13Bits(),n().r14Bits(),n().r15Bits(),n().xmm6());same(q.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(offer2(),RIP2,P+8,nn))&&!q.base().postDirectionFlagSet()&&q.postMxcsr()==F2,"nongrowth postV/freshalias/currentFPDF"); }
        if(mode==1)same(out==stop[0],"foreign Stopped identity");
        List<E> z=new ArrayList<>();prologue(z,0,4);a(z,"R64",H,S+8);a(z,"B",S,0x8c7200);v(z,"R128",S,W1);v(z,"W128",S+8,W1);
        a(z,"R32",H+0xc,0);a(z,"R64",H,S+8);a(z,"W32",H+0xc,1);a(z,"W64",P-0x50,I+0x8c7244);a(z,"CALL",0x8c723f,0x8f8550);
        a(z,"W64",P+8,SAVED_B);a(z,"W64",P,RIP2);a(z,"W8",0x7770,0x77);
        if(mode==0) { a(z,"R64",P+8,SAVED_B);a(z,"R64",P-0x28,n().r15Bits());a(z,"R64",P-0x20,n().r14Bits());a(z,"R64",P-0x18,n().rdiBits());a(z,"R64",P-0x10,n().rsiBits());a(z,"R64",P-8,n().rbxBits());a(z,"R64",P,RIP2); }
        compare(r,want,z);
    }
    private static void cvtStop() {
        Ram r=initial(1),want=initial(1);var out=Range16FullState638.execute(input(1,F0,(pc,p)->{throw new AssertionError("CVTstop budget");}),r,f->{throw new AssertionError("CVTstop call");},ORIGIN);
        same(out instanceof QueueFp604Api.Stopped,"CVT softwareStop");var q=(QueueFp604Api.Stopped)out;
        var vv=new VolatileBits(16777217,A,0,8,S+16,in(1).r10Bits(),in(1).r11Bits(),new Bits128(16777217,0),in(1).xmm1(),in(1).xmm2(),in(1).xmm3(),in(1).xmm4(),in(1).xmm5());
        var nn=new NonvolatileBits(S,1,S+16,H,n().r12Bits(),n().r13Bits(),0,16777218,n().xmm6());
        same(q.reason()==QueueFp604Api.StopReason.MISSING_FP_INPUT&&q.snapshot().instructionRva()==0x8c7104&&q.snapshot().currentState().equals(new GovernmentCrtBoundary185Api.Entry(I,P-0x48,vv,nn))&&q.snapshot().directionFlagSet()&&q.snapshot().mxcsr()==F0&&q.raisedConditionBits()==0&&q.originCallSiteRva()==ORIGIN,"CVT current full stop/suppliedorigin");
        List<E> z=new ArrayList<>();prologue(z,16777217,16777217);a(z,"R64",H+0x10,A);compare(r,want,z);
    }
    private static void growth() {
        Ram r=initial(2),want=initial(2);int[] calls={0};QueueFp604Api.Mxcsr fpIn=QueueFp604Api.Mxcsr.exact(0x1f80);QueueFp604Api.Mxcsr[] firstFP={null};
        var out=Range16FullState638.execute(input(2,fpIn,(pc,p)->a(r.events,"B",p,pc)),r,f->{int k=calls[0]++;
            if(k==0) {
                same(f.preMxcsr().isExact()&&f.preMxcsr().requireExactBits()==0x1fa0,"CVTT addsPrecision beforeallocate");firstFP[0]=f.preMxcsr();
                var vv=new VolatileBits(T,A,32,8,S+32,in(2).r10Bits(),in(2).r11Bits(),new Bits128(0x3fc00000,0),in(2).xmm1(),in(2).xmm2(),in(2).xmm3(),in(2).xmm4(),in(2).xmm5());
                var nn=new NonvolatileBits(S,2,S+32,H,n().r12Bits(),2,0,2,n().xmm6());frame(f,0x8c7131,TARGET1,3,vv,nn,true,firstFP[0]);a(r.events,"CALL",0x8c7131,TARGET1);
                r.writeQword(H,ALT);r.writeQword(H+0x10,A2);return normal(f,offer1(),false,F1,0);
            }
            same(k==1,"onlytwo growth calls");var vv=new VolatileBits(T2,A2,ALT,8,ALT,0,offer1().r11Bits(),W2,offer1().xmm1(),offer1().xmm2(),offer1().xmm3(),offer1().xmm4(),offer1().xmm5());
            var nn=new NonvolatileBits(S+32,2,S+32,H,NEW,2,0,2,n().xmm6());frame(f,0x8c71d7,TARGET2,3,vv,nn,false,F1);a(r.events,"CALL",0x8c71d7,TARGET2);
            r.writeQword(P+0x10,SAVED_12);r.writeQword(P+0x18,SAVED_13);return normal(f,offer2(),true,F2,0);
        },ORIGIN);
        same(calls[0]==2&&out instanceof QueueFp604Api.Normal,"growth twoNormal");var q=(QueueFp604Api.Normal)out;
        var nn=new NonvolatileBits(n().rbxBits(),n().rbpBits(),n().rsiBits(),n().rdiBits(),SAVED_12,SAVED_13,n().r14Bits(),n().r15Bits(),n().xmm6());
        same(q.base().normalReturn().equals(new GovernmentCrtBoundary185Api.NormalReturn(offer2(),RIP,P+8,nn))&&q.base().postDirectionFlagSet()&&q.postMxcsr()==F2,"growth fullpost/currentFPDF/freshspills");
        List<E> z=new ArrayList<>();prologue(z,0,1);a(z,"R64",H+0x10,A);a(z,"W64",P+0x10,n().r12Bits());a(z,"W64",P+0x18,n().r13Bits());a(z,"R32",I+0x49f64f0,0x3fc00000);
        a(z,"R64",A,T);a(z,"R64",T+8,TARGET1);a(z,"W64",P-0x50,I+0x8c7134);a(z,"CALL",0x8c7131,TARGET1);a(z,"W64",H,ALT);a(z,"W64",H+0x10,A2);
        a(z,"R64",H,ALT);a(z,"B",S,0x8c7170);v(z,"R128",S,W1);v(z,"W128",NEW,W1);a(z,"B",S+16,0x8c7170);v(z,"R128",S+16,W2);v(z,"W128",NEW+16,W2);
        a(z,"R64",H,ALT);a(z,"R32",H+0xc,0);a(z,"R64",H+0x10,A2);a(z,"R64",A2,T2);a(z,"R64",T2+0x10,TARGET2);a(z,"W64",P-0x50,I+0x8c71da);a(z,"CALL",0x8c71d7,TARGET2);
        a(z,"W64",P+0x10,SAVED_12);a(z,"W64",P+0x18,SAVED_13);a(z,"W64",H,NEW);a(z,"R64",P+0x10,SAVED_12);a(z,"W32",H+8,2);a(z,"R64",P+0x18,SAVED_13);a(z,"W32",H+0xc,2);epilogue(z);compare(r,want,z);
    }
    private static void signedBlock() {
        Ram r=initial(2),want=initial(2);r.seed(H+0xc,4,-1);want.seed(H+0xc,4,-1);
        var rr=org.xar.ck3.research.m5.GovernmentCallee164Api.registers(new org.xar.ck3.research.m5.GovernmentCallee164Api.Entry(I,P,in(1),n()));
        rr.rdi=H;rr.rbx=S;rr.rsi=S+16;rr.rax=0;rr.rbp=0;rr.r14=-1;
        Range16NoGrowth638.copyAndPrepare(rr,r,(pc,p)->a(r.events,"B",p,pc));
        same(rr.rax==0xffffffffL&&rr.rcx==OLD-16&&rr.rdx==OLD-16&&rr.r8==OLD-16&&rr.r9==OLD&&rr.rbx==S+16&&rr.rsi==S+16&&rr.rsp==P&&rr.x0.equals(W1),"signedMOVSXDdistinctfromEAXz32");
        List<E> z=new ArrayList<>();a(z,"R64",H,OLD);a(z,"B",S,0x8c7200);v(z,"R128",S,W1);v(z,"W128",OLD,W1);a(z,"R32",H+0xc,-1);a(z,"R64",H,OLD);a(z,"W32",H+0xc,-1);compare(r,want,z);
    }
    public static int verify() { empty();nongrowth(0);nongrowth(1);nongrowth(2);cvtStop();growth();signedBlock();return 7; }
    public static void main(String[] args) { System.out.println(verify()); }
}
