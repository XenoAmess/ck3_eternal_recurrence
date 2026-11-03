package org.xar.ck3.study.m6.posterror256;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownAllocateErrorFp625;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.study.m6.poststate240.PostState240Api;

/** Mechanical adaptation of the pre-API frozen256 literals; no new producer/API or consumer. */
public final class Error32PostState256IndependentTest {
    private static final long IMAGE=0x0000000140000000L,S=0x0000000000100008L;
    private static final long P=0x00000000000FFFE0L,C=0x00000000000FFFD8L;
    private static final long CHILD_RET=0x000000014423B195L;
    private static final long OLD_RET=0x0000000140111110L,FRESH_RET=0x0000000140222220L;
    private static final long CALLER_SP=0x0000000000100010L;
    private static final long R12=0xFEDCBA9876543210L,R12_BAD=0xFEDCBA9876543211L;
    private static final QueueFp604Api.Mxcsr M0=new QueueFp604Api.Mxcsr(0x1F80,0xFFC0);
    private static final long[] CHILD_RAX={0x0000000000000000L,0x0000000100000000L,0xFFFFFFFFFFFFFFF0L};
    private static final long[] FINAL_RAX={0x000000014542F210L,0x0000000100000020L,0x0000000000000010L};
    private static final boolean[] POST_DF={true,true,false};
    private static final QueueFp604Api.Mxcsr[] POST_M={
        new QueueFp604Api.Mxcsr(0x5F84,0xFFC4),new QueueFp604Api.Mxcsr(0x3F81,0xFFFF),
        new QueueFp604Api.Mxcsr(0x1F80,0xFFC1)};
    private static final String[] GUARD_MESSAGES={"Return RIP mismatch","Caller RSP mismatch","Nonvolatile mismatch"};

    private Error32PostState256IndependentTest() { }
    public static void main(String[] args) {
        for(int i=0;i<3;i++)normal(i);
        stopped();
        for(int i=0;i<3;i++)ordinaryReturnGuard(i);
        System.out.println("Error32PostState256IndependentTest: 7 frozen generic cases");
    }

    private static void normal(int caseIndex) {
        Ram ram=ram();Port port=new Port(ram,caseIndex);
        QueueFp604Api.Outcome outcome=new Error32PostState256(port).execute(input(),ram);
        need(outcome instanceof QueueFp604Api.Normal,"normal case returned no Normal");
        QueueFp604Api.Normal actual=(QueueFp604Api.Normal)outcome;
        GovernmentCrtBoundary185Api.NormalReturn nr=actual.base().normalReturn();
        need(nr.volatileBits().equals(postV(FINAL_RAX[caseIndex])),"complete postV/sourceRAX differs");
        need(nr.nonvolatileBits().equals(n(R12)),"complete postN including highR12/XMM6 differs");
        need(nr.returnRipBits()==FRESH_RET && nr.callerRspBits()==CALLER_SP,"fresh outerRET/SP differs");
        need(actual.base().postDirectionFlagSet()==POST_DF[caseIndex],"actual child postDF was lost");
        need(actual.postMxcsr()==POST_M[caseIndex] && actual.postMxcsr().equals(POST_M[caseIndex]),
                "actual postMxcsr identity/bits/mask were changed");
        need(port.calls==1,"child was replayed or omitted");
        need(ram.events.equals(normalTrace()),"extra/missing source/provider RAM event");
        need(ram.peek64(C)==CHILD_RET && ram.peek64(S)==FRESH_RET,"normal final stack RAM differs");
    }

    private static void stopped() {
        Ram ram=ram();Port port=new Port(ram,3);
        QueueFp604Api.Outcome outcome=new Error32PostState256(port).execute(input(),ram);
        need(port.stop!=null && outcome==port.stop,"typedStopped object identity changed");
        need(port.calls==1,"typedStop retried or omitted the child");
        QueueFp604Api.Snapshot snapshot=port.stop.snapshot();
        need(snapshot.currentState().equals(new GovernmentCrtBoundary185Api.Entry(IMAGE,C,entryV(),n(R12))),
                "typedStop complete actual child Entry changed");
        need(snapshot.currentState()==port.received.childEntry(),"typedStop child Entry reference changed");
        need(snapshot.instructionRva()==0x424FC74L && !snapshot.directionFlagSet() && snapshot.mxcsr()==M0,
                "typedStop actual location/environment changed");
        need(port.stop.reason()==QueueFp604Api.StopReason.MISSING_POST_STATE
                && port.stop.raisedConditionBits()==0 && port.stop.originCallSiteRva()==0x423B190L,
                "typedStop reason/conditions/source origin changed");
        need(ram.events.equals(List.of(new Access("source","W8",C,CHILD_RET))),
                "typedStop executed childRET/outerRET or extra RAM effects");
        need(ram.peek64(C)==CHILD_RET && ram.peek64(S)==OLD_RET,"typedStop stack prefix differs");
    }

