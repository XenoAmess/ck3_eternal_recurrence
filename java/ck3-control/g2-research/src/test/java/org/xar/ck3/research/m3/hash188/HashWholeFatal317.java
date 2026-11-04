package org.xar.ck3.research.m3.hash188;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m3.hashwholefp309.HashWholeFp309Api;
import org.xar.ck3.research.m3.hashwholefp310.HashWholeFp310;

/**
 * Two finite owned DATA cases from the independently frozen original317 oracle.
 * Source-only handoff: this owner has not compiled or executed this manual.
 * Foreign algorithms, unrepresented flags/XMM/YMM, OS trap delivery and Game are unqualified.
 */
public final class HashWholeFatal317 {
    private HashWholeFatal317() { }
    private static final long BASE=0x140000000L, ENTRY_SP=0x100000L;
    private static final long BODY_SP=0xFFF58L, CHILD_SP=0xFFF50L;
    private static final long MAP=0x2000L, OUTPUT=0x3000L, DESCRIPTOR=0x4000L;
    private static final long ENTRY_RETURN=0xA0B0C0D0E0F00123L, ORIGIN=0x317L;
    private static final boolean INITIAL_DF=true;
    private static final int MXCSR_VALUE=0x2000, MXCSR_KNOWN_MASK=0x6000;

    public static void main(String[] ignored) {
        normalToOwnInt3();
        stoppedIdentityNoInt3();
        System.out.println("HashWholeFatal317: 2 finite owned DATA cases passed");
    }
    private static void normalToOwnInt3() { runCase(false); }
    private static void stoppedIdentityNoInt3() { runCase(true); }

