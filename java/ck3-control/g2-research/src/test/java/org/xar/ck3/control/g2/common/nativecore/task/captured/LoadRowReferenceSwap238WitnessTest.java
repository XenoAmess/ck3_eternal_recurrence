package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;

public final class LoadRowReferenceSwap238WitnessTest {
    static Bits128 x(long b) { return new Bits128(b, b + 1); }
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

    @Test void actualC784FastSwapUsesBothLoadedPointersAndOwnedFrame() {
        long image = 0x8800000100000000L;
        long preSP = 0xF700000000100000L;
        long entrySP = 0xF7000000000FFFF8L;
        long next = 0x880000010337C789L;
        VolatileBits incoming = new VolatileBits(
                0x9100000000000100L, 0xF700000000100050L,
                0x8900000000400010L, 0x9100000000000103L,
                0x9100000000000104L, 0x9100000000000105L,
                0x9100000000000106L,
                new Bits128(0xA100000000000000L, 0xA200000000000000L),
                new Bits128(0xA100000000000010L, 0xA200000000000010L),
                new Bits128(0xA100000000000020L, 0xA200000000000020L),
                new Bits128(0xA100000000000030L, 0xA200000000000030L),
                new Bits128(0xA100000000000040L, 0xA200000000000040L),
                new Bits128(0xA100000000000050L, 0xA200000000000050L));
        NonvolatileBits activeN = new NonvolatileBits(
                0x8900000000400000L, 0xF700000000100071L,
                0xB100000000000002L, 0xB100000000000003L,
                0xB100000000000004L, 0xB100000000000005L,
                0xB100000000000006L, 0xB100000000000007L,
                new Bits128(0xB200000000000000L, 0xB300000000000000L));
        VolatileBits expectedPost = q(incoming,
                0xD199AABBCCDDEEFFL, 0xC122334455667788L,
                0x8900000000400010L, 0x9100000000000103L,
                0x9100000000000104L, 0x9100000000000105L,
                0x9100000000000106L);
        List<Op> expected = List.of(
                new Op("wq", 0xF7000000000FFFF8L, 0x880000010337C789L),
                new Op("wq", 0xF700000000100008L, 0x8900000000400000L),
                new Op("wq", 0xF7000000000FFFF0L, 0xB100000000000003L),
                new Op("rq", 0xF700000000100088L, 0xC122334455667788L),
                new Op("rq", 0x8900000000400048L, 0xD199AABBCCDDEEFFL),
                new Op("wq", 0xF700000000100088L, 0xD199AABBCCDDEEFFL),
                new Op("wq", 0x8900000000400048L, 0xC122334455667788L),
                new Op("rq", 0xF700000000100008L, 0x8900000000400000L),
                new Op("rq", 0xF7000000000FFFF0L, 0xB100000000000003L),
                new Op("rq", 0xF7000000000FFFF8L, 0x880000010337C789L));
        assertEquals(10, expected.size());
        assertEquals(preSP - 8, entrySP);
        assertEquals(image + 0x337C789L, next);
        assertEquals(activeN.rbpBits() - 0x21, incoming.rcxBits());
        assertEquals(activeN.rbxBits() + 0x10, incoming.rdxBits());
        Bytes memory = new Bytes();
        memory.putQ(0xF700000000100088L, 0xC122334455667788L);
        memory.putQ(0x8900000000400048L, 0xD199AABBCCDDEEFFL);
        Ports fallback = new Ports();
        Calls adapter = LoadRowReferenceSwap238Calls.bind(image, memory, fallback);
        assertTrue(memory.ops.isEmpty());
        memory.writeQword(entrySP, next);
        Call matching = new Call(0x337C784L, TargetKind.DIRECT_RVA,
                0xA636F0L, preSP, incoming, activeN);
        assertEquals(expectedPost, adapter.invoke(matching));
        assertEquals(expected, memory.ops);

        VolatileBits foreignReply = v(0xDA00000000001000L);
        List<Call> foreign = List.of(
                new Call(0x337C785L, TargetKind.DIRECT_RVA,
                        0xA636F0L, preSP, incoming, activeN),
                new Call(0x337C784L, TargetKind.DIRECT_RVA,
                        0xA636F1L, preSP, incoming, activeN),
                new Call(0x337C784L, TargetKind.INDIRECT_ABSOLUTE,
                        0xA636F0L, preSP, incoming, activeN));
        int[] foreignCalls = {0};
        fallback.invoke = call -> {
            assertTrue(foreignCalls[0] < foreign.size());
            assertSame(foreign.get(foreignCalls[0]++), call);
            return foreignReply;
        };
        for (Call call : foreign) assertSame(foreignReply, adapter.invoke(call));
        Entry foreignEntry = new Entry(image, entrySP, incoming, activeN);
        Tail foreignTail = new Tail(0x337C784L, TargetKind.DIRECT_RVA,
                0xA636F0L, foreignEntry);
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
        assertSame(foreignNR, adapter.tail(foreignTail));
        int[] gsCalls = {0};
        fallback.gs = () -> {
            gsCalls[0]++;
            return 0xFE0123456789ABCDL;
        };
        assertEquals(0xFE0123456789ABCDL, adapter.readGsQword58());
        assertEquals(3, foreignCalls[0]);
        assertEquals(1, tailCalls[0]);
        assertEquals(1, gsCalls[0]);
        assertEquals(expected, memory.ops);
    }
}
