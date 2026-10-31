package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;

/** Controlled Java observer wiring, not evidence of a natural Native publisher/delegate caller. */
public final class LoadPublisherChildDelegate176Test {
    private static final long B = 0x100000000L;
    private static final long ROOT = 0x200000000L;
    private static final long MIDDLE = 0x300000000L;
    private static final long GRANDCHILD = 0x400000000L;
    private static final long MID_VTABLE = 0x500000000L;
    private static final long GRAND_VTABLE = 0x600000000L;
    private static final long PUBLISH_TARGET = 0x8000000000000028L;
    private static final long DELEGATE_TARGET = 0x9000000000000048L;
    private sealed interface Step permits Read, Write64, Invoke { }
    private record Read(long address, long value) implements Step { }
    private record Write64(long address, long value) implements Step { }
    private record Invoke(LoadIdlerRootPublication175.Invocation expected) implements Step { }

    private static final class Fixture implements LoadIdlerRootPublication175.Memory,
            LoadIdlerChildDelegates176.Memory, LoadIdlerRootPublication175.Ports {
        private final ArrayDeque<Step> steps = new ArrayDeque<>();
        private Fixture q(long address, long value) { steps.add(new Read(address, value)); return this; }
        private Fixture w(long address, long value) { steps.add(new Write64(address, value)); return this; }
        private Fixture call(long site, long target, long receiver) {
            steps.add(new Invoke(new LoadIdlerRootPublication175.Invocation(
                    site, target, receiver, OptionalLong.empty(), true)));
            return this;
        }
        @Override public long readPointer(long address) {
            Read read = assertInstanceOf(Read.class, steps.remove());
            assertEquals(read.address(), address);
            return read.value();
        }
        @Override public int readInt32(long address) { throw new AssertionError("unexpected DWORD read"); }
        @Override public int readUnsigned8(long address) { throw new AssertionError("unexpected BYTE read"); }
        @Override public void writeInt32(long address, int value) { throw new AssertionError("unexpected DWORD write"); }
        @Override public void writeInt64(long address, long value) {
            Write64 write = assertInstanceOf(Write64.class, steps.remove());
            assertEquals(write.address(), address);
            assertEquals(write.value(), value);
        }
        @Override public void invoke(LoadIdlerRootPublication175.Invocation actual) {
            Invoke invoke = assertInstanceOf(Invoke.class, steps.remove());
            assertEquals(invoke.expected(), actual);
            if (actual.siteRva() == 0x383E550L) {
                // The test deliberately supplies this callback; the Native target identity remains unproved.
                LoadIdlerChildDelegates176.forward383e500(actual.rcx(), this, this);
            }
        }
        private void done() { assertEquals(0, steps.size()); }
    }

    @Test public void suppliedPublisherObserverInvokesRealDelegateBeforeReturning() {
        Fixture f = new Fixture().w(B + 0x5C6A520L, ROOT)
                .q(ROOT + 8L, 0L).q(ROOT + 0x10L, MIDDLE)
                .q(MIDDLE, MID_VTABLE).q(MID_VTABLE + 0x28L, PUBLISH_TARGET)
                .call(0x383E550L, PUBLISH_TARGET, MIDDLE)
                .q(MIDDLE + 0x10L, GRANDCHILD).q(GRANDCHILD, GRAND_VTABLE)
                .q(GRAND_VTABLE + 0x48L, DELEGATE_TARGET)
                .call(0x383E50CL, DELEGATE_TARGET, GRANDCHILD);
        LoadIdlerRootPublication175.publish383e520(B, ROOT, f, f);
        f.done();
    }
}
