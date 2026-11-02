package org.xar.ck3.research.m3.manualchain257;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.OptionalLong;
import org.xar.ck3.research.m3.callee246.Callee68d4Memory246;
import org.xar.ck3.research.m3.chain257.Fa90ReleaseChain257;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;

/** New supplied-DATA chain witnesses; no old Test entry, process or hardware claim. */
public final class Fa90ReleaseChainValidation257 {
    private static final long BASE = 0x140000000L;
    private static final long OUTER = 0x1000L;
    private static final long CURRENT = 0x2000L;
    private static final long TERMINAL = 0x9000L;
    private static final long ENTRY_RAX = 0xFEDCBA9876543210L;
    private static int checks;
    private static int events;

    private Fa90ReleaseChainValidation257() { }

    public static void main(String[] args) {
        completeChainObservesAtomicUpdateAndPreservesFailure();
        nullHeadPreservesRemainingCallKnownness();
        equal(events, 48, "new ordered event total");
        System.out.println("PASS groups=2 scenes=3 events=" + events + " checks=" + checks);
    }

    private static void completeChainObservesAtomicUpdateAndPreservesFailure() {
        List<Step> literal = fullPlan();
        equal(literal.size(), 25, "normal literal size");
        Script normal = seeded(literal, false);
        Fa90Api245.Input input = new Fa90Api245.Input(BASE, OUTER, 0L, ENTRY_RAX);
        Fa90ReleaseChain257.execute(normal, new Remainder(normal, input), input);
        normal.done();
        equal(normal.peek32(CURRENT + 0x10L), 0, "parent observes child's decrement");
        equal(normal.peek32(TERMINAL + 0x15CL), 0x7FFFFFFF, "wrapping exchange-add committed");
        equal(normal.peek64(OUTER + 0x90L), 0L, "original entry RDX cleanup");

        // Independent Oracle prefix: the twentieth event is the first child's XADD.
        Script failed = seeded(List.copyOf(literal.subList(0, 20)), true);
        RuntimeException caught = null;
        try {
            Fa90ReleaseChain257.execute(failed, new Remainder(failed, input), input);
        } catch (RuntimeException failure) {
            caught = failure;
        }
        same(caught, failed.atomicMarker, "atomic exception identity");
        failed.done();
        equal(failed.peek32(CURRENT + 0x10L), 0, "prior child effects retained");
        equal(failed.peek32(TERMINAL + 0x15CL), Integer.MIN_VALUE, "failed XADD did not commit");
        equal(failed.peek64(OUTER + 0x90L), CURRENT, "no parent cleanup after child failure");
    }

    private static void nullHeadPreservesRemainingCallKnownness() {
        long entryRdx = 0xF100L;
        List<Step> literal = List.of(
                new Step("Q", OUTER + 0x90L, 0L, 0L),
                new Step("W", OUTER + 0x90L, entryRdx, 0L),
                new Step("P70", 0x424FAE7L, entryRdx, ENTRY_RAX));
        Script script = new Script(literal, false);
        script.seed64(OUTER + 0x90L, 0L);
        Fa90Api245.Input input = new Fa90Api245.Input(BASE, OUTER, entryRdx, ENTRY_RAX);
        Fa90ReleaseChain257.execute(script, new Remainder(script, input), input);
        script.done();
        equal(script.peek64(OUTER + 0x90L), entryRdx, "null-head cleanup retains entry value");
    }

    private static List<Step> fullPlan() {
        List<Step> literal = new ArrayList<>();
        literal.add(new Step("Q", OUTER + 0x90L, CURRENT, 0L));
        literal.add(new Step("A", CURRENT + 0x10L, -1L, 1L));
        literal.add(new Step("Q", CURRENT + 0xE0L, 0L, 0L));
        literal.add(new Step("Q", CURRENT + 0xF0L, 0L, 0L));
        literal.add(new Step("Q", CURRENT + 0xE8L, 0L, 0L));
        literal.add(new Step("Q", CURRENT + 0x100L, 0L, 0L));
        for (int row = 0; row < 6; row++) {
            long offset = row * 0x20L;
            literal.add(new Step("Q", CURRENT + 0x28L + offset, BASE + 0x542F498L, 0L));
            literal.add(new Step("Q", CURRENT + 0x20L + offset, 0L, 0L));
        }
        literal.add(new Step("Q", CURRENT + 0x120L, TERMINAL, 0L));
        literal.add(new Step("X", TERMINAL + 0x15CL, -1L, Integer.MIN_VALUE));
        literal.add(new Step("Q", OUTER + 0x90L, CURRENT, 0L));
        literal.add(new Step("Q", BASE + 0x5C5DCD8L, 0L, 0L));
        literal.add(new Step("I", CURRENT + 0x10L, 0L, 0L));
        literal.add(new Step("P66", 0x424FAD3L, CURRENT, BASE + 0x542F330L));
        literal.add(new Step("W", OUTER + 0x90L, 0L, 0L));
        return List.copyOf(literal);
    }

