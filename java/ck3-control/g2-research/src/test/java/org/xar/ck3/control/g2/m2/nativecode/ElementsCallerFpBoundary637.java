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

public final class ElementsCallerFpBoundary637 {
    private ElementsCallerFpBoundary637() { }
    private static final long IMAGE=0x140000000L,P=0x70001008L,D=0x8000000000001100L,S=0xf000000000002200L;
    private static final long B16=0xb000000000003300L,B4=0xc000000000004400L,ALT4=0xd000000000005500L;
    private static final long RIP=0x1400abcdefL,RET1=IMAGE+0x372984bL,RET2=IMAGE+0x372987cL;
    private static final int KIND=0x87654321,TAIL=0x55667788,FLAG=0xa5;
    private static final long DROOT=0x8100L,SROOT=0x8200L;
    private static final QueueFp604Api.Mxcsr FP3=new QueueFp604Api.Mxcsr(8,12);
    private static VolatileBits offer3() { return bank(0x4000,0x411,0x422,0x433,0x444,0x455); }
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

    private static VolatileBits entryV() { return bank(0x1000,0x111,DROOT,SROOT,0x444,0x555); }
    private static VolatileBits offer1() { return bank(0x2000,0x211,0x222,0x233,0x244,0x255); }
    private static VolatileBits offer2() { return bank(0x3000,0x311,0x322,0x333,0x344,0x355); }
    private static final class Ram implements EmbeddedElementsFp637.Memory {
        private final Map<Long,Byte> bytes=new HashMap<>();private final List<E> events=new ArrayList<>();

        private void seed(long p,int width,long v) { for(int i=0;i<width;i++)bytes.put(p+i,(byte)(v>>>(i*8))); }
        private long peek(long p,int width) { long v=0;for(int i=0;i<width;i++)v|=(bytes.getOrDefault(p+i,(byte)0)&255L)<<(i*8);return v; }
        @Override public int readDword(long p) { int v=(int)peek(p,4);a(events,"R32",p,v);return v; }
        @Override public long readQword(long p) { long v=peek(p,8);a(events,"R64",p,v);return v; }
        @Override public int readUnsignedByte(long p) { int v=(int)peek(p,1);a(events,"R8",p,v);return v; }
        @Override public void writeDword(long p,int v) { a(events,"W32",p,v);seed(p,4,v); }
        @Override public void writeQword(long p,long v) { a(events,"W64",p,v);seed(p,8,v); }
        @Override public void writeByte(long p,int v) { a(events,"W8",p,v&255);seed(p,1,v); }
        @Override public int lockedXaddDword(long p,int v) { throw new AssertionError("unexpected atomic"); }
        @Override public Bits128 read128(long p) { throw new AssertionError("unexpected128 read"); }
        @Override public void write128(long p,Bits128 v) { throw new AssertionError("unexpected128 write"); }
        @Override public void writeWord(long p,int v) { throw new AssertionError("unexpectedWord"); }
        @Override public void write128NonTemporal(long p,Bits128 v) { throw new AssertionError("unexpectedNT128"); }
        @Override public void sfence() { throw new AssertionError("unexpectedFence"); }
        @Override public int readUnsignedWord(long p) { throw new AssertionError("unexpectedWordRead"); }
        @Override public FullCopy437Api.Bits256 read256(long p) { throw new AssertionError("unexpected256"); }
        @Override public void write256(long p,FullCopy437Api.Bits256 v) { throw new AssertionError("unexpected256"); }
        @Override public void write256NonTemporal(long p,FullCopy437Api.Bits256 v) { throw new AssertionError("unexpectedNT256"); }
    }