    private static void ordinaryReturnGuard(int variant) {
        Ram ram=ram();Port port=new Port(ram,4+variant);
        IllegalArgumentException rejected=null;
        try {
            new Error32PostState256(port).execute(input(),ram);
            throw new AssertionError("invalid offered Normal became an Outcome");
        } catch(IllegalArgumentException expected) {
            rejected=expected;
        }
        need(rejected!=null && GUARD_MESSAGES[variant].equals(rejected.getMessage()),
                "ordinary public return guard did not reject the supplied wrong field");
        need(port.calls==1,"validation retried or omitted the child");
        need(ram.events.equals(normalTrace().subList(0,3)),"validation ran outerRET or extra RAM effects");
        need(ram.peek64(C)==CHILD_RET && ram.peek64(S)==FRESH_RET,"validation rolled back child RAM effects");
        need(port.stop==null,"validation was turned into typedStopped");
    }

    private static final class Port implements KnownAllocateErrorFp625.ErrorCalls {
        private final Ram ram;private final int mode;private int calls;
        private KnownAllocateErrorFp625.ErrorCall received;
        private QueueFp604Api.Stopped stop;
        private Port(Ram ram,int mode) { this.ram=ram;this.mode=mode; }

        @Override public QueueFp604Api.Outcome invoke(KnownAllocateErrorFp625.ErrorCall frame) {
            calls++;need(calls==1,"unexpected second child invocation");received=frame;
            GovernmentCrtBoundary185Api.Call actual=frame.original();
            need(actual.callSiteRva()==0x423B190L
                    && actual.kind()==GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA
                    && actual.targetBits()==0x424FC74L && actual.rspBits()==P,
                    "actual CALL site/kind/target/preSP differs");
            need(actual.volatileBits().equals(entryV()) && actual.nonvolatileBits().equals(n(R12)),
                    "actual complete CALL V/N differs");
            need(frame.childEntry().equals(new GovernmentCrtBoundary185Api.Entry(IMAGE,C,entryV(),n(R12))),
                    "true post-push child Entry differs");
            need(!frame.directionFlagSet() && frame.preMxcsr()==M0 && frame.preMxcsr().equals(M0),
                    "explicit current preDF/MXCSR differs");
            need(frame.returnRipBits()==CHILD_RET && ram.peek64(C)==CHILD_RET,
                    "mature204 did not own the exact one source return push");
            if(mode==3) {
                stop=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
                        new QueueFp604Api.Snapshot(frame.childEntry(),0x424FC74L,false,M0),0,0x423B190L);
                return stop; // explicit target-entry Stop: no hardware condition or childRET is invented
            }