    private static Script seeded(List<Step> literal, boolean failExchange) {
        Script script = new Script(literal, failExchange);
        script.seed64(OUTER + 0x90L, CURRENT);
        script.seed32(CURRENT + 0x10L, 1);
        script.seed64(CURRENT + 0xE0L, 0L);
        script.seed64(CURRENT + 0xF0L, 0L);
        script.seed64(CURRENT + 0xE8L, 0L);
        script.seed64(CURRENT + 0x100L, 0L);
        for (int row = 0; row < 6; row++) {
            long offset = row * 0x20L;
            script.seed64(CURRENT + 0x28L + offset, BASE + 0x542F498L);
            script.seed64(CURRENT + 0x20L + offset, 0L);
        }
        script.seed64(CURRENT + 0x120L, TERMINAL);
        script.seed32(TERMINAL + 0x15CL, Integer.MIN_VALUE);
        script.seed64(BASE + 0x5C5DCD8L, 0L);
        return script;
    }

    private record Step(String operation, long address, long value, long extra) { }

    private static final class Script implements Callee68d4Memory246 {
        private final List<Step> literal;
        private final Map<Long, Byte> bytes = new HashMap<>();
        private final boolean failExchange;
        private final RuntimeException atomicMarker = new IllegalStateException("owned atomic marker257");
        private int cursor;

        private Script(List<Step> literal, boolean failExchange) {
            this.literal = List.copyOf(literal);
            this.failExchange = failExchange;
        }
        private void event(Step actual) {
            check(cursor < literal.size(), "unexpected extra event: " + actual);
            Step expected = literal.get(cursor);
            check(actual.equals(expected), "event " + cursor + " expected " + expected + " got " + actual);
            cursor++;
        }
        private long load(long address, int width) {
            long result = 0L;
            for (int i = 0; i < width; i++) {
                Byte value = bytes.get(address + i);
                check(value != null, "unseeded byte at " + Long.toHexString(address + i));
                result |= (value.byteValue() & 0xFFL) << (8 * i);
            }
            return result;
        }
        private void store(long address, long value, int width) {
            for (int i = 0; i < width; i++) {
                bytes.put(address + i, (byte) (value >>> (8 * i)));
            }
        }
        private void seed64(long address, long value) { store(address, value, 8); }
        private void seed32(long address, int value) { store(address, value, 4); }
        private long peek64(long address) { return load(address, 8); }
        private int peek32(long address) { return (int) load(address, 4); }
        private void done() {
            equal(cursor, literal.size(), "literal event exhaustion");
            events += cursor;
        }
        @Override public long readPointer(long address) {
            long value = load(address, 8);
            event(new Step("Q", address, value, 0L));
            return value;
        }
        @Override public int readInt32(long address) {
            int value = (int) load(address, 4);
            event(new Step("I", address, value, 0L));
            return value;
        }
        @Override public void writeInt64(long address, long value) {
            event(new Step("W", address, value, 0L));
            store(address, value, 8);
        }
        @Override public void writeInt32(long address, int value) {
            throw new AssertionError("unexpected split DWORD write");
        }
        @Override public void writeInt16(long address, int value) {
            throw new AssertionError("unexpected WORD write");
        }
        @Override public void atomicAddInt32(long address, int delta) {
            int old = (int) load(address, 4);
            event(new Step("A", address, delta, old));
            store(address, old + delta, 4);
        }
        @Override public int exchangeAddInt32(long address, int delta) {
            int old = (int) load(address, 4);
            event(new Step("X", address, delta, old));
            if (failExchange) { throw atomicMarker; }
            store(address, old + delta, 4);
            return old;
        }
    }

    private static final class Remainder implements Fa90Api245.Ports {
        private final Script script;
        private final Fa90Api245.Input input;
        private Remainder(Script script, Fa90Api245.Input input) {
            this.script = script;
            this.input = input;
        }
        @Override public void call42568fc(F8a8Api242.Memory memory, long site, long rcx, long rdx, long rax) {
            throw new AssertionError("first call must use the new composed chain");
        }
        @Override public void call42566fc(F8a8Api242.Memory memory, long site, long rcx, long rax) {
            same(memory, script, "remaining B374 Memory identity");
            script.event(new Step("P66", site, rcx, rax));
        }
        @Override public void call4256670(F8a8Api242.Memory memory, long site, long rcx,
                OptionalLong rdx, OptionalLong rax) {
            same(memory, script, "remaining tail Memory identity");
            check(OptionalLong.of(input.entryRdx()).equals(rdx), "original RDX remains known on null-head path");
            check(OptionalLong.of(input.entryRax()).equals(rax), "original full RAX remains known on null-head path");
            script.event(new Step("P70", site, rcx, rax.getAsLong()));
        }
    }

    private static void check(boolean value, String message) {
        checks++;
        if (!value) { throw new AssertionError(message); }
    }
    private static void equal(long actual, long expected, String message) {
        check(actual == expected, message + ": " + actual + " != " + expected);
    }
    private static void same(Object actual, Object expected, String message) {
        check(actual == expected, message);
    }
}
