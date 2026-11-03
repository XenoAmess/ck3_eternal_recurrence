package org.xar.ck3.study.m6.offline243;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.full238.TransferFull238;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Budget;
import org.xar.ck3.study.m6.full238.TransferFull238Api.Floating;
import org.xar.ck3.study.m6.full239.Move4Full239;

/** Manual unsupported-port prefix witnesses; no arithmetic or hardware oracle. */
public final class FloatingUnsupportedPrefix243 {
    private static final long I=0x140000000L,S=0xA008L,D=0x2000L,T=0x3000L;
    private static final long A=0x4000L,B=0x5000L,DB=0x6000L,TB=0x7000L;
    private static final long RET=0xFEDCBA9876543210L,CALL_GUARD=0xD15EA5E0C0FFEE01L;
    private static final long MULT=I+0x49F64F0L;
    private static final int CAPACITY=5,COUNT=6,MULTIPLIER=0x7F800001;
    // A scripted stage-1 token, not an assertion about any actual FP environment.
    private static final Bits128 CONVERTED=new Bits128(0x40A00000L,0L);
    private static int scenes,checks;
    private FloatingUnsupportedPrefix243() { }

    public static void main(String[] args) {
        if(args.length==0) {
            reject(true,1);reject(true,2);reject(false,1);reject(false,2);
        } else if(args.length==1) {
            switch(args[0]) {
                case "715-first" -> reject(true,1);
                case "715-second" -> reject(true,2);
                case "B2-first" -> reject(false,1);
                case "B2-second" -> reject(false,2);
                default -> throw new IllegalArgumentException("unknown new-prefix selector");
            }
        } else throw new IllegalArgumentException("expected zero args or one new-prefix selector");
        System.out.println("PASS newPrefixScenes="+scenes+" checks="+checks
                +" floatingStageRejectionOnly=true oldCasesRepeated=false"
                +" arithmeticOracle=false hardwareFP=false Native=false Game=false");
    }

    private static void reject(boolean whole715,int stopStage) {
        long f=S-(whole715?0x478L:0x48L);
        Ram ram=new Ram();
        ram.seedQ(S,RET);ram.seedQ(f-8,CALL_GUARD);
        ram.seedQ(D,DB);ram.seedD(D+8,CAPACITY);ram.seedD(D+0xC,9);ram.seedQ(D+0x10,A);
        ram.seedQ(T,TB);ram.seedD(T+8,17);ram.seedD(T+0xC,COUNT);ram.seedQ(T+0x10,B);
        ram.seedD(MULT,MULTIPLIER);
        Map<Long,Integer> expected=new HashMap<>(ram.bytes);
        NonvolatileBits n=nonvolatile();
        List<Access> prefix=new ArrayList<>();
        if(whole715) {
            expectQ(prefix,expected,S+8,n.rbxBits());
            expectQ(prefix,expected,S+0x10,n.rbpBits());
            expectQ(prefix,expected,S+0x18,n.rsiBits());
            expectQ(prefix,expected,S-8,n.rdiBits());
            expectQ(prefix,expected,S-0x10,n.r12Bits());
            expectQ(prefix,expected,S-0x18,n.r13Bits());
            expectQ(prefix,expected,S-0x20,n.r14Bits());
            expectQ(prefix,expected,S-0x28,n.r15Bits());
            prefix.add(read(8,D+0x10));prefix.add(read(8,T+0x10));
            expectD(prefix,expected,D+0xC,0);
            prefix.add(read(4,T+0xC));prefix.add(read(8,T));prefix.add(read(4,D+8));
        } else {
            expectQ(prefix,expected,S-8,n.rbpBits());
            expectQ(prefix,expected,S-0x10,n.r14Bits());
            expectQ(prefix,expected,S-0x18,n.r15Bits());
            prefix.add(read(8,D+0x10));prefix.add(read(8,T+0x10));
            expectQ(prefix,expected,f+0x50,n.rbxBits());
            expectD(prefix,expected,D+0xC,0);
            prefix.add(read(8,T));
            expectQ(prefix,expected,f+0x28,n.r12Bits());
            prefix.add(read(4,T+0xC));prefix.add(read(4,D+8));
            expectQ(prefix,expected,f+0x58,n.rsiBits());
            expectQ(prefix,expected,f+0x60,n.rdiBits());
            expectQ(prefix,expected,f+0x20,n.r13Bits());
        }
        prefix.add(new Access("FP1",0,0));
        if(stopStage==2) {
            prefix.add(read(4,MULT));prefix.add(new Access("FP2",0,0));
        }
        UnsupportedOperationException original=new UnsupportedOperationException(
                "unsupported-owned-environment-"+(whole715?"715":"B2")+"-stage"+stopStage);
        int[] fp={0},calls={0},bounds={0};
        Floating floating=new Floating() {
            @Override public Bits128 convertSignedDwords(Bits128 input) {
                ram.trace.add(new Access("FP1",0,0));
                equal(++fp[0],1);equal(input,new Bits128(CAPACITY,0));
                if(stopStage==1)throw original;
                return CONVERTED;
            }
            @Override public Bits128 multiplyLowSingle(Bits128 input,int raw) {
                ram.trace.add(new Access("FP2",0,0));
                equal(++fp[0],2);equal(input,CONVERTED);equal(raw,MULTIPLIER);
                throw original;
            }
            @Override public int truncateLowSingle(Bits128 input) {
                throw new AssertionError("stage 3 must not be reached");
            }
        };
        Calls noCalls=new Calls() {
            @Override public VolatileBits invoke(Call call) {
                calls[0]++;throw new AssertionError("CALL before Floating rejection: "+call);
            }
            @Override public NormalReturn tail(Tail tail) {
                calls[0]++;throw new AssertionError("TAIL before Floating rejection");
            }
            @Override public long readGsQword58() {
                calls[0]++;throw new AssertionError("GS before Floating rejection");
            }
        };
        Budget budget=(site,cursor,end)->{
            equal(++bounds[0],1);equal(site,whole715?0x21A5050L:0xB2EEE0L);
            equal(cursor,S);equal(end,0L);
        };
        Entry entry=new Entry(I,S,volatileBits(),n);
        try {
            if(whole715)TransferFull238.execute(entry,ram,noCalls,floating,budget);
            else Move4Full239.execute(entry,ram,noCalls,floating,budget);
            throw new AssertionError("rejection fabricated a normal return");
        } catch(UnsupportedOperationException failure) {
            check(failure==original);
        }
        equal(bounds[0],1);equal(fp[0],stopStage);equal(calls[0],0);
        equal(ram.trace,prefix);equal(ram.bytes,expected);
        equal(ram.peekQ(f-8),CALL_GUARD);equal(ram.peekQ(S),RET);
        check(ram.trace.stream().noneMatch(a->a.kind().equals("R")&&a.address()==S));
        equal(ram.peekD(D+0xC),0);equal(ram.peekD(T+0xC),COUNT);
        equal(ram.peekQ(D),DB);equal(ram.peekQ(T),TB);equal(ram.peekD(D+8),CAPACITY);
        scenes++;
        System.out.println("PASS "+(whole715?"715":"B2")+"-Floating-stage"+stopStage+"-prefix");
    }