    private static void runCase(boolean terminalStops) {
        RawRam ram=publicFixtureRam();
        GovernmentCrtBoundary185Api.LoopBudget budget=(header,address) -> {
            throw new AssertionError("unexpected loop budget step");
        };
        QueueFp604Api.Mxcsr fp=new QueueFp604Api.Mxcsr(MXCSR_VALUE,MXCSR_KNOWN_MASK);
        var input=new HashWholeFp309Api.Input(new QueueFp604Api.Input(
            new FullCopy437Api.Input(new GovernmentCrtBoundary185Api.Entry(
                BASE,ENTRY_SP,initialV(),initialN()),INITIAL_DF,budget),fp),ORIGIN);
        long[] sites={0xC39F2FL,0xC39F83L,0xC39F88L};
        long[] targets={0x86E160L,0x86F210L,0x4232CF4L};
        long[] returns={BASE+0xC39F34L,BASE+0xC39F88L,BASE+0xC39F8DL};
        long[] effectAddresses={0x6001L,0x6002L,0x6003L};
        int[] effectValues={0xA1,0xB2,0xC3};
        VolatileBits[] beforeV={firstCallV(),secondCallV(),scriptedV(2)};
        QueueFp604Api.Normal[] normals=new QueueFp604Api.Normal[3];
        for(int i=0;i<normals.length;i++) {
            normals[i]=new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(scriptedV(i+1),
                    returns[i],BODY_SP,scriptedN()),true),fp);
        }
        var stopEntry=new GovernmentCrtBoundary185Api.Entry(
            BASE,CHILD_SP,scriptedV(3),scriptedN());
        var stopSnapshot=new QueueFp604Api.Snapshot(stopEntry,0x4232CF7L,true,fp);
        var stop=new QueueFp604Api.Stopped(QueueFp604Api.StopReason.MISSING_POST_STATE,
            stopSnapshot,0,0xC39F88L);
        var stopWrapper=new HashWholeFp309Api.Forwarded(stop);
        int[] count={0};
        HashWholeFp309Api.CallFrame[] offeredFrames=new HashWholeFp309Api.CallFrame[3];

        HashWholeFp309Api.Result actual=HashWholeFp310.execute(input,ram,(frame,sameMemory) -> {
            int i=count[0]++;
            check(i<3,"no additional foreign callback");
            check(sameMemory==ram,"identical owned RAM");
            eq(input,frame.ownerInput(),"owner input DATA");
            check(frame.budget()==budget,"budget identity");
            check(frame.childInput().base().budget()==budget,"child budget identity");
            check(frame.originCallSiteRva()==ORIGIN,"origin metadata");
            check(frame.original().kind()==GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,
                "direct source call");
            check(frame.original().callSiteRva()==sites[i],"source call site/order");
            check(frame.original().targetBits()==targets[i],"source call target");
            check(frame.instructionLength()==5,"source instruction length");
            check(frame.original().rspBits()==BODY_SP,"pre-call SP");
            check(frame.returnRipBits()==returns[i],"exact image plus return RVA");
            eq(beforeV[i],frame.original().volatileBits(),"full pre-call V");
            eq(scriptedN(),frame.original().nonvolatileBits(),"full pre-call N");
            eq(new GovernmentCrtBoundary185Api.Entry(BASE,CHILD_SP,beforeV[i],scriptedN()),
                frame.childEntry(),"full child image/SP/V/N");
            check(frame.directionFlagSet(),"explicit child DF");
            check(frame.childInput().base().directionFlagSet(),"explicit child input DF");
            check(frame.preMxcsr()==fp,"exact explicit partial MXCSR object");
            check(frame.preMxcsr().valueBits()==MXCSR_VALUE,"partial MXCSR value");
            check(frame.preMxcsr().knownMaskBits()==MXCSR_KNOWN_MASK,"partial MXCSR mask");
            check(ram.peek(CHILD_SP,8)==returns[i],"exact one owned CALL push");
            exactPrefixBeforeOpaqueEffect(ram,i+1);
            offeredFrames[i]=frame;
            sameMemory.writeByte(effectAddresses[i],effectValues[i]);
            if(terminalStops && i==2) return stopWrapper;
            return new HashWholeFp309Api.Forwarded(normals[i]);
        });

        check(count[0]==3,"both fatal CALLs actually offered exactly once");
        if(terminalStops) {
            check(actual==stopWrapper,"original Forwarded object propagated");
            check(actual instanceof HashWholeFp309Api.Forwarded,"foreign stop arm");
            var forwarded=(HashWholeFp309Api.Forwarded)actual;
            check(forwarded.actual()==stop,"original typed Stopped identity");
            check(stop.snapshot()==stopSnapshot,"original foreign snapshot identity");
            check(stopSnapshot.currentState()==stopEntry,"original foreign entry identity");
            check(stopSnapshot.instructionRva()==0x4232CF7L,"foreign source PC retained");
            eq(new GovernmentCrtBoundary185Api.Entry(BASE,CHILD_SP,scriptedV(3),scriptedN()),
                stopSnapshot.currentState(),"foreign full stop state");
            check(stopSnapshot.directionFlagSet(),"foreign stop DF");
            check(stopSnapshot.mxcsr()==fp,"foreign stop exact partial MXCSR");
            check(stop.reason()==QueueFp604Api.StopReason.MISSING_POST_STATE,"stop reason retained");
            check(stop.raisedConditionBits()==0,"stop conditions retained");
            check(stop.originCallSiteRva()==0xC39F88L,"stop origin retained");
        } else {
            check(actual instanceof HashWholeFp309Api.Int3Boundary,"own INT3 boundary arm");
            var boundary=(HashWholeFp309Api.Int3Boundary)actual;
            check(boundary.terminalFrame()==offeredFrames[2],"actual F88 frame identity");
            check(boundary.terminalNormal()==normals[2],"actual terminal Normal identity");
            var snapshot=boundary.snapshot();
            check(snapshot.instructionRva()==0xC39F8DL,"own unexecuted INT3 source PC");
            eq(new GovernmentCrtBoundary185Api.Entry(BASE,BODY_SP,scriptedV(3),scriptedN()),
                snapshot.currentState(),"own full INT3 state; caller has not returned");
            check(snapshot.directionFlagSet(),"own INT3 DF");
            check(snapshot.mxcsr()==normals[2].postMxcsr(),"exact terminal post-MXCSR reference");
            check(snapshot.mxcsr().knownMaskBits()==MXCSR_KNOWN_MASK,"unknown MXCSR stays unknown");
        }
        exactFinalMemory(ram);
    }

    private static Bits128 initialX(int i) {
        return new Bits128(0x1000000000000000L+i,0x2000000000000000L+i);
    }
    private static Bits128 scriptedX(long lowPrefix,long highPrefix,int i) {
        return new Bits128(lowPrefix+i,highPrefix+i);
    }
    private static VolatileBits initialV() {
        return new VolatileBits(0x0102030405060708L,MAP,OUTPUT,
            0xAABBCCDD80000002L,DESCRIPTOR,0x1112131415161718L,0x2122232425262728L,
            initialX(0),initialX(1),initialX(2),initialX(3),initialX(4),initialX(5));
    }
    private static NonvolatileBits initialN() {
        return new NonvolatileBits(0x1213141516171819L,0x2122232425262728L,
            0x31323334353637AAL,0x4142434445464748L,0x5152535455565758L,
            0x6162636465666768L,0x7172737475767778L,0x8182838485868788L,
            new Bits128(0x3000000000000006L,0x4000000000000006L));
    }
    /** Explicit public reply DATA, not an assumed foreign preservation rule. */
    private static NonvolatileBits scriptedN() {
        return new NonvolatileBits(0x5050L,0xFFFC8L,0x3132333435363701L,
            DESCRIPTOR,0x5152535455565758L,0xFFFFFFFF80000002L,MAP,OUTPUT,
            new Bits128(0x3000000000000006L,0x4000000000000006L));
    }
    private static VolatileBits scriptedV(int index) {
        long p,xl,xh,a;
        switch(index) {
            case 1 -> { p=0xA000000000000000L; xl=0xA100000000000000L; xh=0xA200000000000000L; a=0xA1A2A3A40000001FL; }
            case 2 -> { p=0xB000000000000000L; xl=0xB100000000000000L; xh=0xB200000000000000L; a=0xB1B2B3B480000000L; }
            case 3 -> { p=0xC000000000000000L; xl=0xC100000000000000L; xh=0xC200000000000000L; a=0xC1C2C3C40000001EL; }
            default -> throw new AssertionError("outside three public DATA replies");
        }
        return new VolatileBits(a,p+2,p+3,p+8,p+9,p+10,p+11,
            scriptedX(xl,xh,0),scriptedX(xl,xh,1),scriptedX(xl,xh,2),
            scriptedX(xl,xh,3),scriptedX(xl,xh,4),scriptedX(xl,xh,5));
    }
    private static VolatileBits firstCallV() {
        VolatileBits v=initialV();
        return new VolatileBits(0x5000L,4L,1L,0xAABBCCDD80000002L,10L,
            0x1112131415161718L,0x2122232425262728L,
            v.xmm0(),v.xmm1(),v.xmm2(),v.xmm3(),v.xmm4(),v.xmm5());
    }
    private static VolatileBits secondCallV() {
        VolatileBits v=scriptedV(1);
        return new VolatileBits(v.raxBits(),0x100008L,MAP,v.r8Bits(),v.r9Bits(),
            v.r10Bits(),v.r11Bits(),v.xmm0(),v.xmm1(),v.xmm2(),
            v.xmm3(),v.xmm4(),v.xmm5());
    }

    private static List<String> literalMemoryTrace() {
        return List.of(
            "W64:100010:1213141516171819",
            "W64:ffff8:2122232425262728",
            "W64:ffff0:31323334353637aa",
            "W64:fffe8:4142434445464748",
            "W64:fffe0:5152535455565758",
            "W64:fffd8:6162636465666768",
            "W64:fffd0:7172737475767778",
            "W64:fffc8:8182838485868788",
            "R32:2014:3","R64:2008:5000","R8:5054:0","R8:2018:0",
            "W64:fff50:140c39f34","W8:6001:a1",
            "W64:fff50:140c39f88","W8:6002:b2",
            "W64:fff50:140c39f8d","W8:6003:c3");
    }
    private static void exactPrefixBeforeOpaqueEffect(RawRam actual,int callIndex) {
        eq(literalMemoryTrace().subList(0,13+2*(callIndex-1)),actual.trace(),
            "exact prefix before public opaque effect "+callIndex);
    }
    private static void exactFinalMemory(RawRam actual) {
        eq(literalMemoryTrace(),actual.trace(),"complete source/public-effect access trace");
        RawRam expected=publicFixtureRam();
        expected.seed(0x100010L,8,0x1213141516171819L);
        expected.seed(0xFFFF8L,8,0x2122232425262728L);
        expected.seed(0xFFFF0L,8,0x31323334353637AAL);
        expected.seed(0xFFFE8L,8,0x4142434445464748L);
        expected.seed(0xFFFE0L,8,0x5152535455565758L);
        expected.seed(0xFFFD8L,8,0x6162636465666768L);
        expected.seed(0xFFFD0L,8,0x7172737475767778L);
        expected.seed(0xFFFC8L,8,0x8182838485868788L);
        expected.seed(CHILD_SP,8,BASE+0xC39F8DL);
        expected.seed(0x6001L,1,0xA1);
        expected.seed(0x6002L,1,0xB2);
        expected.seed(0x6003L,1,0xC3);
        check(Arrays.equals(expected.snapshot(),actual.snapshot()),"exact full owned RAM");
    }
    /** Fixture seeding and assertion peeks never enter the source access trace. */
    private static final class RawRam implements FullCopy437Api.Memory {
        private final byte[] bytes=new byte[0x200000];
        private final List<String> trace=new ArrayList<>();
        RawRam() { Arrays.fill(bytes,(byte)0x5A); }
        private int index(long address,int width) {
            if(width<1 || width>8 || address<0 || address>bytes.length-width)
                throw new AssertionError("owned RAM address/width");
            return (int)address;
        }
        long peek(long address,int width) {
            int at=index(address,width); long result=0;
            for(int i=0;i<width;i++) result|=(bytes[at+i]&255L)<<(8*i);
            return result;
        }
        void seed(long address,int width,long value) {
            int at=index(address,width);
            for(int i=0;i<width;i++) bytes[at+i]=(byte)(value>>>(8*i));
        }
        long read(long address,int width) {
            long value=peek(address,width);
            trace.add("R"+(width*8)+":"+Long.toHexString(address)+":"+Long.toHexString(value));
            return value;
        }
        void write(long address,int width,long value) {
            seed(address,width,value);
            trace.add("W"+(width*8)+":"+Long.toHexString(address)+":"+Long.toHexString(peek(address,width)));
        }
        List<String> trace() { return List.copyOf(trace); }
        byte[] snapshot() { return bytes.clone(); }
        @Override public int readDword(long address) { return (int)read(address,4); }
        @Override public long readQword(long address) { return read(address,8); }
        @Override public int readUnsignedByte(long address) { return (int)read(address,1); }
        @Override public void writeQword(long address,long value) { write(address,8,value); }
        @Override public void writeByte(long address,int value) { write(address,1,value); }
        private AssertionError outsidePrefix(String operation) {
            return new AssertionError("operation outside these finite DATA paths: "+operation);
        }
        @Override public void writeDword(long address,int value) { throw outsidePrefix("writeDword"); }
        @Override public int lockedXaddDword(long address,int addend) { throw outsidePrefix("lockedXaddDword"); }
        @Override public Bits128 read128(long address) { throw outsidePrefix("read128"); }
        @Override public void write128(long address,Bits128 value) { throw outsidePrefix("write128"); }
        @Override public void writeWord(long address,int value) { throw outsidePrefix("writeWord"); }
        @Override public void write128NonTemporal(long address,Bits128 value) { throw outsidePrefix("write128NonTemporal"); }
        @Override public void sfence() { throw outsidePrefix("sfence"); }
        @Override public int readUnsignedWord(long address) { throw outsidePrefix("readUnsignedWord"); }
        @Override public FullCopy437Api.Bits256 read256(long address) { throw outsidePrefix("read256"); }
        @Override public void write256(long address,FullCopy437Api.Bits256 value) { throw outsidePrefix("write256"); }
        @Override public void write256NonTemporal(long address,FullCopy437Api.Bits256 value) { throw outsidePrefix("write256NonTemporal"); }
    }
    private static RawRam publicFixtureRam() {
        RawRam ram=new RawRam();
        ram.seed(ENTRY_SP,8,ENTRY_RETURN);
        ram.seed(MAP+8,8,0x5000L);
        ram.seed(MAP+0x10,4,0x11223344L);
        ram.seed(MAP+0x14,4,3);
        ram.seed(MAP+0x18,1,0);
        ram.seed(0x5054L,1,0);
        return ram;
    }
    private static void check(boolean condition,String label) {
        if(!condition) throw new AssertionError(label);
    }
    private static void eq(Object expected,Object actual,String label) {
        if(!Objects.equals(expected,actual)) throw new AssertionError(label);
    }
}