            int normalIndex=mode<3?mode:1;
            long actualChildRip;
            ram.owner="provider";
            try {
                ram.writeQword(S,FRESH_RET);
                actualChildRip=ram.readQword(C);
            } finally {
                ram.owner="source";
            }
            long offeredRip=mode==4?0x000000014423B196L:actualChildRip;
            long offeredSp=mode==5?0x00000000000FFFE8L:P;
            NonvolatileBits offeredN=n(mode==6?R12_BAD:R12);
            GovernmentCrtBoundary185Api.NormalReturn nr=new GovernmentCrtBoundary185Api.NormalReturn(
                    postV(CHILD_RAX[normalIndex]),offeredRip,offeredSp,offeredN);
            return new QueueFp604Api.Normal(new FullCopy437Api.CallResult(nr,POST_DF[normalIndex]),POST_M[normalIndex]);
        }
    }

    private static PostState240Api.Input input() {
        return new PostState240Api.Input(new GovernmentCrtBoundary185Api.Entry(IMAGE,S,entryV(),n(R12)),
                false,M0,0x424E384L);
    }
    private static VolatileBits entryV() {
        return new VolatileBits(0x1122334455667788L,0x2233445566778899L,0x33445566778899AAL,
                0x445566778899AABBL,0x5566778899AABBCCL,0x66778899AABBCCDDL,0x778899AABBCCDDEEL,
                new Bits128(0x0102030405060708L,0x1112131415161718L),
                new Bits128(0x2122232425262728L,0x3132333435363738L),
                new Bits128(0x4142434445464748L,0x5152535455565758L),
                new Bits128(0x6162636465666768L,0x7172737475767778L),
                new Bits128(0x8182838485868788L,0x9192939495969798L),
                new Bits128(0xA1A2A3A4A5A6A7A8L,0xB1B2B3B4B5B6B7B8L));
    }
    private static VolatileBits postV(long rax) {
        return new VolatileBits(rax,0xC100000000000001L,0xD200000000000002L,
                0xA800000000000008L,0xA900000000000009L,0xAA00000000000010L,0xAB00000000000011L,
                new Bits128(0x1011121314151617L,0x18191A1B1C1D1E1FL),
                new Bits128(0x2021222324252627L,0x28292A2B2C2D2E2FL),
                new Bits128(0x3031323334353637L,0x38393A3B3C3D3E3FL),
                new Bits128(0x4041424344454647L,0x48494A4B4C4D4E4FL),
                new Bits128(0x5051525354555657L,0x58595A5B5C5D5E5FL),
                new Bits128(0x6061626364656667L,0x68696A6B6C6D6E6FL));
    }
    private static NonvolatileBits n(long r12) {
        return new NonvolatileBits(0x0B0B0B0B0B0B0B0BL,0x0C0C0C0C0C0C0C0CL,
                0x0D0D0D0D0D0D0D0DL,0x0E0E0E0E0E0E0E0EL,r12,0x1313131313131313L,
                0x1414141414141414L,0x1515151515151515L,
                new Bits128(0x6161616161616161L,0x6262626262626262L));
    }
    private static List<Access> normalTrace() {
        return List.of(new Access("source","W8",C,CHILD_RET),new Access("provider","W8",S,FRESH_RET),
                new Access("provider","R8",C,CHILD_RET),new Access("source","R8",S,FRESH_RET));
    }
    private static Ram ram() { Ram ram=new Ram();ram.seed64(S,OLD_RET);return ram; }
    private static void need(boolean condition,String message) { if(!condition)throw new AssertionError(message); }
    private record Access(String owner,String operation,long address,long value) { }

    /** Strict plain byte RAM; test inspections use peek and never change control-flow data. */
    private static final class Ram implements GovernmentCrtBoundary185Api.Memory {
        private final Map<Long,Byte> bytes=new HashMap<>();
        private final List<Access> events=new ArrayList<>();
        private String owner="source";
        private int raw(long address) {
            Byte value=bytes.get(address);
            if(value==null)throw new AssertionError("Unseeded RAM "+Long.toHexString(address));
            return value&0xFF;
        }
        private void seed64(long address,long value) {
            for(int i=0;i<8;i++)bytes.put(address+i,(byte)(value>>>(8*i)));
        }
        private long peek64(long address) {
            long value=0L;for(int i=0;i<8;i++)value|=(long)raw(address+i)<<(8*i);return value;
        }
        @Override public long readQword(long address) {
            long value=peek64(address);events.add(new Access(owner,"R8",address,value));return value;
        }
        @Override public int readDword(long address) {
            int value=0;for(int i=0;i<4;i++)value|=raw(address+i)<<(8*i);
            events.add(new Access(owner,"R4",address,Integer.toUnsignedLong(value)));return value;
        }
        @Override public int readUnsignedByte(long address) {
            int value=raw(address);events.add(new Access(owner,"R1",address,value));return value;
        }
        @Override public void writeQword(long address,long value) {
            events.add(new Access(owner,"W8",address,value));seed64(address,value);
        }
        @Override public void writeDword(long address,int value) {
            events.add(new Access(owner,"W4",address,Integer.toUnsignedLong(value)));
            for(int i=0;i<4;i++)bytes.put(address+i,(byte)(value>>>(8*i)));
        }
        @Override public void writeByte(long address,int value) {
            events.add(new Access(owner,"W1",address,value&0xFF));bytes.put(address,(byte)value);
        }
        @Override public int lockedXaddDword(long address,int addend) { throw new AssertionError("Unexpected LOCK XADD"); }
        @Override public Bits128 read128(long address) { throw new AssertionError("Unexpected vector load"); }
        @Override public void write128(long address,Bits128 value) { throw new AssertionError("Unexpected vector store"); }
    }
}
