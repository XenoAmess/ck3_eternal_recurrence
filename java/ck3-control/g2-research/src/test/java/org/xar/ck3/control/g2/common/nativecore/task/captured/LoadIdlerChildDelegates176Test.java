package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

/** Literal17B normal effect witnesses; return bits/unwind/natural callers are outside scope. */
public final class LoadIdlerChildDelegates176Test {
    private static final long SELF = 0x100000010L;
    private static final long CHILD = 0x200000000L;
    private static final long VTABLE = 0x300000000L;
    private static final long TARGET40 = 0x8000000000000042L;
    private static final long TARGET48 = 0xF000000000000048L;
    private sealed interface Step permits Read, Invoke { }
    private record Read(long address, long value) implements Step { }
    private record Invoke(LoadIdlerRootPublication175.Invocation expected,
            RuntimeException failure) implements Step { }

    private static final class Fixture implements LoadIdlerChildDelegates176.Memory,
            LoadIdlerRootPublication175.Ports {
        private final ArrayDeque<Step> steps = new ArrayDeque<>();
        private Fixture q(long address, long value) { steps.add(new Read(address, value)); return this; }
        private Fixture call(long site, long target, long receiver, RuntimeException failure) {
            steps.add(new Invoke(new LoadIdlerRootPublication175.Invocation(
                    site, target, receiver, OptionalLong.empty(), true), failure));
            return this;
        }
        @Override public long readPointer(long address) {
            Read read = assertInstanceOf(Read.class, steps.remove());
            assertEquals(read.address(), address);
            return read.value();
        }
        @Override public void invoke(LoadIdlerRootPublication175.Invocation actual) {
            Invoke invoke = assertInstanceOf(Invoke.class, steps.remove());
            assertEquals(invoke.expected(), actual);
            if (invoke.failure() != null) { throw invoke.failure(); }
        }
        private void done() { assertEquals(0, steps.size()); }
    }

    @Test public void bothNullChildrenReadOnlyTheirActualSelf10() {
        Fixture first = new Fixture().q(SELF + 0x10L, 0L);
        LoadIdlerChildDelegates176.forward383e4e0(SELF, first, first);
        first.done();
        Fixture second = new Fixture().q(SELF + 0x10L, 0L);
        LoadIdlerChildDelegates176.forward383e500(SELF, second, second);
        second.done();
    }

    @Test public void bothNonNullChildrenPreserveSlotAndTailSiteAndFullTargetBits() {
        Fixture first = new Fixture().q(SELF + 0x10L, CHILD).q(CHILD, VTABLE)
                .q(VTABLE + 0x40L, TARGET40).call(0x383E4ECL, TARGET40, CHILD, null);
        LoadIdlerChildDelegates176.forward383e4e0(SELF, first, first);
        first.done();
        Fixture second = new Fixture().q(SELF + 0x10L, CHILD).q(CHILD, VTABLE)
                .q(VTABLE + 0x48L, TARGET48).call(0x383E50CL, TARGET48, CHILD, null);
        LoadIdlerChildDelegates176.forward383e500(SELF, second, second);
        second.done();
    }

    @Test public void callbackFailurePropagatesSameObjectWithoutFollowingReads() {
        RuntimeException failure = new IllegalStateException("supplied callback failure");
        Fixture f = new Fixture().q(SELF + 0x10L, CHILD).q(CHILD, VTABLE)
                .q(VTABLE + 0x40L, TARGET40).call(0x383E4ECL, TARGET40, CHILD, failure);
        assertSame(failure, assertThrows(IllegalStateException.class,
                () -> LoadIdlerChildDelegates176.forward383e4e0(SELF, f, f)));
        f.done();
    }

    @Test public void sameEntryAndFixtureRereadChangedChildVtableAndTargetOnNextCall() {
        Fixture f = new Fixture().q(SELF + 0x10L, CHILD).q(CHILD, VTABLE)
                .q(VTABLE + 0x48L, TARGET48).call(0x383E50CL, TARGET48, CHILD, null)
                .q(SELF + 0x10L, 0x500000000L).q(0x500000000L, 0x600000000L)
                .q(0x600000048L, TARGET40).call(0x383E50CL, TARGET40, 0x500000000L, null);
        LoadIdlerChildDelegates176.forward383e500(SELF, f, f);
        LoadIdlerChildDelegates176.forward383e500(SELF, f, f);
        f.done();
    }
}
