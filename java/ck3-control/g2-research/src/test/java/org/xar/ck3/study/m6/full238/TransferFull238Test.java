package org.xar.ck3.study.m6.full238;

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

/** New owned software inputs, no native memory, authority or physical FP environment. */
public final class TransferFull238Test {
    private static final long I=0x140000000L,S=0x9008,F=S-0x478,D=0x2000,T=0x3000,A=0x4000,B=0x5000,DB=0x6000,TB=0x7000,NEW=0x8000;
    private static final long TABLE=0xA000,TARGET=0xBAD001L,RET=0xABCD76543210L;
    private static final Bits128 DATA=new Bits128(0x8899AABBCCDDEEFFL,0x0123456789ABCDEFL);
    private static int scenes,checks;
    private TransferFull238Test() { }
    public static void main(String[] args) {
        if(args.length==1 && args[0].equals("remaining")) {
            run("actual715KnownFreeZero",TransferFull238Test::knownFree);
            run("recursiveCallBoundaryPrefix",TransferFull238Test::recursivePrefix);
            run("savedRbpAliasesHeaderCount",TransferFull238Test::savedAlias);
            System.out.println("PASS remainingScenes="+scenes+" checks="+checks+" firstSixNotRepeated=true represented185Only=true fullHardwareABI=false Native=false Game=false");
            return;
        }
        run("differentEmptyExactEpilogue",TransferFull238Test::empty);
        run("equalStableCompleteCallback",TransferFull238Test::equalStable);
        run("differentOneInPlace",TransferFull238Test::inPlace);
        run("inPlaceHeaderAliasAllRotations",TransferFull238Test::aliasRotations);
        run("growthExplicitFloatingAndTwoCalls",TransferFull238Test::growth);
        run("firstCallbackThrowKeepsPrefix",TransferFull238Test::firstThrow);
        run("actual715KnownFreeZero",TransferFull238Test::knownFree);
        run("recursiveCallBoundaryPrefix",TransferFull238Test::recursivePrefix);
        run("savedRbpAliasesHeaderCount",TransferFull238Test::savedAlias);
        System.out.println("PASS scenes="+scenes+" checks="+checks+" normalWhole7=true guardedPrefix2=true represented185Only=true exact715Known237New1=true floatingEnvironmentOpaque=true fullHardwareABI=false Native=false Game=false");
    }
    private static void empty() {
        Ram m=ram(false,0,3);Entry e=entry(D,n());
        var out=TransferFull238.execute(e,m,null,null,bounded());
        same(out.volatileBits(),change(e.volatileBits(),D,A,T,e.volatileBits().r8Bits(),e.volatileBits().r9Bits(),S-0x28));
        returned(out,n(),RET);same(m.readDword(D+0xC),0);same(m.readDword(T+0xC),0);
        same(m.writes.subList(0,8),List.of(S+0x8,S+0x10,S+0x18,S-0x8,S-0x10,S-0x18,S-0x20,S-0x28));
        same(m.reads.subList(m.reads.size()-9,m.reads.size()),List.of(S+0x8,S+0x10,S+0x18,S-0x28,S-0x20,S-0x18,S-0x10,S-0x8,S));
    }
    private static void equalStable() {
        Ram m=ram(true,2,3);Entry e=entry(D,n());VolatileBits child=v(0x1000);AtomicInteger count=new AtomicInteger();
        Calls ports=new Ports(){@Override public VolatileBits invoke(Call c){
            same(c.callSiteRva(),0x21A508FL);same(c.rspBits(),F);same(c.targetBits(),TARGET);same(c.kind(),TargetKind.INDIRECT_ABSOLUTE);
            same(c.volatileBits(),change(e.volatileBits(),TABLE,A,DB,8L,e.volatileBits().r9Bits(),e.volatileBits().r11Bits()));
            same(m.readQword(F-0x8),I+0x21A5092);same(c.nonvolatileBits().r12Bits(),n().r12Bits());
            m.writeQword(S+0x8,0xC001);m.writeQword(S-0x8,0xD002);m.writeQword(S,0xE003);count.incrementAndGet();return child;
        }};
        var out=TransferFull238.execute(e,m,ports,null,bounded());
        same(count.get(),1);same(out.volatileBits(),change(child,D,0L,child.rdxBits(),child.r8Bits(),child.r9Bits(),S-0x28));
        returned(out,nv(n(),0xC001,n().rbpBits(),n().rsiBits(),0xD002),0xE003);
        same(m.readQword(D),TB);same(m.readQword(T),0L);same(m.readDword(D+0xC),2);same(m.readDword(T+0xC),0);
        same(m.readDword(D+0x8),5);same(m.readDword(T+0x8),0);
    }
    private static void inPlace() {
        Ram m=ram(false,1,4);m.poke128(TB,DATA);Entry e=entry(D,n());
        var out=TransferFull238.execute(e,m,null,null,bounded());
        VolatileBits expected=change(e.volatileBits(),D,1L,DB,DB,e.volatileBits().r9Bits(),S-0x28);
        expected=x0(expected,DATA);same(out.volatileBits(),expected);returned(out,n(),RET);
        same(m.read128(DB),DATA);same(m.readDword(D+0xC),1);same(m.readDword(T+0xC),0);
    }
    private static void growth() {
        Ram m=ram(false,1,0);m.poke128(TB,DATA);m.poke32(I+0x49F64F0L,0x3FC00000);m.poke(TABLE+0x8,TARGET+1);
        Entry e=entry(D,n());VolatileBits first=rax(v(0x2000),NEW),second=v(0x3000);AtomicInteger calls=new AtomicInteger(),fp=new AtomicInteger();
        Floating floating=new Floating(){
            @Override public Bits128 convertSignedDwords(Bits128 input){same(input,new Bits128(0,0));same(fp.getAndIncrement(),0);return input;}
            @Override public Bits128 multiplyLowSingle(Bits128 input,int bits){same(input,new Bits128(0,0));same(bits,0x3FC00000);same(fp.getAndIncrement(),1);return input;}
            @Override public int truncateLowSingle(Bits128 input){same(input,new Bits128(0,0));same(fp.getAndIncrement(),2);return 0;}
        };
        Calls ports=new Ports(){@Override public VolatileBits invoke(Call c){
            same(c.rspBits(),F);same(c.kind(),TargetKind.INDIRECT_ABSOLUTE);
            if(calls.getAndIncrement()==0){
                same(c.callSiteRva(),0x21A51B9L);same(c.targetBits(),TARGET+1);same(c.volatileBits().rcxBits(),A);same(c.volatileBits().rdxBits(),16L);
                same(c.volatileBits().r8Bits(),8L);same(c.volatileBits().r9Bits(),e.volatileBits().r9Bits());same(c.volatileBits().xmm0(),new Bits128(0,0));
                same(c.nonvolatileBits().r13Bits(),1L);same(c.nonvolatileBits().r15Bits(),1L);same(m.readQword(F-0x8),I+0x21A51BC);return first;
            }
            same(c.callSiteRva(),0x21A5223L);same(c.targetBits(),TARGET);same(c.volatileBits().rcxBits(),A);same(c.volatileBits().rdxBits(),DB);
            same(c.volatileBits().r8Bits(),8L);same(c.volatileBits().r9Bits(),first.r9Bits());same(c.volatileBits().xmm0(),DATA);
            same(m.readQword(F-0x8),I+0x21A5226);return second;
        }};
        var out=TransferFull238.execute(e,m,ports,floating,bounded());
        same(calls.get(),2);same(fp.get(),3);same(out.volatileBits(),change(second,D,second.rcxBits(),second.rdxBits(),second.r8Bits(),second.r9Bits(),S-0x28));
        returned(out,n(),RET);same(m.read128(NEW),DATA);same(m.readQword(D),NEW);same(m.readDword(D+0xC),1);same(m.readDword(D+8),1);same(m.readDword(T+0xC),0);
    }
    private static void aliasRotations() {
        Ram m=ram(false,2,4);long begin=D+8;
        m.poke(D,begin);
        Bits128 first=new Bits128((2L<<32)|4L,A),second=DATA;
        Bits128 third=new Bits128(0xC001C002C003C004L,0xC005C006C007C008L);
        Bits128 fourth=new Bits128(0xD001D002D003D004L,0xD005D006D007D008L);
        m.poke128(TB,first);m.poke128(TB+16,second);m.poke128(begin+32,third);m.poke128(begin+48,fourth);
        Entry e=entry(D,n());var out=TransferFull238.execute(e,m,null,null,bounded());
        Bits128 changedFirst=new Bits128((4L<<32)|4L,A);
        same(m.read128(begin),third);same(m.read128(begin+16),fourth);same(m.read128(begin+32),changedFirst);same(m.read128(begin+48),second);
        VolatileBits expected=change(e.volatileBits(),D,begin+48,begin+48,begin+32,begin+16,S-0x28);
        expected=new VolatileBits(expected.raxBits(),expected.rcxBits(),expected.rdxBits(),expected.r8Bits(),expected.r9Bits(),expected.r10Bits(),expected.r11Bits(),fourth,changedFirst,expected.xmm2(),expected.xmm3(),expected.xmm4(),expected.xmm5());
        same(out.volatileBits(),expected);returned(out,n(),RET);same(m.readDword(T+0xC),0);
    }
    private static void firstThrow() {
        Ram m=ram(true,2,3);RuntimeException original=new IllegalStateException("first-child");
        Calls ports=new Ports(){@Override public VolatileBits invoke(Call c){throw original;}};
        try{TransferFull238.execute(entry(D,n()),m,ports,null,bounded());throw new AssertionError("missing throw");}
        catch(RuntimeException failure){check(failure==original);}
        same(m.peek(D),DB);same(m.peek(F-8),I+0x21A5092);same(m.readDword(D+0xC),9);
        check(!m.reads.contains(S));same(m.writes.size(),9);
    }
    private static void knownFree() {
        Ram m=ram(true,2,3);m.poke(D,0);m.poke(TABLE+0x10,I+0x855830);m.poke(TABLE+0x38,I+0x86E140);m.poke(A+0x408,0xB000);m.poke(0xB000,0xC000);m.poke(0xC010,I+0x8571C0);
        Entry e=entry(D,n());var out=KnownTransferForward238.execute(e,m,null,null,null,bounded());
        same(out.volatileBits(),change(e.volatileBits(),D,0L,0L,8L,0xC000L,S-0x28));returned(out,n(),RET);
        same(m.peek(D),TB);same(m.readDword(D+0xC),2);same(m.readDword(T+0xC),0);
        check(m.reads.contains(A+0x408));check(m.reads.contains(F-8));
    }
    private static void recursivePrefix() {
        Ram m=ram(true,1,3);RuntimeException boundary=new UnsupportedOperationException("before-first-recursive");
        Calls ports=new Ports(){@Override public VolatileBits invoke(Call c){m.writeQword(D+0x10,B);return c.volatileBits();}};
        Budget budget=(site,cursor,end)->{if(site==0x21A511AL){same(cursor,F);throw boundary;}};
        try{TransferFull238.execute(entry(D,n()),m,ports,null,budget);throw new AssertionError("missing boundary");}
        catch(RuntimeException failure){check(failure==boundary);}
        same(m.peek(F+0x20),0L);same(m.peek(F+0x28),0L);same(m.peek(F+0x30),F+0x40);
        same(m.peek(F+0x40),I+0x46B3A90L);same(m.peek(F+0x448),I+0x54DE260L);same(m.peek(F-8),I+0x21A5092);
        check(!m.reads.contains(S));
    }
    private static void savedAlias() {
        Ram m=ram(false,0,3);long header=S+8;NonvolatileBits incoming=nv(n(),DB,0x1122334400000003L,A,n().rdiBits());
        var out=TransferFull238.execute(entry(header,incoming),m,null,null,bounded());
        same(out.volatileBits().raxBits(),header);same(out.volatileBits().r11Bits(),S-0x28);
        returned(out,nv(incoming,DB,3L,A,incoming.rdiBits()),RET);same(m.readDword(header+0xC),0);
    }
    private static Ram ram(boolean equal,int count,int capacity){Ram m=new Ram();m.poke(S,RET);m.poke(D,DB);m.poke32(D+8,capacity);m.poke32(D+0xC,9);m.poke(D+0x10,A);m.poke(T,TB);m.poke32(T+8,5);m.poke32(T+0xC,count);m.poke(T+0x10,equal?A:B);m.poke(A,TABLE);m.poke(TABLE+0x10,TARGET);return m;}
    private static Entry entry(long destination,NonvolatileBits n){return new Entry(I,S,change(v(0x100),0xE001,destination,T,0x8000000000000038L,0xF000000000000009L,0xE011),n);}
    private static Budget bounded(){AtomicInteger n=new AtomicInteger();return (site,cursor,end)->{if(n.incrementAndGet()>100)throw new UnsupportedOperationException("finite238budget");};}
    private static Bits128 x(long v){return new Bits128(0x8000000000000000L|v,0xF000000000000000L|v);}
    private static VolatileBits v(long t){return new VolatileBits(t+1,t+2,t+3,t+8,t+9,t+10,t+11,x(t+16),x(t+32),x(t+48),x(t+64),x(t+80),x(t+96));}
    private static NonvolatileBits n(){return new NonvolatileBits(0xB1,0xB2,0xB3,0xB4,0xF000000100000005L,0xB6,0xB7,0xB8,x(0xB9));}
    private static NonvolatileBits nv(NonvolatileBits n,long b,long p,long s,long d){return new NonvolatileBits(b,p,s,d,n.r12Bits(),n.r13Bits(),n.r14Bits(),n.r15Bits(),n.xmm6());}
    private static VolatileBits change(VolatileBits v,long a,long c,long d,long r8,long r9,long r11){return new VolatileBits(a,c,d,r8,r9,v.r10Bits(),r11,v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static VolatileBits rax(VolatileBits v,long a){return change(v,a,v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r11Bits());}
    private static VolatileBits x0(VolatileBits v,Bits128 x){return new VolatileBits(v.raxBits(),v.rcxBits(),v.rdxBits(),v.r8Bits(),v.r9Bits(),v.r10Bits(),v.r11Bits(),x,v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());}
    private static void returned(NormalReturn out,NonvolatileBits n,long rip){same(out.nonvolatileBits(),n);same(out.returnRipBits(),rip);same(out.callerRspBits(),S+8);}
    private static class Ports implements Calls {
        @Override public VolatileBits invoke(Call call){throw new AssertionError("unexpected CALL "+Long.toHexString(call.callSiteRva()));}
        @Override public NormalReturn tail(Tail tail){throw new AssertionError("unexpected TAIL");}
        @Override public long readGsQword58(){throw new AssertionError("unexpected GS");}
    }
    private static final class Ram implements Memory {
        final Map<Long,Integer> data=new HashMap<>();final List<Long> reads=new ArrayList<>(),writes=new ArrayList<>();
        void poke(long a,long v){for(int j=0;j<8;j++)data.put(a+j,(int)(v>>>(j*8))&255);}
        void poke32(long a,int v){for(int j=0;j<4;j++)data.put(a+j,(v>>>(j*8))&255);}
        void poke128(long a,Bits128 v){poke(a,v.lowBits());poke(a+8,v.highBits());}
        long peek(long a){long v=0;for(int j=0;j<8;j++){Integer b=data.get(a+j);if(b==null)throw new UnsupportedOperationException("unheld238RAM "+Long.toHexString(a+j));v|=(long)b<<(j*8);}return v;}
        @Override public long readQword(long a){reads.add(a);return peek(a);}
        @Override public void writeQword(long a,long v){writes.add(a);poke(a,v);}
        @Override public int readDword(long a){int v=0;for(int j=0;j<4;j++)v|=readUnsignedByte(a+j)<<(j*8);return v;}
        @Override public void writeDword(long a,int v){for(int j=0;j<4;j++)writeByte(a+j,v>>>(j*8));}
        @Override public int readUnsignedByte(long a){Integer v=data.get(a);if(v==null)throw new UnsupportedOperationException("unheld238byte");return v;}
        @Override public void writeByte(long a,int v){data.put(a,v&255);}
        @Override public Bits128 read128(long a){return new Bits128(readQword(a),readQword(a+8));}
        @Override public void write128(long a,Bits128 v){writeQword(a,v.lowBits());writeQword(a+8,v.highBits());}
        @Override public int lockedXaddDword(long a,int delta){throw new UnsupportedOperationException("unused238atomic");}
    }
    private static void run(String name,Runnable test){test.run();scenes++;System.out.println("PASS "+name);}
    private static void same(Object actual,Object expected){checks++;if(!java.util.Objects.equals(actual,expected))throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected);}
    private static void check(boolean condition){checks++;if(!condition)throw new AssertionError("check="+checks);}
}
