package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Literal data transposed from the independently frozen original122B oracle, not producer output. */
public final class GovernmentResizeBase203Witness {
    private static final long B=0x100000000L, S=0xC0000008L, RET=0x11223344778899AAL;
    private static final long PRE_SP=0xBFFFFFE0L, PUSH_SLOT=0xBFFFFFD8L;
    private static final NonvolatileBits N=new NonvolatileBits(
            0x2222000022220000L,0x2222000022220001L,0x2222000022220002L,0x2222000022220003L,
            0x2222000022220004L,0x2222000022220005L,0x2222000022220006L,0x2222000022220007L,
            vector(0x2222000022220008L));
    private static final VolatileBits INPUT=bits(0x1000,0,0,0);
    private static final VolatileBits DIRECT_POST=bits(0x2000L,0x70001000L,0xCAFE111122223333L,0xC0DE222233334444L);
    private static final VolatileBits FREE_POST=bits(0x3000L,0xDEAD000055556666L,0xABCD333344445555L,0xBCDE444455556666L);
    private static final VolatileBits ERROR_POST=bits(0x4000L,0x60004000L,0xCDEF555566667777L,0xDEF0666677778888L);
    private static final VolatileBits HEAP_SUCCESS=bits(0x5000L,0x70002000L,0xEFE1777788889999L,0xF0F288889999AAAAL);
    private static final VolatileBits RETRY_HEAP_ZERO=bits(0x6000L,0L,0x1020304050607080L,0x2030405060708090L);
    private static final VolatileBits RETRY_GATE_OK=bits(0x7000L,0xABCD000000000001L,0x30405060708090A0L,0x405060708090A0B0L);
    private static final VolatileBits RETRY_SIZE_OK=bits(0x8000L,0xBCDE000000000001L,0x5060708090A0B0C0L,0x60708090A0B0C0D0L);
    private static final VolatileBits RETRY_SUCCESS=bits(0x9000L,0x70003000L,0x708090A0B0C0D0E0L,0x8090A0B0C0D0E0F0L);
    private static final VolatileBits GATE_HEAP_ZERO=bits(0xA000L,0L,0x9010A0B0C0D0E0F0L,0xA020B0C0D0E0F001L);
    private static final VolatileBits GATE_LOW_ZERO=bits(0xB000L,0x1234567800000000L,0xB030C0D0E0F00112L,0xC040D0E0F0011223L);
    private static final VolatileBits GATE_ERROR=bits(0xC000L,0x60005000L,0xD050E0F001122334L,0xE060F00112233445L);
    private static final VolatileBits SIZE_HEAP_ZERO=bits(0xD000L,0L,0xF070011223344556L,0x1071122334455667L);
    private static final VolatileBits SIZE_GATE_OK=bits(0xE000L,0x2345678900000001L,0x2082233445566778L,0x3093344556677889L);
    private static final VolatileBits SIZE_LOW_ZERO=bits(0xF000L,0x3456789A00000000L,0x40A445566778899AL,0x50B5566778899AABL);
    private static final VolatileBits SIZE_ERROR=bits(0x10000L,0x60007000L,0x60C66778899AABBCL,0x70D778899AABBCCDL);
    private static int assertions;
    private GovernmentResizeBase203Witness() { }
    private record Cell(int width,long address,long value) { }
    private record Event(String operation,long address,long value) { }
    private record ExpectedCall(GovernmentCrtBoundary185Api.Call call,VolatileBits post,
            long physicalReturn,List<Cell> effects) { }
    private record Scene(String name,GovernmentCrtBoundary185Api.Entry entry,
            GovernmentCrtBoundary185Api.NormalReturn expected,List<Cell> seeds,
            List<ExpectedCall> calls,List<Event> events,List<Cell> after,int budgetCount) { }
    private static void equal(Object expected,Object actual,String label) {
        assertions++;
        if(!Objects.equals(expected,actual))throw new AssertionError(label+" expected="+expected+" actual="+actual);
    }
    // These helpers only assemble immutable records from already fixed literal data.
    private static VolatileBits v(long a,long c,long d,long r8,long r9,long r10,long r11,VolatileBits x) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,x.xmm0(),x.xmm1(),x.xmm2(),x.xmm3(),x.xmm4(),x.xmm5());
    }
    private static VolatileBits input(long ptr,long size) {
        return v(0xAAAA000011112222L,ptr,size,0x88889999AAAABBBBL,0x9999AAAABBBBCCCCL,
                0xAAAABBBBCCCCDDDDL,0xBBBBCCCCDDDDEEEEL,INPUT);
    }
    private static NonvolatileBits offeredN(long size,long ptr) {
        return new NonvolatileBits(size,N.rbpBits(),N.rsiBits(),ptr,N.r12Bits(),N.r13Bits(),N.r14Bits(),N.r15Bits(),N.xmm6());
    }

    private static Scene nullDirect() {
        return new Scene("NULL_DIRECT",
            new GovernmentCrtBoundary185Api.Entry(B,S,input(0L,0x28L),N),
            new GovernmentCrtBoundary185Api.NormalReturn(DIRECT_POST,RET,0xC0000010L,N),
            List.of(
                new Cell(8, 0xC0000008L, 0x11223344778899AAL)),
            List.of(
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251F64L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424FDA0L,PRE_SP,v(0xAAAA000011112222L,0x28L,0x28L,0x88889999AAAABBBBL,0x9999AAAABBBBCCCCL,0xAAAABBBBCCCCDDDDL,0xBBBBCCCCDDDDEEEEL,INPUT),offeredN(0x28L,0L)),DIRECT_POST,0x104251F69L,List.of())),
            List.of(
                new Event("WRITE_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("WRITE_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251F69L),
                new Event("READ_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("READ_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0xC0000008L, 0x11223344778899AAL)),
            List.of(),0);
    }
    private static Scene nonnullZero() {
        return new Scene("NONNULL_ZERO",
            new GovernmentCrtBoundary185Api.Entry(B,S,input(0x60001000L,0L),N),
            new GovernmentCrtBoundary185Api.NormalReturn(v(0,FREE_POST.rcxBits(),FREE_POST.rdxBits(),FREE_POST.r8Bits(),FREE_POST.r9Bits(),FREE_POST.r10Bits(),FREE_POST.r11Bits(),FREE_POST),RET,0xC0000010L,N),
            List.of(
                new Cell(8, 0xC0000008L, 0x11223344778899AAL)),
            List.of(
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251F70L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E364L,PRE_SP,v(0xAAAA000011112222L,0x60001000L,0L,0x88889999AAAABBBBL,0x9999AAAABBBBCCCCL,0xAAAABBBBCCCCDDDDL,0xBBBBCCCCDDDDEEEEL,INPUT),offeredN(0L,0x60001000L)),FREE_POST,0x104251F75L,List.of())),
            List.of(
                new Event("WRITE_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("WRITE_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251F75L),
                new Event("READ_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("READ_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0xC0000008L, 0x11223344778899AAL)),
            List.of(),0);
    }
    private static Scene tooLarge() {
        return new Scene("TOO_LARGE",
            new GovernmentCrtBoundary185Api.Entry(B,S,input(0x60001000L,0xFFFFFFFFFFFFFFE1L),N),
            new GovernmentCrtBoundary185Api.NormalReturn(v(0,ERROR_POST.rcxBits(),ERROR_POST.rdxBits(),ERROR_POST.r8Bits(),ERROR_POST.r9Bits(),ERROR_POST.r10Bits(),ERROR_POST.r11Bits(),ERROR_POST),RET,0xC0000010L,N),
            List.of(
                new Cell(8, 0xC0000008L, 0x11223344778899AAL),
                new Cell(8, 0x60004000L, 0xAABBCCDD11223344L)),
            List.of(
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251F7DL,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x423B18CL,PRE_SP,v(0xAAAA000011112222L,0x60001000L,0xFFFFFFFFFFFFFFE1L,0x88889999AAAABBBBL,0x9999AAAABBBBCCCCL,0xAAAABBBBCCCCDDDDL,0xBBBBCCCCDDDDEEEEL,INPUT),offeredN(0xFFFFFFFFFFFFFFE1L,0x60001000L)),ERROR_POST,0x104251F82L,List.of())),
            List.of(
                new Event("WRITE_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("WRITE_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251F82L),
                new Event("WRITE_DWORD", 0x60004000L, 12L),
                new Event("READ_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("READ_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0xC0000008L, 0x11223344778899AAL)),
            List.of(
                new Cell(8, 0x60004000L, 0xAABBCCDD0000000CL)),0);
    }
    private static Scene iatFirst() {
        return new Scene("IAT_FIRST",
            new GovernmentCrtBoundary185Api.Entry(B,S,input(0x60002000L,0x20L),N),
            new GovernmentCrtBoundary185Api.NormalReturn(HEAP_SUCCESS,RET,0xC0000010L,N),
            List.of(
                new Cell(8, 0xC0000008L, 0x11223344778899AAL),
                new Cell(8, 0x105C5DE30L, 0xF1000000A1000001L),
                new Cell(8, 0x1043DA388L, 0x00007FF011112222L)),
            List.of(
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251FB9L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x00007FF011112222L,PRE_SP,v(0xAAAA000011112222L,0xF1000000A1000001L,0L,0x60002000L,0x20L,0xAAAABBBBCCCCDDDDL,0xBBBBCCCCDDDDEEEEL,INPUT),offeredN(0x20L,0x60002000L)),HEAP_SUCCESS,0x104251FBFL,List.of())),
            List.of(
                new Event("WRITE_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("WRITE_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0x105C5DE30L, 0xF1000000A1000001L),
                new Event("READ_QWORD", 0x1043DA388L, 0x00007FF011112222L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251FBFL),
                new Event("READ_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("READ_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0xC0000008L, 0x11223344778899AAL)),
            List.of(),0);
    }
    private static Scene retryFresh() {
        return new Scene("RETRY_FRESH",
            new GovernmentCrtBoundary185Api.Entry(B,S,input(0x60003000L,0x30L),N),
            new GovernmentCrtBoundary185Api.NormalReturn(RETRY_SUCCESS,RET,0xC0000010L,N),
            List.of(
                new Cell(8, 0xC0000008L, 0x11223344778899AAL),
                new Cell(8, 0x105C5DE30L, 0xF2000000A2000002L),
                new Cell(8, 0x1043DA388L, 0x00007FF022223333L)),
            List.of(
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251FB9L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x00007FF022223333L,PRE_SP,v(0xAAAA000011112222L,0xF2000000A2000002L,0L,0x60003000L,0x30L,0xAAAABBBBCCCCDDDDL,0xBBBBCCCCDDDDEEEEL,INPUT),offeredN(0x30L,0x60003000L)),RETRY_HEAP_ZERO,0x104251FBFL,List.of()),
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251F95L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E250L,PRE_SP,v(0L,0x1020304050607080L,0x2030405060708090L,0x6008L,0x6009L,0x600AL,0x600BL,RETRY_HEAP_ZERO),offeredN(0x30L,0x60003000L)),RETRY_GATE_OK,0x104251F9AL,List.of()),
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251FA1L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424CFFCL,PRE_SP,v(0xABCD000000000001L,0x30L,0x405060708090A0B0L,0x7008L,0x7009L,0x700AL,0x700BL,RETRY_GATE_OK),offeredN(0x30L,0x60003000L)),RETRY_SIZE_OK,0x104251FA6L,List.of(
                new Cell(8, 0x105C5DE30L, 0xF3000000A3000003L),
                new Cell(8, 0x1043DA388L, 0x00007FF033334444L))),
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251FB9L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x00007FF033334444L,PRE_SP,v(0xBCDE000000000001L,0xF3000000A3000003L,0L,0x60003000L,0x30L,0x800AL,0x800BL,RETRY_SIZE_OK),offeredN(0x30L,0x60003000L)),RETRY_SUCCESS,0x104251FBFL,List.of())),
            List.of(
                new Event("WRITE_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("WRITE_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0x105C5DE30L, 0xF2000000A2000002L),
                new Event("READ_QWORD", 0x1043DA388L, 0x00007FF022223333L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251FBFL),
                new Event("BUDGET", 0x4251F95L, 0L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251F9AL),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251FA6L),
                new Event("WRITE_QWORD", 0x105C5DE30L, 0xF3000000A3000003L),
                new Event("WRITE_QWORD", 0x1043DA388L, 0x00007FF033334444L),
                new Event("READ_QWORD", 0x105C5DE30L, 0xF3000000A3000003L),
                new Event("READ_QWORD", 0x1043DA388L, 0x00007FF033334444L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251FBFL),
                new Event("READ_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("READ_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0xC0000008L, 0x11223344778899AAL)),
            List.of(
                new Cell(8, 0x105C5DE30L, 0xF3000000A3000003L),
                new Cell(8, 0x1043DA388L, 0x00007FF033334444L)),1);
    }
    private static Scene gateEaxZero() {
        return new Scene("GATE_EAX_ZERO",
            new GovernmentCrtBoundary185Api.Entry(B,S,input(0x60004000L,0x40L),N),
            new GovernmentCrtBoundary185Api.NormalReturn(v(0,GATE_ERROR.rcxBits(),GATE_ERROR.rdxBits(),GATE_ERROR.r8Bits(),GATE_ERROR.r9Bits(),GATE_ERROR.r10Bits(),GATE_ERROR.r11Bits(),GATE_ERROR),RET,0xC0000010L,N),
            List.of(
                new Cell(8, 0xC0000008L, 0x11223344778899AAL),
                new Cell(8, 0x105C5DE30L, 0xF4000000A4000004L),
                new Cell(8, 0x1043DA388L, 0x00007FF044445555L),
                new Cell(8, 0x60005000L, 0x11223344AABBCCDDL)),
            List.of(
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251FB9L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x00007FF044445555L,PRE_SP,v(0xAAAA000011112222L,0xF4000000A4000004L,0L,0x60004000L,0x40L,0xAAAABBBBCCCCDDDDL,0xBBBBCCCCDDDDEEEEL,INPUT),offeredN(0x40L,0x60004000L)),GATE_HEAP_ZERO,0x104251FBFL,List.of()),
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251F95L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E250L,PRE_SP,v(0L,0x9010A0B0C0D0E0F0L,0xA020B0C0D0E0F001L,0xA008L,0xA009L,0xA00AL,0xA00BL,GATE_HEAP_ZERO),offeredN(0x40L,0x60004000L)),GATE_LOW_ZERO,0x104251F9AL,List.of()),
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251F7DL,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x423B18CL,PRE_SP,v(0x1234567800000000L,0xB030C0D0E0F00112L,0xC040D0E0F0011223L,0xB008L,0xB009L,0xB00AL,0xB00BL,GATE_LOW_ZERO),offeredN(0x40L,0x60004000L)),GATE_ERROR,0x104251F82L,List.of())),
            List.of(
                new Event("WRITE_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("WRITE_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0x105C5DE30L, 0xF4000000A4000004L),
                new Event("READ_QWORD", 0x1043DA388L, 0x00007FF044445555L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251FBFL),
                new Event("BUDGET", 0x4251F95L, 0L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251F9AL),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251F82L),
                new Event("WRITE_DWORD", 0x60005000L, 12L),
                new Event("READ_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("READ_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0xC0000008L, 0x11223344778899AAL)),
            List.of(
                new Cell(8, 0x60005000L, 0x112233440000000CL)),1);
    }
    private static Scene sizeEaxZero() {
        return new Scene("SIZE_EAX_ZERO",
            new GovernmentCrtBoundary185Api.Entry(B,S,input(0x60006000L,0x50L),N),
            new GovernmentCrtBoundary185Api.NormalReturn(v(0,SIZE_ERROR.rcxBits(),SIZE_ERROR.rdxBits(),SIZE_ERROR.r8Bits(),SIZE_ERROR.r9Bits(),SIZE_ERROR.r10Bits(),SIZE_ERROR.r11Bits(),SIZE_ERROR),RET,0xC0000010L,N),
            List.of(
                new Cell(8, 0xC0000008L, 0x11223344778899AAL),
                new Cell(8, 0x105C5DE30L, 0xF5000000A5000005L),
                new Cell(8, 0x1043DA388L, 0x00007FF055556666L),
                new Cell(8, 0x60007000L, 0x55667788DDEEFF00L)),
            List.of(
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251FB9L,GovernmentCrtBoundary185Api.TargetKind.INDIRECT_ABSOLUTE,0x00007FF055556666L,PRE_SP,v(0xAAAA000011112222L,0xF5000000A5000005L,0L,0x60006000L,0x50L,0xAAAABBBBCCCCDDDDL,0xBBBBCCCCDDDDEEEEL,INPUT),offeredN(0x50L,0x60006000L)),SIZE_HEAP_ZERO,0x104251FBFL,List.of()),
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251F95L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424E250L,PRE_SP,v(0L,0xF070011223344556L,0x1071122334455667L,0xD008L,0xD009L,0xD00AL,0xD00BL,SIZE_HEAP_ZERO),offeredN(0x50L,0x60006000L)),SIZE_GATE_OK,0x104251F9AL,List.of()),
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251FA1L,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x424CFFCL,PRE_SP,v(0x2345678900000001L,0x50L,0x3093344556677889L,0xE008L,0xE009L,0xE00AL,0xE00BL,SIZE_GATE_OK),offeredN(0x50L,0x60006000L)),SIZE_LOW_ZERO,0x104251FA6L,List.of()),
                new ExpectedCall(new GovernmentCrtBoundary185Api.Call(0x4251F7DL,GovernmentCrtBoundary185Api.TargetKind.DIRECT_RVA,0x423B18CL,PRE_SP,v(0x3456789A00000000L,0x40A445566778899AL,0x50B5566778899AABL,0xF008L,0xF009L,0xF00AL,0xF00BL,SIZE_LOW_ZERO),offeredN(0x50L,0x60006000L)),SIZE_ERROR,0x104251F82L,List.of())),
            List.of(
                new Event("WRITE_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("WRITE_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0x105C5DE30L, 0xF5000000A5000005L),
                new Event("READ_QWORD", 0x1043DA388L, 0x00007FF055556666L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251FBFL),
                new Event("BUDGET", 0x4251F95L, 0L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251F9AL),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251FA6L),
                new Event("WRITE_QWORD", 0xBFFFFFD8L, 0x104251F82L),
                new Event("WRITE_DWORD", 0x60007000L, 12L),
                new Event("READ_QWORD", 0xC0000010L, 0x2222000022220000L),
                new Event("READ_QWORD", 0xC0000000L, 0x2222000022220003L),
                new Event("READ_QWORD", 0xC0000008L, 0x11223344778899AAL)),
            List.of(
                new Cell(8, 0x60007000L, 0x556677880000000CL)),1);
    }
    private static void writeCell(ObservedMemory m,Cell c) {
        if(c.width()==8)m.writeQword(c.address(),c.value());
        else if(c.width()==4)m.writeDword(c.address(),(int)c.value());
        else if(c.width()==1)m.writeByte(c.address(),(int)c.value());
        else throw new AssertionError("unexpected fixed cell width");
    }
    private static void seedCell(MemoryImage m,Cell c) {
        if(c.width()==8)m.writeQword(c.address(),c.value());
        else if(c.width()==4)m.writeDword(c.address(),(int)c.value());
        else if(c.width()==1)m.writeByte(c.address(),(int)c.value());
        else throw new AssertionError("unexpected seed width");
    }
    private static long cellValue(MemoryImage m,Cell c) {
        if(c.width()==8)return m.readQword(c.address());
        if(c.width()==4)return Integer.toUnsignedLong(m.readDword(c.address()));
        if(c.width()==1)return m.readUnsignedByte(c.address());
        throw new AssertionError("unexpected assertion width");
    }
    private static void run(Scene scene) {
        ObservedMemory memory=new ObservedMemory();
        for(Cell seed:scene.seeds())seedCell(memory.backing,seed);
        int[] index={0},budgets={0};
        GovernmentCrtBoundary185Api.Calls script=new GovernmentCrtBoundary185Api.Calls() {
            @Override public VolatileBits invoke(GovernmentCrtBoundary185Api.Call actual) {
                if(index[0]>=scene.calls().size())throw new AssertionError(scene.name()+" extra full Call "+actual);
                ExpectedCall expected=scene.calls().get(index[0]++);
                equal(expected.call(),actual,scene.name()+" full Call "+index[0]);
                equal(expected.physicalReturn(),memory.backing.readQword(PUSH_SLOT),scene.name()+" physical push "+index[0]);
                for(Cell effect:expected.effects())writeCell(memory,effect);
                return expected.post();
            }
            @Override public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail tail) {
                throw new AssertionError(scene.name()+" unexpected tail "+tail);
            }
            @Override public long readGsQword58() { throw new AssertionError(scene.name()+" unexpected GS"); }
        };
        GovernmentCrtBoundary185Api.LoopBudget budget=(header,guard)->{
            equal(0x4251F95L,header,scene.name()+" retry header");
            equal(0L,guard,scene.name()+" no memory guard operand");
            if(budgets[0]>=scene.budgetCount())throw new AssertionError(scene.name()+" extra retry budget");
            budgets[0]++;
            memory.events.add(new Event("BUDGET",header,guard));
        };
        var actual=GovernmentResizeBase203.execute(scene.entry(),memory,script,budget);
        equal(scene.expected(),actual,scene.name()+" complete V/N/XMM/RIP/SP");
        equal(scene.calls().size(),index[0],scene.name()+" exact port count");
        equal(scene.budgetCount(),budgets[0],scene.name()+" exact budget count");
        equal(scene.events(),memory.events,scene.name()+" exact shared memory/budget ordering");
        equal(RET,memory.backing.readQword(S),scene.name()+" actual return retained");
        equal(N.rbxBits(),memory.backing.readQword(0xC0000010L),scene.name()+" saved RBX");
        equal(N.rdiBits(),memory.backing.readQword(0xC0000000L),scene.name()+" saved RDI");
        equal(0,memory.backing.atomicDwords.size(),scene.name()+" no atomics");
        equal(0,memory.backing.atomicBytes.size(),scene.name()+" no byte atomics");
        for(Cell after:scene.after())equal(after.value(),cellValue(memory.backing,after),scene.name()+" fixed after-cell "+after.address());
    }
    public static void main(String[] args) {
        if(args.length!=0)throw new IllegalArgumentException("no arguments");
        assertions=0;
        for(Scene scene:List.of(nullDirect(),nonnullZero(),tooLarge(),iatFirst(),retryFresh(),gateEaxZero(),sizeEaxZero()))run(scene);
        System.out.println("OK: 7 new independent122B scenes, 15 full calls, 3 retry budgets; "+assertions+" explicit assertions; deep callees opaque");
    }
    /** No storage/CPU model: every method forwards to the existing owned fixture image. */
    private static final class ObservedMemory implements GovernmentCrtBoundary185Api.Memory {
        final MemoryImage backing=new MemoryImage();
        final List<Event> events=new ArrayList<>();
        @Override public int readDword(long a) {
            int v=backing.readDword(a);events.add(new Event("READ_DWORD",a,Integer.toUnsignedLong(v)));return v;
        }
        @Override public long readQword(long a) {
            long v=backing.readQword(a);events.add(new Event("READ_QWORD",a,v));return v;
        }
        @Override public int readUnsignedByte(long a) {
            int v=backing.readUnsignedByte(a);events.add(new Event("READ_BYTE",a,v));return v;
        }
        @Override public void writeDword(long a,int v) {
            events.add(new Event("WRITE_DWORD",a,Integer.toUnsignedLong(v)));backing.writeDword(a,v);
        }
        @Override public int lockedXaddDword(long a,int v) {
            events.add(new Event("XADD_DWORD",a,Integer.toUnsignedLong(v)));return backing.lockedXaddDword(a,v);
        }
        @Override public void writeQword(long a,long v) { events.add(new Event("WRITE_QWORD",a,v));backing.writeQword(a,v); }
        @Override public void writeByte(long a,int v) { events.add(new Event("WRITE_BYTE",a,v&255));backing.writeByte(a,v); }
        @Override public Bits128 read128(long a) {
            Bits128 v=backing.read128(a);events.add(new Event("READ128LOW",a,v.lowBits()));events.add(new Event("READ128HIGH",a+8,v.highBits()));return v;
        }
        @Override public void write128(long a,Bits128 v) {
            events.add(new Event("WRITE128LOW",a,v.lowBits()));events.add(new Event("WRITE128HIGH",a+8,v.highBits()));backing.write128(a,v);
        }
    }
}
