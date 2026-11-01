package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;

public final class LoadRowReferenceRebuild236WitnessTest {
    static Bits128 x(long b) { return new Bits128(b, b + 1L); }
    static VolatileBits v(long b) {
        return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,
                x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60));
    }
    static NonvolatileBits n(long b) {
        return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80));
    }
    static VolatileBits q(VolatileBits b,long a,long c,long d,
            long r8,long r9,long r10,long r11) {
        return new VolatileBits(a,c,d,r8,r9,r10,r11,
                b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());
    }
    static final class Ports implements Calls {
        java.util.function.Function<Call,VolatileBits> invoke = c -> {
            throw new AssertionError(c);
        };
        java.util.function.Function<Tail,NormalReturn> tail = t -> {
            throw new AssertionError(t);
        };
        java.util.function.LongSupplier gs = () -> {
            throw new AssertionError("GS58");
        };
        public VolatileBits invoke(Call c) { return invoke.apply(c); }
        public NormalReturn tail(Tail t) { return tail.apply(t); }
        public long readGsQword58() { return gs.getAsLong(); }
    }
    static final LoadRowReferenceCallee337b7e0199Api.Float32 NO_FP =
            new LoadRowReferenceCallee337b7e0199Api.Float32() {
        public int convertSignedDwordToFloatBits(int bits) {
            throw new AssertionError("CVTDQ2PS");
        }
        public int divideScalarFloatBits(int left,int right) {
            throw new AssertionError("DIVSS");
        }
        public boolean orderedAbove(int left,int right) {
            throw new AssertionError("COMISS");
        }
    };

    @Test void actualC7d7RebuildUsesFreshCapacityR10AndC0FastReturn() {
        long image = 0x8100000100000000L;
        long preSP = 0xF200000000100000L;
        long entrySP = preSP - 8;
        long workingSP = entrySP - 0x28;
        long map = 0x8300000000200000L;
        long outerNext = image + 0x337C7DCL;
        long capacityNext = image + 0x337C056L;
        VolatileBits incoming = q(v(0x9100000000001000L),
                0x9111222233334444L, map, 0x9222333344445555L,
                0x9333444455556666L, 0x9444555566667777L,
                0x9555666677778888L, 0x9666777788889999L);
        NonvolatileBits activeN = new NonvolatileBits(
                0x8D00000000300050L, preSP + 0x71, map,
                0x8D00000000300000L, 0x8D00000000300008L,
                0xFFFFFFFF80000009L, 0x8E00000000400000L,
                0x8F00000000500000L, x(0xA100000000006000L));
        long freshR10 = 0xCE00000000700000L;
        VolatileBits capacityReply = q(v(0xC100000000008000L),
                0xCDEF012300000000L, 0xC211223344556677L,
                0xC322334455667788L, 0xC433445566778899L,
                0xC5445566778899AAL, freshR10, 0xC766778899AABBCCL);
        VolatileBits capacityArgs = q(incoming, incoming.raxBits(), 0, 1,
                incoming.r8Bits(), incoming.r9Bits(), map, incoming.r11Bits());
        VolatileBits expectedPost = q(capacityReply, 0xFFFFFFFFL, freshR10, 0,
                capacityReply.r8Bits(), capacityReply.r9Bits(),
                freshR10, capacityReply.r11Bits());
        List<Op> expected = List.of(
                new Op("wq", entrySP, outerNext),
                new Op("rd", map + 0x14, 0xFFFFFFFFL),
                new Op("wq", workingSP - 8, capacityNext),
                new Op("wq", entrySP - 8, activeN.rsiBits()),
                new Op("rq", entrySP - 8, activeN.rsiBits()),
                new Op("rq", entrySP, outerNext));
        assertEquals(6, expected.size());
        assertNotEquals(map, freshR10);
        assertNotEquals(0L, capacityReply.raxBits());
        assertEquals(0, (int) capacityReply.raxBits());
        Bytes memory = new Bytes();
        memory.putD(map + 0x14, 0xFFFFFFFF);
        Ports fallback = new Ports();
        int[] capacityCalls = {0};
        int[] budgetCalls = {0};
        LoopBudget budget = (header, guard) -> {
            budgetCalls[0]++;
            throw new AssertionError("Unexpected loop budget callback");
        };
        fallback.invoke = call -> {
            assertEquals(1, ++capacityCalls[0]);
            assertEquals(new Call(0x337C051L, TargetKind.DIRECT_RVA,
                    0x86E160L, workingSP, capacityArgs, activeN), call);
            assertEquals(expected.subList(0, 3), memory.ops);
            return capacityReply;
        };
        Calls router = LoadRowReferenceRebuild236Calls.bind(
                image, memory, fallback, budget, NO_FP);
        assertTrue(memory.ops.isEmpty());
        assertEquals(0, capacityCalls[0]);
        // The real parent CALL owns this one push before the adapter is entered.
        memory.writeQword(entrySP, outerNext);
        Call matching = new Call(0x337C7D7L, TargetKind.DIRECT_RVA,
                0x337C040L, preSP, incoming, activeN);
        assertEquals(expectedPost, router.invoke(matching));
        assertEquals(expected, memory.ops);
        assertEquals(1, capacityCalls[0]);
        assertEquals(0, budgetCalls[0]);

        VolatileBits foreignV = v(0xDA00000000001000L);
        List<Call> foreign = List.of(
                new Call(0x337C7D8L, TargetKind.DIRECT_RVA,
                        0x337C040L, preSP, incoming, activeN),
                new Call(0x337C7D7L, TargetKind.DIRECT_RVA,
                        0x337C041L, preSP, incoming, activeN),
                new Call(0x337C7D7L, TargetKind.INDIRECT_ABSOLUTE,
                        0x337C040L, preSP, incoming, activeN));
        int[] foreignCalls = {0};
        fallback.invoke = call -> {
            assertTrue(foreignCalls[0] < foreign.size());
            assertSame(foreign.get(foreignCalls[0]++), call);
            return foreignV;
        };
        for (Call call : foreign) assertSame(foreignV, router.invoke(call));
        Entry foreignEntry = new Entry(image, preSP, incoming, activeN);
        Tail foreignTail = new Tail(0x337C065L, TargetKind.DIRECT_RVA,
                0x337C0C0L, foreignEntry);
        NormalReturn foreignNR = new NormalReturn(v(0xDB00000000002000L),
                0xDC11223344556677L, 0xDD22334455667788L,
                n(0xDE00000000003000L));
        int[] tailCalls = {0};
        fallback.tail = transfer -> {
            tailCalls[0]++;
            assertSame(foreignTail, transfer);
            assertSame(foreignEntry, transfer.entry());
            return foreignNR;
        };
        assertSame(foreignNR, router.tail(foreignTail));
        int[] gsCalls = {0};
        fallback.gs = () -> {
            gsCalls[0]++;
            return 0xFA0123456789ABCDL;
        };
        assertEquals(0xFA0123456789ABCDL, router.readGsQword58());
        assertEquals(3, foreignCalls[0]);
        assertEquals(1, tailCalls[0]);
        assertEquals(1, gsCalls[0]);
        assertEquals(1, capacityCalls[0]);
        assertEquals(0, budgetCalls[0]);
        assertEquals(expected, memory.ops);
    }
}
