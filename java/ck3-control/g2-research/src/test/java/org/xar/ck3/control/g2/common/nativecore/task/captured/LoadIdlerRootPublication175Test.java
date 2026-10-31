package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;

/** Literal read/write/call witnesses from the three normal RFs; no native callee execution. */
public final class LoadIdlerRootPublication175Test {
    private static final long B = 0x100000000L;
    private static final long SELF = 0x200000000L;
    private static final long G = B + 0x5C6A520L;
    private sealed interface Step permits Read, Write, Invoke { }
    private record Read(int width, long address, long value) implements Step { }
    private record Write(int width, long address, long value) implements Step { }
    private record Invoke(LoadIdlerRootPublication175.Invocation call) implements Step { }

    private static final class Fixture implements LoadIdlerRootPublication175.Memory,
            LoadIdlerRootPublication175.Ports {
        private final ArrayDeque<Step> steps = new ArrayDeque<>();
        private Fixture q(long a, long v) { steps.add(new Read(64, a, v)); return this; }
        private Fixture b(long a, int v) { steps.add(new Read(8, a, v)); return this; }
        private Fixture w(long a, long v) { steps.add(new Write(64, a, v)); return this; }
        private Fixture i(long site, long target, long receiver, OptionalLong rdx, boolean tail) {
            steps.add(new Invoke(new LoadIdlerRootPublication175.Invocation(site, target, receiver, rdx, tail)));
            return this;
        }
        private long read(int width, long address) {
            Read e = assertInstanceOf(Read.class, steps.remove());
            assertEquals(e.width(), width);
            assertEquals(e.address(), address);
            return e.value();
        }
        @Override public long readPointer(long address) { return read(64, address); }
        @Override public int readUnsigned8(long address) { return (int) read(8, address); }
        @Override public int readInt32(long address) { throw new AssertionError("unexpected DWORD read"); }
        @Override public void writeInt32(long address, int value) { throw new AssertionError("unexpected DWORD write"); }
        @Override public void writeInt64(long address, long value) {
            Write e = assertInstanceOf(Write.class, steps.remove());
            assertEquals(64, e.width());
            assertEquals(e.address(), address);
            assertEquals(e.value(), value);
        }
        @Override public void invoke(LoadIdlerRootPublication175.Invocation call) {
            Invoke e = assertInstanceOf(Invoke.class, steps.remove());
            assertEquals(e.call(), call);
        }
        private void done() { assertEquals(0, steps.size()); }
    }

    private static Fixture emptyPublishedChildren() {
        return new Fixture().w(G, SELF).q(SELF + 8L, 0L).q(SELF + 0x10L, 0L);
    }

    @Test public void firstPublisherKeepsCallOrderFreshChildrenAndConditionalTail() {
        Fixture zeroTailReceiver = emptyPublishedChildren()
                .b(B + 0x5C6A50DL, 0).b(B + 0x5430305L, 0).q(SELF + 0x18L, 0)
                .i(0xC20399L, B + 0x39292B0L, 0L, OptionalLong.empty(), true);
        LoadIdlerRootPublication175.publishC20350(B, SELF, zeroTailReceiver, zeroTailReceiver);
        zeroTailReceiver.done();

        Fixture firstGate = emptyPublishedChildren().b(B + 0x5C6A50DL, 9);
        LoadIdlerRootPublication175.publishC20350(B, SELF, firstGate, firstGate);
        firstGate.done();

        Fixture secondGate = emptyPublishedChildren().b(B + 0x5C6A50DL, 0).b(B + 0x5430305L, 1);
        LoadIdlerRootPublication175.publishC20350(B, SELF, secondGate, secondGate);
        secondGate.done();

        Fixture callbacks = new Fixture().w(G, SELF)
                .q(SELF + 8L, 0xA000L).q(0xA000L, 0xB000L).q(0xB028L, 0xC000L)
                .i(0xC2036CL, 0xC000L, 0xA000L, OptionalLong.empty(), false)
                .q(SELF + 0x10L, 0xD000L).q(0xD000L, 0xE000L).q(0xE028L, 0xF000L)
                .i(0xC2037BL, 0xF000L, 0xD000L, OptionalLong.empty(), false)
                .b(B + 0x5C6A50DL, 0).b(B + 0x5430305L, 0).q(SELF + 0x18L, 0x1234L)
                .i(0xC20399L, B + 0x39292B0L, 0x1234L, OptionalLong.empty(), true);
        LoadIdlerRootPublication175.publishC20350(B, SELF, callbacks, callbacks);
        callbacks.done();
    }

    @Test public void secondPublisherDistinguishesFirstCallAndFreshSecondTail() {
        Fixture callbacks = new Fixture().w(G, SELF)
                .q(SELF + 8L, 0xA000L).q(0xA000L, 0xB000L).q(0xB028L, 0xC000L)
                .i(0x383E53CL, 0xC000L, 0xA000L, OptionalLong.empty(), false)
                .q(SELF + 0x10L, 0xD000L).q(0xD000L, 0xE000L).q(0xE028L, 0xF000L)
                .i(0x383E550L, 0xF000L, 0xD000L, OptionalLong.empty(), true);
        LoadIdlerRootPublication175.publish383e520(B, SELF, callbacks, callbacks);
        callbacks.done();

        Fixture noChildren = emptyPublishedChildren();
        LoadIdlerRootPublication175.publish383e520(B, SELF, noChildren, noChildren);
        noChildren.done();
    }

    @Test public void releaseOwnRootCallsChildrenWithKnownOneThenClearsOriginalSlots() {
        Fixture f = new Fixture().w(SELF, B + 0x49458D0L)
                .q(SELF + 8L, 0xA000L).q(0xA000L, 0xB000L).q(0xB000L, 0xC000L)
                .i(0x383E158L, 0xC000L, 0xA000L, OptionalLong.of(1L), false).w(SELF + 8L, 0L)
                .q(SELF + 0x10L, 0xD000L).q(0xD000L, 0xE000L).q(0xE000L, 0xF000L)
                .i(0x383E16FL, 0xF000L, 0xD000L, OptionalLong.of(1L), false).w(SELF + 0x10L, 0L)
                .q(G, SELF).w(G, 0L)
                .i(0x383E18EL, B + 0x383E8C0L, SELF + 0x30L, OptionalLong.empty(), false)
                .w(SELF, B + 0x49459F8L);
        LoadIdlerRootPublication175.release383e130(B, SELF, f, f);
        f.done();
    }

    @Test public void releaseForeignRootStillStoresSameValueAndSkipsNullChildClears() {
        Fixture f = new Fixture().w(SELF, B + 0x49458D0L)
                .q(SELF + 8L, 0L).q(SELF + 0x10L, 0L).q(G, 0xCAFEL).w(G, 0xCAFEL)
                .i(0x383E18EL, B + 0x383E8C0L, SELF + 0x30L, OptionalLong.empty(), false)
                .w(SELF, B + 0x49459F8L);
        LoadIdlerRootPublication175.release383e130(B, SELF, f, f);
        f.done();
    }
}
