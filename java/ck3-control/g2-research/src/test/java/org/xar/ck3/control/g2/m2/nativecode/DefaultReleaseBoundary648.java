package org.xar.ck3.control.g2.m2.nativecode;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import static org.xar.ck3.control.g2.m2.nativecode.StaticFixture648.e;

/** New C0 direct-public witness, from held14B ASM and frozen independent literal oracle.
 * API-BINDING-ANNEX-RELEASE648 records the later live-RET and foreign SP/N choices.
 * No target body, model Test, old verify, physical-memory or hardware ABI claim is used. */
public final class DefaultReleaseBoundary648 {
    private DefaultReleaseBoundary648() { }
    private static final long IMAGE=0x0000000140000000L, SP=0x0000000070006008L;
    private static final long INITIAL_RET=0x0000000140123456L;
    private static final long ZERO_LIVE_RET=0x8877665544332211L;
    private static final long ALIAS_RET=0x1122334455667788L;
    private static final long FOREIGN_RIP=0x0000000140555555L;
    private static final long FOREIGN_SP=0x8000000070006010L;
    private static final long MARKER=0x9800L;
    private static final VolatileBits V_INPUT = new VolatileBits(
            0xfedcba9876543210L,0x8000000000001111L,0xf000000000002222L,0x8888888888888888L,0x9999999999999999L,0xaaaabbbbccccddddL,0x123456789abcdef0L,
            new Bits128(0x1000000000000100L,0xeffffffffffffeffL),
            new Bits128(0x1000000000000101L,0xeffffffffffffefeL),
            new Bits128(0x1000000000000102L,0xeffffffffffffefdL),
            new Bits128(0x1000000000000103L,0xeffffffffffffefcL),
            new Bits128(0x1000000000000104L,0xeffffffffffffefbL),
            new Bits128(0x1000000000000105L,0xeffffffffffffefaL));
    private static final VolatileBits V_ZERO = new VolatileBits(
            0xfedcba9876543210L,0x8000000000001111L,0x0000000000000000L,0x8888888888888888L,0x9999999999999999L,0xaaaabbbbccccddddL,0x123456789abcdef0L,
            new Bits128(0x1000000000000100L,0xeffffffffffffeffL),
            new Bits128(0x1000000000000101L,0xeffffffffffffefeL),
            new Bits128(0x1000000000000102L,0xeffffffffffffefdL),
            new Bits128(0x1000000000000103L,0xeffffffffffffefcL),
            new Bits128(0x1000000000000104L,0xeffffffffffffefbL),
            new Bits128(0x1000000000000105L,0xeffffffffffffefaL));
    private static final VolatileBits V_MOV = new VolatileBits(
            0xfedcba9876543210L,0xf000000000002222L,0xf000000000002222L,0x8888888888888888L,0x9999999999999999L,0xaaaabbbbccccddddL,0x123456789abcdef0L,
            new Bits128(0x1000000000000100L,0xeffffffffffffeffL),
            new Bits128(0x1000000000000101L,0xeffffffffffffefeL),
            new Bits128(0x1000000000000102L,0xeffffffffffffefdL),
            new Bits128(0x1000000000000103L,0xeffffffffffffefcL),
            new Bits128(0x1000000000000104L,0xeffffffffffffefbL),
            new Bits128(0x1000000000000105L,0xeffffffffffffefaL));
    private static final VolatileBits V_TAIL = new VolatileBits(
            0xf00000000000b001L,0x800000000000b002L,0x900000000000b003L,0x123400000000b004L,0x567800000000b005L,0x9abc00000000b00aL,0xdef000000000b00bL,
            new Bits128(0x3000000000000300L,0xcffffffffffffcffL),
            new Bits128(0x3000000000000301L,0xcffffffffffffcfeL),
            new Bits128(0x3000000000000302L,0xcffffffffffffcfdL),
            new Bits128(0x3000000000000303L,0xcffffffffffffcfcL),
            new Bits128(0x3000000000000304L,0xcffffffffffffcfbL),
            new Bits128(0x3000000000000305L,0xcffffffffffffcfaL));
    private static final NonvolatileBits N_INPUT = new NonvolatileBits(
            0x8000000000010101L,0xf000000000020202L,0x9000000000030303L,0x1234000000040404L,0xabcdef1200050505L,0x8000000000060606L,0xf000000000070707L,0x0fedcba900080808L,
            new Bits128(0x1000000000000606L,0xeffffffffffff9f9L));
    private static final NonvolatileBits N_FOREIGN = new NonvolatileBits(
            0x8000000000010100L,0xf000000000020202L,0x9000000000030303L,0x1234000000040404L,0xabcdef1200050505L,0x8000000000060606L,0xf000000000070707L,0x0fedcba900080808L,
            new Bits128(0x1000000000000606L,0xeffffffffffff9f9L));

