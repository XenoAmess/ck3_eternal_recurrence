package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.HashMap;
import java.util.Map;
import java.util.OptionalLong;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadIdlerRootPublication175.Invocation;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

/** New returning paths through real gate/bind/getter, supplied software inputs only. */
public final class WindowValueReturnPathsWitness178Test {
    // Strict fixture reused unchanged; both returning path witnesses are new.
    private static final long B = 0x100000000L;
    private static final long ROOT = 0x200000000L;
    private static final long SINGLETON = 0x300000000L;
    private static final long VTABLE = 0x400000000L;
    private static final long KNOWN_GETTER = B + 0x3E098F0L;
    private static final long WINDOW_FIRST = 0x8000000000001234L;
    private static final long WINDOW_SECOND = 0xFEDCBA9876543210L;
    private static final long QUERY_TARGET = 0x9000000000000040L;
    private static final long OLD_TAIL = 0xA0000000000000E8L;
    private static final long NEW_TAIL = 0xB000000000000EE8L;

    @Test public void existingSingletonReadsRealGetterAndKeepsFull64ThroughQueryAndTail() {
        Fixture f = new Fixture().q(B + 0x5CB87F8L, ROOT).b(ROOT + 0x161L, 0x80)
                .q(B + 0x5C6A688L, SINGLETON).q(SINGLETON, VTABLE)
                .q(VTABLE + 0x10L, KNOWN_GETTER)
                // bind intercepts the actual known virtual call and executes the real8B getter.
                .q(B + 0x5C6A690L, WINDOW_FIRST)
                .q(B + 0x54D5040L, QUERY_TARGET)
                .call(new Invocation(0x3976B1BL, QUERY_TARGET, WINDOW_FIRST,
                        OptionalLong.empty(), false), 2L, null)
                .q(B + 0x54D50E8L, OLD_TAIL)
                .call(new Invocation(0x3976B48L, OLD_TAIL, WINDOW_FIRST,
                        OptionalLong.of(0x1001L), true), 0L, null);
        LoadIdlerVirtualGate178.run3976ac0(B, f, LoadIdlerWindowValueConsumer178.bind(B, f, f));
        f.done();
    }

    @Test public void freshAllocationPublishesBeforeGetterAndReadsTailAfterOpaqueMutation() {
        Fixture f = new Fixture().track(B + 0x54D50E8L, OLD_TAIL);
        f.q(B + 0x5CB87F8L, ROOT).b(ROOT + 0x161L, 1).q(B + 0x5C6A688L, 0L)
                .call(new Invocation(0x3976AF1L, B + 0x4223B94L, 8L,
                        OptionalLong.empty(), false), SINGLETON, null)
                .w(B + 0x5C6A688L, SINGLETON).w(SINGLETON, B + 0x499F998L)
                .q(SINGLETON, B + 0x499F998L).q(B + 0x499F9A8L, KNOWN_GETTER)
                // This Memory read must occur; there is no fake external virtual return.
                .q(B + 0x5C6A690L, WINDOW_SECOND)
                .q(B + 0x54D5040L, QUERY_TARGET)
                .call(new Invocation(0x3976B1BL, QUERY_TARGET, WINDOW_SECOND,
                        OptionalLong.empty(), false), 1L,
                        () -> f.patch(B + 0x54D50E8L, NEW_TAIL))
                .q(B + 0x54D50E8L, NEW_TAIL)
                .call(new Invocation(0x3976B33L, NEW_TAIL, WINDOW_SECOND,
                        OptionalLong.of(0L), true), 0L, null);
        LoadIdlerVirtualGate178.run3976ac0(B, f, LoadIdlerWindowValueConsumer178.bind(B, f, f));
        f.done();
    }

private static final class Fixture implements LoadIdlerVirtualGate178.Memory, LoadIdlerVirtualGate178.Ports {
    private sealed interface Step { }
    private record PtrRead(long address, long value) implements Step { }
    private record ByteRead(long address, int value) implements Step { }
    private record Write64(long address, long value) implements Step { }
    private record Call(Invocation expected, long suppliedRax, Runnable after) implements Step { }

    private final ArrayDeque<Step> expected = new ArrayDeque<>();
    private final Map<Long, Long> storage = new HashMap<>();

    Fixture q(long address, long value) {
        expected.addLast(new PtrRead(address, value));
        return this;
    }

    Fixture b(long address, int value) {
        expected.addLast(new ByteRead(address, value));
        return this;
    }

    Fixture w(long address, long value) {
        expected.addLast(new Write64(address, value));
        return this;
    }

    Fixture call(Invocation expectedCall, long suppliedRax, Runnable after) {
        expected.addLast(new Call(expectedCall, suppliedRax, after));
        return this;
    }

    Fixture track(long address, long initialValue) {
        storage.put(address, initialValue);
        return this;
    }

    void patch(long address, long value) {
        storage.put(address, value);
    }

    void done() {
        assertEquals(0, expected.size());
    }

    public long readPointer(long address) {
        if (expected.isEmpty()) throw new AssertionError("Unexpected readPointer at " + address);
        Step step = expected.removeFirst();
        if (!(step instanceof PtrRead)) throw new AssertionError("Expected pointer read but got " + step.getClass().getSimpleName());
        PtrRead pr = (PtrRead) step;
        assertEquals(address, pr.address());
        if (storage.containsKey(address)) {
            assertEquals(pr.value(), storage.get(address).longValue());
            return storage.get(address);
        } else {
            return pr.value();
        }
    }

    public int readUnsigned8(long address) {
        if (expected.isEmpty()) throw new AssertionError("Unexpected readUnsigned8 at " + address);
        Step step = expected.removeFirst();
        if (!(step instanceof ByteRead)) throw new AssertionError("Expected byte read but got " + step.getClass().getSimpleName());
ByteRead br = (ByteRead) step;
assertEquals(address, br.address());
return br.value();
}

public void writeInt64(long address, long value) {
if (expected.isEmpty()) throw new AssertionError("Unexpected writeInt64 at " + address);
Step step = expected.removeFirst();
if (!(step instanceof Write64)) throw new AssertionError("Expected write but got " + step.getClass().getSimpleName());
Write64 wr = (Write64) step;
assertEquals(address, wr.address());
assertEquals(value, wr.value());
storage.put(address, value);
}

public long invoke(Invocation callObj) {
if (expected.isEmpty()) throw new AssertionError("Unexpected invoke at site " + callObj.siteRva());
Step step = expected.removeFirst();
if (!(step instanceof Call)) throw new AssertionError("Expected call but got " + step.getClass().getSimpleName());
Call c = (Call) step;
        assertEquals(c.expected(), callObj);
        // Run after action if present

if (c.after() != null) c.after().run();

return c.suppliedRax();
    }
}

}