    private record Access(String kind,int width,long address) { }
    private static Access read(int width,long address){return new Access("R",width,address);}
    private static void expectQ(List<Access> trace,Map<Long,Integer> data,long a,long value) {
        trace.add(new Access("W",8,a));put(data,a,value,8);
    }
    private static void expectD(List<Access> trace,Map<Long,Integer> data,long a,int value) {
        trace.add(new Access("W",4,a));put(data,a,Integer.toUnsignedLong(value),4);
    }
    private static void put(Map<Long,Integer> data,long a,long value,int width) {
        for(int j=0;j<width;j++)data.put(a+j,(int)(value>>>(j*8))&255);
    }
    private static final class Ram implements Memory {
        final Map<Long,Integer> bytes=new HashMap<>();
        final List<Access> trace=new ArrayList<>();
        void seedQ(long a,long value){put(bytes,a,value,8);}
        void seedD(long a,int value){put(bytes,a,Integer.toUnsignedLong(value),4);}
        long peekQ(long a){return peek(a,8);}
        int peekD(long a){return (int)peek(a,4);}
        private long peek(long a,int width) {
            long value=0;
            for(int j=0;j<width;j++) {
                Integer b=bytes.get(a+j);
                if(b==null)throw new AssertionError("unexpected unheld RAM "+Long.toHexString(a+j));
                value|=(long)b<<(j*8);
            }
            return value;
        }
        @Override public long readQword(long a){trace.add(read(8,a));return peekQ(a);}
        @Override public int readDword(long a){trace.add(read(4,a));return peekD(a);}
        @Override public void writeQword(long a,long value){trace.add(new Access("W",8,a));seedQ(a,value);}
        @Override public void writeDword(long a,int value){trace.add(new Access("W",4,a));seedD(a,value);}
        @Override public int readUnsignedByte(long a){throw new AssertionError("unexpected byte read");}
        @Override public void writeByte(long a,int value){throw new AssertionError("unexpected byte write");}
        @Override public Bits128 read128(long a){throw new AssertionError("unexpected 128-bit read");}
        @Override public void write128(long a,Bits128 value){throw new AssertionError("unexpected 128-bit write");}
        @Override public int lockedXaddDword(long a,int delta){throw new AssertionError("unexpected atomic");}
    }
    private static Bits128 x(long tag){return new Bits128(0x8000000000000000L|tag,0xF000000000000000L|tag);}
    private static VolatileBits volatileBits() {
        return new VolatileBits(0xF00000000000E001L,D,T,0xA000000000000008L,
                0xB000000000000009L,0xC00000000000000AL,0xD00000000000000BL,
                x(1),x(2),x(3),x(4),x(5),x(6));
    }
    private static NonvolatileBits nonvolatile() {
        return new NonvolatileBits(0x81000000000000B1L,0x82000000000000B2L,
                0x83000000000000B3L,0x84000000000000B4L,0xF000000100000005L,
                0x86000000000000B6L,0x87000000000000B7L,0x88000000000000B8L,x(7));
    }
    private static void check(boolean condition){checks++;if(!condition)throw new AssertionError("check="+checks);}
    private static void equal(Object actual,Object expected) {
        checks++;if(!Objects.equals(actual,expected))throw new AssertionError("check="+checks+" actual="+actual+" expected="+expected);
    }
}