    private static NonvolatileBits cleanupN() { NonvolatileBits n=originalN();return new NonvolatileBits(1,S,DROOT,n.rdiBits(),n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6()); }
    private static NonvolatileBits assignN() { NonvolatileBits n=originalN();return new NonvolatileBits(1,S,DROOT,D,n.r12Bits(),n.r13Bits(),D+0x48,n.r15Bits(),n.xmm6()); }
    private static NonvolatileBits lowerN() { NonvolatileBits n=originalN();return new NonvolatileBits(S,S,0,D,n.r12Bits(),n.r13Bits(),D+0x48,n.r15Bits(),n.xmm6()); }
    private static Ram initial() {
        Ram r=new Ram();for(int i=0;i<0x50;i++)r.seed(D+i,1,0xcc);
        r.seed(P,8,RIP);r.seed(DROOT,8,D);r.seed(DROOT+8,4,1);r.seed(DROOT+0xc,4,1);
        r.seed(SROOT,8,S);r.seed(SROOT+0xc,4,1);
        r.seed(S+8,4,KIND);r.seed(S+0x10,8,B16);r.seed(S+0x1c,4,2);
        r.seed(S+0x28,8,B4);r.seed(S+0x34,4,3);r.seed(S+0x40,4,0x12345678);r.seed(S+0x44,1,0x5a);return r;
    }
    private static List<E> expected(int mode) {
        List<E> z=new ArrayList<>();NonvolatileBits n=originalN();
        a(z,"W64",P+8,n.rbxBits());a(z,"W64",P+0x10,n.rbpBits());a(z,"W64",P+0x18,n.rsiBits());a(z,"W64",P+0x20,n.rdiBits());
        a(z,"W64",P-8,n.r12Bits());a(z,"W64",P-0x10,n.r14Bits());a(z,"W64",P-0x18,n.r15Bits());
        a(z,"R32",SROOT+0xc,1);a(z,"R64",SROOT,S);a(z,"W64",P-0x50,IMAGE+0x37282e6);a(z,"PARENT",0x37282e1,0x889780);
        a(z,"R32",DROOT+0xc,1);a(z,"R64",DROOT,D);a(z,"W32",DROOT+0xc,1);a(z,"R64",DROOT,D);a(z,"BUDGET",0x37283b0,S);
        a(z,"W64",P-0x50,IMAGE+0x37283bb);a(z,"PARENT",0x37283b6,0x37297f0);
        a(z,"W64",P-0x48,1);a(z,"W64",P-0x40,DROOT);a(z,"W64",P-0x58,D);
        a(z,"W64",D,IMAGE+0x45648a0);a(z,"R32",S+8,KIND);a(z,"W32",D+8,KIND);
        a(z,"W64",D+0x18,0);a(z,"W64",D+0x20,0);a(z,"W64",D+0x10,0);a(z,"W64",D+0x18,0);a(z,"W64",D+0x20,IMAGE+0x54de260);
        a(z,"R32",S+0x1c,2);a(z,"R64",S+0x10,B16);a(z,"W64",P-0x80,RET1);a(z,"LOWER",0x3729846,0x8c70b0);
        a(z,"W64",S+0x28,ALT4);a(z,"W32",S+0x34,-1);
        if(mode==2)return z;
        a(z,"W64",D+0x30,0);a(z,"W64",D+0x38,0);a(z,"W64",D+0x28,0);a(z,"W64",D+0x30,0);a(z,"W64",D+0x38,IMAGE+0x54de268);
        a(z,"R64",S+0x28,ALT4);a(z,"R32",S+0x34,-1);a(z,"W64",P-0x80,RET2);a(z,"LOWER",0x3729877,0xadd0d0);
        if(mode==1) { a(z,"W8",0x7700,0x77);return z; }
        a(z,"W32",S+0x40,TAIL);a(z,"W8",S+0x44,FLAG);
        a(z,"R32",S+0x40,TAIL);a(z,"R64",P-0x40,DROOT);a(z,"W32",D+0x40,TAIL);
        a(z,"R8",S+0x44,FLAG);a(z,"R64",P-0x48,1);a(z,"W8",D+0x44,FLAG);
        a(z,"R64",P-0x58,D);a(z,"R64",P-0x50,IMAGE+0x37283bb);
        a(z,"R64",P+8,n.rbxBits());a(z,"R64",P+0x10,n.rbpBits());a(z,"R64",P+0x18,n.rsiBits());a(z,"R64",P+0x20,n.rdiBits());
        a(z,"R64",P-0x18,n.r15Bits());a(z,"R64",P-0x10,n.r14Bits());a(z,"R64",P-8,n.r12Bits());a(z,"R64",P,RIP);return z;
    }
    private static void checkEvents(Ram r,Ram wanted,List<E> expected) {
        for(E e:expected)switch(e.kind()) {
            case "W8" -> wanted.seed(e.address(),1,e.value());case "W32" -> wanted.seed(e.address(),4,e.value());
            case "W64" -> wanted.seed(e.address(),8,e.value());default -> { }
        }
        if(!r.events.equals(expected)) {
            int i=0;while(i<r.events.size()&&i<expected.size()&&r.events.get(i).equals(expected.get(i)))i++;
            throw new AssertionError("637 event "+i+" actual="+(i<r.events.size()?r.events.get(i):"END")+" expected="+(i<expected.size()?expected.get(i):"END"));
        }
        if(!r.bytes.equals(wanted.bytes))throw new AssertionError("complete byteRAM");
    }
    private static void checkParent(EmbeddedElementsFp637.CallFrame f,int i) {
        long site=i==0?0x37282e1:0x37283b6,target=i==0?0x889780:0x37297f0,ret=IMAGE+site+5;
        VolatileBits v=i==0?entryV():change(offer1(),1,D,S,offer1().r8Bits(),offer1().r9Bits());NonvolatileBits n=i==0?cleanupN():assignN();
        GovernmentCrtBoundary185Api.Call wanted=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,P-0x48,v,n);
        EmbeddedElements578Api.CallFrame old=f.original();
        if(!old.call().equals(wanted)||!old.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(IMAGE,P-0x50,v,n))||old.instructionLength()!=5||old.returnRipBits()!=ret||old.directionFlagSet()!=(i==0)||f.preMxcsr()!=(i==0?FP0:FP1))throw new AssertionError("parent frame "+i);
    }
    private static void checkLower(Element172Fp636Api.CallFrame f,int i) {
        long site=i==0?0x3729846:0x3729877,target=i==0?0x8c70b0:0xadd0d0,ret=i==0?RET1:RET2;
        VolatileBits v=i==0?change(offer1(),IMAGE+0x54de260,D+0x10,0,B16,B16+32):change(offer2(),-1,D+0x28,0,ALT4,ALT4-4);
        GovernmentCrtBoundary185Api.Call wanted=new GovernmentCrtBoundary185Api.Call(site,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,target,P-0x78,v,lowerN());
        if(!f.call().equals(wanted)||!f.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(IMAGE,P-0x80,v,lowerN()))||f.instructionLength()!=5||f.returnRipBits()!=ret||f.directionFlagSet()!=(i!=0)||f.preMxcsr()!=(i==0?FP1:FP2))throw new AssertionError("lower frame "+i);
    }
    private static void one(int mode) {
        Ram r=initial(),wanted=initial();int[] parent={0},lower={0};QueueFp604Api.Stopped[] stopped={null};EmbeddedElementsFp637.CallFrame[] seen={null};
        Element172Fp636Api.Calls low=f->{
            int i=lower[0]++;if(i>1)throw new AssertionError("extra lower");checkLower(f,i);a(r.events,"LOWER",f.call().callSiteRva(),f.call().targetBits());
            if(i==0) {
                r.writeQword(S+0x28,ALT4);r.writeDword(S+0x34,-1);
                return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(offer2(),RET1+(mode==2?1:0),P-0x78,lowerN()),true),FP2);
            }
            if(mode==1) {
                r.writeByte(0x7700,0x77);stopped[0]=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,new QueueFp604Api.Snapshot(f.childEntry(),f.call().callSiteRva(),f.directionFlagSet(),f.preMxcsr()),0,f.call().callSiteRva());return stopped[0];
            }
            r.writeDword(S+0x40,TAIL);r.writeByte(S+0x44,FLAG);
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(offer3(),RET2,P-0x78,lowerN()),false),FP3);
        };
        EmbeddedElementsFp637.Calls foreign=f->{
            if(f!=seen[0]||f.original().call().callSiteRva()!=0x37282e1)throw new AssertionError("exact foreignframe identity");
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(new GovernmentCrtBoundary185Api.NormalReturn(offer1(),IMAGE+0x37282e6,P-0x48,cleanupN()),false),FP1);
        };
        EmbeddedElementsFp637.Calls bound=EmbeddedElementsFp637.bind172(r,low,foreign);
        EmbeddedElementsFp637.Calls observer=f->{int i=parent[0]++;if(i>1)throw new AssertionError("extra parent");checkParent(f,i);seen[0]=f;a(r.events,"PARENT",f.original().call().callSiteRva(),f.original().call().targetBits());return bound.invoke(f);};
        GovernmentCrtBoundary185Api.LoopBudget budget=(pc,address)->a(r.events,"BUDGET",pc,address);
        boolean rejected=false;
        try {
            QueueFp604Api.Outcome out=EmbeddedElementsFp637.execute(new QueueFp604Api.Input(new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,P,entryV(),originalN()),true,budget),FP0),r,observer);
            if(mode==2)throw new AssertionError("badNormal accepted");
            if(mode==1) { if(out!=stopped[0])throw new AssertionError("Stopped identity across both wholeentries"); }
            else {
                if(!(out instanceof QueueFp604Api.Normal normal))throw new AssertionError("missingNormal");GovernmentCrtBoundary185Api.NormalReturn nr=normal.base().normalReturn();
                if(!nr.volatileBits().equals(change(offer3(),DROOT,offer3().rcxBits(),offer3().rdxBits(),offer3().r8Bits(),offer3().r9Bits()))||!nr.nonvolatileBits().equals(originalN())||nr.returnRipBits()!=RIP||nr.callerRspBits()!=P+8||normal.base().postDirectionFlagSet()||normal.postMxcsr()!=FP3)throw new AssertionError("whole parent fullstate/currentFPDF");
            }
        } catch(IllegalArgumentException ex) { if(mode!=2)throw ex;rejected=true; }
        if(rejected!=(mode==2)||parent[0]!=2||lower[0]!=(mode==2?1:2))throw new AssertionError("path/callcounts");checkEvents(r,wanted,expected(mode));
    }
    public static int verify() { one(0);one(1);one(2);return 3; }
    public static void main(String[] args) { System.out.println(verify()); }
}
