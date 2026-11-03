package org.xar.ck3.study.m6.full239;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Budget;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Floating;

/** Controlled owned RAM/whole-state ports, no actual COPY/Reverse/allocator implementation claims. */
public final class Transfer4Full239Test {
    private static final long I=0x140000000L,S=0x9008,F=S-0x48,D=0x2000,T=0x3000,A=0x4000,B=0x5000,DB=0x6000,TB=0x7000,NEW=0x8000,TABLE=0xA000;
    private static final long TARGET=0xBAD001L,RET=0xABCD76543210L;
    private static int scenes,checks;
    private Transfer4Full239Test() { }
    public static void main(String[] args) {
        run("moveEmptySelectiveSaves",Transfer4Full239Test::empty);
        run("swapStableActualRax",Transfer4Full239Test::swap);
        run("actualMoveCallsActualSwap",Transfer4Full239Test::moveEqual);
        run("copyAndThreeReverseFullFrames",Transfer4Full239Test::inplace);
        run("growthZeroCopyStillWholeCall",Transfer4Full239Test::growth);
        run("firstThrowKeepsSourcePrefix",Transfer4Full239Test::firstThrow);
        run("swapDifferentMutualBoundaryPrefix",Transfer4Full239Test::swapPrefix);
        System.out.println("PASS scenes="+scenes+" checks="+checks+" normalWhole5=true guardedPrefix2=true actualMutualKnown1=true directSevenSiteUnion=true controlledCopyReverseOnly=true represented185Only=true fullHardwareABI=false Native=false Game=false");
    }
    private static void empty() {
        Ram m=ram(false,0,4);Entry e=entry();var out=Move4Full239.execute(e,m,null,null,bounded());
        equal(out.volatileBits(),change(e.volatileBits(),D,A,T,e.volatileBits().r8Bits(),e.volatileBits().r9Bits(),e.volatileBits().r11Bits()));returned(out,n(),RET);
        equal(m.readDword(D+0xC),0);equal(m.readDword(T+0xC),0);
        check(!m.reads.contains(F+0x58)&&!m.reads.contains(F+0x60)&&!m.reads.contains(F+0x20));
        equal(m.writes,List.of(S-8,S-16,S-24,F+0x50,F+0x28));
    }
    private static void swap() {
        Ram m=ram(true,2,4);Entry e=entry();var out=Swap4Full239.execute(e,m,null,null,bounded());
        equal(out.volatileBits(),change(e.volatileBits(),5L,4L,T,e.volatileBits().r8Bits(),e.volatileBits().r9Bits(),S-8));returned(out,n(),RET);
        equal(m.peek(D),TB);equal(m.peek(T),DB);equal(m.readDword(D+0xC),2);equal(m.readDword(T+0xC),9);equal(m.readDword(D+8),5);equal(m.readDword(T+8),4);
    }
    private static void moveEqual() {
        Ram m=ram(true,2,4);Entry e=entry();VolatileBits child=v(0x1000);AtomicInteger count=new AtomicInteger();
        Calls calls=new Ports(){@Override public VolatileBits invoke(Call c){
            equal(c.callSiteRva(),0xB2EF06L);equal(c.targetBits(),TARGET);equal(c.kind(),TargetKind.INDIRECT_ABSOLUTE);equal(c.rspBits(),F);
            equal(c.volatileBits(),change(e.volatileBits(),TABLE,A,DB,4L,e.volatileBits().r9Bits(),e.volatileBits().r11Bits()));equal(m.readQword(F-8),I+0xB2EF09);
            equal(c.nonvolatileBits().r12Bits(),n().r12Bits());count.incrementAndGet();return child;
        }};
        var out=Move4Full239.execute(e,m,calls,null,bounded());
        equal(count.get(),1);equal(out.volatileBits(),change(child,D,0L,T,child.r8Bits(),child.r9Bits(),F-0x10));returned(out,n(),RET);
        equal(m.peek(F-8),I+0xB2EF1D);equal(m.peek(D),TB);equal(m.peek(T),0L);equal(m.readDword(D+0xC),2);equal(m.readDword(T+0xC),0);
    }
    private static void inplace() {
        Ram m=ram(false,1,4);Entry e=entry();AtomicInteger count=new AtomicInteger();VolatileBits[] child={v(0x2000),v(0x3000),v(0x4000),v(0x5000)};
        Calls calls=new Ports(){@Override public VolatileBits invoke(Call c){
            int index=count.getAndIncrement();equal(c.kind(),TargetKind.DIRECT_RVA);equal(c.rspBits(),F);
            if(index==0){equal(c.callSiteRva(),0xB2EFFEL);equal(c.targetBits(),0x4226860L);equal(c.volatileBits().rcxBits(),DB);equal(c.volatileBits().rdxBits(),TB);equal(c.volatileBits().r8Bits(),4L);equal(c.volatileBits().r9Bits(),e.volatileBits().r9Bits());equal(m.readQword(F-8),I+0xB2F003);m.writeDword(DB,0x11223344);m.writeDword(D+0xC,1);}
            else{
                long site=index==1?0xB2F02DL:index==2?0xB2F038L:0xB2F043L;
                equal(c.callSiteRva(),site);equal(c.targetBits(),0x4220AA4L);equal(m.readQword(F-8),I+site+5);
                equal(c.volatileBits().rcxBits(),index==2?DB+4:DB);equal(c.volatileBits().rdxBits(),index==1?DB+4:DB+8);
                equal(c.volatileBits().r8Bits(),child[index-1].r8Bits());equal(c.volatileBits().r9Bits(),child[index-1].r9Bits());
            }
            return child[index];
        }};
        var out=Move4Full239.execute(e,m,calls,null,bounded());
        equal(count.get(),4);equal(out.volatileBits(),rax(child[3],D));returned(out,n(),RET);equal(m.readDword(D+0xC),2);equal(m.readDword(T+0xC),0);equal(m.readDword(DB),0x11223344);
    }
    private static void growth() {
        Ram m=ram(false,1,0);m.poke(TABLE+8,TARGET+1);m.poke32(I+0x49F64F0L,0x3FC00000);m.poke32(DB,0x01020304);m.poke32(TB,0x11223344);
        Entry e=entry();AtomicInteger count=new AtomicInteger(),fp=new AtomicInteger();VolatileBits[] child={rax(v(0x6000),NEW),v(0x7000),v(0x8000),v(0x9000),v(0xA000)};
        Floating floating=new Floating(){
            @Override public Bits128 convertSignedDwords(Bits128 input){equal(input,new Bits128(0,0));equal(fp.getAndIncrement(),0);return input;}
            @Override public Bits128 multiplyLowSingle(Bits128 input,int bits){equal(input,new Bits128(0,0));equal(bits,0x3FC00000);equal(fp.getAndIncrement(),1);return input;}
            @Override public int truncateLowSingle(Bits128 input){equal(input,new Bits128(0,0));equal(fp.getAndIncrement(),2);return 0;}
        };
        Calls calls=new Ports(){@Override public VolatileBits invoke(Call c){
            int index=count.getAndIncrement();equal(c.rspBits(),F);long site;
            if(index==0){site=0xB2EF9EL;equal(c.kind(),TargetKind.INDIRECT_ABSOLUTE);equal(c.targetBits(),TARGET+1);equal(c.volatileBits().rcxBits(),A);equal(c.volatileBits().rdxBits(),4L);equal(c.volatileBits().r8Bits(),4L);equal(c.volatileBits().r9Bits(),e.volatileBits().r9Bits());}
            else if(index==4){site=0xB2EFE5L;equal(c.kind(),TargetKind.INDIRECT_ABSOLUTE);equal(c.targetBits(),TARGET);equal(c.volatileBits().rcxBits(),A);equal(c.volatileBits().rdxBits(),DB);equal(c.volatileBits().r8Bits(),4L);equal(c.volatileBits().r9Bits(),child[3].r9Bits());}
            else{
                site=index==1?0xB2EFADL:index==2?0xB2EFBBL:0xB2EFD2L;equal(c.kind(),TargetKind.DIRECT_RVA);equal(c.targetBits(),0x4226860L);
                equal(c.volatileBits().rcxBits(),index==3?NEW+4:NEW);equal(c.volatileBits().rdxBits(),index==2?TB:DB);equal(c.volatileBits().r8Bits(),index==1?0L:4L);equal(c.volatileBits().r9Bits(),child[index-1].r9Bits());
                if(index==2){m.writeDword(NEW,0x11223344);m.writeDword(D+0xC,1);}if(index==3)m.writeDword(NEW+4,0x01020304);
            }
            equal(c.callSiteRva(),site);equal(m.readQword(F-8),I+site+(index==0||index==4?3:5));return child[index];
        }};
        var out=Move4Full239.execute(e,m,calls,floating,bounded());
        equal(count.get(),5);equal(fp.get(),3);equal(out.volatileBits(),rax(child[4],D));returned(out,n(),RET);equal(m.peek(D),NEW);equal(m.readDword(D+0xC),1);equal(m.readDword(D+8),1);equal(m.readDword(T+0xC),0);equal(m.readDword(NEW),0x11223344);equal(m.readDword(NEW+4),0x01020304);
    }
    private static void firstThrow() {
        Ram m=ram(true,2,4);RuntimeException original=new IllegalStateException("first-free239");
        Calls calls=new Ports(){@Override public VolatileBits invoke(Call c){throw original;}};
        try{Move4Full239.execute(entry(),m,calls,null,bounded());throw new AssertionError("missingthrow");}catch(RuntimeException failure){check(failure==original);}
        equal(m.writes,List.of(S-8,S-16,S-24,F-8));equal(m.peek(D),DB);equal(m.readDword(D+0xC),9);check(!m.reads.contains(S));
    }
    private static void swapPrefix() {
        Ram m=ram(false,1,4);RuntimeException boundary=new UnsupportedOperationException("beforemutual239");long frame=S-0x458;
        Budget budget=(site,cursor,end)->{if(site==0xB2EE82L){equal(cursor,frame);throw boundary;}};
        try{Swap4Full239.execute(entry(),m,null,null,budget);throw new AssertionError("missingboundary");}catch(RuntimeException failure){check(failure==boundary);}
        equal(m.peek(frame+0x40),I+0x44BBB10L);equal(m.peek(frame+0x448),I+0x54DE268L);equal(m.peek(frame+0x20),0L);equal(m.peek(frame+0x28),0L);equal(m.peek(frame+0x30),frame+0x40);check(!m.reads.contains(S));
    }
    private static Ram ram(boolean same,int count,int capacity){Ram m=new Ram();m.poke(S,RET);m.poke(D,DB);m.poke32(D+8,capacity);m.poke32(D+0xC,9);m.poke(D+0x10,A);m.poke(T,TB);m.poke32(T+8,5);m.poke32(T+0xC,count);m.poke(T+0x10,same?A:B);m.poke(A,TABLE);m.poke(TABLE+0x10,TARGET);return m;}
    private static Entry entry(){return new Entry(I,S,change(v(0x100),0xE001,D,T,0x8000000000000038L,0xF000000000000009L,0xE011),n());}
    private static Bits128 x(long t){return new Bits128(0x8000000000000000L|t,0xF000000000000000L|t);}
    private static VolatileBits v(long t){return new VolatileBits(t+1,t+2,t+3,t+8,t+9,t+10,t+11,x(t+16),x(t+32),x(t+48),x(t+64),x(t+80),x(t+96));}
    private static NonvolatileBits n(){return new NonvolatileBits(0xB1,0xB2,0xB3,0xB4,0xF000000100000005L,0xB6,0xB7,0xB8,x(0xB9));}
    private static VolatileBits change(VolatileBits v,long a,long c,long d,long r8,long r9,long r11){return new VolatileBits(a,c,d,r8,r9,v.r10Bits(),r11,v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static VolatileBits rax(VolatileBits v,long a){return change(v,a,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r11Bits());}
    private static void returned(NormalReturn out,NonvolatileBits n,long rip){equal(out.nonvolatileBits(),n);equal(out.returnRipBits(),rip);equal(out.callerRspBits(),S+8);}
    private static Budget bounded(){AtomicInteger n=new AtomicInteger();return (site,cursor,end)->{if(n.incrementAndGet()>100)throw new UnsupportedOperationException("239budget");};}
    private static class Ports implements Calls{
        @Override public VolatileBits invoke(Call c){throw new AssertionError("unexpected239CALL "+Long.toHexString(c.callSiteRva()));}
        @Override public NormalReturn tail(Tail t){throw new AssertionError("unexpected239TAIL");}
        @Override public long readGsQword58(){throw new AssertionError("unexpected239GS");}
    }
    private static final class Ram implements Memory{
        final Map<Long,Integer> data=new HashMap<>();final List<Long> reads=new ArrayList<>(),writes=new ArrayList<>();
        void poke(long a,long v){for(int j=0;j<8;j++)data.put(a+j,(int)(v>>>(j*8))&255);}
        void poke32(long a,int v){for(int j=0;j<4;j++)data.put(a+j,(v>>>(j*8))&255);}
        long peek(long a){long v=0;for(int j=0;j<8;j++){Integer b=data.get(a+j);if(b==null)throw new UnsupportedOperationException("unheld239RAM "+Long.toHexString(a+j));v|=(long)b<<(j*8);}return v;}
        @Override public long readQword(long a){reads.add(a);return peek(a);}
        @Override public void writeQword(long a,long v){writes.add(a);poke(a,v);}
        @Override public int readDword(long a){int v=0;for(int j=0;j<4;j++)v|=readUnsignedByte(a+j)<<(j*8);return v;}
        @Override public void writeDword(long a,int v){for(int j=0;j<4;j++)writeByte(a+j,v>>>(j*8));}
        @Override public int readUnsignedByte(long a){Integer v=data.get(a);if(v==null)throw new UnsupportedOperationException("unheld239byte");return v;}
        @Override public void writeByte(long a,int v){data.put(a,v&255);}
        @Override public Bits128 read128(long a){return new Bits128(readQword(a),readQword(a+8));}
        @Override public void write128(long a,Bits128 v){writeQword(a,v.lowBits());writeQword(a+8,v.highBits());}
        @Override public int lockedXaddDword(long a,int delta){throw new UnsupportedOperationException("unused239atomic");}
    }
    private static void run(String name,Runnable test){test.run();scenes++;System.out.println("PASS "+name);}
    private static void equal(Object actual,Object expected){checks++;if(!java.util.Objects.equals(actual,expected))throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected);}
    private static void check(boolean condition){checks++;if(!condition)throw new AssertionError("check="+checks);}
}
