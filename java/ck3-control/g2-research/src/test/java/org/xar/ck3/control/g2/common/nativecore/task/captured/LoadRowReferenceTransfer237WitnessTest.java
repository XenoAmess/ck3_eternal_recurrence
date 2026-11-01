package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
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
public final class LoadRowReferenceTransfer237WitnessTest {
 static Bits128 x(long b) {return new Bits128(b,b+1L);}
 static VolatileBits v(long b) {return new VolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,x(b+10),x(b+20),x(b+30),x(b+40),x(b+50),x(b+60));}
 static NonvolatileBits n(long b) {return new NonvolatileBits(b,b+1,b+2,b+3,b+4,b+5,b+6,b+7,x(b+80));}
 static VolatileBits q(VolatileBits b,long a,long c,long d,long r8,long r9,long r10,long r11) {return new VolatileBits(a,c,d,r8,r9,r10,r11,b.xmm0(),b.xmm1(),b.xmm2(),b.xmm3(),b.xmm4(),b.xmm5());}
 static final class Ports implements Calls {
  java.util.function.Function<Call,VolatileBits> invoke=c->{throw new AssertionError(c);};
  java.util.function.Function<Tail,NormalReturn> tail=t->{throw new AssertionError(t);};
  java.util.function.LongSupplier gs=()->{throw new AssertionError("GS58");};
  public VolatileBits invoke(Call c) {return invoke.apply(c);}
  public NormalReturn tail(Tail t) {return tail.apply(t);}
  public long readGsQword58() {return gs.getAsLong();}
 }

 static final LoadRowReferenceCallee337b7e0199Api.Float32 NO_FP=new LoadRowReferenceCallee337b7e0199Api.Float32() {
  public int convertSignedDwordToFloatBits(int bits) {throw new AssertionError("CVTDQ2PS");}
  public int divideScalarFloatBits(int left,int right) {throw new AssertionError("DIVSS");}
  public boolean orderedAbove(int left,int right) {throw new AssertionError("COMISS");}
 };

    @Test void actualC71dNullSourcePreservesWholeVolatileExceptRcx() {
        long image = 0x8200000100000000L;
        long preSP = 0xF300000000100000L;
        long entrySP = preSP - 8;
        long source = 0x8300000000400010L;
        long next = image + 0x337C722L;
        VolatileBits incoming = q(v(0x9100000000001000L),
                0x9111111122222222L, preSP + 0x50, source,
                0x9333333344444444L, 0x9444444455555555L,
                0x9555555566666666L, 0x9666666677777777L);
        NonvolatileBits activeN = new NonvolatileBits(
                source - 0x10, preSP + 0x71, 0xA100000000002000L,
                0xA200000000003001L, source - 8, 0xFFFFFFFF80000009L,
                0xA300000000004000L, 0xA400000000005000L,
                x(0xA500000000006000L));
        VolatileBits expectedPost = q(incoming, incoming.raxBits(), 0, source,
                incoming.r8Bits(), incoming.r9Bits(),
                incoming.r10Bits(), incoming.r11Bits());
        List<Op> expected = List.of(
                new Op("wq", entrySP, next),
                new Op("wq", entrySP + 8, activeN.rbxBits()),
                new Op("wq", entrySP - 8, activeN.rdiBits()),
                new Op("rq", source + 0x38, 0),
                new Op("rq", entrySP + 8, activeN.rbxBits()),
                new Op("rq", entrySP - 8, activeN.rdiBits()),
                new Op("rq", entrySP, next));
        assertEquals(7, expected.size());
        Bytes memory = new Bytes();
        memory.putQ(source + 0x38, 0);
        Ports fallback = new Ports();
        Calls adapter = LoadRowReferenceTransfer237Calls.bind(image, memory, fallback);
        assertTrue(memory.ops.isEmpty());
        memory.writeQword(entrySP, next);
        Call matching = new Call(0x337C71DL, TargetKind.DIRECT_RVA,
                0x87C9B0L, preSP, incoming, activeN);
        assertEquals(expectedPost, adapter.invoke(matching));
        assertEquals(expected, memory.ops);

        VolatileBits foreignReply = v(0xDA00000000003000L);
        List<Call> foreign = List.of(
                new Call(0x337C71EL, TargetKind.DIRECT_RVA,
                        0x87C9B0L, preSP, incoming, activeN),
                new Call(0x337C71DL, TargetKind.DIRECT_RVA,
                        0x87C9B1L, preSP, incoming, activeN),
                new Call(0x337C71DL, TargetKind.INDIRECT_ABSOLUTE,
                        0x87C9B0L, preSP, incoming, activeN));
        int[] foreignCalls = {0};
        fallback.invoke = call -> {
            assertTrue(foreignCalls[0] < foreign.size());
            assertSame(foreign.get(foreignCalls[0]++), call);
            return foreignReply;
        };
        for (Call call : foreign) assertSame(foreignReply, adapter.invoke(call));
        Entry foreignEntry = new Entry(image, preSP, incoming, activeN);
        Tail foreignTail = new Tail(0x337C71DL, TargetKind.DIRECT_RVA,
                0x87C9B0L, foreignEntry);
        NormalReturn foreignNR = new NormalReturn(v(0xDB00000000004000L),
                0xDC11223344556677L, 0xDD22334455667788L,
                n(0xDE00000000005000L));
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
            return 0xFA11223344556677L;
        };
        assertEquals(0xFA11223344556677L, adapter.readGsQword58());
        assertEquals(3, foreignCalls[0]);
        assertEquals(1, tailCalls[0]);
        assertEquals(1, gsCalls[0]);
        assertEquals(expected, memory.ops);
    }

    @Test void actualC72fSelfAliasStillCopiesKeyBeforeSkippingPayload() {
        long image = 0x8500000100000000L;
        long preSP = 0xF600000000200000L;
        long entrySP = preSP - 8;
        long object = 0x8700000000600000L;
        long payload = 0xC123456789ABCDEFL;
        long next = image + 0x337C734L;
        VolatileBits incoming = q(v(0x9200000000001000L),
                0x9211223344556677L, object, object,
                0x9433445566778899L, 0x95445566778899AAL,
                0x965566778899AABBL, 0x9766778899AABBCCL);
        NonvolatileBits activeN = new NonvolatileBits(
                object - 8, preSP + 0x71, 0xA600000000002000L,
                0xA700000000003001L, object, 0xFFFFFFFF8000000AL,
                0xA800000000004000L, object,
                x(0xA900000000006000L));
        VolatileBits expectedPost = q(incoming, object, object, object,
                incoming.r8Bits(), incoming.r9Bits(),
                incoming.r10Bits(), incoming.r11Bits());
        List<Op> expected = List.of(
                new Op("wq", entrySP, next),
                new Op("wq", entrySP + 8, activeN.rbxBits()),
                new Op("wq", entrySP + 0x10, activeN.rsiBits()),
                new Op("wq", entrySP - 8, activeN.rdiBits()),
                new Op("rq", object, payload),
                new Op("wq", object, payload),
                new Op("rq", entrySP + 0x10, activeN.rsiBits()),
                new Op("rq", entrySP + 8, activeN.rbxBits()),
                new Op("rq", entrySP - 8, activeN.rdiBits()),
                new Op("rq", entrySP, next));
        assertEquals(10, expected.size());
        Bytes memory = new Bytes();
        memory.putQ(object, payload);
        Ports fallback = new Ports();
        Calls adapter = LoadRowReferenceTransfer237Calls.bind(image, memory, fallback);
        assertTrue(memory.ops.isEmpty());
        memory.writeQword(entrySP, next);
        Call matching = new Call(0x337C72FL, TargetKind.DIRECT_RVA,
                0xE23EA0L, preSP, incoming, activeN);
        assertEquals(expectedPost, adapter.invoke(matching));
        assertEquals(expected, memory.ops);

        Call foreign = new Call(0x337C730L, TargetKind.DIRECT_RVA,
                0xE23EA0L, preSP, incoming, activeN);
        VolatileBits foreignReply = v(0xDF00000000003000L);
        int[] foreignCalls = {0};
        fallback.invoke = call -> {
            assertEquals(1, ++foreignCalls[0]);
            assertSame(foreign, call);
            return foreignReply;
        };
        assertSame(foreignReply, adapter.invoke(foreign));
        assertEquals(1, foreignCalls[0]);
        assertEquals(expected, memory.ops);
    }

}
