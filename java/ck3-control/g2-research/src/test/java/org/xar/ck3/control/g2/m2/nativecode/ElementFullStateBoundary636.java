package org.xar.ck3.control.g2.m2.nativecode;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

public final class ElementFullStateBoundary636 {
    private ElementFullStateBoundary636() { }
    private static final long IMAGE=0x140000000L,P=0x70001008L,D=0x8000000000001100L,S=0xf000000000002200L;
    private static final long B16=0xb000000000003300L,B4=0xc000000000004400L,ALT4=0xd000000000005500L;
    private static final long RIP=0x1400abcdefL,RET1=IMAGE+0x372984bL,RET2=IMAGE+0x372987cL;
    private static final int KIND=0x87654321,TAIL=0x55667788,FLAG=0xa5;
    private static final QueueFp604Api.Mxcsr FP0=new QueueFp604Api.Mxcsr(0,0);
    private static final QueueFp604Api.Mxcsr FP1=new QueueFp604Api.Mxcsr(0x20,0x20);
    private static final QueueFp604Api.Mxcsr FP2=new QueueFp604Api.Mxcsr(0x5,0x25);
    private record E(String kind,long address,long value) { }
    private static void a(List<E> x,String k,long address,long value) { x.add(new E(k,address,value)); }
    private static Bits128 x(long q) { return new Bits128(q,~q); }
    private static VolatileBits bank(long b,long rax,long rcx,long rdx,long r8,long r9) {
        return new VolatileBits(rax,rcx,rdx,r8,r9,b+10,b+11,x(b),x(b+1),x(b+2),x(b+3),x(b+4),x(b+5));
    }
    private static VolatileBits change(VolatileBits v,long rax,long rcx,long rdx,long r8,long r9) {
        return new VolatileBits(rax,rcx,rdx,r8,r9,v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static NonvolatileBits originalN() { return new NonvolatileBits(0x101,0x102,0x103,0x104,0x105,0x106,0x107,0x108,x(0x109)); }
    private static NonvolatileBits callN() { NonvolatileBits n=originalN();return new NonvolatileBits(S,n.rbpBits(),0,D,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6()); }
    private static VolatileBits entryV() { return bank(0x1000,0x111,D,S,0x444,0x555); }
    private static VolatileBits offer1() { return bank(0x2000,0x211,0x222,0x233,0x244,0x255); }
    private static VolatileBits offer2() { return bank(0x3000,0x311,0x322,0x333,0x344,0x355); }
    private static final class Ram implements Element172Fp636Api.Memory {
        private final Map<Long,Byte> bytes=new HashMap<>();private final List<E> events=new ArrayList<>();
        private Registers visible;private final List<Long> raxAtQwordRead=new ArrayList<>();
        private void seed(long p,int width,long v) { for(int i=0;i<width;i++)bytes.put(p+i,(byte)(v>>>(i*8))); }
        private long peek(long p,int width) { long v=0;for(int i=0;i<width;i++)v|=(bytes.getOrDefault(p+i,(byte)0)&255L)<<(i*8);return v; }
        @Override public int readDword(long p) { int v=(int)peek(p,4);a(events,"R32",p,v);return v; }
        @Override public long readQword(long p) { if(visible!=null)raxAtQwordRead.add(visible.rax);long v=peek(p,8);a(events,"R64",p,v);return v; }
        @Override public int readUnsignedByte(long p) { int v=(int)peek(p,1);a(events,"R8",p,v);return v; }
        @Override public void writeDword(long p,int v) { a(events,"W32",p,v);seed(p,4,v); }
        @Override public void writeQword(long p,long v) { a(events,"W64",p,v);seed(p,8,v); }
        @Override public void writeByte(long p,int v) { a(events,"W8",p,v&255);seed(p,1,v); }
        @Override public int lockedXaddDword(long p,int v) { throw new AssertionError("unexpected atomic"); }
        @Override public Bits128 read128(long p) { throw new AssertionError("unexpected128 read"); }
        @Override public void write128(long p,Bits128 v) { throw new AssertionError("unexpected128 write"); }
    }
    private static Ram initial() {
        Ram r=new Ram();for(int i=0;i<0x50;i++)r.seed(D+i,1,0xcc);
        r.seed(P,8,RIP);r.seed(S+8,4,KIND);r.seed(S+0x10,8,B16);r.seed(S+0x1c,4,2);
        r.seed(S+0x28,8,B4);r.seed(S+0x34,4,3);r.seed(S+0x40,4,0x12345678);r.seed(S+0x44,1,0x5a);return r;
    }
    private static List<E> expected(int mode) {
        List<E> z=new ArrayList<>();NonvolatileBits n=originalN();
        a(z,"W64",P+8,n.rbxBits());a(z,"W64",P+0x10,n.rsiBits());a(z,"W64",P-8,n.rdiBits());
        a(z,"W64",D,IMAGE+0x45648a0);a(z,"R32",S+8,KIND);a(z,"W32",D+8,KIND);
        a(z,"W64",D+0x18,0);a(z,"W64",D+0x20,0);a(z,"W64",D+0x10,0);a(z,"W64",D+0x18,0);a(z,"W64",D+0x20,IMAGE+0x54de260);
        a(z,"R32",S+0x1c,2);a(z,"R64",S+0x10,B16);a(z,"W64",P-0x30,RET1);a(z,"CALL",0x3729846,0x8c70b0);
        a(z,"W64",S+0x28,ALT4);a(z,"W32",S+0x34,-1);
        if(mode==2)return z;
        a(z,"W64",D+0x30,0);a(z,"W64",D+0x38,0);a(z,"W64",D+0x28,0);a(z,"W64",D+0x30,0);a(z,"W64",D+0x38,IMAGE+0x54de268);
        a(z,"R64",S+0x28,ALT4);a(z,"R32",S+0x34,-1);a(z,"W64",P-0x30,RET2);a(z,"CALL",0x3729877,0xadd0d0);
        if(mode==1) { a(z,"W8",0x7700,0x77);return z; }
        a(z,"W32",S+0x40,TAIL);a(z,"W8",S+0x44,FLAG);
        a(z,"R32",S+0x40,TAIL);a(z,"R64",P+0x10,n.rsiBits());a(z,"W32",D+0x40,TAIL);
        a(z,"R8",S+0x44,FLAG);a(z,"R64",P+8,n.rbxBits());a(z,"W8",D+0x44,FLAG);
        a(z,"R64",P-8,n.rdiBits());a(z,"R64",P,RIP);return z;
    }
    private static void checkEvents(Ram r,Ram wanted,List<E> expected) {
        for(E e:expected)switch(e.kind()) {
            case "W8" -> wanted.seed(e.address(),1,e.value());case "W32" -> wanted.seed(e.address(),4,e.value());
            case "W64" -> wanted.seed(e.address(),8,e.value());default -> { }
        }
        if(!r.events.equals(expected)) {
            int i=0;while(i<r.events.size()&&i<expected.size()&&r.events.get(i).equals(expected.get(i)))i++;
            throw new AssertionError("636 event "+i+" actual="+(i<r.events.size()?r.events.get(i):"END")+" expected="+(i<expected.size()?expected.get(i):"END"));
        }
        if(!r.bytes.equals(wanted.bytes))throw new AssertionError("complete byte RAM");
    }
    private static void checkFrame(Element172Fp636Api.CallFrame f,int i) {
        long site=i==0?0x3729846:0x3729877,target=i==0?0x8c70b0:0xadd0d0,ret=i==0?RET1:RET2;
        VolatileBits v=i==0?change(entryV(),IMAGE+0x54de260,D+0x10,0,B16,B16+32):change(offer1(),-1,D+0x28,0,ALT4,ALT4-4);
        GovernmentCrtBoundary185Api.Call wanted=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,P-0x28,v,callN());
        if(!f.call().equals(wanted)||!f.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(IMAGE,P-0x30,v,callN()))||f.instructionLength()!=5||f.returnRipBits()!=ret||f.directionFlagSet()!=(i==0)||f.preMxcsr()!=(i==0?FP0:FP1))throw new AssertionError("complete CALL frame "+i);
    }
    private static void whole(int mode) {
        Ram r=initial(),wanted=initial();int[] cursor={0};QueueFp604Api.Stopped[] offered={null};
        Element172Fp636Api.Calls calls=f->{
            int i=cursor[0]++;if(i>1)throw new AssertionError("extraCALL");checkFrame(f,i);a(r.events,"CALL",f.call().callSiteRva(),f.call().targetBits());
            if(i==0) {
                r.writeQword(S+0x28,ALT4);r.writeDword(S+0x34,-1);
                return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(offer1(),RET1+(mode==2?1:0),P-0x28,callN()),false),FP1);
            }
            if(mode==1) {
                r.writeByte(0x7700,0x77);offered[0]=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(f.childEntry(),f.call().callSiteRva(),f.directionFlagSet(),f.preMxcsr()),0,f.call().callSiteRva());return offered[0];
            }
            r.writeDword(S+0x40,TAIL);r.writeByte(S+0x44,FLAG);
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(offer2(),RET2,P-0x28,callN()),true),FP2);
        };
        boolean rejected=false;
        try {
            QueueFp604Api.Outcome out=Element172FullState636.execute(new Element172Fp636Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,P,entryV(),originalN()),true,FP0),r,calls);
            if(mode==2)throw new AssertionError("badNormal accepted");
            if(mode==1) { if(out!=offered[0])throw new AssertionError("Stopped identity"); }
            else {
                if(!(out instanceof QueueFp604Api.Normal normal))throw new AssertionError("missingNormal");
                GovernmentCrtBoundary185Api.NormalReturn nr=normal.base().normalReturn();
                if(!nr.volatileBits().equals(change(offer2(),D,offer2().rcxBits(),offer2().rdxBits(),offer2().r8Bits(),offer2().r9Bits()))||!nr.nonvolatileBits().equals(originalN())||nr.returnRipBits()!=RIP||nr.callerRspBits()!=P+8||!normal.base().postDirectionFlagSet()||normal.postMxcsr()!=FP2)throw new AssertionError("full Normal/postFPDF");
            }
        } catch(IllegalArgumentException ex) { if(mode!=2)throw ex;rejected=true; }
        if(rejected!=(mode==2)||cursor[0]!=(mode==2?1:2))throw new AssertionError("path/callcount");
        checkEvents(r,wanted,expected(mode));
    }
    private static void epilogueAlias() {
        long t=0x990000L,d=t-0x10,s=t+0x38,bx=0x5544332211223344L;
        Ram r=new Ram();r.seed(t+0x20,8,0x777);r.seed(t+0x28,8,RIP);r.seed(t+0x30,8,0x554433221100ffeeL);
        r.seed(t+0x38,8,0x778899aabbccddeeL);r.seed(s+0x40,4,0x11223344);r.seed(s+0x44,1,0x5a);
        Ram wanted=new Ram();wanted.bytes.putAll(r.bytes);
        Registers regs=GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(IMAGE,t,entryV(),originalN()));regs.rdi=d;regs.rbx=s;r.visible=regs;
        QueueFp604Api.Normal out=Element172Epilogue636.finish(regs,r,false,FP0);GovernmentCrtBoundary185Api.NormalReturn nr=out.base().normalReturn();
        NonvolatileBits n=originalN(),expectedN=new NonvolatileBits(bx,n.rbpBits(),0x778899aabbccddeeL,0x777,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());
        if(!nr.nonvolatileBits().equals(expectedN)||nr.volatileBits().raxBits()!=d||nr.returnRipBits()!=RIP||nr.callerRspBits()!=t+0x30||out.postMxcsr()!=FP0||out.base().postDirectionFlagSet())throw new AssertionError("epilogue aliasfullstate");
        List<E> x=new ArrayList<>();a(x,"R32",s+0x40,0x11223344);a(x,"R64",t+0x38,0x778899aabbccddeeL);a(x,"W32",d+0x40,0x11223344);
        a(x,"R8",s+0x44,0x5a);a(x,"R64",t+0x30,bx);a(x,"W8",d+0x44,0x5a);a(x,"R64",t+0x20,0x777);a(x,"R64",t+0x28,RIP);
        if(!r.raxAtQwordRead.equals(List.of(0x11223344L,0x5aL,d,d)))throw new AssertionError("public Registers EAX prefix at Memory reads");
        checkEvents(r,wanted,x);if(r.peek(t+0x30,8)!=0x5544335a11223344L)throw new AssertionError("post-restore savedcell alias");
    }
    public static int verify() { whole(0);whole(1);whole(2);epilogueAlias();return 4; }
    public static void main(String[] args) { System.out.println(verify()); }
}
