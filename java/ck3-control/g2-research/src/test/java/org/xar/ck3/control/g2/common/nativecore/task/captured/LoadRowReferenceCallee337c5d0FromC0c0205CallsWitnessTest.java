package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Bytes;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture.Op;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c5d0203WitnessTest.Ports;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c5d0203WitnessTest.x;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c5d0203WitnessTest.v;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c5d0203WitnessTest.nv;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c5d0203WitnessTest.q;
import static org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337c5d0203WitnessTest.NO_FP;

public final class LoadRowReferenceCallee337c5d0FromC0c0205CallsWitnessTest {
    @Test
    void actualC198ExistingKeyBindingAndForeignIdentity() {
        final long image = 0x190000000L;
        final long preSp = 0x700080000L;
        final long self = 0x241000L, table = 0x6B5000L;
        final long out = 0x8C7000L, keySlot = 0xAD9000L;
        final long hash = 0xD3C2000000000009L;
        final long row = 0x6B52D0L;
        Bytes m = new Bytes();
        m.putQ(self + 8, table);
        m.putD(self + 0x14, 15);
        m.putB(row + 4, 1);
        m.putQ(row + 8, 0xF13456789ABCDE01L);
        m.putQ(keySlot, 0xF13456789ABCDE01L);
        m.putQ(out, 0x1122334455667788L);
        m.putQ(out + 8, 0xFFEEDDCCBBAA9988L);
        VolatileBits incoming = new VolatileBits(
                0xE100000000000001L, self, out, hash, keySlot,
                0xE600000000000006L, 0xE700000000000007L,
                x(0xA100000000000010L), x(0xA200000000000020L),
                x(0xA300000000000030L), x(0xA400000000000040L),
                x(0xA500000000000050L), x(0xA600000000000060L));
        NonvolatileBits saved = nv(0xC200000000000020L);
        VolatileBits foreignV = v(0xD500000000000010L);
        NormalReturn foreignNr = new NormalReturn(foreignV,
                0xFD00000000000001L, 0xFC00000000000002L, nv(0xDB00000000000030L));
        List<Call> foreignCalls = new ArrayList<>();
        List<Tail> foreignTails = new ArrayList<>();
        int[] gsCalls = {0};
        Ports fallback = new Ports() {
            @Override public VolatileBits invoke(Call call) {
                foreignCalls.add(call);
                return foreignV;
            }
            @Override public NormalReturn tail(Tail transfer) {
                foreignTails.add(transfer);
                return foreignNr;
            }
            @Override public long readGsQword58() {
                gsCalls[0]++;
                return 0xFA123456789ABCDEL;
            }
        };
        int[] lookupSteps = {0};
        LoopBudget budget = (header, cursor) -> {
            assertEquals(0x337C615L, header);
            assertEquals(0x6B52D0L, cursor);
            assertEquals(0, lookupSteps[0]++);
        };
        Calls bound = LoadRowReferenceCallee337c5d0FromC0c0205Calls.bind(
                image, m, fallback, budget, NO_FP);
        Call selected = new Call(0x337C198L, TargetKind.DIRECT_RVA,
                0x337C5D0L, preSp, incoming, saved);
        m.writeQword(preSp - 8, image + 0x337C198L + 5);
        VolatileBits actual = bound.invoke(selected);
        VolatileBits expected = new VolatileBits(
                0x8C7000L, 15L, 0x8C7000L, 0xD3C2000000000009L, 0xAD9000L,
                9L, 0xE700000000000007L,
                x(0xA100000000000010L), x(0xA200000000000020L),
                x(0xA300000000000030L), x(0xA400000000000040L),
                x(0xA500000000000050L), x(0xA600000000000060L));
        assertEquals(expected, actual);
        assertEquals(1, lookupSteps[0]);
        assertTrue(foreignCalls.isEmpty());
        assertTrue(foreignTails.isEmpty());
        assertEquals(0, gsCalls[0]);
        assertEquals(0x6B52D0L, m.rawQ(out));
        assertEquals(0xFFEEDDCCBBAA9900L, m.rawQ(out + 8));
        assertEquals(List.of(new Op("wq", out, 0x6B52D0L)), m.writesAt(out));
        assertEquals(List.of(new Op("wb", out + 8, 0L)), m.writesAt(out + 8));
        assertEquals(List.of(new Op("wq", preSp - 8, image + 0x337C19DL)),
                m.writesAt(preSp - 8));
        assertTrue(m.ops.contains(new Op("rq", preSp - 8, image + 0x337C19DL)));
        assertEquals(saved.rbpBits(), m.rawQ(preSp - 16));
        assertEquals(saved.rbxBits(), m.rawQ(preSp - 24));
        assertEquals(saved.rsiBits(), m.rawQ(preSp - 32));
        assertEquals(saved.rdiBits(), m.rawQ(preSp - 40));
        assertEquals(saved.r13Bits(), m.rawQ(preSp - 48));
        assertEquals(saved.r14Bits(), m.rawQ(preSp - 56));
        assertEquals(saved.r15Bits(), m.rawQ(preSp - 64));

        int memoryOps = m.ops.size();
        Call wrongSite = new Call(0x337C193L, TargetKind.DIRECT_RVA,
                0x337C5D0L, preSp, incoming, saved);
        Call wrongTarget = new Call(0x337C198L, TargetKind.DIRECT_RVA,
                0x337C5D1L, preSp, incoming, saved);
        Call indirect = new Call(0x337C198L, TargetKind.INDIRECT_ABSOLUTE,
                0x337C5D0L, preSp, incoming, saved);
        assertSame(foreignV, bound.invoke(wrongSite));
        assertSame(foreignV, bound.invoke(wrongTarget));
        assertSame(foreignV, bound.invoke(indirect));
        assertEquals(3, foreignCalls.size());
        assertSame(wrongSite, foreignCalls.get(0));
        assertSame(wrongTarget, foreignCalls.get(1));
        assertSame(indirect, foreignCalls.get(2));
        Entry tailEntry = new Entry(image, preSp, incoming, saved);
        Tail foreignTail = new Tail(0x337C198L, TargetKind.DIRECT_RVA,
                0x337C5D0L, tailEntry);
        assertSame(foreignNr, bound.tail(foreignTail));
        assertEquals(1, foreignTails.size());
        assertSame(foreignTail, foreignTails.get(0));
        assertSame(tailEntry, foreignTails.get(0).entry());
        assertEquals(0xFA123456789ABCDEL, bound.readGsQword58());
        assertEquals(1, gsCalls[0]);
        assertEquals(memoryOps, m.ops.size());
        assertEquals(1, lookupSteps[0]);
    }
}