    private static void check(boolean ok,String why) {
        if(!ok)throw new AssertionError(why);
    }
    private static byte[] filled(int count,int value) {
        byte[] result=new byte[count];
        for(int i=0;i<count;i++)result[i]=(byte)value;
        return result;
    }
    private static StaticFixture648.Ram initialRam() {
        StaticFixture648.Ram ram=new StaticFixture648.Ram();
        ram.seedBytes(0x0000000070005fc8L,filled(128,0x5a));
        ram.seedBytes(0x9800L,filled(4,0xcc));
        ram.seedBytes(0xf000000000002222L,filled(24,0xdd));
        ram.seedBytes(0x8000000000001111L,filled(24,0xee));
        ram.seed(SP,8,INITIAL_RET);
        return ram;
    }
    // These loops only expand the fixed literal fixture and write overlays to bytes.
    // They do not execute or reproduce any C0 instruction/control flow.
    private static void fillExpected(Map<Long,Byte> bytes,long address,int count,int value) {
        for(int i=0;i<count;i++)bytes.put(address+i,(byte)value);
    }
    private static void put64(Map<Long,Byte> bytes,long address,long value) {
        for(int i=0;i<8;i++)bytes.put(address+i,(byte)(value>>>(8*i)));
    }
    private static Map<Long,Byte> initialExpectedBytes() {
        Map<Long,Byte> bytes=new HashMap<>();
        fillExpected(bytes,0x0000000070005fc8L,128,0x5a);
        fillExpected(bytes,0x9800L,4,0xcc);
        fillExpected(bytes,0xf000000000002222L,24,0xdd);
        fillExpected(bytes,0x8000000000001111L,24,0xee);
        put64(bytes,0x0000000070006008L,0x0000000140123456L);
        return bytes;
    }
    private static Map<Long,Byte> callbackExpectedBytes(int markerValue) {
        Map<Long,Byte> bytes=initialExpectedBytes();
        bytes.put(0x9800L,(byte)markerValue);
        put64(bytes,0x0000000070006008L,0x1122334455667788L);
        return bytes;
    }
    private static void checkState(StaticFixture648.Ram ram,Map<Long,Byte> expected,
            List<StaticFixture648.Event> trace) {
        check(expected.size()==180,"literal owned-byte count");
        check(ram.fullBytes().equals(expected),"complete owned RAM/padding mismatch");
        check(ram.events.equals(trace),"complete access/port trace mismatch: "+ram.events);
    }
    private static DefaultStaticFp648Api.TailFrame expectedTail(QueueFp604Api.Mxcsr u) {
        return new DefaultStaticFp648Api.TailFrame(
                new GovernmentCrtBoundary185Api.Tail(0x8571c8L,
                        GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x40ec530L,
                        new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,V_MOV,N_INPUT)),true,u);
    }
    private static void checkTailPrefix(DefaultStaticFp648Api.TailFrame actual,
            DefaultStaticFp648Api.TailFrame expected,StaticFixture648.Ram ram,
            Map<Long,Byte> independentInitialBytes,int[] tailCount) {
        check(++tailCount[0]==1,"tail callback count");
        // The expected full record was created before target entry from literal banks.
        check(expected.equals(actual),"complete outgoing TailFrame/current DF mismatch");
        check(actual.preMxcsr()==expected.preMxcsr(),"outgoing current MXCSR object");
        ram.events.add(e("PORT_TAIL",0x8571c8L,0x40ec530L));
        checkState(ram,independentInitialBytes,List.of(e("PORT_TAIL",0x8571c8L,0x40ec530L)));
    }
    private abstract static class TailOnlyCalls implements DefaultStaticFp648Api.Calls {
        @Override public final QueueFp604Api.Outcome invoke(DefaultStaticFp648Api.CallFrame frame) {
            throw new AssertionError("C0 contains no CALL port");
        }
    }

    public static void zeroRdxNullCallsFreshRet() {
        StaticFixture648.Ram ram=initialRam();
        QueueFp604Api.Mxcsr u=new QueueFp604Api.Mxcsr(0,0);
        DefaultStaticFp648Api.Input input=new DefaultStaticFp648Api.Input(
                new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,V_ZERO,N_INPUT),true,u);
        // Fixture setup after Input construction; it is not an access event or callback.
        ram.seed(SP,8,ZERO_LIVE_RET);
        Map<Long,Byte> expectedBytes=initialExpectedBytes();
        put64(expectedBytes,0x0000000070006008L,0x8877665544332211L);
        List<StaticFixture648.Event> expectedTrace=List.of(
                e("R64",0x0000000070006008L,0x8877665544332211L));
        QueueFp604Api.Normal expected=new QueueFp604Api.Normal(new FullCopy437Api.CallResult(
                new GovernmentCrtBoundary185Api.NormalReturn(V_ZERO,0x8877665544332211L,
                        0x0000000070006010L,N_INPUT),true),u);
        QueueFp604Api.Outcome actual=DefaultReleaseWithFp648.fromSlot10(input,ram,null);
        check(expected.equals(actual),"zero full V/N/RIP/SP/DF/FP");
        check(actual instanceof QueueFp604Api.Normal,"zero must complete Normal");
        QueueFp604Api.Normal normal=(QueueFp604Api.Normal)actual;
        check(normal.postMxcsr()==u,"zero keeps SAME unknown MXCSR");
        checkState(ram,expectedBytes,expectedTrace);
    }

    public static void nonzeroSameTailNormal() {
        StaticFixture648.Ram ram=initialRam();
        Map<Long,Byte> before=initialExpectedBytes();
        Map<Long,Byte> expectedBytes=callbackExpectedBytes(0x55);
        List<StaticFixture648.Event> expectedTrace=List.of(
                e("PORT_TAIL",0x8571c8L,0x40ec530L),e("W8",0x9800L,0x55),
                e("W64",0x0000000070006008L,0x1122334455667788L));
        QueueFp604Api.Mxcsr u=new QueueFp604Api.Mxcsr(0,0);
        QueueFp604Api.Mxcsr p=new QueueFp604Api.Mxcsr(8,12);
        DefaultStaticFp648Api.Input input=new DefaultStaticFp648Api.Input(
                new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,V_INPUT,N_INPUT),true,u);
        DefaultStaticFp648Api.TailFrame expectedFrame=expectedTail(u);
        GovernmentCrtBoundary185Api.NormalReturn expectedNR=new GovernmentCrtBoundary185Api.NormalReturn(
                V_TAIL,FOREIGN_RIP,FOREIGN_SP,N_FOREIGN);
        QueueFp604Api.Normal offered=new QueueFp604Api.Normal(
                new FullCopy437Api.CallResult(expectedNR,false),p);
        int[] tailCount={0};
        DefaultStaticFp648Api.Calls calls=new TailOnlyCalls() {
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                checkTailPrefix(frame,expectedFrame,ram,before,tailCount);
                ram.writeByte(MARKER,0x55);
                ram.writeQword(SP,ALIAS_RET);
                return offered;
            }
        };
        QueueFp604Api.Outcome actual=DefaultReleaseWithFp648.fromSlot10(input,ram,calls);
        check(actual==offered,"tail Normal must be SAME complete foreign object");
        QueueFp604Api.Normal normal=(QueueFp604Api.Normal)actual;
        check(normal.base().normalReturn().equals(expectedNR),"tail complete changed V/N/RIP/SP");
        check(!normal.base().postDirectionFlagSet(),"tail foreign post DF");
        check(normal.postMxcsr()==p,"tail SAME partial post MXCSR");
        check(tailCount[0]==1,"one Normal tail");
        checkState(ram,expectedBytes,expectedTrace);
    }

    public static void nonzeroSameStopped() {
        StaticFixture648.Ram ram=initialRam();
        Map<Long,Byte> before=initialExpectedBytes();
        Map<Long,Byte> expectedBytes=callbackExpectedBytes(0x66);
        List<StaticFixture648.Event> expectedTrace=List.of(
                e("PORT_TAIL",0x8571c8L,0x40ec530L),e("W8",0x9800L,0x66),
                e("W64",0x0000000070006008L,0x1122334455667788L));
        QueueFp604Api.Mxcsr u=new QueueFp604Api.Mxcsr(0,0);
        DefaultStaticFp648Api.Input input=new DefaultStaticFp648Api.Input(
                new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,V_INPUT,N_INPUT),true,u);
        DefaultStaticFp648Api.TailFrame expectedFrame=expectedTail(u);
        QueueFp604Api.Snapshot expectedSnapshot=new QueueFp604Api.Snapshot(
                new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,V_MOV,N_INPUT),0x40ec530L,true,u);
        QueueFp604Api.Stopped offered=new QueueFp604Api.Stopped(
                QueueFp604Api.StopReason.MISSING_POST_STATE,expectedSnapshot,0,0x8571c8L);
        int[] tailCount={0};
        DefaultStaticFp648Api.Calls calls=new TailOnlyCalls() {
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                checkTailPrefix(frame,expectedFrame,ram,before,tailCount);
                ram.writeByte(MARKER,0x66);
                ram.writeQword(SP,ALIAS_RET);
                return offered;
            }
        };
        QueueFp604Api.Outcome actual=DefaultReleaseWithFp648.fromSlot10(input,ram,calls);
        check(actual==offered,"tail Stopped must be SAME foreign object");
        QueueFp604Api.Stopped stopped=(QueueFp604Api.Stopped)actual;
        check(stopped.reason()==QueueFp604Api.StopReason.MISSING_POST_STATE,"Stopped reason");
        check(stopped.snapshot().equals(expectedSnapshot),"complete explicit Stop snapshot");
        check(stopped.snapshot().mxcsr()==u,"Stopped SAME snapshot MXCSR");
        check(stopped.raisedConditionBits()==0&&stopped.originCallSiteRva()==0x8571c8L,
                "Stopped conditions and origin");
        check(tailCount[0]==1,"one Stopped tail");
        checkState(ram,expectedBytes,expectedTrace);
    }

    public static void nonzeroSameArbitraryException() {
        StaticFixture648.Ram ram=initialRam();
        Map<Long,Byte> before=initialExpectedBytes();
        Map<Long,Byte> expectedBytes=callbackExpectedBytes(0x77);
        List<StaticFixture648.Event> expectedTrace=List.of(
                e("PORT_TAIL",0x8571c8L,0x40ec530L),e("W8",0x9800L,0x77),
                e("W64",0x0000000070006008L,0x1122334455667788L));
        QueueFp604Api.Mxcsr u=new QueueFp604Api.Mxcsr(0,0);
        DefaultStaticFp648Api.Input input=new DefaultStaticFp648Api.Input(
                new GovernmentCrtBoundary185Api.Entry(IMAGE,SP,V_INPUT,N_INPUT),true,u);
        DefaultStaticFp648Api.TailFrame expectedFrame=expectedTail(u);
        UnsupportedOperationException sentinel=new UnsupportedOperationException("owned C0 foreign sentinel");
        int[] tailCount={0};
        DefaultStaticFp648Api.Calls calls=new TailOnlyCalls() {
            @Override public QueueFp604Api.Outcome tail(DefaultStaticFp648Api.TailFrame frame) {
                checkTailPrefix(frame,expectedFrame,ram,before,tailCount);
                ram.writeByte(MARKER,0x77);
                ram.writeQword(SP,ALIAS_RET);
                throw sentinel;
            }
        };
        try {
            DefaultReleaseWithFp648.fromSlot10(input,ram,calls);
            throw new AssertionError("foreign exception did not escape");
        } catch(RuntimeException actual) {
            check(actual==sentinel,"same arbitrary exception identity");
        }
        check(tailCount[0]==1,"one throwing tail");
        // Arbitrary throw supplies no post-register/DF/FP Snapshot.
        checkState(ram,expectedBytes,expectedTrace);
    }

    public static int verify() {
        zeroRdxNullCallsFreshRet();
        nonzeroSameTailNormal();
        nonzeroSameStopped();
        nonzeroSameArbitraryException();
        return 4;
    }
    public static void main(String[] args) {System.out.println(verify());}
}
