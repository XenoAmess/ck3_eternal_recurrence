package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m4.Free61FullState201WitnessRunner.Image;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;

public final class Free61FullState201WitnessTest {
    private static final long I = 0x180000000L, PRE = 0x10010L;
    private static class RejectCalls implements Calls {
        @Override public VolatileBits invoke(Call c) { throw new AssertionError("unexpected call " + c); }
        @Override public NormalReturn tail(Tail t) { throw new AssertionError("unexpected tail"); }
        @Override public long readGsQword58() { throw new AssertionError("unexpected GS"); }
    }
    private static Map<Long,Integer> qword(long a, long v) {
        Map<Long,Integer> m = new HashMap<>(); Free61FullState201WitnessBook.q(m, a, v); return m;
    }
    @Test public void threeIndependentOriginalBodyWitnesses() {
        var witnesses = new Free61FullState201WitnessBook().witnesses();
        assertEquals(3, witnesses.size());
        for (var w : witnesses) Free61FullState201WitnessRunner.verify(w);
    }
    @Test public void twoRealNullCallerSitesKeepFullStateAndSingleExistingReturn() {
        VolatileBits v = Free61FullState201WitnessBook.v(0xFEDCBA9876543210L, 0L, 21);
        NonvolatileBits n = Free61FullState201WitnessBook.n(0x7766554433221100L, 21);
        for (long site : new long[]{0x424DC48L, 0x424DC6CL}) {
            Map<Long,Integer> seed = qword(PRE - 8L, I + site + 5L);
            Image image = new Image(seed);
            Calls bound = Free61FullState201Calls.bind(I, image, new RejectCalls());
            assertEquals(v, bound.invoke(new Call(site, TargetKind.DIRECT_RVA, 0x424E364L, PRE, v, n)));
            assertEquals(seed, image.snapshot());
            assertEquals(List.of(PRE - 8L), image.readQwordAddresses());
            assertEquals(List.of(), image.writeQwordAddresses());
        }
    }
    @Test public void foreignInvokeTailAndGsForwardExactObjects() {
        VolatileBits in = Free61FullState201WitnessBook.v(0x9000000000000001L, 0L, 22);
        VolatileBits out = Free61FullState201WitnessBook.v(0x8000000000000001L, 2L, 23);
        NonvolatileBits n = Free61FullState201WitnessBook.n(9L, 22);
        Entry e = new Entry(I, PRE, in, n);
        NormalReturn nr = new NormalReturn(out, 0xABCDL, PRE + 8L, n);
        List<Call> received = new ArrayList<>();
        Tail[] gotTail = new Tail[1];
        Calls fallback = new RejectCalls() {
            @Override public VolatileBits invoke(Call c) { received.add(c); return out; }
            @Override public NormalReturn tail(Tail t) { gotTail[0] = t; return nr; }
            @Override public long readGsQword58() { return 0xF000000000000001L; }
        };
        Image image = new Image(Map.of());
        Calls bound = Free61FullState201Calls.bind(I, image, fallback);
        Call[] foreign = {
            new Call(0x424DC48L, TargetKind.INDIRECT_ABSOLUTE, 0x424E364L, PRE, in, n),
            new Call(0x424DC49L, TargetKind.DIRECT_RVA, 0x424E364L, PRE, in, n),
            new Call(0x424DC6CL, TargetKind.DIRECT_RVA, 0x424E365L, PRE, in, n)
        };
        for (int j = 0; j < foreign.length; j++) {
            assertSame(out, bound.invoke(foreign[j])); assertSame(foreign[j], received.get(j));
        }
        Tail tail = new Tail(0x424DC48L, TargetKind.DIRECT_RVA, 0x424E364L, e);
        assertSame(nr, bound.tail(tail)); assertSame(tail, gotTail[0]);
        assertEquals(0xF000000000000001L, bound.readGsQword58());
        assertEquals(Map.of(), image.snapshot());
        assertEquals(List.of(), image.readQwordAddresses());
        assertEquals(List.of(), image.writeQwordAddresses());
    }
    @Test public void realMemoryCorruptionReachesReturnAndNonvolatileGuards() {
        VolatileBits in = Free61FullState201WitnessBook.v(0x3333444455556666L, 0x9000L, 24);
        NonvolatileBits n = Free61FullState201WitnessBook.n(0x1234567890ABCDEFL, 24);
        // Synthetic nonnull adapter inputs exercise reachable guards, not the natural null-only 199 edge.
        for (boolean corruptReturn : new boolean[]{false, true}) {
            Map<Long,Integer> seed = qword(PRE - 8L, I + 0x424DC48L + 5L);
            Free61FullState201WitnessBook.q(seed, I + 0x5C5DE30L, 0x5555L);
            Free61FullState201WitnessBook.q(seed, I + 0x43DA748L, 0x8877665544332211L);
            Image image = new Image(seed);
            Calls callback = new RejectCalls() {
                @Override public VolatileBits invoke(Call c) {
                    assertEquals(0x424E37AL, c.callSiteRva());
                    assertEquals(PRE - 0x30L, c.rspBits());
                    image.mutate(qword(corruptReturn ? PRE - 8L : PRE - 16L, 0xFEE1DEADL));
                    return Free61FullState201WitnessBook.v(0xABCD00000001L, 0x4444L, 25);
                }
            };
            Calls bound = Free61FullState201Calls.bind(I, image, callback);
            IllegalStateException ex = assertThrows(IllegalStateException.class, () -> bound.invoke(
                    new Call(0x424DC48L, TargetKind.DIRECT_RVA, 0x424E364L, PRE, in, n)));
            assertEquals(corruptReturn ? "returnRip mismatch" : "nonvolatile mismatch", ex.getMessage());
        }
    }
    @Test public void unsupportedOpaqueCallPropagatesAfterActualStackWrites() {
        VolatileBits in = Free61FullState201WitnessBook.v(0x1111222233334444L, 0x7000L, 26);
        NonvolatileBits n = Free61FullState201WitnessBook.n(0x1234432112344321L, 26);
        long entrySP = PRE - 8L;
        Map<Long,Integer> seed = qword(entrySP, 0x2222333344445555L);
        Free61FullState201WitnessBook.q(seed, I + 0x5C5DE30L, 0x8000L);
        Free61FullState201WitnessBook.q(seed, I + 0x43DA748L, 0x55667788L);
        Image image = new Image(seed);
        UnsupportedOperationException opaque = new UnsupportedOperationException("unimplemented target");
        Calls callback = new RejectCalls() {
            @Override public VolatileBits invoke(Call c) { throw opaque; }
        };
        assertSame(opaque, assertThrows(UnsupportedOperationException.class,
                () -> Free61FullState201.execute(new Entry(I, entrySP, in, n), image, callback)));
        assertEquals(List.of(entrySP - 8L, entrySP - 0x30L), image.writeQwordAddresses());
        Map<Long,Integer> expected = new HashMap<>(seed);
        Free61FullState201WitnessBook.q(expected, entrySP - 8L, n.rbxBits());
        Free61FullState201WitnessBook.q(expected, entrySP - 0x30L, I + 0x424E380L);
        assertEquals(expected, image.snapshot());
    }
}
