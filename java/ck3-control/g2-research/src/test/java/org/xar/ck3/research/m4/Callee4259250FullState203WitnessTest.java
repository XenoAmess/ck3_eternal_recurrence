package org.xar.ck3.research.m4;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.research.m4.Free61FullState201WitnessBook.*;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m4.Free61FullState201WitnessRunner.Image;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185WitnessApi.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;

public final class Callee4259250FullState203WitnessTest {
    private static final long I=0x180000000L, PRE=0xA010L, ENTRY=PRE-8L;
    private static class Reject implements Calls {
        @Override public VolatileBits invoke(Call c) { throw new AssertionError("unexpected call"); }
        @Override public NormalReturn tail(Tail t) { throw new AssertionError("unexpected tail"); }
        @Override public long readGsQword58() { throw new AssertionError("unexpected GS"); }
    }
    private static Map<Long,Integer> word(long a,long value) { Map<Long,Integer> m=new HashMap<>(); q(m,a,value); return m; }
    @Test public void independentThreeSourceLiterals() {
        var book=new Callee4259250FullState203WitnessBook().witnesses(); assertEquals(3,book.size());
        for(var w:book) {
            Image image=new Image(w.memorySeed()); int[] cursor={0};
            Calls ports=new Reject() {
                @Override public VolatileBits invoke(Call c) {
                    assertTrue(cursor[0]<w.events().size());
                    CallStep step=assertInstanceOf(CallStep.class,w.events().get(cursor[0]++));
                    assertEquals(step.expected(),c); assertEquals(step.expectedMemoryBefore(),image.snapshot());
                    image.mutate(step.mutation()); return step.normalPost();
                }
                @Override public NormalReturn tail(Tail t) {
                    assertTrue(cursor[0]<w.events().size());
                    TailStep step=assertInstanceOf(TailStep.class,w.events().get(cursor[0]++));
                    assertEquals(step.expected(),t); assertEquals(step.expectedMemoryBefore(),image.snapshot());
                    image.mutate(step.mutation()); return step.normalPost();
                }
            };
            NormalReturn actual=Callee4259250FullState203.execute(w.entry(),image,ports);
            assertEquals(w.expected(),actual); assertEquals(w.expectedFinalBytes(),image.snapshot());
            assertEquals(w.events().size(),cursor[0]);
            if(w.entry().volatileBits().rcxBits()!=0L) {
                assertSame(w.expected(),actual); assertEquals(List.of(),image.writeQwordAddresses());
                assertEquals(List.of(w.entry().imageBaseBits()+0x5C5DE30L,w.entry().imageBaseBits()+0x43DA7C8L),image.readQwordAddresses());
            }
        }
    }
    @Test public void naturalCallerConsumesFullTailWithoutSecondPushOrPreRead() {
        VolatileBits in=v(0xABCDEF0123456789L,0x8000000000000001L,40),post=v(0xF123456789ABCDEFL,5L,41);
        NonvolatileBits n=n(0x8765432187654321L,40);
        Map<Long,Integer> seed=word(ENTRY,I+0x425B84DL); q(seed,I+0x5C5DE30L,0x1122334455667788L); q(seed,I+0x43DA7C8L,0x8877665544332211L);
        Image image=new Image(seed);
        Calls ports=new Reject() {
            @Override public NormalReturn tail(Tail t) {
                assertEquals(new Tail(0x4259282L,TargetKind.INDIRECT_ABSOLUTE,0x8877665544332211L,
                        new Entry(I,ENTRY,args(in,0x1122334455667788L,0L,in.rcxBits()),n)),t);
                return new NormalReturn(post,image.readQword(t.entry().rspBits()),t.entry().rspBits()+8L,n);
            }
        };
        Calls bound=Callee4259250FullState203Calls.bind(I,image,ports);
        assertSame(post,bound.invoke(new Call(0x425B848L,TargetKind.DIRECT_RVA,0x4259250L,PRE,in,n)));
        assertEquals(seed,image.snapshot()); assertEquals(List.of(),image.writeQwordAddresses());
        assertEquals(List.of(I+0x5C5DE30L,I+0x43DA7C8L,ENTRY),image.readQwordAddresses());
    }
    @Test public void foreignFrameTailAndGsForwardExactObjects() {
        VolatileBits in=v(1L,0L,42),post=v(2L,3L,43); NonvolatileBits n=n(4L,42);
        Call[] got={null}; Tail[] tailGot={null}; NormalReturn nr=new NormalReturn(post,5L,6L,n);
        Calls ports=new Reject() {
            @Override public VolatileBits invoke(Call c) { got[0]=c; return post; }
            @Override public NormalReturn tail(Tail t) { tailGot[0]=t; return nr; }
            @Override public long readGsQword58() { return 0xF000000000000001L; }
        };
        Image image=new Image(Map.of()); Calls bound=Callee4259250FullState203Calls.bind(I,image,ports);
        for(Call c:List.of(new Call(0x425B848L,TargetKind.INDIRECT_ABSOLUTE,0x4259250L,PRE,in,n),
                new Call(0x425B849L,TargetKind.DIRECT_RVA,0x4259250L,PRE,in,n),
                new Call(0x425B848L,TargetKind.DIRECT_RVA,0x4259251L,PRE,in,n))) {
            assertSame(post,bound.invoke(c)); assertSame(c,got[0]);
        }
        Tail t=new Tail(0x425B848L,TargetKind.DIRECT_RVA,0x4259250L,new Entry(I,ENTRY,in,n));
        assertSame(nr,bound.tail(t)); assertSame(t,tailGot[0]); assertEquals(0xF000000000000001L,bound.readGsQword58());
        assertEquals(List.of(),image.readQwordAddresses()); assertEquals(List.of(),image.writeQwordAddresses());
    }
    @Test public void opaqueFailureAndActualCorruptReturnCannotBecomeSuccess() {
        VolatileBits in=v(0x8877665544332211L,0L,44); NonvolatileBits n=n(0x1234567890ABCDEFL,44);
        Map<Long,Integer> seed=word(ENTRY,I+0x425B84DL); Image image=new Image(seed);
        UnsupportedOperationException failure=new UnsupportedOperationException("unknown original target");
        Calls ports=new Reject() { @Override public VolatileBits invoke(Call c) { throw failure; } };
        assertSame(failure,assertThrows(UnsupportedOperationException.class,
                ()->Callee4259250FullState203.execute(new Entry(I,ENTRY,in,n),image,ports)));
        assertEquals(List.of(ENTRY-0x30L),image.writeQwordAddresses());
        Map<Long,Integer> expected=new HashMap<>(seed); q(expected,ENTRY-0x30L,I+0x425925EL); assertEquals(expected,image.snapshot());
        // Synthetic null adapter input, not the natural nonnull Resize201 edge. Real RET memory is changed.
        Map<Long,Integer> seed2=new HashMap<>(seed); q(seed2,0x7000L,0xDEADBEEF01234567L); Image corrupted=new Image(seed2);
        int[] calls={0};
        Calls ports2=new Reject() {
            @Override public VolatileBits invoke(Call c) {
                calls[0]++;
                if(c.callSiteRva()==0x4259259L) return v(0x7000L,7L,45);
                assertEquals(0x4259264L,c.callSiteRva());
                corrupted.mutate(word(ENTRY,0xFEDCBA9876543210L)); return v(8L,9L,46);
            }
        };
        Calls bound=Callee4259250FullState203Calls.bind(I,corrupted,ports2);
        IllegalStateException ex=assertThrows(IllegalStateException.class,()->bound.invoke(new Call(0x425B848L,TargetKind.DIRECT_RVA,0x4259250L,PRE,in,n)));
        assertEquals("RIP mismatch",ex.getMessage()); assertEquals(2,calls[0]);
    }
}
